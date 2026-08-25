# 🏥 Labo Santé — Architecture de données pour un laboratoire de santé

## 📋 Description

Ce projet met en place une architecture de données complète pour un laboratoire de santé fictif.  
Il utilise **Docker** pour orchestrer plusieurs services : une base de données relationnelle (PostgreSQL), une base de données NoSQL (MongoDB), et des outils de monitoring et d'administration.

---

## 🏗️ Architecture

```
labo-sante/
├── app/
│   ├── Dockerfile              # Image Python pour l'ingestion
│   ├── main.py                 # Point d'entrée : lance les deux ingestions
│   ├── ingest_postgres.py      # Ingestion optimisée des CSV dans PostgreSQL
│   ├── ingest_mongo.py         # Ingestion optimisée du JSON dans MongoDB
│   └── requirements.txt        # Dépendances Python
├── data/
│   ├── data_small/             # ~84 061 lignes / 60 000 documents
│   ├── data_medium/            # ~840 061 lignes / 600 000 documents
│   └── data_large/             # ~8 400 061 lignes / 6 000 000 documents
├── docker-compose.yml          # Orchestration des 6 services
├── .env.example                # Modèle de configuration
└── .gitignore                  # Protection des fichiers sensibles
```

---

## 🐳 Services Docker

| Service | Rôle | Port |
|---|---|---|
| `postgres` | Base de données relationnelle | 5432 |
| `mongodb` | Base de données NoSQL | 27017 |
| `ingestor` | Script Python d'ingestion des données | - |
| `pgadmin` | Interface d'administration PostgreSQL | 5050 |
| `mongo-express` | Interface d'administration MongoDB | 8081 |
| `portainer` | Monitoring des conteneurs Docker | 9000 |

---

## 🗄️ Modèle de données

### PostgreSQL (données structurées)

- **doctors** : médecins (id, prénom, nom, spécialité, hôpital, téléphone)
- **medications** : médicaments (id, nom, dosage, unité, catégorie)
- **patients** : patients (id, prénom, nom, date de naissance, genre, groupe sanguin, médecin référent)
- **prescriptions** : prescriptions (id, consultation, médicament, date, durée)

### MongoDB (données non structurées)

- **consultations** : documents JSON enrichis (id, date, diagnostic, symptômes, patient, médecin, notes)

---

## 🚀 Installation et lancement

### Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé
- [Git](https://git-scm.com/) installé

### Étapes

**1. Clone le repo :**
```bash
git clone https://github.com/An-euge24/labo-sante.git
cd labo-sante
```

**2. Crée le fichier `.env` à partir du modèle :**
```bash
cp env.example .env
```

**3. Modifie le `.env` avec tes valeurs :**
```env
POSTGRES_USER=admin
POSTGRES_PASSWORD=motdepasse
POSTGRES_DB=labo_sante
PGADMIN_EMAIL=adn@labo.com
PGADMIN_PASSWORD=motdepasse
MONGO_USER=admin
MONGO_PASSWORD=motdepasse
MONGO_EXPRESS_USER=admin
MONGO_EXPRESS_PASSWORD=motdepasse
DATA_SIZE=small        # small | medium | large
CLEAN_INSERT=true      # true = nettoie avant d'insérer | false = conserve les données
```

**4. Lance tous les services :**
```bash
docker compose up -d
```

---

## ⚙️ Variables d'environnement

| Variable | Description | Valeurs possibles |
|---|---|---|
| `DATA_SIZE` | Taille du dataset à insérer | `small`, `medium`, `large` |
| `CLEAN_INSERT` | Nettoie les données avant d'insérer | `true` (dev), `false` (prod) |

### Différence entre les deux modes `CLEAN_INSERT` :

| Mode | Usage | Comportement |
|---|---|---|
| `CLEAN_INSERT=true` | Développement / tests | Supprime les données existantes, repart de zéro |
| `CLEAN_INSERT=false` | Production | Conserve les données, ignore les doublons |

---

## 🌐 Accès aux interfaces

| Interface | URL | Identifiants |
|---|---|---|
| pgAdmin | http://localhost:5050 | adn@labo.com / voir .env |
| Mongo Express | http://localhost:8081 | admin / voir .env |
| Portainer | http://localhost:9000 | admin / créé au 1er lancement |

---

## ⚡ Optimisations d'ingestion

### PostgreSQL : execute_values

Remplacement de l'insertion ligne par ligne par un **insert en batch** :

```python
# Avant (lent) : 1 requête SQL par ligne
for _, row in df.iterrows():
    cur.execute(query, values)   # 60 000 requêtes pour 60 000 lignes

# Après (rapide) : 1 seule requête pour tout
execute_values(cur, query, all_values, page_size=1000)
```

### MongoDB : index + insert_many

Ajout d'un **index sur `consultation_id`** et insertion par **batch de 5000 documents** :

```python
# Index : évite de parcourir toute la collection à chaque insert
collection.create_index([("consultation_id", ASCENDING)], unique=True)

# insert_many : envoie 5000 documents en une seule requête réseau
collection.insert_many(batch, ordered=False)
```

---

## 📊 Performances d'ingestion (résultats mesurés)

### Temps d'ingestion PostgreSQL

| Table | data_small | data_medium | data_large |
|---|---|---|---|
| doctors | 0.30s | 4.22s | 41.14s |
| medications | 0.01s | 0.02s | 0.01s |
| patients | 1.76s | 23.01s | 240.06s |
| prescriptions | 4.46s | 59.65s | 566.78s |
| **Total PostgreSQL** | **~6.5s** | **~87s** | **~848s** |

### Temps d'ingestion MongoDB

| Dataset | Documents | Temps |
|---|---|---|
| data_small | 60 000 | 0.98s |
| data_medium | 600 000 | 13.98s |
| data_large | 6 000 000 | 202.12s |

### Ressources système observées (docker stats)

| Métrique | data_small | data_medium | data_large |
|---|---|---|---|
| CPU ingestor | ~100% | ~99% | ~99% |
| RAM ingestor | ~54 MB | ~1.75 GB | ~5.48 GB |
| RAM MongoDB | ~457 MB | ~461 MB | ~1.04 GB |
| RAM PostgreSQL | ~146 MB | ~150 MB | ~261 MB |

### Conclusion

> **x10 données = x10 temps = x10 RAM** : l'architecture est linéaire et prévisible.

---

## 🔄 Changer de dataset

Modifie simplement le `.env` :
```env
DATA_SIZE=medium   # ou small / large
```

Puis relance l'ingestor :
```bash
docker compose up --build ingestor
```

---

## 🔒 Sécurité

- Le fichier `.env` (mots de passe) est protégé par le `.gitignore` et n'est jamais poussé sur GitHub
- Utilise `env.example` comme modèle sans données sensibles

---

## 🛠️ Technologies utilisées

- **Docker & Docker Compose** : orchestration des services
- **PostgreSQL 15** : base de données relationnelle
- **MongoDB 6** : base de données NoSQL
- **Python 3.11** : scripts d'ingestion
- **pandas** : lecture des fichiers CSV
- **psycopg2 + execute_values** : connecteur PostgreSQL optimisé
- **pymongo** : connecteur MongoDB
- **pgAdmin 4** : administration PostgreSQL
- **Mongo Express** : administration MongoDB
- **Portainer** : monitoring Docker
