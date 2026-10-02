"""Proyección reproducible y offline de las dos capturas verificadas de la demo.

No descarga ni reemplaza evidencia. Interpretación manual acotada, versionada.
"""
import argparse
import json
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    base = ROOT / "data/demo"
    captures = json.loads((base / "captures.json").read_text(encoding="utf-8"))
    observations = []

    def add(capture, provider, service, raw_service, price, excerpt, *, modality=None,
            unit=None, scope=None, comparable=False, city=None, effective=None, note=None):
        observations.append({"id":f"{capture}-{len(observations)+1:02d}", "capture_id":capture,
            "provider":provider, "service":service, "service_raw":raw_service,
            "price_raw":price, "source_excerpt":excerpt, "currency":"ARS",
            "province":None, "city":city, "modality":modality,"unit":unit,"scope":scope,
            "effective_date":effective, "evidence_kind":"public_capture",
            "comparability_established":comparable,"comparability_note":note})

    soup = BeautifulSoup((base / "bairescloud.html").read_bytes(),"html.parser")
    for tr in soup.select("tbody tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cells) != 3:
            continue
        name, device, price = cells
        service = None
        if "malware" in name.lower(): service = "malware"
        elif "Formateo" in name: service = "formateo"
        elif "Conexión Remota" in name: service = "soporte_tecnico"
        if service is None:
            continue
        remote = service == "soporte_tecnico"
        add("bairescloud","BairesCloud",service,name,price," ".join(cells),
            modality="remoto" if remote else None, unit="hora" if remote else None,
            scope="Conexión remota por 1 hora · PC/Notebook/AIO" if remote else None,
            comparable=remote,effective="2026-02 (mes publicado; día desconocido)",
            note="Tarifario argentino en pesos ($). Febrero 2026 publicado; vigencia actual sin confirmar. Buenos Aires en título, sin provincia/ciudad inequívoca. Equipos: " + device +
                 (". Referencia individual de una hora; tareas e impuestos no detallados." if remote else ". Modalidad y unidad de cobro no establecidas; excluida del benchmark."))

    text = " ".join(BeautifulSoup((base / "bitz.html").read_bytes(),"html.parser").stripped_strings)
    # Se exige coincidencia literal. Los textos originales no se corrigen.
    for service, name, price, excerpt, kwargs in [
        ("malware","Eliminación de malware","$40,000","Eliminación de malware Precio: $40,000",{}),
        ("soporte_tecnico","Conexión Remota (hasta 1 hora)","$40,000",
         "Conexión Remota (hasta 1 hora) Problemas Generales. $40,000",
         {"modality":"remoto","unit":"sesión de hasta 1 hora",
          "scope":"Problemas generales · sesión remota de hasta 1 hora", "comparable":True}),
        ("soporte_tecnico","Visita a domicilio","Consultar","Visita a domicilio Hasta 1 hora. Consultar",
         {"modality":"domicilio","unit":"sesión de hasta 1 hora"}),
        ("formateo","Formateo + Configuración","$35,000",
         "Formateo + Configuración Características del equipo: PC Antigua Básica $15,000 PC Todas $35,000",{}),
        ("mantenimiento","Mantenimiento Básico","$40,000",
         "Mantenimiento Básico Características del equipo: PC Antigua Básica $20,000 PC Gamer Integrados/Básica $40,000",{}),
    ]:
        if excerpt not in text:
            raise ValueError(f"Cambió la estructura de la captura: {name}")
        add("bitz","Bitz Computación",service,name,price,excerpt,city="Villa de Mayo",
            note="Sucre 186 - Villa de Mayo publicado en contacto; provincia no declarada. Pesos ($) de comercio argentino. Fecha efectiva desconocida. Hora máxima de sesión se conserva separada de tarifa por hora.",**kwargs)
    result = {"schema_version":"enki-demo-evidence-v1", "captures":captures,
              "observations":observations,
              "policy":"Capturas HTTP 200 con TLS verificado. Fuentes de proveedores. Fechas efectivas sólo cuando publicadas. Comparabilidad conservadora; no representa el mercado argentino."}
    (base / "evidence.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"{len(observations)} observaciones proyectadas offline.")


if __name__ == "__main__":
    main()
