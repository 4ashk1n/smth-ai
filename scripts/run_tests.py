from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def load_env_file(env_file: Path) -> None:
    if not env_file.exists():
        raise FileNotFoundError(f"Env file not found: {env_file}")

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ[key] = value


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pytest with env loaded from .env.test")
    parser.add_argument(
        "--env-file",
        default="ai_module/.env.test",
        help="Path to env file (default: ai_module/.env.test)",
    )
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Arguments passed to pytest after '--'",
    )

    args = parser.parse_args()

    env_file = Path(args.env_file).resolve()
    load_env_file(env_file)

    pytest_args = args.pytest_args
    if pytest_args and pytest_args[0] == "--":
        pytest_args = pytest_args[1:]

    if not pytest_args:
        pytest_args = [
            "ai_module/features/recommendations/tests",
            "ai_module/features/suggestions/tests",
            "-q",
            "-p",
            "no:cacheprovider",
        ]

    print(f"Using env file: {env_file}")
    print(f"DATABASE_URL: {os.environ.get('DATABASE_URL', '')}")

    result = subprocess.run([sys.executable, "-m", "pytest", *pytest_args], check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
