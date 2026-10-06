import matplotlib

matplotlib.use("Agg")

from datetime import date

import pandas as pd
import requests

from curso_proknowc import esquema, reconhecimento


def _tabela():
    return esquema.completar(
        pd.DataFrame(
            {
                "id": ["a", "b", "c", "d"],
                "doi": ["10.1000/a", "10.1000/b", None, "10.1000/d"],
                "titulo": ["Artigo A", "Artigo B", "Artigo C", "Artigo D"],
                "citacoes": [10, 5, 3, 1],
                "citacoes_fonte": ["scopus", "ieee", "scopus", "scopus"],
                "citacoes_por_base": [{"scopus": 10}, {"ieee": 5}, {"scopus": 3}, {"scopus": 1}],
            }
        )
    )


# Respostas falsas do OpenAlex (o DOI vem como URL, como na API real). 10.1000/d não existe lá.
CONTAGENS = {"10.1000/a": 60, "10.1000/b": 30}


def _openalex_falso(chamadas=None):
    def obter(url, params):
        if chamadas is not None:
            chamadas.append((url, params))
        dois = params["filter"].removeprefix("doi:").split("|")
        return {"results": [{"doi": f"https://doi.org/{d}", "cited_by_count": CONTAGENS[d]} for d in dois if d in CONTAGENS]}

    return obter


def test_atualizar_citacoes_preenche_fonte_e_data_sem_mexer_nas_bases(monkeypatch):
    monkeypatch.setattr(reconhecimento, "_obter_json", _openalex_falso())
    tabela, avisos = reconhecimento.atualizar_citacoes(_tabela())
    assert tabela.loc[0, "citacoes"] == 60
    assert tabela.loc[1, "citacoes"] == 30
    assert tabela.loc[0, "citacoes_fonte"] == "openalex"
    assert tabela.loc[0, "citacoes_data"] == date.today().isoformat()
    assert tabela.loc[0, "citacoes_por_base"] == {"scopus": 10}
    assert tabela.loc[1, "citacoes_por_base"] == {"ieee": 5}


def test_sem_doi_e_nao_encontrado_ficam_sem_citacao_com_aviso(monkeypatch):
    # Fonte única: não se mistura a contagem de uma base com as do OpenAlex.
    monkeypatch.setattr(reconhecimento, "_obter_json", _openalex_falso())
    tabela, avisos = reconhecimento.atualizar_citacoes(_tabela())
    assert pd.isna(tabela.loc[2, "citacoes"]) and pd.isna(tabela.loc[2, "citacoes_fonte"])
    assert pd.isna(tabela.loc[3, "citacoes"]) and pd.isna(tabela.loc[3, "citacoes_fonte"])
    assert tabela.loc[3, "citacoes_por_base"] == {"scopus": 1}
    assert any("Artigo C" in a and "sem DOI" in a for a in avisos)
    assert any("10.1000/d" in a and "não encontrado" in a for a in avisos)


def test_consulta_em_lotes_com_email_e_chave(monkeypatch):
    chamadas = []
    monkeypatch.setattr(reconhecimento, "_obter_json", _openalex_falso(chamadas))
    monkeypatch.setattr(reconhecimento, "LOTE_OPENALEX", 2)
    reconhecimento.atualizar_citacoes(_tabela(), email="eu@exemplo.org", chave="abc")
    assert [c[1]["filter"] for c in chamadas] == ["doi:10.1000/a|10.1000/b", "doi:10.1000/d"]
    assert chamadas[0][1]["mailto"] == "eu@exemplo.org"
    assert chamadas[0][1]["api_key"] == "abc"


def test_falha_de_rede_vira_aviso_e_deixa_sem_citacao(monkeypatch):
    def sem_rede(url, params):
        raise requests.ConnectionError("sem conexão")

    monkeypatch.setattr(reconhecimento, "_obter_json", sem_rede)
    tabela, avisos = reconhecimento.atualizar_citacoes(_tabela())
    assert tabela["citacoes"].isna().all()
    assert any("Não foi possível" in a for a in avisos)


def test_dividir_por_corte():
    # total 19: a começa em 0%, b em 52,6%, c em 78,9%, d em 94,7%
    acima, abaixo = reconhecimento.dividir_por_corte(_tabela(), percentual=80)
    assert acima["id"].tolist() == ["a", "b", "c"]
    assert abaixo["id"].tolist() == ["d"]
    acima, abaixo = reconhecimento.dividir_por_corte(_tabela(), percentual=50)
    assert acima["id"].tolist() == ["a"]
    assert abaixo["id"].tolist() == ["b", "c", "d"]


def test_dividir_sem_citacoes_deixa_todos_abaixo():
    tabela = _tabela().assign(citacoes=0)
    acima, abaixo = reconhecimento.dividir_por_corte(tabela)
    assert acima.empty and len(abaixo) == 4


def test_artigos_por_corte():
    contagem = reconhecimento.artigos_por_corte(_tabela(), percentuais=[50, 80, 95])
    assert contagem.to_dict("list") == {"corte (%)": [50, 80, 95], "artigos acima do corte": [1, 3, 4]}


def test_curva_citacoes():
    curva = reconhecimento.curva_citacoes(_tabela())
    assert curva["posicao"].tolist() == [1, 2, 3, 4]
    assert round(curva["percentual_acumulado"].iloc[-1], 6) == 100


def test_grafico_curva_tem_linha_do_corte():
    figura = reconhecimento.grafico_curva(_tabela(), percentual=80)
    eixo = figura.axes[0]
    assert "acumuladas" in eixo.get_title()
    assert any(80 in linha.get_ydata() for linha in eixo.get_lines())
