from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.models import Base  # Import Base for metadata


class DatabaseManager:
    """SQLAlchemy based Database connection manager"""

    def __init__(self):
        self.engine = None
        self.SessionLocal = None

    def connect(self):
        """Establish database engines and session factories"""
        try:
            # 1. Oracle Engine (using oracledb)
            oracle_url = (
                f"oracle+oracledb://{settings.db_username}:"
                f"{settings.db_password}@{settings.db_host}:"
                f"{settings.db_port}/?service_name={settings.db_service_name}"
            )

            self.engine = create_engine(
                oracle_url,
                # Connection Pool Settings
                pool_pre_ping=True,  # Verify connections before use
                pool_size=5,  # Base pool size
                max_overflow=10,  # Max additional connections
                pool_recycle=3600,  # Recycle connections after 1 hour
                pool_timeout=30,  # Wait max 30s for connection
                echo_pool=False,  # Set to True for debugging
                # Query Settings
                echo=settings.debug,  # Log SQL queries in debug mode
            )

            # Event listener: log pool checkouts (optional)
            if settings.debug:

                @event.listens_for(self.engine, "connect")
                def receive_connect(dbapi_conn, connection_record):
                    print(f"New DB connection: {id(dbapi_conn)}")

            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

            # Note: We don't call Base.metadata.create_all() here
            # Database schema is managed by DBA, not by the application
            # ORM models are used for type safety and query building only

            print("SQLAlchemy Engine initialized successfully")
        except Exception as e:
            print(f"Database initialization error: {e}")
            raise

    def disconnect(self):
        """Dispose of the engine"""
        if self.engine:
            self.engine.dispose()
            print("Database engine disposed")

    def get_session(self) -> Session:
        """
        Get a new database session.
        DEPRECATED: Use get_db() dependency instead.
        """
        if not self.SessionLocal:
            self.connect()

        if self.SessionLocal is None:
            raise RuntimeError("Database session factory not initialized")

        return self.SessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope for a series of operations.

        Usage:
            with oracle_db.session_scope() as session:
                session.execute(...)
                # auto-commit on success, auto-rollback on error
        """
        if not self.SessionLocal:
            self.connect()

        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


class RedisDB:
    """Redis connection manager"""

    def __init__(self):
        self.client = None

    def connect(self):
        from redis import Redis

        try:
            self.client = Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=(settings.redis_password if settings.redis_password else None),
                decode_responses=True,
            )
            self.client.ping()
            print("Redis connected successfully")
        except Exception as e:
            print(f"Redis connection error: {e}")
            raise

    def disconnect(self):
        if self.client:
            self.client.close()
            print("Redis disconnected")

    def get_client(self):
        if not self.client:
            self.connect()
        return self.client


# Global instances
oracle_db = DatabaseManager()
redis_db = RedisDB()
