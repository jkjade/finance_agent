"""질문을 상품 도메인(테이블) 하나로 분류한다."""

from app import llm
from app.domains import DOMAINS, Domain

ROUTER_TOOL = {
    "type": "function",
    "function": {
        "name": "select_domain",
        "description": "사용자 질문이 어떤 상품군에 대한 것인지 하나를 고른다.\n"
        + "\n".join(f"{d.key}: {d.name}" for d in DOMAINS.values())
        + "\nnone: 해당 없음",
        "parameters": {
            "type": "object",
            "properties": {"domain": {"type": "string", "enum": [*DOMAINS, "none"]}},
            "required": ["domain"],
        },
    },
}

SYSTEM = "너는 금융상품 질문 분류기다. 질문을 읽고 select_domain 도구로 상품군을 고른다."


def route(question: str) -> Domain | None:
    msg = llm.chat(
        [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}],
        tools=[ROUTER_TOOL],
        tool_choice={"type": "function", "function": {"name": "select_domain"}},
    )
    key = llm.parse_arguments(msg.tool_calls[0].function.arguments)["domain"]
    return DOMAINS.get(key)
