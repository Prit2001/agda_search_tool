import psycopg2
from contextlib import contextmanager
from config import DB_PARAMS


@contextmanager
def get_cursor():
    with psycopg2.connect(**DB_PARAMS) as conn, conn.cursor() as cur:
        yield cur
