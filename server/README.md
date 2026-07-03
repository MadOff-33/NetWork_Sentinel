# NetworkSentinel — Serveur (NAS)

Partie **serveur** de NetworkSentinel : une API Flask qui scanne le réseau en
tâche de fond et expose l'état au client GUI (`src/gui_app.py`).

Ces fichiers ont été **rapatriés depuis le conteneur Docker en production**
(NAS Synology, 2026-07-03). Ils n'étaient jusqu'ici sauvegardés nulle part
dans le dépôt — c'est désormais corrigé.

## Contenu

| Fichier | Rôle |
|---|---|
| `server.py` | API Flask (port 5050) + boucle de scan en arrière-plan |
| `Dockerfile` | Image basée sur `python:3.9-slim` (Scapy + outils réseau) |
| `requirements.txt` | Dépendances du serveur |
| `docker-compose.yml` | Déploiement (réseau host, volume data, restart always) |

## Endpoints exposés

| Méthode | Route | Description |
|---|---|---|
| GET | `/status` | État courant (appareils, alertes, performances) |
| GET | `/history` | 30 derniers points de l'historique débit/ping |
| POST | `/authorize` | Marque une MAC comme fiable (`{"mac": "..."}`) |
| POST | `/update_settings` | Écrit la config (intervalle, email) |

> ⚠️ **Aucune authentification** sur ces routes aujourd'hui. À sécuriser
> (voir le plan d'audit, Sprint 2).

## Dépendance importante

`server.py` importe les modules métier de `../src/`
(`scanner`, `security`, `analyzer`, `notifier`, `logger`). Le
`docker-compose.yml` utilise donc **la racine du dépôt comme contexte de
build** — c'est déjà configuré, ne buildez pas depuis `server/` avec
`docker build .`.

## Variables d'environnement

| Variable | Rôle |
|---|---|
| `SMTP_PASSWORD` | Mot de passe d'application email (prioritaire sur config.json) |
| `API_TOKEN` | Si défini, toutes les routes POST exigent le header `X-Auth-Token` |
| `DATA_DIR` | Dossier de données (défaut `/app/data`) |

## Déploiement initial

```bash
# Depuis le dossier server/ (le NAS doit avoir docker compose)
SMTP_PASSWORD='xxxx' API_TOKEN='un-token-long-aleatoire' docker compose up -d --build
```

Le mode `network_mode: host` est **obligatoire** : sans lui, le scan ARP
(Scapy) ne voit pas le réseau local.

## Mettre à jour le serveur du NAS (production actuelle)

Le NAS fait tourner l'image `network-sentinel:v1` (ancienne, sans token ni
scan à la demande). Pour passer à la version du dépôt :

```bash
# 1. Copier le depot sur le NAS (ex: /volume1/docker/NetworkSentinel-src)
scp -r . Mike@192.168.1.100:/volume1/docker/NetworkSentinel-src

# 2. Sur le NAS (ssh Mike@192.168.1.100) :
cd /volume1/docker/NetworkSentinel-src
sudo docker build -f server/Dockerfile -t network-sentinel:v2 .
sudo docker stop network-sentinel && sudo docker rm network-sentinel
sudo docker run -d --name network-sentinel --network host --restart always \
     -v /volume1/docker/NetworkSentinel/data:/app/data \
     -e SMTP_PASSWORD='mot-de-passe-application' \
     -e API_TOKEN='un-token-long-aleatoire' \
     network-sentinel:v2
```

Les données existantes (`known_devices.json`, historique) sont conservées :
elles vivent dans le volume, pas dans l'image. Pensez ensuite à retirer
`smtp_password` de `/volume1/docker/NetworkSentinel/data/config.json` et à
reporter le token dans `client_config.json` côté PC.
