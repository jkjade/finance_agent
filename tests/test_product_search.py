import json

from app.domains import DOMAINS
from app.llm import parse_arguments
from app.schema import Field
from app.tools.product_search import LIMIT, build_query, build_search_tool, select_columns

BOND = DOMAINS["bond"]
FIELDS = (
    Field("pd_nm", "상품명/채권명"),
    Field("buy_yield", "매수수익률/매수금리"),
)


def test_select_columns_strips_comment_and_drops_unknown():
    args = {"select": ["pd_nm: 상품명/채권명", "buy_yield", "pd_fund_mgmt_co", "id"]}
    assert select_columns(FIELDS, args) == ["pd_nm", "buy_yield"]


def test_build_query():
    q = build_query(BOND, ["pd_nm", "buy_yield"]).as_string(None)
    assert q == f'SELECT "pd_nm", "buy_yield" FROM "prbd01n001" LIMIT {LIMIT}'


def test_tool_lists_fields_once_as_select_enum():
    fn = build_search_tool(BOND, FIELDS)["function"]
    assert fn["parameters"]["properties"]["select"]["items"]["enum"] == ["pd_nm: 상품명/채권명", "buy_yield: 매수수익률/매수금리"]
    assert json.dumps(fn, ensure_ascii=False).count("매수수익률/매수금리") == 1


def test_parse_arguments_accepts_str_and_dict():
    assert parse_arguments('{"select": ["pd_nm"]}') == {"select": ["pd_nm"]}
    assert parse_arguments({"select": ["pd_nm"]}) == {"select": ["pd_nm"]}
