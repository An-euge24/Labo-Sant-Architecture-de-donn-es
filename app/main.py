"""
main.py
Point d'entrée du conteneur Python.
Lance l'ingestion PostgreSQL puis MongoDB dans le bon ordre.
"""

import subprocess
import sys

print("🚀 Lancement de l'ingestion complète...")

# Lance ingest_postgres.py comme un script indépendant
subprocess.run([sys.executable, "ingest_postgres.py"], check=True)

# Lance ingest_mongo.py comme un script indépendant
subprocess.run([sys.executable, "ingest_mongo.py"], check=True)

print("🎉 Toutes les ingestions sont terminées !")