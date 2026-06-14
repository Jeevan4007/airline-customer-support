"""One-time loader: read `data/Flights_Schedule_Data_v1.csv` and insert rows into the
PostgreSQL `flights` table (created if missing).

Usage:
    python scripts/load_flights_csv.py

Environment variables read from `.env`:
    PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE, PGSSLMODE
    FLIGHTS_CSV_PATH (optional; default: data/Flights_Schedule_Data_v1.csv)
"""

import sys
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# Make `backend` importable when running this script from the repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend import config  # noqa: E402


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS flights (
    id              BIGSERIAL PRIMARY KEY,
    flight_no       TEXT,
    airline_code    TEXT,
    airline_name    TEXT,
    origin          TEXT,
    destination     TEXT,
    departure_date  DATE,
    departure_time  TIME,
    arrival_date    DATE,
    arrival_time    TIME,
    status          TEXT,
    delay_minutes   INTEGER,
    delay_reason    TEXT,
    terminal        TEXT,
    gate            TEXT,
    aircraft_type   TEXT,
    seats_total     INTEGER,
    seats_booked    INTEGER,
    fare_inr        INTEGER
);
"""

INSERT_COLUMNS = [
    "flight_no", "airline_code", "airline_name", "origin", "destination",
    "departure_date", "departure_time", "arrival_date", "arrival_time",
    "status", "delay_minutes", "delay_reason", "terminal", "gate",
    "aircraft_type", "seats_total", "seats_booked", "fare_inr",
]


def main() -> None:
    csv_path = Path(config.FLIGHTS_CSV_PATH)
    if not csv_path.exists():
        sys.exit(
            f"CSV not found at {csv_path}. Download it from "
            f"https://github.com/MLOPS-test/Artifacts/raw/refs/heads/main/datasets/"
            f"Flights_Schedule_Data_v1.csv and place it in data/."
        )

    print(f"Reading {csv_path} ...")
    df = pd.read_csv(csv_path)
    print(f"  -> {len(df)} rows, columns: {list(df.columns)}")

    # Keep only the columns we expect, in the right order
    df = df[[c for c in INSERT_COLUMNS if c in df.columns]]

    print("Connecting to Postgres ...")
    conn = psycopg2.connect(**config.DB_PARAMS)
    cur = conn.cursor()

    print("Ensuring flights table exists ...")
    cur.execute(CREATE_TABLE_SQL)

    print(f"Inserting {len(df)} rows ...")
    rows = [tuple(None if pd.isna(v) else v for v in row) for row in df.itertuples(index=False)]
    placeholders = "(" + ",".join(["%s"] * len(df.columns)) + ")"
    cols_sql = ",".join(df.columns)
    execute_values(
        cur,
        f"INSERT INTO flights ({cols_sql}) VALUES %s",
        rows,
        template=placeholders,
    )

    conn.commit()
    cur.close()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
