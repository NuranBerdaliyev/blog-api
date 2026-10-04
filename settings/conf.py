import os
from pathlib import Path
from decouple import Config, RepositoryEnv

BASE_DIR = Path(__file__).resolve().parent.parent

env_path=BASE_DIR / ".env"
if os.path.exists(env_path):
    config = Config(RepositoryEnv(env_path))
else:
    from decouple import config

BLOG_ENV_ID = config("BLOG_ENV_ID", default="local")
BLOG_SECRET_KEY = config("BLOG_SECRET_KEY")
BLOG_DB_NAME = config("BLOG_DB_NAME", default="db.sqlite3")