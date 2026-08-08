from scripts import guardar_compragamer_sqlite


def test_main_delega_la_ingesta_al_flujo_oficial(monkeypatch, tmp_path, capsys):
    ruta_db = str(tmp_path / "compragamer.db")
    llamadas = []

    def ejecutar_ingesta_falsa(db_path):
        llamadas.append(db_path)
        return 3

    monkeypatch.setattr(
        guardar_compragamer_sqlite,
        "ejecutar_ingesta",
        ejecutar_ingesta_falsa,
    )

    guardadas = guardar_compragamer_sqlite.main(db_path=ruta_db)

    assert guardadas == 3
    assert llamadas == [ruta_db]
    assert "3" in capsys.readouterr().out
