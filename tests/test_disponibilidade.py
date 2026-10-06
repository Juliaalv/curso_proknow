import pandas as pd
import pytest
import requests

from curso_proknowc import disponibilidade
from curso_proknowc.disponibilidade import consultar_doi, verificar_disponibilidade

EMAIL = "participante@exemplo.org"

ABERTO_COM_PDF = {
    "is_oa": True,
    "best_oa_location": {"url": "https://repo.org/artigo", "url_for_pdf": "https://repo.org/artigo.pdf"},
    "oa_locations": [],
}
ABERTO_PDF_EM_OUTRA = {
    "is_oa": True,
    "best_oa_location": {"url": "https://editora.com/artigo", "url_for_pdf": None},
    "oa_locations": [
        {"url": "https://editora.com/artigo", "url_for_pdf": None},
        {"url": "https://arxiv.org/abs/1", "url_for_pdf": "https://arxiv.org/pdf/1"},
    ],
}
ABERTO_SEM_PDF = {
    "is_oa": True,
    "best_oa_location": {"url": "https://editora.com/artigo", "url_for_pdf": None},
    "oa_locations": [{"url": "https://editora.com/artigo", "url_for_pdf": None}],
}
FECHADO = {"is_oa": False, "best_oa_location": None, "oa_locations": []}


def _falso(respostas, chamadas=None):
    """Substitui a chamada HTTP: devolve a resposta do DOI ou levanta a exceção cadastrada."""

    def consultar(doi, email):
        if chamadas is not None:
            chamadas.append((doi, email))
        resposta = respostas[doi]
        if isinstance(resposta, Exception):
            raise resposta
        return resposta

    return consultar


def _erro_http(status):
    resposta = requests.Response()
    resposta.status_code = status
    return requests.HTTPError(f"{status} Error", response=resposta)


def test_aberto_com_pdf_na_melhor_localizacao(monkeypatch):
    monkeypatch.setattr(disponibilidade, "_consultar_unpaywall", _falso({"10.1/a": ABERTO_COM_PDF}))
    r = consultar_doi("10.1/a", EMAIL)
    assert r["acesso_aberto"] is True
    assert r["url_pdf"] == "https://repo.org/artigo.pdf"
    assert r["buscar_capes"] is False


def test_prefere_localizacao_com_pdf(monkeypatch):
    monkeypatch.setattr(disponibilidade, "_consultar_unpaywall", _falso({"10.1/b": ABERTO_PDF_EM_OUTRA}))
    assert consultar_doi("10.1/b", EMAIL)["url_pdf"] == "https://arxiv.org/pdf/1"


def test_sem_pdf_usa_url_da_melhor_localizacao(monkeypatch):
    monkeypatch.setattr(disponibilidade, "_consultar_unpaywall", _falso({"10.1/c": ABERTO_SEM_PDF}))
    r = consultar_doi("10.1/c", EMAIL)
    assert r["url_pdf"] == "https://editora.com/artigo"
    assert r["buscar_capes"] is False


def test_fechado_vai_para_capes(monkeypatch):
    monkeypatch.setattr(disponibilidade, "_consultar_unpaywall", _falso({"10.1/d": FECHADO}))
    r = consultar_doi("10.1/d", EMAIL)
    assert r["acesso_aberto"] is False
    assert r["url_pdf"] is None
    assert r["buscar_capes"] is True


def test_sem_doi_vai_para_capes_sem_consultar(monkeypatch):
    chamadas = []
    monkeypatch.setattr(disponibilidade, "_consultar_unpaywall", _falso({}, chamadas))
    r = consultar_doi(None, EMAIL)
    assert r["acesso_aberto"] is None
    assert r["buscar_capes"] is True
    assert "sem DOI" in r["obs_disponibilidade"]
    assert chamadas == []


def test_falha_de_rede_vira_mensagem(monkeypatch):
    erro = requests.ConnectionError("sem conexão")
    monkeypatch.setattr(disponibilidade, "_consultar_unpaywall", _falso({"10.1/e": erro}))
    r = consultar_doi("10.1/e", EMAIL)
    assert r["acesso_aberto"] is None
    assert r["buscar_capes"] is True
    assert "falha na consulta" in r["obs_disponibilidade"]


def test_doi_nao_encontrado(monkeypatch):
    monkeypatch.setattr(disponibilidade, "_consultar_unpaywall", _falso({"10.1/f": _erro_http(404)}))
    r = consultar_doi("10.1/f", EMAIL)
    assert r["buscar_capes"] is True
    assert "não encontrado" in r["obs_disponibilidade"]


@pytest.mark.parametrize("email", [None, "", "   ", "sem-arroba"])
def test_email_obrigatorio(email):
    with pytest.raises(ValueError, match="e-mail"):
        verificar_disponibilidade(pd.DataFrame({"doi": ["10.1/a"]}), email)


def test_tabela_inteira_nao_para_numa_falha(monkeypatch):
    chamadas = []
    respostas = {"10.1/a": ABERTO_COM_PDF, "10.1/e": requests.Timeout("demorou"), "10.1/d": FECHADO}
    monkeypatch.setattr(disponibilidade, "_consultar_unpaywall", _falso(respostas, chamadas))
    tabela = pd.DataFrame({"id": [1, 2, 3, 4], "doi": ["10.1/a", "10.1/e", None, "10.1/d"]})

    resultado = verificar_disponibilidade(tabela, EMAIL)

    assert list(resultado["acesso_aberto"]) == [True, None, None, False]
    assert list(resultado["url_pdf"]) == ["https://repo.org/artigo.pdf", None, None, None]
    assert list(resultado["buscar_capes"]) == [False, True, True, True]
    assert {e for _, e in chamadas} == {EMAIL}
    assert "acesso_aberto" not in tabela.columns
