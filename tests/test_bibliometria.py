import matplotlib

matplotlib.use("Agg")

import pandas as pd
import pytest
import requests

from curso_proknowc import bibliometria, esquema


def _portfolio():
    return esquema.completar(
        pd.DataFrame(
            {
                "id": ["R00001", "R00002", "R00003"],
                "doi": ["10.1/a", "10.1/b", None],
                "titulo": ["Artigo A", "Artigo B", "Artigo C"],
                "autores": [["Silva, J.", "Santos, M."], ["Silva, J.", "Lima, P."], ["Costa, R."]],
                "ano": [2020, 2022, 2022],
                "periodico": ["Energy", "Energy", "Applied Energy"],
                "palavras_chave": [["lstm", "wind speed"], ["lstm", "forecasting"], ["wind speed"]],
                "grupo": ["A", "A", "repescagem"],
            }
        )
    )


# Respostas falsas do OpenAlex, por DOI e por lista de IDs.
OBRAS = {
    "10.1/a": {"id": "https://openalex.org/W1", "referenced_works": ["https://openalex.org/W10", "https://openalex.org/W11"]},
    "10.1/b": {"id": "https://openalex.org/W2", "referenced_works": ["https://openalex.org/W10", "https://openalex.org/W12"]},
}
DETALHES = {
    "W10": {"id": "https://openalex.org/W10", "title": "Referência muito citada", "publication_year": 2015, "doi": "https://doi.org/10.9999/X"},
    "W11": {"id": "https://openalex.org/W11", "title": "Outra", "publication_year": 2016, "doi": None},
    "W12": {"id": "https://openalex.org/W12", "title": "Mais uma", "publication_year": 2017, "doi": None},
}


def _openalex_falso(chamadas=None):
    def obter(url, params):
        if chamadas is not None:
            chamadas.append((url, params))
        if "/works/doi:" in url:
            doi = url.split("doi:")[1]
            if doi not in OBRAS:
                raise requests.HTTPError("404 Not Found")
            return OBRAS[doi]
        ids = params["filter"].removeprefix("openalex:").split("|")
        return {"results": [DETALHES[i] for i in ids if i in DETALHES]}

    return obter


def test_obter_referencias_preenche_coluna_e_avisa_sem_doi(monkeypatch):
    monkeypatch.setattr(bibliometria, "_obter_json", _openalex_falso())
    tabela, avisos = bibliometria.obter_referencias(_portfolio())
    assert tabela.loc[0, "referencias"] == ["W10", "W11"]
    assert tabela.loc[1, "referencias"] == ["W10", "W12"]
    assert tabela.loc[2, "referencias"] is None
    assert any("Artigo C" in aviso and "sem DOI" in aviso for aviso in avisos)


def test_obter_referencias_repassa_email_e_chave(monkeypatch):
    chamadas = []
    monkeypatch.setattr(bibliometria, "_obter_json", _openalex_falso(chamadas))
    bibliometria.obter_referencias(_portfolio(), email="eu@exemplo.org", chave="abc")
    assert chamadas[0][1]["mailto"] == "eu@exemplo.org"
    assert chamadas[0][1]["api_key"] == "abc"


def test_falha_de_rede_vira_aviso_legivel(monkeypatch):
    def sem_rede(url, params):
        raise requests.ConnectionError("sem conexão")

    monkeypatch.setattr(bibliometria, "_obter_json", sem_rede)
    tabela, avisos = bibliometria.obter_referencias(_portfolio())
    assert tabela["referencias"].isna().all()
    assert any("10.1/a" in aviso and "Não foi possível" in aviso for aviso in avisos)


def test_mais_citadas_conta_e_detalha(monkeypatch):
    monkeypatch.setattr(bibliometria, "_obter_json", _openalex_falso())
    tabela, _ = bibliometria.obter_referencias(_portfolio())
    mais, avisos = bibliometria.referencias_mais_citadas(tabela, n=2)
    assert avisos == []
    assert list(mais.columns) == ["openalex_id", "vezes_citada", "titulo", "ano", "doi", "alinhada"]
    primeira = mais.iloc[0]
    assert primeira["openalex_id"] == "W10"
    assert primeira["vezes_citada"] == 2
    assert primeira["titulo"] == "Referência muito citada"
    assert primeira["doi"] == "10.9999/x"
    assert len(mais) == 2
    assert not mais["alinhada"].any()


def test_mais_citadas_sem_rede_devolve_tabela_sem_detalhes(monkeypatch):
    def sem_rede(url, params):
        raise requests.Timeout("demorou")

    tabela = _portfolio()
    tabela["referencias"] = [["W10"], ["W10", "W12"], None]
    monkeypatch.setattr(bibliometria, "_obter_json", sem_rede)
    mais, avisos = bibliometria.referencias_mais_citadas(tabela)
    assert list(mais["openalex_id"]) == ["W10", "W12"]
    assert mais["titulo"].isna().all()
    assert avisos and "Não foi possível" in avisos[0]


def test_incorporar_sem_nenhuma_marcada_devolve_o_portfolio_sem_avisos(recwarn):
    mais = pd.DataFrame(columns=["openalex_id", "vezes_citada", "titulo", "ano", "doi", "alinhada"])
    resultado = bibliometria.incorporar_complementares(_portfolio(), mais)
    assert list(resultado["id"]) == list(_portfolio()["id"])
    assert not [w for w in recwarn if issubclass(w.category, FutureWarning)]


def test_incorporar_complementares():
    mais = pd.DataFrame(
        {
            "openalex_id": ["W10", "W12", "W2"],
            "vezes_citada": [2, 1, 1],
            "titulo": ["Referência muito citada", "Mais uma", "Artigo B"],
            "ano": [2015, 2017, 2022],
            "doi": ["10.9/x", None, "10.1/b"],
            "alinhada": [True, False, True],
        }
    )
    resultado = bibliometria.incorporar_complementares(_portfolio(), mais)
    assert len(resultado) == 4  # Artigo B já está no portfólio
    nova = resultado.iloc[-1]
    assert nova["grupo"] == "complementar"
    assert nova["titulo"] == "Referência muito citada"
    assert nova["doi"] == "10.9/x"
    assert nova["ano"] == 2015
    assert nova["titulo_norm"] == "referencia muito citada"
    assert resultado["id"].is_unique


def test_frequencias_de_coluna_simples_e_de_lista():
    tabela = _portfolio()
    periodicos = bibliometria.frequencias(tabela, "periodico")
    assert periodicos.iloc[0].tolist() == ["Energy", 2]
    autores = bibliometria.frequencias(tabela, "autores", n=1)
    assert autores.iloc[0].tolist() == ["Silva, J.", 2]
    assert len(autores) == 1


def test_graficos_em_portugues():
    tabela = _portfolio()
    figura = bibliometria.grafico_frequencias(tabela, "palavras_chave")
    assert "Palavras-chave" in figura.axes[0].get_title()
    figura = bibliometria.grafico_anos(tabela)
    assert figura.axes[0].get_xlabel() == "Ano de publicação"


def test_rede_de_coautoria():
    grafo = bibliometria.rede_coautoria(_portfolio())
    assert grafo.nodes["Silva, J."]["artigos"] == 2
    assert grafo.has_edge("Silva, J.", "Santos, M.")
    assert grafo.edges["Silva, J.", "Lima, P."]["peso"] == 1
    assert "Costa, R." in grafo.nodes


def test_rede_de_palavras_chave_com_minimo():
    grafo = bibliometria.rede_palavras_chave(_portfolio(), minimo=2)
    assert set(grafo.nodes) == {"lstm", "wind speed"}
    assert grafo.edges["lstm", "wind speed"]["peso"] == 1


def test_html_pyvis(tmp_path):
    grafo = bibliometria.rede_coautoria(_portfolio())
    caminho = bibliometria.html_pyvis(grafo, tmp_path / "rede.html")
    conteudo = caminho.read_text(encoding="utf-8")
    assert "Silva, J." in conteudo


def test_exportar_vosviewer(tmp_path):
    grafo = bibliometria.rede_coautoria(_portfolio())
    mapa, rede = bibliometria.exportar_vosviewer(grafo, tmp_path, "coautoria")
    linhas_mapa = mapa.read_text(encoding="utf-8").splitlines()
    assert linhas_mapa[0] == "id\tlabel\tweight<Artigos>"
    assert any(linha.endswith("\tSilva, J.\t2") for linha in linhas_mapa)
    linhas_rede = rede.read_text(encoding="utf-8").splitlines()
    assert len(linhas_rede) == grafo.number_of_edges()
    assert all(len(linha.split("\t")) == 3 for linha in linhas_rede)
