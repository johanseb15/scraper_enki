from src.aplicacion.semantic_normalization_live import (
    classify_new_observation,
)


def test_instalacion_so_con_backup_no_se_admite_como_servicio_simple_comparable():
    """
    Una instalación de sistema operativo que incluye explícitamente backup
    representa un servicio compuesto.

    El precio observado no puede asignarse artificialmente sólo al formateo.
    """
    resultado = classify_new_observation(
        "Instalación de Sistema Operativo con Backup de Datos",
        province="Córdoba",
    )

    assert resultado.semantic_role == "COMPOSITE_SERVICE"
    assert resultado.market_scope == "MIXED_OR_UNKNOWN"
    assert resultado.matched_services == (
        "FORMATEO_INSTALACION_SO|BACKUP_DATOS"
    )
    assert resultado.canonical_service == ""
    assert resultado.comparability_key == ""
