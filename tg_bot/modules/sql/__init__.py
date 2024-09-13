import time
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, Query
from sqlalchemy.exc import SQLAlchemyError
from tg_bot import DB_URI, KInit, log

class CachingQuery(Query):
    def __init__(self, *args, cache=None, **kwargs):
        super().__init__(*args, ** kwargs)
        self.cache = cache or {}

    def __iter__(self):
        cache_key = self.cache_key()
        result = self.cache.get(cache_key)

        if result is None:
            result = list(super().__iter__())
            self.cache[cache_key] = result

        return iter(result)

    def cache_key(self):
        stmt = self.with_labels().statement
        compiled = stmt.compile()
        params = compiled.params
        return " ".join([str(compiled)] + [str(params[k]) for k in sorted(params)])

def get_db_uri():
    if DB_URI and DB_URI.startswith("postgres://"):
        return DB_URI.replace("postgres://", "postgresql://", 1)
    return DB_URI

def create_db_engine():
    return create_engine(
        get_db_uri(),
        client_encoding="utf8",
        echo=KInit.DEBUG,
        pool_size=KInit.POSTGRES_POOL_SIZE,
        max_overflow=KInit.POSTGRES_MAX_OVERFLOW,
        pool_timeout=KInit.POSTGRES_POOL_TIMEOUT,
        pool_recycle=KInit.POSTGRES_POOL_RECYCLE
    )

def start(max_retries=3, retry_delay=5):
    for attempt in range(max_retries):
        try:
            engine = create_db_engine()
            log.info("[PostgreSQL] Connecting to database...")
            BASE.metadata.bind = engine
            BASE.metadata.create_all(engine)
            return scoped_session(
                sessionmaker(bind=engine, autoflush=False, query_cls=CachingQuery)
            )
        except SQLAlchemyError as e:
            log.warning(f"[PostgreSQL] Connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                log.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                log.exception("[PostgreSQL] Failed to connect after maximum retries")
                raise

BASE = declarative_base()

try:
    SESSION: scoped_session = start()
    log.info("[PostgreSQL] Connection successful, session started.")
except Exception as e:
    log.exception(f"[PostgreSQL] Failed to start session: {e}")
    exit(1)
