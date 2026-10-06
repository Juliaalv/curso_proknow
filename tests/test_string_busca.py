from curso_proknowc import string_busca as s

EIXOS = {
    "Wind Speed": ["wind speed", "wind velocity"],
    "Forecasting": ["forecast*", "prediction"],
}


def test_termo_composto_ganha_aspas():
    assert s.preparar_termo("wind speed") == '"wind speed"'
    assert s.preparar_termo("  forecast* ") == "forecast*"


def test_termo_ja_com_aspas_nao_duplica():
    assert s.preparar_termo('"wind speed"') == '"wind speed"'


def test_sem_curinga_remove_asterisco():
    assert s.preparar_termo("forecast*", curinga=False) == "forecast"


def test_string_generica_or_dentro_and_entre_eixos():
    assert s.string_generica(EIXOS) == '("wind speed" OR "wind velocity") AND (forecast* OR prediction)'


def test_string_scopus():
    assert s.string_scopus(EIXOS) == 'TITLE-ABS-KEY(("wind speed" OR "wind velocity") AND (forecast* OR prediction))'


def test_string_web_of_science():
    assert s.string_wos(EIXOS) == 'TS=(("wind speed" OR "wind velocity") AND (forecast* OR prediction))'


def test_string_ieee_busca_em_titulo_resumo_e_palavras_chave():
    esperado = (
        '(("Document Title":"wind speed" OR "Abstract":"wind speed" OR "Index Terms":"wind speed")'
        ' AND ("Document Title":forecast* OR "Abstract":forecast* OR "Index Terms":forecast*))'
    )
    assert s.string_ieee({"Wind Speed": ["wind speed"], "Forecasting": ["forecast*"]}) == esperado


def test_termos_vazios_sao_ignorados():
    assert s.string_generica({"A": ["wind speed", " "], "B": ["forecast*"]}) == '("wind speed") AND (forecast*)'


def test_gerar_strings_traz_todas_as_bases():
    strings = s.gerar_strings(EIXOS, curinga=False)
    assert set(strings) == {"generica", "scopus", "web_of_science", "ieee"}
    assert "forecast*" not in strings["scopus"]
    assert "forecast OR prediction" in strings["scopus"]


def test_aviso_para_palavra_solta_que_ja_esta_num_termo_composto():
    mensagens = s.avisos({"Wind Speed": ["wind", "wind speed"], "Forecasting": ["forecast*"]})
    assert len(mensagens) == 1
    assert '"wind"' in mensagens[0]


def test_aviso_para_curinga_com_raiz_curta():
    mensagens = s.avisos({"Forecasting": ["for*"]})
    assert len(mensagens) == 1
    assert '"for*"' in mensagens[0]


def test_aviso_para_eixo_vazio():
    mensagens = s.avisos({"Wind Speed": ["wind speed"], "Forecasting": [""]})
    assert mensagens == ['O eixo "Forecasting" está vazio e será ignorado na busca.']


def test_sem_avisos_para_eixos_do_exemplo():
    assert s.avisos(EIXOS) == []
