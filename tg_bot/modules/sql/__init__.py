from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, Query
from tg_bot import DB_URI, KInit, log


class CachingQuery(Query):
    """
    A subclass of Query that implements caching using the cache-aside caching pattern.

    Attributes:
        cache (dict): A dictionary used for caching query results.

    Methods:
        __iter__(): Overrides the __iter__ method of the parent class to implement caching.
        cache_key(): Generates a cache key based on the query's SQL statement and parameters.
    """

    def __init__(self, *args, cache=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = cache or {}

    def __iter__(self):
        """
        Overrides the __iter__ method of the parent class to implement caching.

        Returns:
            iter: An iterator over the cached query results.
        """
        cache_key = self.cache_key()
        result = self.cache.get(cache_key)

        if result is None:
            result = list(super().__iter__())
            self.cache[cache_key] = result

        return iter(result)

    def cache_key(self):
        """
        Generates a cache key based on the query's SQL statement and parameters.

        Returns:
            str: The cache key.
        """
        stmt = self.with_labels().statement
        compiled = stmt.compile()
        params = compiled.params
        return " ".join([str(compiled)] + [str(params[k]) for k in sorted(params)])


if DB_URI and DB_URI.startswith("postgres://"):
    DB_URI = DB_URI.replace("postgres://", "postgresql://", 1)


def start() -> scoped_session:
    engine = create_engine(DB_URI, client_encoding="utf8", echo=KInit.DEBUG, pool_size=KInit.POSTGRES_POOL_SIZE, max_overflow=0)
    log.info("[PostgreSQL] Connecting to database......")
    BASE.metadata.bind = engine
    BASE.metadata.create_all(engine)
    return scoped_session(
        sessionmaker(bind=engine, autoflush=False, query_cls=CachingQuery)
    )


BASE = declarative_base()
try:
    SESSION: scoped_session = start()
except Exception as e:
    log.exception(f"[PostgreSQL] Failed to connect due to {e}")
    exit()

log.info("[PostgreSQL] Connection successful, session started.")
