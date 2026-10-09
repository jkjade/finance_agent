"""DB 컬럼 코멘트를 읽어 Tool 에 넘길 필드 목록을 만든다."""

from dataclasses import dataclass
from functools import lru_cache

from app.db import get_conn


@dataclass(frozen=True)
class Field:
    name: str
    comment: str


@lru_cache
def get_fields(table: str) -> tuple[Field, ...]:
    """테이블의 컬럼(대리키 id 제외)과 코멘트."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT a.attname, col_description(a.attrelid, a.attnum)
            FROM pg_attribute a
            WHERE a.attrelid = %s::regclass AND a.attnum > 0 AND NOT a.attisdropped AND a.attname <> 'id'
            ORDER BY a.attnum
            """,
            (table,),
        ).fetchall()
    return tuple(Field(name, comment or "") for name, comment in rows)


def format_fields(fields: tuple[Field, ...]) -> list[str]:
    """`컬럼명: 컬럼코멘트` 형식."""
    return [f"{f.name}: {f.comment}" for f in fields]
