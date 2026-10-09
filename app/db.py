import psycopg

from app import config


def dsn() -> str:
    # SQLAlchemy 형식(postgresql+psycopg://)을 libpq 형식으로 변환
    return config.DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")


def get_conn() -> psycopg.Connection:
    return psycopg.connect(dsn())
