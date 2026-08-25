# Dockerfile — Service Python Ingestor
# Construit l'image du conteneur qui va ingérer les données

# Base : image officielle Python 3.11 légère
FROM python:3.11-slim

# Définit le dossier de travail à l'intérieur du conteneur
WORKDIR /app

# Copie le fichier des dépendances en premier (optimisation du cache Docker)
COPY requirements.txt .

# Installe les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copie tous les scripts Python dans le conteneur
COPY . .

# Commande exécutée au démarrage du conteneur
CMD ["python", "main.py"] 
