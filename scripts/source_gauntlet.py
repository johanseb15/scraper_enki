"""Ejecuta explícitamente el Source Gauntlet contra fuentes reales."""

from __future__ import annotations

# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

import argparse
from contextlib import nullcontext
from dataclasses import asdict
import json
from pathlib import Path
import tempfile

from src.infraestructura.diagnostico.source_gauntlet import (
    FuenteDiagnostico,
    diagnosticar_api_mercadolibre,
    diagnosticar_fuente,
)


FUENTES = [
    FuenteDiagnostico("REED Technology", "https://www.reed.ar/servicio-tecnico/7137-reparacion-de-pc.html", "Córdoba"),
    FuenteDiagnostico("CiroWhite Informática", "https://cirowhiteinformatica.com.ar/landing/", "Tucumán"),
    FuenteDiagnostico("Compustark", "https://www.compustark.com.ar/", "Santa Fe"),
    FuenteDiagnostico("DMR", "https://dmrwebdesign.com.ar/mantenimiento.html", "Mendoza"),
    FuenteDiagnostico("Interinfo", "https://www.interinfo.net.ar/", "Rosario"),
    FuenteDiagnostico("ACSI", "https://acsisalta.com/reparaciones/", "Salta"),
    FuenteDiagnostico("Visual Informática", "https://visualinformatica.com.ar/Tienda/ServicioTecnico", "Santa Fe"),
    FuenteDiagnostico("Informática Paraná", "https://informaticaparana.com.ar/", "Paraná"),
    FuenteDiagnostico("Novatecnica", "https://www.novatecnica.com.ar/", "Neuquén"),
    FuenteDiagnostico("Fixsur", "https://www.fixsur.com.ar/", "Buenos Aires"),
]

MERCADO_LIBRE_WEB = [
    FuenteDiagnostico(
        "Mercado Libre web — servicio técnico pc",
        "https://listado.mercadolibre.com.ar/servicio-tecnico-pc",
        "Argentina",
    ),
    FuenteDiagnostico(
        "Mercado Libre web — notebook",
        "https://listado.mercadolibre.com.ar/notebook",
        "Argentina",
    ),
]


def ejecutar(browser: str, timeout: float, snapshots: Path | None) -> dict:
    contexto = nullcontext(snapshots) if snapshots else tempfile.TemporaryDirectory(prefix="enki_gauntlet_")
    with contexto as directorio:
        snapshot_dir = Path(directorio) if directorio else None
        fuentes = []
        for fuente in [*FUENTES, *MERCADO_LIBRE_WEB]:
            print(f"[gauntlet] {fuente.nombre}", flush=True)
            fuentes.append(
                diagnosticar_fuente(
                    fuente,
                    browser=browser,
                    timeout=timeout,
                    snapshot_dir=snapshot_dir,
                ).to_dict()
            )
        return {
            "fuentes_web": fuentes,
            "mercado_libre_api": diagnosticar_api_mercadolibre(timeout=timeout),
            "snapshots_temporales": snapshots is None,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnóstico explícito de fuentes reales")
    parser.add_argument("--browser", choices=("auto", "never", "always"), default="auto")
    parser.add_argument("--timeout", type=float, default=20)
    parser.add_argument("--snapshots", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    reporte = ejecutar(args.browser, args.timeout, args.snapshots)
    contenido = json.dumps(reporte, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(contenido, encoding="utf-8")
        print(f"[gauntlet] reporte: {args.output}")
    else:
        print(contenido)


if __name__ == "__main__":
    main()
