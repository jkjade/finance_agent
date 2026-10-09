"""상품 도메인(테이블) 레지스트리. 라우터가 질문을 이 중 하나로 분류한다."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Domain:
    key: str
    table: str
    name: str


DOMAINS: dict[str, Domain] = {
    d.key: d
    for d in [
        Domain("bond", "prbd01n001", "국내 채권"),
        Domain("etf_kr", "pref01n001", "국내 ETF"),
        Domain("etf_global", "pref02n001", "해외 ETF"),
        Domain("fund", "prfd01n001", "펀드"),
    ]
}
