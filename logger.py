# logger.py
# log/ 폴더에 일자별 로그 파일(log/YYYY-MM-DD.log)을 남긴다. 콘솔에도 같은 내용을 출력한다.
#
# 사용:
#   from logger import get_logger
#   log = get_logger(__name__)
#   log.info("메시지")  / log.warning(...) / log.error(...) / log.exception(...)  (exception은 except 안에서, 트레이스백 포함)
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

LOG_DIR = "log"
LOG_RETENTION_DAYS = 30  # 이 기간(일)이 지난 로그 파일은 삭제
LOG_LEVEL = logging.INFO  # 더 자세히 보려면 logging.DEBUG
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

ROOT_NAME = "rss_bot"


class DailyFileHandler(logging.Handler):
    """기록하는 시점의 날짜로 log/YYYY-MM-DD.log 파일에 추가한다. 날짜가 바뀌면 새 파일로 넘어간다."""

    def __init__(self, log_dir: str = LOG_DIR):
        super().__init__()
        self.log_dir = Path(log_dir)
        self._date = None
        self._stream = None

    def _open(self, date: str):
        if self._stream:
            self._stream.close()
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._stream = open(self.log_dir / f"{date}.log", "a", encoding="utf-8")
        self._date = date

    def emit(self, record: logging.LogRecord):
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            if today != self._date:
                self._open(today)
            self._stream.write(self.format(record) + "\n")
            self._stream.flush()
        except Exception:
            self.handleError(record)

    def close(self):
        if self._stream:
            self._stream.close()
            self._stream = None
        super().close()


def cleanup_old_logs(log_dir: str = LOG_DIR, days: int = LOG_RETENTION_DAYS) -> list:
    """파일명 날짜(YYYY-MM-DD.log) 기준으로 보관 기간이 지난 로그 파일을 삭제하고 삭제한 파일명을 반환한다."""
    cutoff = (datetime.now() - timedelta(days=days)).date()
    removed = []
    for path in Path(log_dir).glob("*.log"):
        try:
            file_date = datetime.strptime(path.stem, "%Y-%m-%d").date()
        except ValueError:
            continue  # 날짜 형식이 아닌 파일은 건드리지 않음
        if file_date < cutoff:
            try:
                path.unlink()
                removed.append(path.name)
            except OSError:
                pass
    return sorted(removed)


def _setup() -> logging.Logger:
    root = logging.getLogger(ROOT_NAME)
    if root.handlers:
        return root  # 이미 설정됨

    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler = DailyFileHandler()
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    root.addHandler(file_handler)
    root.addHandler(console_handler)
    root.setLevel(LOG_LEVEL)
    root.propagate = False

    # 처리되지 않은 예외로 프로그램이 종료될 때도 로그에 남긴다
    def _excepthook(exc_type, exc, tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc, tb)
            return
        root.critical("처리되지 않은 예외로 종료", exc_info=(exc_type, exc, tb))

    sys.excepthook = _excepthook

    # 실행할 때마다 보관 기간이 지난 로그 정리
    removed = cleanup_old_logs()
    if removed:
        root.info(f"{LOG_RETENTION_DAYS}일 지난 로그 {len(removed)}개 삭제: {', '.join(removed)}")
    return root


def get_logger(name: str = ROOT_NAME) -> logging.Logger:
    """모듈별 로거를 반환한다. (예: rss_bot.app)"""
    root = _setup()
    if name == "__main__":
        name = Path(sys.argv[0]).stem or ROOT_NAME  # 직접 실행한 스크립트 이름 (예: app)
    if name in (ROOT_NAME, None):
        return root
    return root.getChild(name)
