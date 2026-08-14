from src.aplicacion.semantic_normalization_live import (
    classify_new_observation,
)


def test_os_basic_is_local_formateo():
    r = classify_new_observation(
        "Instalación de Sistema Operativo Básico MÁS POPULAR",
        province="Córdoba",
    )
    assert r.semantic_role == "SINGLE_SERVICE"
    assert r.market_scope == "LOCAL_SERVICE"
    assert r.canonical_service == "FORMATEO_INSTALACION_SO"
    assert r.comparability_key == "Córdoba::FORMATEO_INSTALACION_SO"


def test_os_optimized_is_same_canonical():
    r = classify_new_observation(
        "Instalación de Sistema Operativo Optimizado MÁS POPULAR",
        province="Córdoba",
    )
    assert r.canonical_service == "FORMATEO_INSTALACION_SO"


def test_os_complete_is_same_canonical():
    r = classify_new_observation(
        "Instalación Completa de Sistema Operativo MÁS POPULAR",
        province="Córdoba",
    )
    assert r.canonical_service == "FORMATEO_INSTALACION_SO"


def test_pc_no_inicia_maps_to_existing_v4_canonical():
    r = classify_new_observation(
        "Recuperación de PC que No Inicia (pero Enciende) MÁS POPULAR",
        province="Córdoba",
    )
    assert r.semantic_role == "SINGLE_SERVICE"
    assert r.canonical_service == "REPARACION_INICIO_WINDOWS"
    assert r.comparability_key == "Córdoba::REPARACION_INICIO_WINDOWS"


def test_disk_change_clone_is_composite_not_comparable():
    r = classify_new_observation(
        "Cambio+Clonado de Disco en PC de Escritorio MÁS POPULAR",
        province="Córdoba",
    )
    assert r.semantic_role == "COMPOSITE_SERVICE"
    assert r.market_scope == "MIXED_OR_UNKNOWN"
    assert r.canonical_service == ""
    assert r.comparability_key == ""


def test_disk_change_clone_notebook_is_composite():
    r = classify_new_observation(
        "Cambio+Clonado de Disco en Notebook / AIO MÁS POPULAR",
        province="Córdoba",
    )
    assert r.semantic_role == "COMPOSITE_SERVICE"
    assert r.canonical_service == ""


def test_hardware_bundle_is_goods_not_service():
    r = classify_new_observation(
        "Ryzen 3 3200G CPU Integrada GPU DDR4 8GB RAM SSD 240GB Storage",
        province="Buenos Aires",
    )
    assert r.semantic_role == "HARDWARE_PRODUCT"
    assert r.market_scope == "GOODS_MARKET"
    assert r.canonical_service == ""
    assert r.comparability_key == ""


def test_unknown_is_conservatively_unmapped():
    r = classify_new_observation(
        "Servicio especial premium",
        province="CABA",
    )
    assert r.semantic_role == "UNMAPPED"
    assert r.market_scope == "UNKNOWN"
    assert r.canonical_service == ""
