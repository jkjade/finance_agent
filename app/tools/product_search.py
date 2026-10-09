"""상품 조회 Tool.

LLM 은 조회할 컬럼(select)만 고르고,
SQL 은 이 모듈이 만든다.
"""

from decimal import Decimal

from psycopg import sql

from app.db import get_conn
from app.domains import Domain
from app.schema import Field, format_fields

LIMIT = 3


def build_search_tool(domain: Domain, fields: tuple[Field, ...]) -> dict:
    return {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                f"{domain.name} 상품을 조회한다."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "select": {
                        "type": "array",
                        "items": {"type": "string", "enum": format_fields(fields)},
                        "description": "조회할 컬럼 목록. 질문에 답하는 데 필요한 컬럼만 고른다.",
                    }
                },
                "required": ["select"],
            },
        },
    }


def build_query(domain: Domain, columns: list[str]) -> sql.Composed:
    return sql.SQL("SELECT {} FROM {} LIMIT {}").format(
        sql.SQL(", ").join(map(sql.Identifier, columns)), sql.Identifier(domain.table), sql.Literal(LIMIT)
    )


def _jsonable(v):
    return float(v) if isinstance(v, Decimal) else v


def select_columns(fields: tuple[Field, ...], args: dict) -> list[str]:
    # enum 값("컬럼명: 컬럼코멘트")에서 ':' 앞의 컬럼명만 쓰고, 테이블에 없는 컬럼은 뺀다
    names = {f.name for f in fields}
    return [c for c in (s.split(":", 1)[0].strip() for s in args.get("select", [])) if c in names]


def search_products(domain: Domain, fields: tuple[Field, ...], args: dict) -> dict:
    columns = select_columns(fields, args)
    if not columns:
        return {"count": 0, "rows": []}
    query = build_query(domain, columns)
    with get_conn() as conn:
        conn.read_only = True
        with conn.cursor() as cur:
            cur.execute(query)
            columns = [d.name for d in cur.description]
            rows = [{c: _jsonable(v) for c, v in zip(columns, r)} for r in cur.fetchall()]
    return {"count": len(rows), "rows": rows}
