import os
from pathlib import Path
from typing import Optional

# Base paths
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
ROOT_DATA_DIR = ROOT_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

# In serverless environments (Vercel / AWS Lambda), the deployment directory is read-only.
# Default SQLite fallback path to writable /tmp to eliminate OperationalError when Postgres is not yet linked.
_IS_SERVERLESS = bool(
    os.environ.get("VERCEL")
    or os.environ.get("VERCEL_ENV")
    or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
    or os.environ.get("LAMBDA_TASK_ROOT")
    or "/var/task" in str(BASE_DIR)
)

if _IS_SERVERLESS:
    DB_PATH = Path("/tmp") / "probmail.db"
else:
    DB_PATH = BASE_DIR / "probmail.db"

PRIMARY_DATASET_FILENAME = "enron_spam_data.csv"
SAMPLE_DATASET_PATH = BASE_DIR / "data" / "sample_dataset.csv"

# Ensure directories exist
try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

def resolve_dataset_path(filename: str = PRIMARY_DATASET_FILENAME) -> Optional[Path]:
    """
    Robustly resolves the absolute path to the dataset file regardless of the directory
    from which the application is started (e.g. workspace root, backend dir, or any cwd).
    """
    candidates = []

    # 1. Environment variable override
    env_path = os.environ.get("DATASET_PATH")
    if env_path:
        candidates.append(Path(env_path).resolve())

    # 2. Known static paths within backend and workspace
    candidates.extend([
        DATA_DIR / filename,
        ROOT_DATA_DIR / filename,
        BASE_DIR / filename,
        ROOT_DIR / filename,
        Path.cwd() / "data" / filename,
        Path.cwd() / "backend" / "data" / filename,
        Path.cwd() / filename,
    ])

    # 3. Check direct candidate matches
    for candidate in candidates:
        try:
            if candidate.exists() and candidate.is_file() and candidate.stat().st_size > 0:
                return candidate.resolve()
        except (PermissionError, OSError):
            continue

    # 4. Search up the directory tree (up to 4 levels)
    curr = Path(__file__).resolve().parent
    for _ in range(4):
        for subfolder in ["data", "backend/data", ""]:
            target = curr / subfolder / filename if subfolder else curr / filename
            try:
                if target.exists() and target.is_file() and target.stat().st_size > 0:
                    return target.resolve()
            except (PermissionError, OSError):
                pass
        curr = curr.parent

    return None

# Application Settings
SECRET_KEY = os.environ.get("SECRET_KEY", "probmail-secure-secret-key-2026")
DEFAULT_MAX_FEATURES = 1500
DEFAULT_K_BEST = 50
DEFAULT_TEST_SIZE = 0.2
RANDOM_STATE = 42

# Allowed file extensions
ALLOWED_EXTENSIONS = {"csv", "txt"}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
