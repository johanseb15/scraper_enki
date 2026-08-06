import pytest

class RegistradorDeFallosDetallados:
    """Plugin personalizado para capturar nombres y detalles de los tests fallidos en todo el proyecto."""
    def __init__(self):
        self.fallos = []

    def pytest_runtest_logreport(self, report):
        # Capturamos si la prueba falló en cualquier fase (setup, call, teardown)
        if report.failed:
            nombre_test = report.nodeid
            # Obtenemos el texto completo del traceback y error
            detalle = getattr(report, "longreprtext", str(report.longrepr))
            self.fallos.append((nombre_test, detalle))

    def pytest_sessionfinish(self, session, exitstatus):
        archivo_salida = "tests_fallidos.txt"
        with open(archivo_salida, "w", encoding="utf-8") as f:
            if self.fallos:
                f.write(f"=== TOTAL DE TESTS FALLIDOS: {len(self.fallos)} ===\n\n")
                for nombre, detalle in self.fallos:
                    f.write(f"TEST: {nombre}\n")
                    f.write(f"DETALLE DEL ERROR:\n{detalle}\n")
                    f.write("=" * 80 + "\n\n")
            else:
                f.write("¡Ningún test falló en la última ejecución!\n")
        
        print(f"\n[INFO] Escaneo de todo el proyecto finalizado.")
        print(f"[INFO] Resultados detallados guardados en '{archivo_salida}'. Tests fallidos: {len(self.fallos)}")

if __name__ == "__main__":
    registrador = RegistradorDeFallosDetallados()
    # Ejecuta pytest en todo el proyecto sin rutas estáticas
    pytest.main(["--cache-clear"], plugins=[registrador])