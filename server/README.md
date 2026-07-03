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
(`scanner`, `security`, `analyzer`, `notifier`). Pour builder l'image,
le contexte Docker doit inclure ce dossier `src/`. En production, le conteneur
embarque une copie de `src/` dans `/app/src`.

## Déploiement

```bash
docker compose up -d --build
```

Le mode `network_mode: host` est **obligatoire** : sans lui, le scan ARP
(Scapy) ne voit pas le réseau local.
