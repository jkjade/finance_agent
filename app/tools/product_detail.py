"""상품 상세조회 Tool."""

from psycopg import sql

from app.db import get_conn

TABLES = ["prbd01n001", "pref01n001", "pref02n001", "prfd01n001"]


def load_fields() -> list[tuple[str, str]]:
    # DB 에서 (컬럼명, 코멘트) 목록을 읽는다 (4개 테이블 합집합)
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT ON (a.attname) a.attname, col_description(a.attrelid, a.attnum)
            FROM pg_attribute a
            WHERE a.attrelid = ANY(%s::regclass[]) AND a.attnum > 0 AND NOT a.attisdropped AND a.attname <> 'id'
            ORDER BY a.attname
            """,
            (TABLES,),
        ).fetchall()
    return rows


FIELDS = load_fields()


TOOL = {
    "type": "function",
    "function": {
        "name": "get_product_detail",
        "description": "상품 하나를 id 로 조회해 지정한 컬럼 값을 가져온다.",
        "parameters": {
            "type": "object",
            "properties": {
                "table": {
                    "type": "string",
                    "enum": TABLES,
                    "description": "prbd01n001: 국내 채권, pref01n001: 국내 ETF, pref02n001: 해외 ETF, prfd01n001: 펀드",
                },
                "id": {"type": "integer", "description": "상품 id"},
                "fields": {
                    "type": "array",
                    "items": {"type": "string", "enum": [name for name, _ in FIELDS]},
                    "description": "조회할 컬럼 목록. 컬럼명: 설명\n" + "\n".join(f"{n}: {c}" for n, c in FIELDS),
                },
            },
            "required": ["table", "id", "fields"],
        },
    },
}


def get_product_detail(table: str, id: int, fields: list[str]) -> dict:
    query = sql.SQL("SELECT {} FROM {} WHERE id = %s").format(
        sql.SQL(", ").join(map(sql.Identifier, fields)), sql.Identifier(table)
    )
    with get_conn() as conn:
        cur = conn.execute(query, (id,))
        return dict(zip([d.name for d in cur.description], cur.fetchone()))
