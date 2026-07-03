# Fichier : README.md
# 🛡️ Network Sentinel 2025

**Version :** 1.0.0
**Langage :** Python 3.10+
**Auteur :** Dev & User

## 📋 Description
Network Sentinel est un outil d'audit réseau local développé en Python. [cite_start]Il combine la simplicité d'automatisation de Python [cite: 17] [cite_start]avec des capacités d'analyse de données[cite: 11].
Il permet de cartographier le réseau (ARP Scan), de détecter les intrusions (MAC Address filtering) et de mesurer la performance réelle de la connexion.

## 🚀 Fonctionnalités
* **Auto-Discovery :** Détection automatique de la plage IP locale.
* **Security Monitor :** Détection des nouveaux appareils inconnus (Intrusion Detection).
* **Performance Benchmark :**
    * Mesure de latence (Ping).
    * Double moteur de test de débit : API Speedtest (si disponible) + Fallback Téléchargement Direct (si API bloquée).
* **Persistance :** Historisation des données dans `data/` (CSV et JSON).

## 📂 Architecture
D:\NetworkSentinel
├── data/                   # Base de données (JSON/CSV)
├── logs/                   # Journaux d'erreurs
├── src/
│   ├── analyzer.py         # Moteur de test de débit (Hybrid)
│   ├── scanner.py          # Moteur de scan ARP (Scapy)
│   ├── security.py         # Logique de comparaison des intrusions
│   └── ui.py               # Interface Console (UX)
└── main.py                 # Point d'entrée

## 🛠️ Installation & Usage

1. **Pré-requis :**
   - Python 3.x installé.
   - Droits Administrateur (requis pour les paquets ARP bruts).
   - Npcap installé (Windows) en mode "WinPcap compatible".

2. **Installation des dépendances :**
   ```bash
   pip install -r requirements.txt