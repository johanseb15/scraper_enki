def test_parsea_producto_real_de_venex():
    html = """
    <div class="product-box">
        <h3 class="product-box-title">
            Placa De Video RTX 4060
        </h3>

        <span class="current-price">
            $ 589.999
        </span>
    </div>
    """

    parser = VenexParser()

    resultado = parser.parsear(
        html_content=html,
        url_fuente="https://www.venex.com.ar/componentes-de-pc"
    )

    assert len(resultado) == 1
    assert resultado[0].empresa_nombre == "Venex"
    assert resultado[0].servicio_raw == "Placa De Video RTX 4060"
    assert resultado[0].precio_raw == "$ 589.999"