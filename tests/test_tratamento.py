from curso_proknowc import tratamento as t


def test_doi_remove_prefixo_url_e_poe_em_minusculas():
    assert t.normalizar_doi("https://doi.org/10.1016/J.RENENE.2022.01.001") == "10.1016/j.renene.2022.01.001"
    assert t.normalizar_doi(" doi:10.1109/X.1 ") == "10.1109/x.1"


def test_doi_invalido_vira_vazio():
    assert t.normalizar_doi("") is None
    assert t.normalizar_doi("sem doi") is None


def test_titulo_remove_html_espacos_e_ponto_final():
    assert t.limpar_titulo("  Wind <i>speed</i>   forecasting. ") == "Wind speed forecasting"
    assert t.limpar_titulo("") is None


def test_titulo_normalizado_para_comparacao():
    assert t.normalizar_titulo("Previsão de Vento: um Estudo!") == "previsao de vento um estudo"


def test_autores_scopus_viram_sobrenome_iniciais():
    assert t.autores_scopus("Silva J.; da Costa M.A.") == ["Silva, J.", "da Costa, M.A."]


def test_autores_scopus_formato_antigo_com_virgula():
    assert t.autores_scopus("Wang Y., Li X.") == ["Wang, Y.", "Li, X."]


def test_autores_ieee_viram_sobrenome_iniciais():
    assert t.autores_ieee("Maria A. Santos; Jean-Pierre Dupont") == ["Santos, M.A.", "Dupont, J.-P."]


def test_inteiro():
    assert t.inteiro("2022") == 2022
    assert t.inteiro("abc") is None
    assert t.inteiro("") is None


def test_lista_palavras_minusculas_sem_duplicatas():
    assert t.lista_palavras("Wind speed; LSTM;wind speed; ") == ["wind speed", "lstm"]


def test_resumo_marcador_de_ausencia_vira_vazio():
    assert t.limpar_resumo("[No abstract available]") is None
    assert t.limpar_resumo("Um <b>resumo</b>.") == "Um resumo."


def test_tipo_documento_vocabulario_unico():
    assert t.tipo_documento("Article") == "artigo"
    assert t.tipo_documento("Review") == "revisão"
    assert t.tipo_documento("Conference Paper") == "conferência"
    assert t.tipo_documento("IEEE Conferences") == "conferência"
    assert t.tipo_documento("IEEE Journals") == "artigo"
    assert t.tipo_documento("Book Chapter") == "capítulo"
    assert t.tipo_documento("Editorial") == "outro"
    assert t.tipo_documento("") is None


def test_idioma_vira_codigo_e_usa_o_primeiro():
    assert t.idioma("English; Chinese") == "en"
    assert t.idioma("Portuguese") == "pt"
    assert t.idioma("") is None
