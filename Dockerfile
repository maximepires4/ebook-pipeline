# Base légère Python
FROM python:3.12-slim

# Variables d'environnement pour Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Installation des dépendances système (curl pour télécharger kepubify)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# --- Installation sécurisée de Kepubify (v4.0.4) ---
# On fixe la version et on place le binaire dans le PATH global
RUN curl -L "https://github.com/pgaskin/kepubify/releases/download/v4.0.4/kepubify-linux-64bit" -o /usr/local/bin/kepubify \
    && chmod +x /usr/local/bin/kepubify

# Vérification simple que kepubify fonctionne
RUN kepubify --version

# Copie des requirements et installation
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# Création des dossiers pour les volumes et attribution des droits
RUN mkdir -p /app/data /app/output /app/config

# --- Sécurité : Utilisateur non-root ---
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Bascule vers l'utilisateur standard
USER appuser

# Point d'entrée : lance le pipeline sur le dossier data
ENTRYPOINT ["python", "main.py"]
CMD ["/app/data"]
