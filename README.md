RSS를 지원하는 언론사 뉴스를 수집하여 디스코드 웹훅으로 전송하는 bot

언론사 추가예정 현재 [보안뉴스, 데일리시큐] 구현
각 언론사 수집 후 .json파일로 저장

.env에 DISCORD_WEBHOOK_URL 값 지정필요

하루 동안 디스코드로 전송된 기사(필터에 걸린 기사 제외)는 daily.json에 누적 저장되며, 날짜가 바뀌면 초기화됨

summarize.py: daily.json의 기사에 순번을 붙여 Claude API(Haiku)로 보내고, 중복·스팸·단순 홍보 기사를 제외한 가치 있는 기사 번호를 받아
@주제 제목별로 분류된 결과를 제목·description·링크로 변환해 daily_summary.json에 저장한 뒤 Gmail로 전송 (주제 제목은 볼드체)
.env에 ANTHROPIC_API_KEY, SENDER_EMAIL, SENDER_PASSWD(Gmail 앱 비밀번호), Receive_email(쉼표로 여러 명 가능) 값 지정필요 (pip install -r requirements.txt)

crontab 예시 (날짜가 바뀌기 전에 실행해야 해당 날짜의 daily.json이 요약됨)
50 23 * * * cd /path/to/RSS_Bot && python3 summarize.py >> summarize.log 2>&1
