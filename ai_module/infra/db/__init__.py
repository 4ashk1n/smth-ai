from contextlib import contextmanager
from typing import Iterator, TYPE_CHECKING

from ai_module.app.config import settings

if TYPE_CHECKING:
    from psycopg import Connection


@contextmanager
def get_connection() -> Iterator["Connection"]:
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is empty")

    try:
        from psycopg import connect
        from psycopg.rows import dict_row
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "psycopg is not installed. Run `pip install -r ai_module/requirements.txt`."
        ) from exc

    conn = connect(settings.database_url, row_factory=dict_row, autocommit=True)
    try:
        yield conn
    finally:
        conn.close()


__all__ = ["get_connection"]



