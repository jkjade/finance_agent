import os

DATABASE_URL = os.environ.get("DATABASE_URL", "")
CLOVASTUDIO_API_KEY = os.environ.get("CLOVASTUDIO_API_KEY", "")
CLOVA_MODEL = os.environ.get("CLOVA_MODEL", "HCX-005")
CLOVA_BASE_URL = os.environ.get("CLOVA_BASE_URL", "https://clovastudio.stream.ntruss.com/v1/openai")
