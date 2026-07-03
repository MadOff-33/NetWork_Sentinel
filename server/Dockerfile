FROM python:3.9-slim

# Installation des outils système nécessaires pour Scapy et le réseau
RUN apt-get update && apt-get install -y \
    gcc \
    libpcap-dev \
    net-tools \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Lancement du serveur
CMD ["python", "server.py"]