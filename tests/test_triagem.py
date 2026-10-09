import pandas as pd
import pytest

from curso_proknowc import triagem


def _tabela():
    return pd.DataFrame(
        {
            "id": ["R00001", "R00002", "R00003"],
            "titulo": ["Wind speed forecasting with LSTM", "Solar panel cleaning robots", "Deep learning for wind power"],
            "resumo": ["LSTM networks forecast wind speed.", "Robots clean solar panels.", None],
            "decisao_titulo": None,
            "motivo_exclusao": None,
        }
    )


@pytest.fixture
def arquivo(tmp_path):
    return tmp_path / "drive" / "decisoes.csv"


def test_sem_arquivo_nada_decidido(arquivo):
    tabela = _tabela()
    assert triagem.progresso(tabela, "titulo", arquivo) == (0, 3)
    assert triagem.proximo(tabela, "titulo", arquivo)["id"] == "R00001"


def test_registrar_salva_na_hora_e_retoma_de_onde_parou(arquivo):
    tabela = _tabela()
    triagem.registrar(arquivo, "R00001", "titulo", "aceito")
    triagem.registrar(arquivo, "R00002", "titulo", "rejeitado", "fala de energia solar")
    assert arquivo.exists()
    # Simula a sessão caindo: tudo é relido do arquivo.
    assert triagem.progresso(tabela, "titulo", arquivo) == (2, 3)
    assert triagem.proximo(tabela, "titulo", arquivo)["id"] == "R00003"
    decisoes = triagem.carregar_decisoes(arquivo, "titulo")
    assert list(decisoes["decisao"]) == ["aceito", "rejeitado"]
    assert list(decisoes["motivo"]) == ["", "fala de energia solar"]


def test_etapas_sao_independentes(arquivo):
    tabela = _tabela()
    triagem.registrar(arquivo, "R00001", "titulo", "aceito")
    assert triagem.progresso(tabela, "resumo", arquivo) == (0, 3)
    assert triagem.proximo(tabela, "resumo", arquivo)["id"] == "R00001"


def test_valores_invalidos(arquivo):
    with pytest.raises(ValueError):
        triagem.registrar(arquivo, "R00001", "titulo", "talvez")
    with pytest.raises(ValueError):
        triagem.registrar(arquivo, "R00001", "introducao", "aceito")


def test_desfazer_volta_a_ultima_decisao_da_etapa(arquivo):
    tabela = _tabela()
    triagem.registrar(arquivo, "R00001", "titulo", "aceito")
    triagem.registrar(arquivo, "R00001", "resumo", "aceito")
    triagem.registrar(arquivo, "R00002", "titulo", "rejeitado")
    assert triagem.desfazer(arquivo, "titulo") == "R00002"
    assert triagem.proximo(tabela, "titulo", arquivo)["id"] == "R00002"
    assert triagem.progresso(tabela, "resumo", arquivo) == (1, 3)
    assert triagem.desfazer(arquivo, "titulo") == "R00001"
    assert triagem.desfazer(arquivo, "titulo") is None


def test_nova_decisao_substitui_a_anterior(arquivo):
    triagem.registrar(arquivo, "R00001", "titulo", "aceito")
    triagem.registrar(arquivo, "R00001", "titulo", "rejeitado")
    decisoes = triagem.carregar_decisoes(arquivo, "titulo")
    assert list(decisoes["decisao"]) == ["rejeitado"]


def test_texto_com_virgula_e_quebra_de_linha(arquivo):
    triagem.registrar(arquivo, "R00001", "titulo", "rejeitado", 'fora do tema, "solar"\nsem vento')
    assert triagem.carregar_decisoes(arquivo, "titulo")["motivo"].iloc[0] == 'fora do tema, "solar"\nsem vento'


def test_aplicar_separa_aceitos_e_rejeitados(arquivo):
    tabela = _tabela()
    triagem.registrar(arquivo, "R00001", "titulo", "aceito")
    triagem.registrar(arquivo, "R00002", "titulo", "rejeitado", "energia solar")
    triagem.registrar(arquivo, "R00003", "titulo", "rejeitado")
    aceitos, rejeitados = triagem.aplicar(tabela, "titulo", arquivo)
    assert list(aceitos["id"]) == ["R00001"]
    assert list(aceitos["decisao_titulo"]) == ["aceito"]
    assert aceitos["motivo_exclusao"].isna().all()
    assert list(rejeitados["id"]) == ["R00002", "R00003"]
    assert list(rejeitados["decisao_titulo"]) == ["rejeitado", "rejeitado"]
    assert list(rejeitados["motivo_exclusao"]) == ["não alinhado pelo título", "não alinhado pelo título"]
    assert list(rejeitados["motivo_pesquisador"]) == ["energia solar", None]


def test_aplicar_cria_a_coluna_da_etapa(arquivo):
    tabela = _tabela()
    for id_artigo in tabela["id"]:
        triagem.registrar(arquivo, id_artigo, "texto", "rejeitado")
    _, rejeitados = triagem.aplicar(tabela, "texto", arquivo)
    assert list(rejeitados["decisao_texto"]) == ["rejeitado"] * 3
    assert rejeitados["motivo_exclusao"].iloc[0] == "não alinhado pelo texto completo"


def test_aplicar_com_pendentes_avisa(arquivo):
    triagem.registrar(arquivo, "R00001", "titulo", "aceito")
    with pytest.raises(ValueError, match="2 artigo"):
        triagem.aplicar(_tabela(), "titulo", arquivo)


def test_ordenar_por_similaridade():
    pytest.importorskip("sklearn")
    ordenada = triagem.ordenar_por_similaridade(_tabela(), "previsão de wind speed com LSTM")
    assert ordenada["id"].iloc[0] == "R00001"
    assert ordenada["id"].iloc[-1] == "R00002"
    assert list(ordenada.index) == [0, 1, 2]


def test_interface_monta_e_registra_cliques(arquivo):
    pytest.importorskip("ipywidgets")
    tabela = _tabela()
    tela = triagem.interface(tabela, "resumo", arquivo)
    tela.motivo.value = "fora do tema"
    tela.rejeitar.click()
    tela.aceitar.click()
    assert triagem.progresso(tabela, "resumo", arquivo) == (2, 3)
    assert tela.barra.value == 2
    assert tela.motivo.value == ""
    tela.voltar.click()
    assert triagem.progresso(tabela, "resumo", arquivo) == (1, 3)
    decisoes = triagem.carregar_decisoes(arquivo, "resumo")
    assert list(decisoes["motivo"]) == ["fora do tema"]


def test_tela_do_texto_completo_orienta_a_ler_na_base():
    artigo = pd.Series({"id": "R1", "titulo": "Wind", "resumo": "Resumo longo", "doi": "10.1/abc",
                        "url_pdf": "https://repo.org/a.pdf", "buscar_capes": False})
    tela = triagem._texto(artigo, "texto")
    assert "Leia o texto completo" in tela
    assert "Resumo longo" not in tela
    assert 'href="https://doi.org/10.1/abc"' in tela
    assert 'href="https://repo.org/a.pdf"' in tela
    assert "CAPES" not in tela


def test_tela_do_texto_completo_fechado_indica_capes():
    artigo = pd.Series({"id": "R1", "titulo": "Wind", "doi": "10.1/abc", "url_pdf": None, "buscar_capes": True})
    tela = triagem._texto(artigo, "texto")
    assert "Portal de Periódicos CAPES" in tela
    assert "PDF" not in tela


def test_tela_do_texto_completo_sem_doi_nem_disponibilidade():
    tela = triagem._texto(pd.Series({"id": "R1", "titulo": "Wind"}), "texto")
    assert "Leia o texto completo" in tela
    assert "doi.org" not in tela
