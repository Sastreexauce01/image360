### README.md
# Image 360° Generator API

API FastAPI pour générer des images panoramiques 360° à partir d'un ensemble d'images.

## Installation

1. Créer un environnement virtuel:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

2. Installer les dépendances:
```bash
pip install -r requirements.txt
```

## Utilisation

1. Démarrer l'API:
```bash
python -m app.main
# ou
uvicorn app.main:app --reload
```

2. Accéder à la documentation:
- API: http://localhost:8000
- Documentation Swagger: http://localhost:8000/docs
- Documentation ReDoc: http://localhost:8000/redoc

## Endpoints

### POST /api/v1/generate-360
Génère une image panoramique 360°

**Paramètres:**
- `images`: Liste d'images (2-20 fichiers)
- `quality`: Qualité (low, medium, high)
- `format`: Format de sortie (jpg, png)
- `resolution`: Résolution (2K, 4K, 8K)

**Exemple d'utilisation:**
```bash
curl -X POST "http://localhost:8000/api/v1/generate-360" \
  -F "images=@image1.jpg" \
  -F "images=@image2.jpg" \
  -F "quality=high" \
  -F "format=jpg" \
  -F "resolution=4K" \
  --output panorama_360.jpg
```

### GET /api/v1/supported-formats
Retourne les formats et options supportés

## Configuration

Créer un fichier `.env` à la racine:
```
DEBUG=True
MAX_FILE_SIZE=10485760
MAX_FILES=20
TEMP_DIR=/tmp
```