"""상품 상세조회 Tool."""

from psycopg import sql

from app.db import get_conn


def get_product_detail(table: str, id: int, fields: list[str]) -> dict:
    query = sql.SQL("SELECT {} FROM {} WHERE id = %s").format(
        sql.SQL(", ").join(map(sql.Identifier, fields)), sql.Identifier(table)
    )
    with get_conn() as conn:
        cur = conn.execute(query, (id,))
        return dict(zip([d.name for d in cur.description], cur.fetchone()))
