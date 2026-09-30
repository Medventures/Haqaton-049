import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
# DATA_DIR переопределяется окружением, если справочники лежат не в
# <repo>/data (например, в бандле сервиса api на Vercel).
DATA_DIR = Path(os.environ["DATA_DIR"]) if os.environ.get("DATA_DIR") else REPO_ROOT / "data"
SCHEMAS_DIR = DATA_DIR / "schemas"
FIXTURES_DIR = DATA_DIR / "fixtures"
