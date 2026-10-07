import datetime as dt
import os
from pathlib import Path

import psycopg
from openpyxl import load_workbook
from psycopg import sql

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# 데이터로 유일성을 검증한 자연키. 중복 적재 방지용 UNIQUE 제약.
UNIQUE_KEYS = {
    "prbd01n001": ["pd_no", "pd_exg_mkt", "info_base_dt", "info_seq"],
    "pref01n001": ["pd_itm_no"],
    "pref02n001": ["pd_itm_no"],
    "prfd01n001": ["itm_no"],
}

# 스키마상 NOT NULL 이지만 실제 데이터에 빈 값이 있어 제약을 해제하는 컬럼
NULLABLE_OVERRIDES = {
    "pref01n001": {"pd_exg_mkt_cd"},  # 1,780행 중 3행 빈 값
    "prfd01n001": {"zrin_fd_ivst_risk_gcd"},  # 23,676행 중 14,987행 빈 값
}


def dsn() -> str:
    # SQLAlchemy 형식(postgresql+psycopg://)을 libpq 형식으로 변환
    return os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")


def read_schema(path: Path) -> list[dict]:
    ws = load_workbook(path, read_only=True).active
    rows = ws.iter_rows(values_only=True)
    header = next(rows)
    assert header[:5] == ("순번", "컬럼명", "데이터타입", "Nullable", "컬럼코멘트"), header
    return [
        {"name": r[1], "type": r[2], "nullable": r[3] == "YES", "comment": r[4]}
        for r in rows
        if r[1]
    ]


def to_text(v):
    """엑셀 셀 값을 COPY 용 문자열로. 빈 값/공백만 있는 값은 NULL."""
    if v is None:
        return None
    if isinstance(v, str):
        v = v.strip()
        return v or None
    if isinstance(v, bool):
        return str(v).lower()
    if isinstance(v, float):
        return repr(v)
    if isinstance(v, (dt.datetime, dt.date)):
        return v.strftime("%Y%m%d")
    return str(v)


def create_table(cur, table: str, columns: list[dict]) -> None:
    overrides = NULLABLE_OVERRIDES.get(table, set())
    defs = [sql.SQL("id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY")]
    for c in columns:
        nullable = c["nullable"] or c["name"] in overrides
        defs.append(
            sql.SQL("{} {}{}").format(
                sql.Identifier(c["name"]),
                sql.SQL(c["type"]),
                sql.SQL("" if nullable else " NOT NULL"),
            )
        )
    if table in UNIQUE_KEYS:
        defs.append(
            sql.SQL("CONSTRAINT {} UNIQUE ({})").format(
                sql.Identifier(f"{table}_nk"),
                sql.SQL(", ").join(map(sql.Identifier, UNIQUE_KEYS[table])),
            )
        )
    cur.execute(
        sql.SQL("CREATE TABLE IF NOT EXISTS {} ({})").format(
            sql.Identifier(table), sql.SQL(", ").join(defs)
        )
    )
    cur.execute(sql.SQL("COMMENT ON COLUMN {}.id IS {}").format(
        sql.Identifier(table), sql.Literal("대리키(1부터 시작)")
    ))
    for c in columns:
        if c["comment"]:
            cur.execute(
                sql.SQL("COMMENT ON COLUMN {}.{} IS {}").format(
                    sql.Identifier(table), sql.Identifier(c["name"]), sql.Literal(c["comment"])
                )
            )


def load_data(cur, table: str, columns: list[dict], path: Path) -> int:
    ws = load_workbook(path, read_only=True).active
    rows = ws.iter_rows(values_only=True)
    header = [h.strip() if isinstance(h, str) else h for h in next(rows)]
    names = [c["name"] for c in columns]
    missing = set(names) - set(header)
    extra = {h for h in header if h} - set(names)
    if missing or extra:
        raise ValueError(f"{path.name}: 스키마와 컬럼 불일치 missing={missing} extra={extra}")
    pos = [header.index(n) for n in names]

    cur.execute(sql.SQL("TRUNCATE {} RESTART IDENTITY").format(sql.Identifier(table)))
    copy_stmt = sql.SQL("COPY {} ({}) FROM STDIN").format(
        sql.Identifier(table), sql.SQL(", ").join(map(sql.Identifier, names))
    )
    n = 0
    with cur.copy(copy_stmt) as copy:
        for r in rows:
            if all(v is None for v in r):
                continue
            copy.write_row([to_text(r[i]) if i < len(r) else None for i in pos])
            n += 1
    return n


def main() -> None:
    schema_files = sorted(p for p in DATA_DIR.glob("*_schema.xlsx") if not p.name.startswith("~$"))
    with psycopg.connect(dsn()) as conn:
        for schema_path in schema_files:
            table = schema_path.name.removesuffix("_schema.xlsx")
            data_path = DATA_DIR / f"{table}_data.xlsx"
            columns = read_schema(schema_path)
            with conn.cursor() as cur:
                create_table(cur, table, columns)
                n = load_data(cur, table, columns, data_path) if data_path.exists() else 0
            conn.commit()
            print(f"{table}: {len(columns)} columns, {n} rows")


if __name__ == "__main__":
    main()
