RSS를 지원하는 언론사 뉴스를 수집하여 디스코드 웹훅으로 전송하는 bot

언론사 추가예정 현재 [보안뉴스, 데일리시큐] 구현
각 언론사 수집 후 .json파일로 저장

.env에 DISCORD_WEBHOOK_URL 값 지정필요

하루 동안 디스코드로 전송된 기사(필터에 걸린 기사 제외)는 daily.json에 누적 저장되며, 날짜가 바뀌면 초기화됨

summarize.py: daily.json의 기사에 순번을 붙여 Claude API(Haiku)로 보내고, 중복·스팸·단순 홍보 기사를 제외한 번호 목록을 받아 daily_summary.json에 저장
.env에 ANTHROPIC_API_KEY 값 지정필요 (pip install -r requirements.txt)

crontab 예시 (날짜가 바뀌기 전에 실행해야 해당 날짜의 daily.json이 요약됨)
50 23 * * * cd /path/to/RSS_Bot && python3 summarize.py >> summarize.log 2>&1
