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


def test_anciens_appareils_sans_trusted_sont_approuves(tmp_path):
    # Retro-compatibilite : les bases d'avant l'ajout du champ 'trusted'
    path = tmp_path / "known_devices.json"
    path.write_text(json.dumps({"aa:bb:cc:dd:ee:05": {"ip": "10.0.0.6"}}))
    mon = SecurityMonitor(data_path=str(path))
    assert mon.known_devices["aa:bb:cc:dd:ee:05"]["trusted"] is True
