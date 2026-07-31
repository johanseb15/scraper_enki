from src.dominio.servicios import ServicioCanonico
from src.extractor import extraer_datos

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
    assert resultados[0].servicio == ServicioCanonico.FORMATEO
