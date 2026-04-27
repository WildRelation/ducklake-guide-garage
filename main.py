import duckdb

# ── Garage credentials ───────────────────────────────────────────────────────
GARAGE_KEY_ID     = "<your-key-id>"       # starts with GK...
GARAGE_SECRET_KEY = "<your-secret-key>"
GARAGE_ENDPOINT   = "<deployment-name>.app.cloud.cbh.kth.se"
GARAGE_REGION     = "garage"
BUCKET_NAME       = "ducklake"

# ── PostgreSQL credentials (private, reachable via SSH tunnel) ───────────────
PG_HOST     = "localhost"   # the tunnel forwards localhost:5432 → cbhcloud
PG_DB       = "<your-postgres-db>"
PG_USER     = "<your-postgres-user>"
PG_PASSWORD = "<your-postgres-password>"
PG_PORT     = 5432


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
