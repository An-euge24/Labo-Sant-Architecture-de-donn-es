"""
ingest_postgres.py
Insère les données CSV (doctors, patients, medications, prescriptions)
dans PostgreSQL. Idempotent : ne crée pas de doublons si relancé.
"""

import os
import time
import pandas as pd  # pour lire les CSV
import psycopg2

# ════════════════════════════════════════
# CONFIGURATION (depuis les variables .env)
# ════════════════════════════════════════
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "port": 5432,
    "dbname": os.getenv("POSTGRES_DB", "labo_sante"),
    "user": os.getenv("POSTGRES_USER", "admin"),
    "password": os.getenv("POSTGRES_PASSWORD", "motdepasse123"),
}

# Taille du dataset à ingérer : small / medium / large
DATA_SIZE = os.getenv("DATA_SIZE", "small")
DATA_PATH = f"/app/data/data_{DATA_SIZE}"

# ════════════════════════════════════════
# CONNEXION À POSTGRESQL
# ════════════════════════════════════════
def get_connection():
    return psycopg2.connect(**DB_CONFIG)

# ════════════════════════════════════════
# CRÉATION DES TABLES (si elles n'existent pas)
# ════════════════════════════════════════
def create_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                id          VARCHAR(50) PRIMARY KEY,
                first_name  VARCHAR(100) NOT NULL,
                last_name   VARCHAR(100) NOT NULL,
                specialty   VARCHAR(100),
                hospital    VARCHAR(200),
                phone       VARCHAR(50)
            );

            CREATE TABLE IF NOT EXISTS medications (
                id        VARCHAR(50) PRIMARY KEY,
                name      VARCHAR(200) NOT NULL,
                dosage    VARCHAR(50),
                unit      VARCHAR(50),
                category  VARCHAR(100)
            );

            CREATE TABLE IF NOT EXISTS patients (
                id          VARCHAR(50) PRIMARY KEY,
                first_name  VARCHAR(100) NOT NULL,
                last_name   VARCHAR(100) NOT NULL,
                dob         DATE,
                gender      VARCHAR(20),
                blood_type  VARCHAR(10),
                doctor_id   VARCHAR(50) REFERENCES doctors(id)
            );

            CREATE TABLE IF NOT EXISTS prescriptions (
                id               VARCHAR(50) PRIMARY KEY,
                consultation_id  VARCHAR(50),
                medication_id    VARCHAR(50) REFERENCES medications(id),
                date             DATE NOT NULL,
                duration_days    INT
            );
        """)
        conn.commit()
    print("✅ Tables créées (ou déjà existantes)")

# ════════════════════════════════════════
# INGESTION DES DONNÉES
# ════════════════════════════════════════
def ingest_table(conn, filename, table, columns, conflict_key):
    """
    Lit un CSV et l'insère dans PostgreSQL.
    ON CONFLICT DO NOTHING = idempotent (pas de doublons si relancé)
    """
    filepath = f"{DATA_PATH}/{filename}"
    df = pd.read_csv(filepath)

    start = time.time()
    count = 0

    with conn.cursor() as cur:
        for _, row in df.iterrows():
            values = [row[col] if pd.notna(row[col]) else None for col in columns]
            placeholders = ", ".join(["%s"] * len(columns))
            cols = ", ".join(columns)

            query = f"""
                INSERT INTO {table} ({cols})
                VALUES ({placeholders})
                ON CONFLICT ({conflict_key}) DO NOTHING
            """
            cur.execute(query, values)
            count += 1

        conn.commit()

    duration = round(time.time() - start, 2)
    print(f"✅ {table} : {count} lignes insérées en {duration}s")

# ════════════════════════════════════════
# MAIN
# ════════════════════════════════════════
if __name__ == "__main__":
    print(f"🚀 Démarrage de l'ingestion PostgreSQL — dataset: {DATA_SIZE}")

    conn = get_connection()

    # Supprime les tables existantes pour repartir proprement
    with conn.cursor() as cur:
        cur.execute("""
            DROP TABLE IF EXISTS prescriptions;
            DROP TABLE IF EXISTS patients;
            DROP TABLE IF EXISTS medications;
            DROP TABLE IF EXISTS doctors;
        """)
        conn.commit()

    create_tables(conn)

    # Ordre important : doctors avant patients (clé étrangère)
    ingest_table(conn, "doctors.csv", "doctors",
                 ["id", "first_name", "last_name", "specialty", "hospital", "phone"], "id")

    ingest_table(conn, "medications.csv", "medications",
                 ["id", "name", "dosage", "unit", "category"], "id")

    ingest_table(conn, "patients.csv", "patients",
                 ["id", "first_name", "last_name", "dob", "gender", "blood_type", "doctor_id"], "id")

    ingest_table(conn, "prescriptions.csv", "prescriptions",
                 ["id", "consultation_id", "medication_id", "date", "duration_days"], "id")

    conn.close()
    print("🎉 Ingestion PostgreSQL terminée !")
