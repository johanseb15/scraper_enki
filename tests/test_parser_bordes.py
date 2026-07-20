from src.extractor import extraer_datos

def test_si_no_hay_tabla_devuelve_lista_vacia():
    html = "<html><body><h1>Hola</h1></body></html>"
    
    resultados = extraer_datos(html)
    
    assert resultados == []

def test_filas_imcompletas_se_ignoran():
    html = """
    <table>
        <tr>
        <th>Servicio</th>
        <th>Equipo</th>
        <th>Freelance</th>
        <th>Local</th>
        </tr>

        <tr>
            <td>Malware</td>
            <td>PC</td>
            <td>$29.816</td>
        </tr>

        <tr>
            <td>Formateo</td>
            <td>Notebook</td>
            <td>$20.000</td>
            <td>$35.000</td>
        </tr>
    </table>
    """
    resultados = extraer_datos(html)

    assert len(resultados) == 1
    assert resultados[0].servicio == "Formateo"

def test_distintos_formatos_de_precio():
    html = """
    <table>
        <tr>
        <th>Servicio</th>
        <th>Equipo</th>
        <th>Freelance</th>
        <th>Local</th>
        </tr>

        <tr>
            <td>Malware</td>
            <td>PC</td>
            <td>ARS 29.816</td>
            <td>$ 41.411</td>
        </tr>
    </table>
    """
    resultados = extraer_datos(html)

    assert resultados[0].precio_freelance == 29816
    assert resultados[0].precio_local == 41411