# db.py
import os
from dotenv import load_dotenv
import psycopg2
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
# Ensure that the DATABASE_URL is set; raise an error if not found.
if not DATABASE_URL:
    raise RuntimeError("Please set DATABASE_URL in .env")


def get_conn():
    """
    Create and return a new connection to the PostgreSQL database.

    This function uses the connection string defined in the DATABASE_URL environment variable.
    Returns:
        psycopg2.extensions.connection: A new database connection object.
    """
    return psycopg2.connect(DATABASE_URL)
