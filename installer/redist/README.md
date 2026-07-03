# Redistribution de Npcap (édition autonome)

L'édition autonome scanne le réseau en local (ARP via Scapy) et a donc besoin
du pilote **Npcap**. Ce dossier permet de **bundler** Npcap dans l'installeur.

## Comment ça marche

L'installeur [`installer_standalone.iss`](../installer_standalone.iss) gère
Npcap automatiquement :

- **Si `installer/redist/npcap-installer.exe` est présent** → il est copié et
  lancé en silencieux (`/S`) pendant l'installation, uniquement si Npcap n'est
  pas déjà installé sur la machine.
- **S'il est absent** → l'installeur affiche un message invitant l'utilisateur
  à télécharger Npcap lui-même sur https://npcap.com.

Le fichier `npcap-installer.exe` n'est **pas versionné** (exclu par `.gitignore`).
Placez-le ici manuellement avant de compiler l'installeur.

## Deux stratégies — à choisir selon votre usage

### Option A — Ne rien bundler (usage perso / interne / open-source)
Ne mettez rien dans ce dossier. L'utilisateur installe Npcap lui-même
(gratuit). C'est le comportement par défaut, **sans contrainte de licence**.

### Option B — Bundler Npcap (produit commercial « clé en main »)
Pour redistribuer Npcap **à l'intérieur de votre installeur**, la licence
gratuite de Npcap ne suffit pas : il faut une **licence Npcap OEM**
(payante, auprès de Nmap Software LLC — voir https://npcap.com/oem/).

Une fois la licence OEM obtenue :
1. Téléchargez l'installeur Npcap fourni avec votre licence OEM.
2. Renommez-le `npcap-installer.exe` et placez-le dans ce dossier.
3. Recompilez : `ISCC installer/installer_standalone.iss`.

> ⚖️ Les conditions exactes (nombre de copies autorisées, redistribution,
> version silencieuse) évoluent : **vérifiez toujours les termes en vigueur sur
> npcap.com avant toute distribution commerciale**. Le client (version NAS)
> n'est pas concerné : il n'embarque pas Scapy et n'a donc pas besoin de Npcap.
