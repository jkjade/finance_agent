"""HyperCLOVA X (CLOVA Studio OpenAI 호환 API) 클라이언트."""

import json
from functools import lru_cache

from openai import OpenAI
from openai.types.chat import ChatCompletionMessage

from app import config


@lru_cache
def client() -> OpenAI:
    return OpenAI(api_key=config.CLOVASTUDIO_API_KEY, base_url=config.CLOVA_BASE_URL)


def chat(messages: list[dict], tools: list[dict] | None = None, tool_choice=None) -> ChatCompletionMessage:
    kwargs = {
        "model": config.CLOVA_MODEL,
        "messages": messages,
        "max_tokens": 1024,
        "temperature": 0.1,
    }
    if tools:
        kwargs["tools"] = tools
    if tool_choice is not None:
        kwargs["tool_choice"] = tool_choice
    return client().chat.completions.create(**kwargs).choices[0].message


def parse_arguments(arguments) -> dict:
    # OpenAI 표준은 JSON 문자열, CLOVA v3 는 객체로 줄 수 있어 둘 다 받는다
    if isinstance(arguments, dict):
        return arguments
    return json.loads(arguments or "{}")
