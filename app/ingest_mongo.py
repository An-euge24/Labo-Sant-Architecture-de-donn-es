"""
ingest_mongo.py
Insère les consultations (JSON) dans MongoDB.
Idempotent : utilise upsert pour ne pas créer de doublons.
"""

import os            # pour lire les variables d'environnement
import json          # pour lire les fichiers JSON
import time          # pour mesurer le temps d'ingestion
from pymongo import MongoClient, UpdateOne # pour se connecter à MongoDB et faire des opérations upsert

# ════════════════════════════════════════
# CONFIGURATION (depuis les variables .env)
# ════════════════════════════════════════
MONGO_HOST = os.getenv("MONGO_HOST", "mongodb")
MONGO_USER = os.getenv("MONGO_USER", "admin")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "motdepasse123")
MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:27017/"

# Taille du dataset : small / medium / large
DATA_SIZE = os.getenv("DATA_SIZE", "small")
DATA_PATH = f"/app/data/data_{DATA_SIZE}"

# ════════════════════════════════════════
# CONNEXION À MONGODB
# ════════════════════════════════════════
def get_client():
    return MongoClient(MONGO_URI)

# ════════════════════════════════════════
# INGESTION DES CONSULTATIONS
# ════════════════════════════════════════
def ingest_consultations(client):
    """
    Lit le fichier consultations.json et insère les documents dans MongoDB.
    Upsert = idempotent : si la consultation existe déjà, elle est mise à jour.
    """
    filepath = f"{DATA_PATH}/consultations.json"

    with open(filepath, "r", encoding="utf-8") as f:
        consultations = json.load(f)

    db = client["labo_sante"]               # base de données
    collection = db["consultations"]        # collection (équivalent d'une table)

    start = time.time()

    # Prépare les opérations upsert (insert si absent, update si présent)
    operations = [
        UpdateOne(
            {"consultation_id": doc["consultation_id"]},  # filtre : clé unique
            {"$set": doc},                                 # mise à jour du document
            upsert=True                                    # crée si n'existe pas
        )
        for doc in consultations
    ]

    result = collection.bulk_write(operations)

    duration = round(time.time() - start, 2)
    print(f"✅ consultations : {result.upserted_count} insérées, "
          f"{result.modified_count} mises à jour en {duration}s")

# ════════════════════════════════════════
# MAIN
# ════════════════════════════════════════
if __name__ == "__main__":
    print(f"🚀 Démarrage de l'ingestion MongoDB — dataset: {DATA_SIZE}")

    client = get_client()
    ingest_consultations(client)
    client.close()

    print("🎉 Ingestion MongoDB terminée !")
