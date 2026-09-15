import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Vercel의 서버리스 함수는 프로젝트 디렉터리가 읽기 전용이고 /tmp만 쓰기 가능하다.
# (배치/계정 데이터는 인스턴스가 재시작되면 초기화되는 임시 저장소이므로,
#  운영 환경에서는 Postgres 등 외부 DB로 교체를 권장한다.)
if os.environ.get("VERCEL"):
    DB_PATH = "/tmp/payroll.db"
else:
    DB_PATH = os.path.join(BASE_DIR, "data", "payroll.db")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "payroll-guard-dev-key")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + DB_PATH
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
