# summarize.py
# daily.json에 쌓인 하루치 기사를 Claude API에 보내 중복/스팸/단순 홍보 기사를 걸러낸다.
# 각 기사에 순번을 붙여 전송하고, 결과는 남길 기사의 번호 목록으로 받는다.
#
# 사용: python summarize.py   (crontab으로 하루 한 번 실행)
# 필요: .env 또는 환경변수에 ANTHROPIC_API_KEY
from datetime import datetime
from typing import List

import anthropic
from pydantic import BaseModel

from util import load_env, load_json, save_json
from daily import DAILY_PATH
from gmail import send_summary_mail

SUMMARY_PATH = "daily_summary.json"

MODEL = "claude-haiku-5-5"

# 추론 강도 (output_config.effort)
#   "low"    : 가장 빠르고 저렴, 생각을 거의 하지 않음
#   "medium" : 기본값 (현재 설정)
#   "high"   : 더 꼼꼼하게 판단, 토큰 사용 증가
#   "xhigh"  : high보다 더 깊게
#   "max"    : 최대 추론, 가장 느리고 비쌈
EFFORT = "medium"

# 응답 최대 토큰 (생각(thinking) 토큰도 여기에 포함된다)
MAX_TOKENS = 16000

SYSTEM_PROMPT = """당신은 보안·IT 뉴스 큐레이터입니다.
사용자가 하루 동안 수집된 기사 목록을 보냅니다. 각 기사는 [번호] 형식의 순번과 언론사, 제목, 본문 요약(description)으로 이루어져 있습니다.

기사들의 제목과 description을 읽고, 아래 기준으로 걸러낸 뒤 남길 기사의 번호만 반환하세요.

1. 중복 제외: 같은 사건·발표·이슈를 다룬 기사는 언론사가 달라도 중복으로 봅니다.
   중복 묶음에서는 내용이 가장 구체적이고 정보가 많은 기사 하나만 남기고 나머지는 제외합니다.
2. 스팸·단순 홍보 제외: 특정 업체의 제품·서비스 출시나 기능 소개, 수상·인증 획득 자랑,
   행사·이벤트·전시 참가 안내, 협약(MOU) 체결 소식처럼 독자에게 새로운 정보나 시사점이 없는
   보도자료성 기사는 제외합니다. 인사·부고 기사도 제외합니다.
3. 가치 있는 기사만 남기고 분류: 1, 2번을 거친 기사 중에서도 독자에게 실질적인 정보 가치가 있는 기사만 남깁니다.
   보안 사고·침해, 취약점, 위협·공격 동향, 정책·규제 변화, 업계에 영향을 주는 동향 분석이 이에 해당합니다.
   정보 가치가 낮거나 위 범주에 해당하지 않는 기사는 제외합니다.

반환하는 번호는 입력에 있는 번호만 사용하세요."""


class Selection(BaseModel):
    keep: List[int]  # 남길 기사 번호 (오름차순)


def build_prompt(items: list) -> str:
    """각 기사에 1부터 순번을 붙여 하나의 텍스트로 만든다."""
    lines = []
    for n, item in enumerate(items, start=1):
        lines.append(
            f"[{n}] ({item.get('source', '')}) {item.get('title', '')}\n"
            f"{item.get('description', '')}"
        )
    return "\n\n".join(lines)


def select_articles(client: anthropic.Anthropic, items: list) -> List[int]:
    """Claude에게 기사 목록을 보내고 남길 기사 번호를 받는다."""
    response = client.messages.parse(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        output_config={"effort": EFFORT},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_prompt(items)}],
        output_format=Selection,
    )

    if response.stop_reason == "refusal":
        raise RuntimeError(f"Claude가 요청을 거절했습니다: {response.stop_details}")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("응답이 max_tokens에서 잘렸습니다. MAX_TOKENS를 늘리거나 EFFORT를 낮추세요.")

    # 범위 밖 번호와 중복 번호 제거
    return sorted({n for n in response.parsed_output.keep if 1 <= n <= len(items)})


def main():
    load_env()
    daily = load_json(DAILY_PATH)
    items = daily.get("items", [])
    if not items:
        print("daily.json에 기사가 없습니다.")
        return

    client = anthropic.Anthropic()  # ANTHROPIC_API_KEY 환경변수 사용
    try:
        keep = select_articles(client, items)
    except anthropic.APIConnectionError as e:
        print(f"[SUMMARY ERROR] 네트워크 오류: {e}")
        return
    except anthropic.APIStatusError as e:
        print(f"[SUMMARY ERROR] API 오류 {e.status_code}: {e.message}")
        return
    except RuntimeError as e:
        print(f"[SUMMARY ERROR] {e}")
        return

    # 반환받은 번호 -> 제목, description, 링크
    selected = [
        {
            "title": items[n - 1].get("title", ""),
            "description": items[n - 1].get("description", ""),
            "link": items[n - 1].get("link", ""),
        }
        for n in keep
    ]
    summary = {
        "date": daily.get("date"),
        "created_at": datetime.now().strftime("%Y-%m-%d_%H:%M:%S"),
        "total": len(items),
        "count": len(selected),
        "items": selected,
    }
    save_json(summary, SUMMARY_PATH)
    print(f"{daily.get('date')}: {len(items)}건 중 {len(selected)}건 선별 -> {SUMMARY_PATH}")

    try:
        send_summary_mail(summary)
        print("메일 전송 완료")
    except Exception as e:
        print(f"[MAIL ERROR] {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
