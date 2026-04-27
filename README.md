# How to Use DuckDB in Python to Connect to a DuckLake (PostgreSQL + Garage) Deployed on cbhcloud

## How it works

DuckLake is not a service on its own — it is a **format** that defines how to organize a data lake. It requires two services to work:

```
DuckLake = PostgreSQL (catalog) + Garage (parquet files)
```

**DuckDB** is the engine that understands the DuckLake format and connects both pieces together.

| Component | Role |
|---|---|
| **PostgreSQL** | Metadata catalog — stores table names, schemas, and transaction history |
| **Garage** | S3-compatible object storage — stores the actual `.parquet` data files |
| **DuckDB** (local Python) | Query engine — reads the catalog and the files, returns results |

When you run `SELECT * FROM my_lake.main.some_table`, DuckDB:
1. Asks PostgreSQL — *where are the files for this table?*
2. Goes to Garage — *downloads that `.parquet` file*
3. Returns the results to you

### What is a bucket?

A **bucket** is a root folder in Garage. You cannot store files without one. Think of it like this:

```
Garage
  └── ducklake/            ← bucket
        └── table1.parquet
        └── table2.parquet
```

### What are Garage access keys?

Unlike MinIO which uses a single root user/password, Garage uses **key pairs**:
- **Key ID** — starts with `GK`, acts as a username
- **Secret key** — acts as a password

Keys are created via the Garage CLI and granted per-bucket permissions.

---

## Prerequisites

- Python 3.10+
- OpenSSH (pre-installed on Linux, macOS, and Windows 10/11)
- Your PostgreSQL and Garage deployments running on cbhcloud
- A Garage bucket created and a key with read/write access (see [garage-cbhcloud](https://github.com/WildRelation/garage-cbhcloud))

---

## Step 1 — Check visibility settings

| Service | Visibility |
|---|---|
| PostgreSQL | Private — connect via SSH tunnel |
| Garage | Public — connect directly via HTTPS |

PostgreSQL uses the wire protocol on port 5432 which is not exposed publicly by cbhcloud. Garage uses HTTPS on port 3900 which is exposed publicly.

---

## Step 2 — Open an SSH tunnel to PostgreSQL

Open a terminal and leave this command running — **do not close it**:

```bash
ssh -L 5432:localhost:5432 <your-postgres-deployment>@deploy.cloud.cbh.kth.se -N
```

This forwards `localhost:5432` on your machine to the PostgreSQL server. Works on Linux, macOS, and Windows PowerShell.

> **Example (cbhcloud):**
> ```bash
> ssh -L 5432:localhost:5432 ducklake-postgres2@deploy.cloud.cbh.kth.se -N
> ```

---

## Step 3 — Set up the Python environment

**Linux / macOS:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## Step 4 — Fill in your credentials in `main.py`

```python
# ── Garage credentials ───────────────────────────────────────────────────────
GARAGE_KEY_ID     = "<your-key-id>"       # starts with GK...
GARAGE_SECRET_KEY = "<your-secret-key>"
GARAGE_ENDPOINT   = "<deployment-name>.app.cloud.cbh.kth.se"
GARAGE_REGION     = "garage"
BUCKET_NAME       = "ducklake"

# ── PostgreSQL credentials ───────────────────────────────────────────────────
PG_HOST     = "localhost"
PG_DB       = "<your-postgres-db>"
PG_USER     = "<your-postgres-user>"
PG_PASSWORD = "<your-postgres-password>"
PG_PORT     = 5432
```

> **Example (cbhcloud):**
> ```python
> GARAGE_KEY_ID     = "GK6759c84613351dac5b8367db"
> GARAGE_SECRET_KEY = "1edeb1f895689da26a41ba6ced853ea61465e4df1eef31682da5f7d7f6e9fb96"
> GARAGE_ENDPOINT   = "ducklake-garage.app.cloud.cbh.kth.se"
> GARAGE_REGION     = "garage"
> BUCKET_NAME       = "ducklake"
>
> PG_HOST     = "localhost"
> PG_DB       = "ducklake"
> PG_USER     = "duck"
> PG_PASSWORD = "123456"
> PG_PORT     = 5432
> ```

---

## Step 5 — Run the script

With the SSH tunnel active (Step 2), open a second terminal:

```bash
python main.py
```

---

## Key notes

**Why `localhost` as the PostgreSQL host?**
The SSH tunnel forwards `localhost:5432` to the real server. If you close the tunnel terminal, the script cannot reach PostgreSQL.

**Why `REGION 'garage'`?**
Garage requires the region to match the `s3_region` value in its `garage.toml` config. The default is `garage`.

**Why `URL_STYLE 'path'`?**
Garage only supports path-style URLs (`endpoint.com/bucket`), not virtual-hosted style (`bucket.endpoint.com`).

**Why must `DATA_PATH` match exactly?**
DuckLake stores the data path inside the PostgreSQL catalog on first initialization. If you use a different path, DuckDB throws a mismatch error.

**Does this involve Docker?**
Not on your side. PostgreSQL and Garage run as Docker containers managed by cbhcloud. You do not need Docker locally.

**Does this involve an API?**
No. DuckDB connects directly to PostgreSQL using the Postgres wire protocol and to Garage using the S3 protocol. There is no HTTP server or REST API involved.
