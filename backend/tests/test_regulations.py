from app.regulations import chunk_text


def test_division_respeta_parrafos_y_limite():
    text = "Párrafo uno.\n\nPárrafo dos.\n\nPárrafo tres."
    chunks = chunk_text(text, max_chars=30)
    assert len(chunks) == 2
    assert chunks[0] == "Párrafo uno.\n\nPárrafo dos."
    assert chunks[1] == "Párrafo tres."


def test_texto_vacio():
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []


def test_parrafo_mayor_que_el_limite_se_conserva_completo():
    long_paragraph = "a" * 50
    chunks = chunk_text(long_paragraph, max_chars=10)
    assert chunks == [long_paragraph]


def test_sin_parrafos_dobles_queda_un_chunk():
    text = "linea uno\nlinea dos\nlinea tres"
    chunks = chunk_text(text, max_chars=900)
    assert chunks == [text]
