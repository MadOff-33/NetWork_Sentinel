# 🛡️ Network Sentinel

**Surveillance de réseau local 24h/24** — détection d'intrus (scan ARP), scan de ports,
mesure de performance, alertes email — pilotée depuis une interface graphique Windows.

**Langage :** Python 3.9+ · **Licence :** projet personnel

## 📐 Architecture

Le système fonctionne en **deux moitiés** :

```
┌──────────────────────┐         HTTP :5050          ┌──────────────────────────┐
│   PC Windows         │ ──────────────────────────► │   NAS Synology (Docker)  │
│   CLIENT (GUI)       │   /status /history          │   SERVEUR (Flask)        │
│   main.py            │   /authorize /scan_now      │   server/server.py       │
│   src/gui_app.py     │ ◄────────────────────────── │   scan ARP en continu    │
└──────────────────────┘         JSON                └──────────────────────────┘
```

- **Le serveur (NAS)** est le moteur : il tourne 24h/24 dans un conteneur Docker,
  scanne le réseau à intervalle régulier, mémorise les appareils, détecte les
  nouveaux venus et envoie les alertes email. Voir [server/README.md](server/README.md).
- **Le client (PC)** est une télécommande : il affiche l'état, les graphiques
  d'historique, et permet d'autoriser les nouveaux appareils. Il ne scanne rien
  lui-même. À lancer **à la demande**.

> 💡 Une ancienne version **autonome** (tout sur le PC, sans NAS) est archivée sur
> la branche git `feature/standalone`.

## 📂 Structure du dépôt

```
NetworkSentinel/
├── main.py                    # Point d'entrée du CLIENT
├── src/                       # Modules partagés client/serveur
│   ├── gui_app.py             #   Interface graphique (client)
│   ├── scanner.py             #   Scan ARP - Scapy (utilisé par le serveur)
│   ├── security.py            #   Détection d'intrusion (serveur)
│   ├── analyzer.py            #   Tests de performance (serveur)
│   ├── notifier.py            #   Alertes email (serveur)
│   ├── port_scanner.py        #   Scan de ports TCP
│   └── logger.py              #   Logging centralisé (logs/)
├── server/                    # Partie SERVEUR (déployée sur le NAS)
│   ├── server.py              #   API Flask + boucle de scan
│   ├── Dockerfile             #   Image Docker
│   └── docker-compose.yml     #   Déploiement
├── tests/                     # Tests unitaires et d'API (pytest)
├── tools/debug_network.py     # Diagnostic réseau (Scapy vs route réelle)
└── docs/                      # Plans et documentation
```

## 🚀 Installation du client (PC)

```bash
pip install -r requirements.txt
copy client_config.example.json client_config.json
:: éditez client_config.json : IP du NAS + token API éventuel
python main.py
```

## 🐳 Installation du serveur (NAS)

Voir la documentation dédiée : **[server/README.md](server/README.md)**
(build Docker, volume de données, variables d'environnement, mise à jour).

## ⚙️ Configuration

| Fichier | Où | Contenu |
|---|---|---|
| `client_config.json` | PC (racine du projet) | `nas_ip`, `api_token` |
| `data/config.json` | NAS (volume Docker) | intervalle, plage IP, email |
| Variables d'env. conteneur | NAS | `SMTP_PASSWORD`, `API_TOKEN` |

**Aucun secret n'est versionné** : les mots de passe passent par des variables
d'environnement, et `data/`, `config.json`, `client_config.json` sont exclus par
`.gitignore`.

## 🧪 Tests & développement

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
pytest -v          # tests unitaires + API
ruff check .       # lint
```

## 🔒 Sécurité — points connus

- L'API du serveur est accessible sur le LAN ; les routes de modification (POST)
  peuvent être protégées par un token (`API_TOKEN` côté serveur, `api_token` côté
  client). Sans token configuré, l'API reste ouverte — réservez-la à un réseau de
  confiance.
- Le scan ARP nécessite des privilèges élevés (conteneur en `network_mode: host`
  sur le NAS ; droits administrateur si exécution locale).
- Cet outil est destiné à **votre propre réseau** uniquement.

## 🛠️ Build de l'exe client (optionnel)

```bash
pip install -r requirements-dev.txt
pyinstaller NetworkSentinel.spec
```

L'exécutable est généré dans `dist/` (non versionné).
