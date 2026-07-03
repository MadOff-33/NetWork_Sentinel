# 📖 Network Sentinel — Fiche d'utilisation

Fiche pratique à garder sous la main. Deux parties : **régler vos appareils**
(pour qu'ils soient bien reconnus) et **utiliser l'application** au quotidien.

---

## 1. Lancer l'application

Double-cliquez sur le raccourci **« Network Sentinel »** du Bureau.
(Ou : `D:\NetworkSentinel\Lancer NetworkSentinel.bat`.)

Le NAS travaille 24h/24 tout seul ; l'application sert juste à **consulter et
piloter**. Vous pouvez la fermer, la surveillance continue.

---

## 2. Bien faire reconnaître un appareil (iPhone / iPad / Android)

Certains téléphones changent d'adresse MAC automatiquement (« adresse privée »),
ce qui les fait apparaître comme de nouveaux intrus. **Ce réglage est sur
l'appareil, pas sur la Box ni dans l'app.**

### iPhone / iPad
1. **Réglages → Wi-Fi**
2. Touchez le **ⓘ** à droite du nom de votre Wi-Fi maison
3. **« Adresse Wi-Fi privée »** :
   - iOS 18+ : choisir **« Fixe »** (adresse privée mais stable chez vous)
   - iOS 14–17 : **désactiver** l'interrupteur
   - ❌ à éviter : **« Rotative »** (c'est elle qui crée des faux intrus)
4. Pour un nom lisible : **Réglages → Général → Informations → Nom**
   (ex : « iPhone 15 Delphine »)

### Android (Samsung, etc.)
1. **Paramètres → Connexions → Wi-Fi**
2. Roue crantée du réseau maison → **« Type d'adresse MAC »**
3. Choisir **« MAC du téléphone »** (au lieu de « MAC aléatoire »)

### Retrouver un appareil « anonyme » dans la liste
S'il apparaît en `iPhone-2`, `Device-7`… : sur l'appareil, notez son adresse
(**Réglages → Général → Informations → Adresse Wi-Fi**) et comparez-la aux MAC
affichées dans l'application ou la Box.

---

## 3. Les boutons de l'application

Onglet **⚠️ Intrus / Nouveaux** — chaque appareil non encore validé :

| Bouton | Effet |
|---|---|
| **Champ nom + 💾** | Donne un nom personnalisé (ex : `iphone17_mike`). Marche aussi dans l'onglet Connus. Jamais écrasé par les scans. |
| **VALIDER** | Marque l'appareil comme sûr → il passe dans « Connus », plus d'alerte. |
| **BLOQUER** | Le marque **🚫 BLOQUÉ** : sort du décompte d'intrus, plus d'email. *(Le blocage réseau réel se fait sur la Box — voir ci-dessous.)* |
| **DÉBLOQUER** | Annule le blocage (l'appareil redevient un intrus à trier). |
| **💡 = Nom ?** | Apparaît quand un intrus est probablement un appareil connu dont la MAC a changé. Un clic confirme et lui redonne son nom + sa validation. |

### Important : « Bloquer » ne coupe pas le Wi-Fi
L'application **ne peut pas** débrancher un appareil du réseau — seule votre
**Box** le peut. Le statut BLOQUÉ sert à votre suivi (« indésirable connu, ne
plus m'alerter »). Pour couper réellement l'accès : interface de la Box →
liste noire / contrôle d'accès Wi-Fi.

---

## 4. Réflexes utiles

- **ACTUALISER** : recharge l'état du NAS.
- **SCAN NAS IMMÉDIAT** : force le NAS à re-scanner tout de suite.
- **Temps Réel (Auto)** : rafraîchit en continu.
- Onglet **Historique Graphique** : débit et latence dans le temps.
- Onglet **Paramètres** : IP du NAS, fréquence de scan, alertes email,
  et **« Enregistrer connexion (PC) »** pour mémoriser l'IP du NAS.

---

## 5. En cas de souci

- **« NAS Injoignable »** : le NAS est éteint, ou l'IP est fausse
  (onglet Paramètres). Par défaut : `192.168.1.100`.
- **Un appareil connu repasse en intrus** : c'est une MAC aléatoire —
  utilisez **💡 Ré-identifier**, ou réglez « Adresse privée → Fixe » (§2).
- **Trop d'emails d'alerte** : validez ou bloquez les appareils concernés.
