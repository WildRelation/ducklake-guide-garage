import os
import duckdb
from dotenv import load_dotenv

load_dotenv()

# ── Garage credentials ───────────────────────────────────────────────────────
GARAGE_KEY_ID     = os.environ["GARAGE_KEY_ID"]
GARAGE_SECRET_KEY = os.environ["GARAGE_SECRET_KEY"]
GARAGE_ENDPOINT   = os.environ["GARAGE_ENDPOINT"]
GARAGE_REGION     = os.getenv("GARAGE_REGION", "garage")
BUCKET_NAME       = os.getenv("BUCKET_NAME", "ducklake")

# ── PostgreSQL credentials (private, reachable via SSH tunnel) ───────────────
PG_HOST     = os.getenv("PG_HOST", "localhost")
PG_DB       = os.environ["PG_DB"]
PG_USER     = os.environ["PG_USER"]
PG_PASSWORD = os.environ["PG_PASSWORD"]
PG_PORT     = int(os.getenv("PG_PORT", "5432"))


def connect():
    """Returns a DuckDB connection with the DuckLake catalog attached."""
    con = duckdb.connect()

    con.execute("INSTALL ducklake;")
    con.execute("INSTALL postgres;")
    con.execute("LOAD ducklake;")
    con.execute("LOAD postgres;")

    con.execute(f"""
    CREATE OR REPLACE SECRET garage_secret (
        TYPE s3,
        KEY_ID '{GARAGE_KEY_ID}',
        SECRET '{GARAGE_SECRET_KEY}',
        ENDPOINT '{GARAGE_ENDPOINT}',
        REGION '{GARAGE_REGION}',
        URL_STYLE 'path',
        USE_SSL true
    );
    """)

    con.execute(f"""
    ATTACH 'ducklake:postgres:host={PG_HOST} dbname={PG_DB} user={PG_USER} password={PG_PASSWORD} port={PG_PORT}'
    AS my_lake (DATA_PATH 's3://{BUCKET_NAME}/');
    """)

    return con


def main():
    con = connect()
    print("Connected to DuckLake.\n")

    tables = con.execute("""
        SELECT database, schema, name
        FROM (SHOW ALL TABLES)
        WHERE database = 'my_lake'
    """).fetchall()

    print("Tables in my_lake:")
    if tables:
        for db, schema, name in tables:
            print(f"  {db}.{schema}.{name}")
    else:
        print("  (empty — no tables yet)")


if __name__ == "__main__":
    main()
