# Fichier : tests/test_port_scanner.py
# Evaluation de risque des ports (sans reseau).
from src.port_scanner import PortScanner


def test_aucun_port_est_securise():
    color, msg, risk = PortScanner().assess_risk([])
    assert risk == 0
    assert msg == "Sécurisé"


def test_port_danger_telnet():
    color, msg, risk = PortScanner().assess_risk([23])
    assert risk == 2
    assert "23" in msg


def test_port_attention_smb():
    color, msg, risk = PortScanner().assess_risk([445])
    assert risk == 1


def test_port_info_https():
    color, msg, risk = PortScanner().assess_risk([443])
    assert risk == 0
    assert "443" in msg


def test_le_pire_risque_gagne():
    # HTTPS (0) + RDP (2) => danger global
    color, msg, risk = PortScanner().assess_risk([443, 3389])
    assert risk == 2


def test_port_inconnu_risque_zero():
    color, msg, risk = PortScanner().assess_risk([54321])
    assert risk == 0


def test_scan_device_sans_port_retourne_liste_vide(monkeypatch):
    scanner = PortScanner()
    monkeypatch.setattr(scanner, "quick_scan", lambda ip: [])
    assert scanner.scan_device("10.0.0.1") == []


def test_scan_device_formate_les_resultats(monkeypatch):
    scanner = PortScanner()
    monkeypatch.setattr(scanner, "quick_scan", lambda ip: [23])
    out = scanner.scan_device("10.0.0.1")
    assert len(out) == 1
    assert "Telnet" in out[0]
    assert "DANGER" in out[0]
