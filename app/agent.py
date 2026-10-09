"""질문 → 라우터(도메인 결정) → 해당 도메인 필드만 가진 상품 조회 Tool → 답변."""

import json

from app import llm
from app.router import route
from app.schema import get_fields
from app.tools.product_search import build_search_tool, search_products

MAX_TOOL_ROUNDS = 3

SYSTEM = (
    "너는 금융상품 조회 에이전트다."
    "조회 결과에 없는 내용은 지어내지 않는다. 결과가 없으면 조건을 완화해 다시 조회하거나, 없다고 답한다. "
    "수치는 조회된 값과 단위를 그대로 쓴다."
)

UNROUTED_ANSWER = "어떤 상품군(채권, 국내 ETF, 해외 ETF, 펀드)에 대한 질문인지 조금 더 구체적으로 알려주세요."


def _arguments_str(arguments) -> str:
    # 대화 이력에 다시 넣을 때는 OpenAI 형식(JSON 문자열)으로 통일
    return arguments if isinstance(arguments, str) else json.dumps(arguments, ensure_ascii=False)


def answer(question: str) -> str:
    domain = route(question)
    if domain is None:
        return UNROUTED_ANSWER

    fields = get_fields(domain.table)
    tool = build_search_tool(domain, fields)
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]

    for _ in range(MAX_TOOL_ROUNDS):
        msg = llm.chat(messages, tools=[tool])
        if not msg.tool_calls:
            return msg.content or ""
        messages.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": c.id,
                        "type": "function",
                        "function": {"name": c.function.name, "arguments": _arguments_str(c.function.arguments)},
                    }
                    for c in msg.tool_calls
                ],
            }
        )
        for call in msg.tool_calls:
            result = search_products(domain, fields, llm.parse_arguments(call.function.arguments))
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result, ensure_ascii=False, default=str)}
            )

    # 도구 호출 한도 도달: 지금까지의 결과로 답하게 한다
    return llm.chat(messages, tools=[tool], tool_choice="none").content or ""
