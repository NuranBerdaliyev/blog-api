#!/usr/bin/env python
import os
import sys
from decouple import Config, RepositoryEnv

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(base_dir, ".env")

    if os.path.exists(env_path):
        config = Config(RepositoryEnv(env_path))
        env_id = config("BLOG_ENV_ID", default="local")
    else:
        env_id = os.environ.get("BLOG_ENV_ID", "local")

    settings_module = f"settings.env.{env_id}"
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
