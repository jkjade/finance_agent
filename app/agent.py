"""사용법: python -m app.agent "질문" """

import json
import sys

from openai import OpenAI

from app import config
from app.tools import product_detail

client = OpenAI(api_key=config.CLOVASTUDIO_API_KEY, base_url=config.CLOVA_BASE_URL)

# Tool 추가 시 여기에 등록
TOOLS = [
    product_detail.TOOL
    # search_product.TOOL
    ]
FUNCTIONS = {"get_product_detail": product_detail.get_product_detail}

SYSTEM_PROMPT = (
    "너는 금융상품(국내 채권, 국내 ETF, 해외 ETF, 펀드) 조회 에이전트다.\n"
    "- 상품 정보는 반드시 도구로 조회한 결과로만 답한다. 추측하거나 지어내지 않는다.\n"
    "- 수치는 조회된 값을 그대로 쓴다.\n"
    "- 조회 결과에 없는 해석, 투자 권유, 일반적인 안내 문구는 덧붙이지 않는다.\n"
    "- 금융상품 조회와 관계없는 질문에는 도구를 쓰지 않고 짧게 답한다."
)


def answer(question: str) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}]
    while True:
        msg = client.chat.completions.create(model=config.CLOVA_MODEL, messages=messages, tools=TOOLS).choices[0].message
        print(msg.tool_calls)
        if not msg.tool_calls:
            return msg.content
        messages.append(msg)
        for call in msg.tool_calls:
            result = FUNCTIONS[call.function.name](**json.loads(call.function.arguments))
            messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result, ensure_ascii=False)})


if __name__ == "__main__":
    print(answer(sys.argv[1]))
