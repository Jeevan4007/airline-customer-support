# Data directory

This folder holds the two datasets used by the system. The actual files are **not** committed
to git (see `.gitignore`); download them once before running the loader scripts.

## 1. Flights data (PostgreSQL)

* **File:** `Flights_Schedule_Data_v1.csv`
* **Source:** <https://github.com/MLOPS-test/Artifacts/raw/refs/heads/main/datasets/Flights_Schedule_Data_v1.csv>
* **Loaded by:** `scripts/load_flights_csv.py` — creates the `flights` table and inserts every row.

```bash
curl -L -o data/Flights_Schedule_Data_v1.csv \
  https://github.com/MLOPS-test/Artifacts/raw/refs/heads/main/datasets/Flights_Schedule_Data_v1.csv
python scripts/load_flights_csv.py
```

## 2. Airline FAQ knowledge base (Pinecone)

* **File:** `Knowledge_Base_for_Airline_Info_and_FAQs.pdf`
* **Source:** <https://raw.githubusercontent.com/MLOPS-test/Artifacts/refs/heads/main/datasets/Knowledge_Base_for_Airline_Info_and_FAQs.pdf>
* **Loaded by:** `scripts/ingest_pdf.py` — chunks the PDF and upserts to Pinecone.

```bash
curl -L -o data/Knowledge_Base_for_Airline_Info_and_FAQs.pdf \
  https://raw.githubusercontent.com/MLOPS-test/Artifacts/refs/heads/main/datasets/Knowledge_Base_for_Airline_Info_and_FAQs.pdf
python scripts/ingest_pdf.py
```
