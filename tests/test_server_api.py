# Fichier : tests/test_server_api.py
# API Flask du serveur NAS (test_client, sans reseau ni thread de scan).
import importlib


def load_server(monkeypatch, tmp_path, token=None):
    """(Re)charge server.server avec un DATA_DIR isole et un token eventuel."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    if token:
        monkeypatch.setenv("API_TOKEN", token)
    else:
        monkeypatch.delenv("API_TOKEN", raising=False)
    import server.server as srv
    importlib.reload(srv)
    return srv


def test_status_expose_les_cles_vitales(monkeypatch, tmp_path):
    srv = load_server(monkeypatch, tmp_path)
    client = srv.app.test_client()
    r = client.get("/status")
    assert r.status_code == 200
    data = r.get_json()
    for key in ("devices", "alerts", "performance", "last_update"):
        assert key in data
    assert "ping_ms" in data["performance"]


def test_authorize_sans_mac_renvoie_400(monkeypatch, tmp_path):
    srv = load_server(monkeypatch, tmp_path)
    client = srv.app.test_client()
    r = client.post("/authorize", json={})
    assert r.status_code == 400


def test_history_vide_renvoie_liste_vide(monkeypatch, tmp_path):
    srv = load_server(monkeypatch, tmp_path)
    client = srv.app.test_client()
    r = client.get("/history")
    assert r.status_code == 200
    assert r.get_json() == []


def test_scan_now_declenche_l_evenement(monkeypatch, tmp_path):
    srv = load_server(monkeypatch, tmp_path)
    client = srv.app.test_client()
    assert not srv.scan_request.is_set()
    r = client.post("/scan_now", json={})
    assert r.status_code == 200
    assert srv.scan_request.is_set()


def test_post_sans_token_refuse_quand_token_configure(monkeypatch, tmp_path):
    srv = load_server(monkeypatch, tmp_path, token="secret123")
    client = srv.app.test_client()
    r = client.post("/scan_now", json={})
    assert r.status_code == 401


def test_post_avec_mauvais_token_refuse(monkeypatch, tmp_path):
    srv = load_server(monkeypatch, tmp_path, token="secret123")
    client = srv.app.test_client()
    r = client.post("/scan_now", json={}, headers={"X-Auth-Token": "mauvais"})
    assert r.status_code == 401


def test_post_avec_bon_token_accepte(monkeypatch, tmp_path):
    srv = load_server(monkeypatch, tmp_path, token="secret123")
    client = srv.app.test_client()
    r = client.post("/scan_now", json={}, headers={"X-Auth-Token": "secret123"})
    assert r.status_code == 200


def test_get_reste_libre_meme_avec_token(monkeypatch, tmp_path):
    # Seules les routes POST (modification) sont protegees.
    srv = load_server(monkeypatch, tmp_path, token="secret123")
    client = srv.app.test_client()
    assert client.get("/status").status_code == 200


def test_update_settings_ecrit_la_config(monkeypatch, tmp_path):
    srv = load_server(monkeypatch, tmp_path)
    client = srv.app.test_client()
    r = client.post("/update_settings", json={"scan_interval": 60})
    assert r.status_code == 200
    assert (tmp_path / "config.json").exists()


def test_detect_ip_range_renvoie_un_slash_24(monkeypatch, tmp_path):
    srv = load_server(monkeypatch, tmp_path)
    assert srv.detect_ip_range().endswith(".0/24")
