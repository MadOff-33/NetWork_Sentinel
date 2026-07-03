# NetworkSentinel — Plan d'implémentation Sprints 0-4

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transformer le projet en dépôt complet, fiable, sécurisé et testé, avec l'architecture Client (PC) ↔ Serveur (NAS Docker) comme référence.

**Architecture:** Le NAS (conteneur Docker `network-sentinel`, Flask :5050) est le moteur 24/7 ; le PC n'exécute que le client GUI (`src/gui_app.py`) à la demande. La version standalone est archivée sur la branche `feature/standalone`. Le NAS n'est **pas** redéployé dans ce plan (le code serveur du dépôt est mis à niveau ; le redéploiement sera proposé au bilan).

**Tech Stack:** Python 3.x, CustomTkinter, Flask, Scapy, pandas, pytest, ruff, GitHub Actions.

## Global Constraints

- NE PAS toucher au NAS (ni conteneur, ni fichiers `/volume1`) — lecture seule autorisée.
- NE PAS créer de remote GitHub (l'utilisateur le fera a posteriori).
- Ne jamais committer : `data/`, `config.json`, `client_config.json`, `dist/`, `build/`, `__pycache__/`, mots de passe.
- Seule action système PC autorisée : arrêter l'exe autonome + supprimer son raccourci de démarrage (validé par l'utilisateur).
- Client lancé À LA DEMANDE (décision par défaut, réversible).
- Compatibilité ascendante : le client mis à jour doit fonctionner avec le serveur actuel du NAS (token d'auth optionnel des deux côtés).
- Messages de commit en français, suffixés `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

---

## SPRINT 0 — Prêt pour GitHub

### Task 1: .gitignore + snapshot + branche d'archive
**Files:** Create `.gitignore` ; branche `feature/standalone`.
- [ ] Créer `.gitignore` (build/, dist/, __pycache__/, *.pyc, logs/, data/, config.json, client_config.json, .venv/, *.exe, *.lnk)
- [ ] `git add -A && git commit` : snapshot complet (inclut fichiers " - Local", server/, spec…)
- [ ] `git branch feature/standalone` (archive de la version autonome)

### Task 2: Restructuration master (référence = client+serveur)
**Files:** Delete `main - Local.py`, `src/gui_app - Local.py` ; Move `debug_network.py` → `tools/debug_network.py` ; Create `client_config.example.json`, `server/config.example.json`.
- [ ] `git rm` des fichiers " - Local" ; `git mv debug_network.py tools/`
- [ ] Exemples de config SANS secrets (client: nas_ip/api_token ; serveur: scan_interval/email/ip_range)
- [ ] Commit

### Task 3: Dépendances
**Files:** Modify `requirements.txt` ; Create `requirements-dev.txt`.
- [ ] `requirements.txt` (client) : customtkinter, matplotlib, pandas, requests, colorama, tabulate, scapy, ping3 — versions épinglées (>= plancher) ; retirer speedtest-cli, pywin32?, winshell (winshell/pywin32 gardés: raccourci démarrage), pyinstaller → dev
- [ ] `requirements-dev.txt` : pyinstaller, pytest, ruff, flask (pour tests serveur)
- [ ] `server/requirements.txt` : retirer speedtest-cli (import supprimé Task 8)
- [ ] Commit

### Task 4: README principal réécrit
**Files:** Modify `README.md`.
- [ ] Architecture réelle (schéma client↔serveur), installation, usage, lien server/README.md, avertissement sécurité, retrait des artefacts `[cite…]`
- [ ] Commit

### Task 5: Désactivation de l'exe autonome au démarrage (action système validée)
- [ ] `Stop-Process -Name NetworkSentinel` (2 processus)
- [ ] Supprimer `%APPDATA%\...\Startup\NetworkSentinel.lnk`
- [ ] Vérifier : plus de processus, plus de lnk. (dist/ conservé sur disque, ignoré par git)

## SPRINT 1 — Fiabilisation

### Task 6: Logging centralisé
**Files:** Create `src/logger.py` ; Modify `src/analyzer.py`, `src/security.py`, `src/notifier.py`, `src/scanner.py`, `server/server.py`.
**Produces:** `get_logger(name) -> logging.Logger` (RotatingFileHandler logs/networksentinel.log 500KB×3 + console).
```python
# src/logger.py
import logging, os
from logging.handlers import RotatingFileHandler
_LOG_DIR = "logs"
def get_logger(name):
    logger = logging.getLogger(name)
    if logger.handlers: return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    try:
        os.makedirs(_LOG_DIR, exist_ok=True)
        fh = RotatingFileHandler(os.path.join(_LOG_DIR, "networksentinel.log"),
                                 maxBytes=500_000, backupCount=3, encoding="utf-8")
        fh.setFormatter(fmt); logger.addHandler(fh)
    except OSError: pass
    sh = logging.StreamHandler(); sh.setFormatter(fmt); logger.addHandler(sh)
    return logger
```
- [ ] Remplacer chaque `except: pass` / `except: return X` par `except <Type> as e: log.warning/error(...)` + comportement identique
- [ ] Commit par groupe (src/, server/)

### Task 7: Client robuste (threads, timeouts, config)
**Files:** Modify `src/gui_app.py`, `main.py`.
- [ ] Toute mise à jour de widget depuis le worker passe par `self.after(0, ...)` (lbl_status lignes 145-148-150 actuelles)
- [ ] `threading.Thread(..., daemon=True)`
- [ ] `timeout=5` sur TOUS les requests (authorize_device, push_settings)
- [ ] Lecture `entry_ip` dans le thread GUI avant lancement du worker (pas depuis le worker)
- [ ] Sauvegarde de `client_config.json` quand l'IP NAS change (bouton/évènement) + champ token (Task 11)
- [ ] Gestion double-clic scan (btn désactivé pendant l'audit)
- [ ] Commit

### Task 8: Serveur — plage IP auto-détectée + analyzer nettoyé
**Files:** Modify `server/server.py`, `src/analyzer.py`, `tools/debug_network.py` (référence).
```python
def detect_ip_range():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close()
        return ".".join(ip.split(".")[:3]) + ".0/24"
    except OSError:
        return "192.168.1.0/24"
```
- [ ] `ip_range` lu depuis config.json sinon `detect_ip_range()`
- [ ] `src/analyzer.py` : retirer `import speedtest` (inutilisé) ; taille du download test paramétrable (`size_mb=10` par défaut)
- [ ] Commit

## SPRINT 2 — Sécurité

### Task 9: Mot de passe SMTP hors config
**Files:** Modify `src/notifier.py`, `server/docker-compose.yml`, `server/README.md`.
- [ ] `send_alert` : `password = os.environ.get("SMTP_PASSWORD") or self.config.get("smtp_password")`
- [ ] docker-compose : bloc `environment:` documenté (SMTP_PASSWORD, API_TOKEN)
- [ ] Commit

### Task 10: Authentification API par token (optionnelle, rétro-compatible)
**Files:** Modify `server/server.py`, `src/gui_app.py`.
- [ ] Serveur : `API_TOKEN = os.environ.get("API_TOKEN", "")` ; `@app.before_request` → si token défini et `request.method == "POST"` et header `X-Auth-Token` ≠ token → 401. (GET reste libre en LAN, POST protégé.)
- [ ] Client : header `X-Auth-Token` envoyé sur les POST si `api_token` présent dans client_config.json
- [ ] Commit

### Task 11: Scan à la demande + plafond d'historique
**Files:** Modify `server/server.py`, `src/gui_app.py`.
- [ ] Serveur : `scan_request = threading.Event()` ; boucle attend `scan_request.wait(timeout=interval)` au lieu de `time.sleep` ; route POST `/scan_now` → `scan_request.set()`
- [ ] Serveur : après append CSV, si > 20 000 lignes → tronquer aux 10 000 dernières
- [ ] Client : bouton "🔎 SCAN NAS IMMÉDIAT" → POST `/scan_now`
- [ ] Commit

## SPRINT 3 — Tests & Qualité

### Task 12: Environnement de test (.venv) 
- [ ] `python -m venv .venv` ; installer requirements + requirements-dev
- [ ] Vérifier `pytest --version`

### Task 13: Tests unitaires
**Files:** Create `tests/test_security.py`, `tests/test_port_scanner.py`, `tests/test_notifier.py`, `tests/test_analyzer.py`, `tests/conftest.py` ; Delete stub vide `tests/test_scanner.py` ou le remplir.
Tests clés (exemples réels dans les fichiers) :
```python
def test_nouvel_appareil_est_non_approuve(tmp_path):
    mon = SecurityMonitor(data_path=str(tmp_path/"kd.json"))
    new, known = mon.analyze_intrusions([{"ip":"10.0.0.2","mac":"aa:bb"}])
    assert len(new) == 1 and new[0]["trusted"] is False
def test_appareil_approuve_passe_en_connu(tmp_path): ...
def test_assess_risk_danger(): assert PortScanner().assess_risk([23])[2] == 2
def test_smtp_password_env_prioritaire(monkeypatch): ...
def test_save_history_cree_csv(tmp_path): ...
```
- [ ] Rédiger, exécuter (rouge→vert), commit

### Task 14: Tests API serveur (Flask test client)
**Files:** Create `tests/test_server_api.py`.
- [ ] Import `server.server` avec sys.path racine ; `app.test_client()` ; tests : GET /status 200+clés ; POST /authorize sans MAC → 400 ; avec API_TOKEN défini, POST sans header → 401, avec header → passe ; /scan_now déclenche l'Event
- [ ] Commit

### Task 15: Lint + CI
**Files:** Create `.github/workflows/ci.yml`, `pyproject.toml` (section ruff).
- [ ] ruff config (line-length 120, target py39) ; corriger les findings simples
- [ ] Workflow : push/PR → install deps → ruff check → pytest
- [ ] Commit

## SPRINT 4 — Améliorations produit

### Task 16: Graphique avec vraies dates
**Files:** Modify `src/gui_app.py`.
- [ ] `update_graph` : si colonne `timestamp` présente → `pd.to_datetime` en abscisse, rotation labels, sinon fallback index
- [ ] Commit

### Task 17: Notification Windows locale sur intrusion (sans dépendance)
**Files:** Modify `src/gui_app.py`.
- [ ] Si nouvelles alertes vs dernier état → toast via PowerShell (guarded try/except, silencieux si échec) ; mémoriser MACs déjà notifiées
- [ ] Commit

### Task 18: Doc build & déploiement final
**Files:** Modify `README.md`, `server/README.md`, `NetworkSentinel.spec` (excludes documentés en commentaire uniquement).
- [ ] Section "Mettre à jour le serveur NAS" (procédure docker compose, à exécuter par l'utilisateur)
- [ ] Section build client PyInstaller (optionnelle)
- [ ] Commit

## VÉRIFICATION FINALE (verification-before-completion)
- [ ] `pytest -v` → tout vert (sortie collée au bilan)
- [ ] `ruff check .` → 0 erreur
- [ ] `python -m py_compile` sur tous les .py
- [ ] Smoke test client : import de `src.gui_app` sans mainloop
- [ ] Vérif git : `git log --oneline`, `git status` propre, aucun secret tracké (`git grep -i password` sur le contenu tracké)
- [ ] Vérif système : exe arrêté, lnk supprimé
- [ ] Bilan final complet à l'utilisateur
