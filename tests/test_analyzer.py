# Fichier : tests/test_analyzer.py
# Persistance de l'historique de performance (sans reseau).
import pandas as pd

from src.analyzer import NetworkAnalyzer


def test_save_history_cree_le_csv(tmp_path):
    csv = tmp_path / "sub" / "history.csv"
    analyzer = NetworkAnalyzer(history_file=str(csv))
    analyzer._save_to_history({"timestamp": "2026-07-03 12:00:00", "ping_ms": 12.5,
                               "download_mbps": 300, "upload_mbps": 250})
    assert csv.exists()
    df = pd.read_csv(csv)
    assert len(df) == 1
    assert df.iloc[0]["ping_ms"] == 12.5


def test_save_history_ajoute_sans_dupliquer_entete(tmp_path):
    csv = tmp_path / "history.csv"
    analyzer = NetworkAnalyzer(history_file=str(csv))
    row = {"timestamp": "t", "ping_ms": 1, "download_mbps": 2, "upload_mbps": 3}
    analyzer._save_to_history(row)
    analyzer._save_to_history(row)
    df = pd.read_csv(csv)
    assert len(df) == 2
    assert list(df.columns) == ["timestamp", "ping_ms", "download_mbps", "upload_mbps"]


def test_tailles_de_test_parametrables():
    analyzer = NetworkAnalyzer(download_size_mb=1, upload_size_mb=1)
    assert analyzer.download_size_mb == 1
    assert analyzer.upload_size_mb == 1
