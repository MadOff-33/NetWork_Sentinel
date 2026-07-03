# Fichier : tests/test_notifier.py
# Chargement de config et priorite du mot de passe SMTP (sans envoi reel).
import json

from src.notifier import EmailNotifier


def test_config_absente_retourne_none(tmp_path):
    notifier = EmailNotifier(config_file=str(tmp_path / "inexistant.json"))
    assert notifier.config is None


def test_config_vide_retourne_none(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("")
    notifier = EmailNotifier(config_file=str(path))
    assert notifier.config is None


def test_config_corrompue_retourne_none(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{pas du json")
    notifier = EmailNotifier(config_file=str(path))
    assert notifier.config is None


def test_config_valide_est_chargee(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"email_enabled": True, "smtp_user": "a@b.c"}))
    notifier = EmailNotifier(config_file=str(path))
    assert notifier.config["smtp_user"] == "a@b.c"


def test_email_desactive_ne_tente_pas_envoi(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"email_enabled": False}))
    notifier = EmailNotifier(config_file=str(path))
    assert notifier.send_alert([{"mac": "aa:bb"}]) is False


def test_parametres_manquants_refuse_envoi(tmp_path):
    # email_enabled mais pas de serveur/mot de passe -> False sans exception
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"email_enabled": True, "smtp_user": "a@b.c"}))
    notifier = EmailNotifier(config_file=str(path))
    assert notifier.send_alert([{"mac": "aa:bb"}]) is False


def test_smtp_password_env_prioritaire(tmp_path, monkeypatch):
    """Le mot de passe de l'environnement doit primer sur celui du fichier."""
    captured = {}

    class FakeSMTP:
        def __init__(self, server, port):
            captured["server"] = server

        def starttls(self):
            pass

        def login(self, user, password):
            captured["password"] = password

        def sendmail(self, *a):
            pass

        def quit(self):
            pass

    path = tmp_path / "config.json"
    path.write_text(json.dumps({
        "email_enabled": True,
        "smtp_server": "smtp.example.com",
        "smtp_port": 587,
        "smtp_user": "a@b.c",
        "smtp_password": "ancien-du-fichier",
        "alert_emails": ["dest@example.com"],
    }))
    monkeypatch.setenv("SMTP_PASSWORD", "secret-env")
    monkeypatch.setattr("src.notifier.smtplib.SMTP", FakeSMTP)

    notifier = EmailNotifier(config_file=str(path))
    assert notifier.send_alert([{"ip": "10.0.0.2", "mac": "aa:bb"}]) is True
    assert captured["password"] == "secret-env"


def test_destinataire_unique_en_chaine_accepte(tmp_path, monkeypatch):
    """Retro-compatibilite : 'alert_email' (singulier, chaine) fonctionne."""
    sent = {}

    class FakeSMTP:
        def __init__(self, *a):
            pass

        def starttls(self):
            pass

        def login(self, *a):
            pass

        def sendmail(self, sender, recipients, body):
            sent["recipients"] = recipients

        def quit(self):
            pass

    path = tmp_path / "config.json"
    path.write_text(json.dumps({
        "email_enabled": True,
        "smtp_server": "smtp.example.com",
        "smtp_port": 587,
        "smtp_user": "a@b.c",
        "smtp_password": "x",
        "alert_email": "seul@example.com",
    }))
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    monkeypatch.setattr("src.notifier.smtplib.SMTP", FakeSMTP)

    notifier = EmailNotifier(config_file=str(path))
    assert notifier.send_alert([{"mac": "aa:bb"}]) is True
    assert sent["recipients"] == ["seul@example.com"]
