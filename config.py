import os

from sqlalchemy.pool import NullPool

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 프로바이더마다 주입하는 접속 문자열 환경변수 이름이 다르다.
# - DATABASE_URL: Neon, Supabase, Render, Heroku 등 범용 관례
# - POSTGRES_URL / POSTGRES_URL_NON_POOLING: Vercel Postgres(Storage 탭)가 자동 주입하는 이름
_DATABASE_URL_ENV_KEYS = ("DATABASE_URL", "POSTGRES_URL", "POSTGRES_URL_NON_POOLING")


def _resolve_database_uri():
    """지원되는 이름의 환경변수가 있으면 영구 Postgres를, 없으면 SQLite를 사용한다.

    Vercel의 서버리스 함수는 프로젝트 디렉터리가 읽기 전용이고 /tmp만 쓰기 가능하다.
    /tmp는 인스턴스가 재시작되면 초기화되는 임시 저장소이므로, Postgres 접속 정보 없이
    VERCEL 환경에서 SQLite로 폴백하는 것은 로컬 개발/데모용일 뿐 운영에는 적합하지 않다.
    """
    for key in _DATABASE_URL_ENV_KEYS:
        url = os.environ.get(key)
        if url:
            # Heroku/Vercel/Supabase 등 일부 프로바이더는 "postgres://" 스킴을 내려주는데,
            # SQLAlchemy 1.4+는 "postgresql://"만 인식한다.
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url

    if os.environ.get("VERCEL"):
        print(
            "[payroll-guard] WARNING: DATABASE_URL(또는 POSTGRES_URL)이 설정되지 않아 "
            "휘발성 /tmp SQLite로 폴백합니다. 인스턴스가 재시작되면 계정/검증 이력이 초기화됩니다. "
            "Vercel 프로젝트 Settings > Environment Variables에 접속 정보를 등록하세요."
        )
        return "sqlite:////tmp/payroll.db"
    return "sqlite:///" + os.path.join(BASE_DIR, "data", "payroll.db")


_DATABASE_URI = _resolve_database_uri()
_IS_POSTGRES = _DATABASE_URI.startswith("postgresql://")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "payroll-guard-dev-key")
    SQLALCHEMY_DATABASE_URI = _DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB

    if _IS_POSTGRES:
        # 서버리스 함수는 매 호출마다 별도 프로세스/컨테이너일 수 있어 SQLAlchemy 자체 커넥션
        # 풀을 유지하는 의미가 없고, 오히려 idle 커넥션이 재사용되며 "connection closed"
        # 류 오류로 이어지기 쉽다. NullPool로 매 요청마다 새로 접속하고 즉시 반납한다.
        SQLALCHEMY_ENGINE_OPTIONS = {"poolclass": NullPool, "pool_pre_ping": True}
