# Image de base avec Python et dépendances nécessaires
FROM python:3.11-slim-bullseye

# Dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libssl-dev \
    pkg-config \
    cron \
    git \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Installer Rust et Cargo (requis pour cryo)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Installer cryo
RUN cargo install cryo_cli

# Créer le répertoire de l'application
WORKDIR /app
RUN mkdir -p /app/logs

# Copier les fichiers nécessaires
COPY requirements.txt .
COPY README.md .
COPY scripts ./scripts
COPY data ./data
COPY .git .git
COPY .gitignore ./

# Rendre les scripts exécutables
RUN chmod +x ./scripts/*.sh

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Point d'entrée personnalisé
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]