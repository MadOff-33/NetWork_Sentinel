# Image du serveur NetworkSentinel.
# A builder depuis la RACINE du depot (le serveur importe src/) :
#   docker build -f server/Dockerfile -t network-sentinel:v2 .
# ou via server/docker-compose.yml (contexte deja configure).
FROM python:3.9-slim

# Outils systeme necessaires pour Scapy et le reseau
RUN apt-get update && apt-get install -y \
    gcc \
    libpcap-dev \
    net-tools \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/server.py .
COPY src ./src

# Lancement du serveur
CMD ["python", "server.py"]
