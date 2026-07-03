# Fichier : tests/test_security.py
# Logique de detection d'intrusion (SecurityMonitor).
import json

from src.security import SecurityMonitor


def _monitor(tmp_path):
    return SecurityMonitor(data_path=str(tmp_path / "known_devices.json"))


def test_nouvel_appareil_est_non_approuve(tmp_path):
    mon = _monitor(tmp_path)
    new, known = mon.analyze_intrusions([{"ip": "10.0.0.2", "mac": "aa:bb:cc:dd:ee:01"}])
    assert len(new) == 1
    assert len(known) == 0
    assert new[0]["trusted"] is False
    assert new[0]["status"] == "NEW"


def test_appareil_approuve_passe_en_connu(tmp_path):
    mon = _monitor(tmp_path)
    mac = "aa:bb:cc:dd:ee:02"
    mon.analyze_intrusions([{"ip": "10.0.0.3", "mac": mac}])
    assert mon.trust_device(mac) is True

    # Rechargement depuis le disque : la confiance doit persister
    mon2 = _monitor(tmp_path)
    new, known = mon2.analyze_intrusions([{"ip": "10.0.0.3", "mac": mac}])
    assert len(new) == 0
    assert len(known) == 1
    assert known[0]["mac"] == mac


def test_appareil_non_approuve_reste_en_alerte(tmp_path):
    mon = _monitor(tmp_path)
    mac = "aa:bb:cc:dd:ee:03"
    mon.analyze_intrusions([{"ip": "10.0.0.4", "mac": mac}])

    # Deuxieme scan sans validation : toujours en "nouveaux"
    new, known = mon.analyze_intrusions([{"ip": "10.0.0.4", "mac": mac}])
    assert len(new) == 1
    assert len(known) == 0


def test_changement_ip_est_suivi(tmp_path):
    mon = _monitor(tmp_path)
    mac = "aa:bb:cc:dd:ee:04"
    mon.analyze_intrusions([{"ip": "10.0.0.5", "mac": mac}])
    mon.trust_device(mac)
    new, known = mon.analyze_intrusions([{"ip": "10.0.0.99", "mac": mac}])
    assert known[0]["ip"] == "10.0.0.99"


def test_trust_device_inconnu_retourne_false(tmp_path):
    mon = _monitor(tmp_path)
    assert mon.trust_device("00:00:00:00:00:00") is False


def test_fichier_corrompu_ne_plante_pas(tmp_path):
    path = tmp_path / "known_devices.json"
    path.write_text("{ceci n'est pas du json")
    mon = SecurityMonitor(data_path=str(path))
    assert mon.known_devices == {}


def test_le_nom_du_scan_est_conserve(tmp_path):
    """Le nom resolu par le serveur (hostname/fabricant) doit etre stocke."""
    mon = _monitor(tmp_path)
    new, _ = mon.analyze_intrusions([{"ip": "10.0.0.7", "mac": "aa:bb:cc:dd:ee:07", "name": "iPhone-de-Mike"}])
    assert new[0]["name"] == "iPhone-de-Mike"

    # Persiste apres rechargement
    mon2 = _monitor(tmp_path)
    assert mon2.known_devices["aa:bb:cc:dd:ee:07"]["name"] == "iPhone-de-Mike"


def test_un_meilleur_nom_remplace_inconnu(tmp_path):
    mon = _monitor(tmp_path)
    mac = "aa:bb:cc:dd:ee:08"
    mon.analyze_intrusions([{"ip": "10.0.0.8", "mac": mac, "name": "Inconnu"}])
    mon.analyze_intrusions([{"ip": "10.0.0.8", "mac": mac, "name": "(Apple, Inc.)"}])
    assert mon.known_devices[mac]["name"] == "(Apple, Inc.)"


def test_rename_device_persiste(tmp_path):
    mon = _monitor(tmp_path)
    mac = "aa:bb:cc:dd:ee:09"
    mon.analyze_intrusions([{"ip": "10.0.0.9", "mac": mac}])
    assert mon.rename_device(mac, "iphone17_mike") is True

    mon2 = _monitor(tmp_path)
    assert mon2.known_devices[mac]["custom_name"] == "iphone17_mike"


def test_rename_mac_inconnue_retourne_false(tmp_path):
    mon = _monitor(tmp_path)
    assert mon.rename_device("00:00:00:00:00:99", "fantome") is False


def test_custom_name_survit_aux_scans_suivants(tmp_path):
    """Le nom personnalise ne doit JAMAIS etre ecrase par le scan."""
    mon = _monitor(tmp_path)
    mac = "aa:bb:cc:dd:ee:10"
    mon.analyze_intrusions([{"ip": "10.0.0.10", "mac": mac, "name": "(Apple, Inc.)"}])
    mon.rename_device(mac, "iphone17_mike")
    mon.trust_device(mac)

    _, known = mon.analyze_intrusions([{"ip": "10.0.0.10", "mac": mac, "name": "autre-hostname"}])
    assert known[0]["custom_name"] == "iphone17_mike"


def test_appareil_valide_ne_revient_jamais_en_intrus(tmp_path):
    """Garantie demandee : une fois valide, plus jamais dans les intrus."""
    mon = _monitor(tmp_path)
    mac = "aa:bb:cc:dd:ee:11"
    mon.analyze_intrusions([{"ip": "10.0.0.11", "mac": mac}])
    mon.trust_device(mac)

    # 50 scans plus tard, IP changee, nom change : toujours 'connu'
    for i in range(50):
        new, known = mon.analyze_intrusions([{"ip": f"10.0.0.{i + 20}", "mac": mac, "name": f"host{i}"}])
        assert new == []
        assert known[0]["mac"] == mac


def test_suggestion_reidentification_quand_nom_correspond(tmp_path):
    """Une nouvelle MAC dont le nom correspond a un appareil de confiance
    doit etre signalee comme probable re-identification."""
    mon = _monitor(tmp_path)
    # Appareil de confiance existant
    mon.analyze_intrusions([{"ip": "10.0.0.20", "mac": "aa:bb:cc:00:00:01", "name": "galaxy-a12.home"}])
    mon.trust_device("aa:bb:cc:00:00:01")
    mon.rename_device("aa:bb:cc:00:00:01", "Galaxy de Mike")

    # Nouvelle MAC (aleatoire) mais meme nom de base + suffixe DHCP
    new, _ = mon.analyze_intrusions([{"ip": "10.0.0.99", "mac": "ff:ee:dd:00:00:02", "name": "galaxy-a12-1.home"}])
    assert len(new) == 1
    assert new[0].get("suggested_match") is not None
    assert new[0]["suggested_match"]["mac"] == "aa:bb:cc:00:00:01"
    assert new[0]["suggested_match"]["name"] == "Galaxy de Mike"


def test_pas_de_suggestion_sans_correspondance(tmp_path):
    mon = _monitor(tmp_path)
    mon.analyze_intrusions([{"ip": "10.0.0.20", "mac": "aa:bb:cc:00:00:03", "name": "livebox.home"}])
    mon.trust_device("aa:bb:cc:00:00:03")
    new, _ = mon.analyze_intrusions([{"ip": "10.0.0.99", "mac": "ff:ee:dd:00:00:04", "name": "chromecast.home"}])
    assert new[0].get("suggested_match") is None


def test_pas_de_suggestion_vers_appareil_non_approuve(tmp_path):
    """On ne suggere que des appareils DE CONFIANCE (sinon aucun interet)."""
    mon = _monitor(tmp_path)
    mon.analyze_intrusions([{"ip": "10.0.0.20", "mac": "aa:bb:cc:00:00:05", "name": "pc-mystere.home"}])
    # non valide
    new, _ = mon.analyze_intrusions([{"ip": "10.0.0.99", "mac": "ff:ee:dd:00:00:06", "name": "pc-mystere.home"}])
    assert new[-1].get("suggested_match") is None


def test_suggestion_non_persistee_sur_disque(tmp_path):
    mon = _monitor(tmp_path)
    mon.analyze_intrusions([{"ip": "10.0.0.20", "mac": "aa:bb:cc:00:00:07", "name": "nest.home"}])
    mon.trust_device("aa:bb:cc:00:00:07")
    mon.analyze_intrusions([{"ip": "10.0.0.99", "mac": "ff:ee:dd:00:00:08", "name": "nest-2.home"}])

    raw = json.loads((tmp_path / "known_devices.json").read_text())
    assert "suggested_match" not in raw["ff:ee:dd:00:00:08"]


def test_link_device_copie_nom_et_approuve(tmp_path):
    mon = _monitor(tmp_path)
    mon.analyze_intrusions([{"ip": "10.0.0.20", "mac": "aa:bb:cc:00:00:09", "name": "x"}])
    mon.trust_device("aa:bb:cc:00:00:09")
    mon.rename_device("aa:bb:cc:00:00:09", "iPhone de Mike")
    mon.analyze_intrusions([{"ip": "10.0.0.99", "mac": "ff:ee:dd:00:00:10", "name": "y"}])

    assert mon.link_device("ff:ee:dd:00:00:10", "aa:bb:cc:00:00:09") is True
    linked = mon.known_devices["ff:ee:dd:00:00:10"]
    assert linked["trusted"] is True
    assert linked["custom_name"] == "iPhone de Mike"


def test_link_device_mac_absente_retourne_false(tmp_path):
    mon = _monitor(tmp_path)
    assert mon.link_device("00:00:00:00:00:aa", "00:00:00:00:00:bb") is False


def test_anciens_appareils_sans_trusted_sont_approuves(tmp_path):
    # Retro-compatibilite : les bases d'avant l'ajout du champ 'trusted'
    path = tmp_path / "known_devices.json"
    path.write_text(json.dumps({"aa:bb:cc:dd:ee:05": {"ip": "10.0.0.6"}}))
    mon = SecurityMonitor(data_path=str(path))
    assert mon.known_devices["aa:bb:cc:dd:ee:05"]["trusted"] is True
