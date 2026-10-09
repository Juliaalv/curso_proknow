"""Teste de representatividade e análise bibliométrica do portfólio (A9).

Parte 1: referências de cada artigo pelo OpenAlex (`referenced_works`), as mais citadas pelo
portfólio e a incorporação das que o pesquisador marcar como alinhadas (grupo "complementar").
Parte 2: contagens e gráficos (periódicos, autores, palavras-chave e anos).
"""

from collections import Counter

import matplotlib.pyplot as plt
import pandas as pd
import requests

from curso_proknowc import esquema
from curso_proknowc.tratamento import normalizar_doi, normalizar_titulo

OPENALEX = "https://api.openalex.org"
LOTE_OPENALEX = 50  # máximo de IDs por consulta com filtro

ROTULOS = {
    "periodico": "Periódicos",
    "autores": "Autores",
    "palavras_chave": "Palavras-chave",
    "ano": "Anos",
}


# ---------- Parte 1: representatividade ----------


def _obter_json(url: str, params: dict) -> dict:
    """Única função que acessa a rede (substituída nos testes)."""
    resposta = requests.get(url, params=params, timeout=30)
    resposta.raise_for_status()
    return resposta.json()


def _parametros(email=None, chave=None) -> dict:
    params = {}
    if email:
        params["mailto"] = email
    if chave:
        params["api_key"] = chave
    return params


def _id_curto(url_openalex: str) -> str:
    return url_openalex.rsplit("/", 1)[-1]


def obter_referencias(portfolio: pd.DataFrame, email=None, chave=None):
    """Preenche `referencias` com os IDs do OpenAlex citados por cada artigo. Devolve (tabela, avisos)."""
    tabela = portfolio.copy()
    params = _parametros(email, chave) | {"select": "id,referenced_works"}
    referencias, avisos = [], []
    for _, artigo in tabela.iterrows():
        if not artigo["doi"]:
            referencias.append(None)
            avisos.append(f"O artigo '{artigo['titulo']}' está sem DOI; suas referências não foram consultadas.")
            continue
        try:
            obra = _obter_json(f"{OPENALEX}/works/doi:{artigo['doi']}", params)
            referencias.append([_id_curto(r) for r in obra.get("referenced_works", [])])
        except (requests.RequestException, ValueError) as erro:
            referencias.append(None)
            avisos.append(f"Não foi possível consultar o DOI {artigo['doi']} no OpenAlex ({erro}).")
    tabela["referencias"] = referencias
    return tabela, avisos


def _detalhar(ids: list, params: dict) -> dict:
    detalhes = {}
    for inicio in range(0, len(ids), LOTE_OPENALEX):
        lote = ids[inicio : inicio + LOTE_OPENALEX]
        filtro = params | {
            "filter": "openalex:" + "|".join(lote),
            "per_page": LOTE_OPENALEX,
            "select": "id,title,publication_year,doi",
        }
        for obra in _obter_json(f"{OPENALEX}/works", filtro).get("results", []):
            detalhes[_id_curto(obra["id"])] = obra
    return detalhes


def referencias_mais_citadas(portfolio: pd.DataFrame, n=20, email=None, chave=None):
    """As n referências mais citadas pelo portfólio, com título/ano/DOI quando o OpenAlex responde.

    A coluna `alinhada` vem False: o pesquisador marca as alinhadas. Devolve (tabela, avisos).
    """
    contagem = Counter(r for refs in portfolio["referencias"] if refs is not None for r in refs)
    mais = pd.DataFrame(contagem.most_common(n), columns=["openalex_id", "vezes_citada"])
    avisos = []
    try:
        detalhes = _detalhar(list(mais["openalex_id"]), _parametros(email, chave))
    except (requests.RequestException, ValueError) as erro:
        detalhes = {}
        avisos.append(f"Não foi possível obter título, ano e DOI das referências no OpenAlex ({erro}).")
    obra = mais["openalex_id"].map(lambda i: detalhes.get(i, {}))
    mais["titulo"] = obra.map(lambda o: o.get("title"))
    mais["ano"] = obra.map(lambda o: o.get("publication_year")).astype("Int64")
    mais["doi"] = obra.map(lambda o: normalizar_doi(o.get("doi")))
    mais["alinhada"] = False
    return mais, avisos


def incorporar_complementares(portfolio: pd.DataFrame, mais_citadas: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta ao portfólio as referências marcadas como alinhadas, no grupo "complementar".

    As que já estão no portfólio (mesmo DOI) não são repetidas.
    """
    marcadas = mais_citadas[mais_citadas["alinhada"].astype(bool)]
    dois_portfolio = set(portfolio["doi"].dropna())
    marcadas = marcadas[~marcadas["doi"].isin(dois_portfolio)]
    if marcadas.empty:
        return portfolio.copy()
    novas = pd.DataFrame(
        {
            "id": [f"C{n:05d}" for n in range(1, len(marcadas) + 1)],
            "doi": list(marcadas["doi"]),
            "titulo": list(marcadas["titulo"]),
            "titulo_norm": [normalizar_titulo(t) for t in marcadas["titulo"]],
            "ano": list(marcadas["ano"]),
            "etapa_atual": "representatividade",
            "grupo": "complementar",
        }
    )
    return esquema.completar(pd.concat([portfolio, novas], ignore_index=True))


# ---------- Parte 2: bibliometria ----------


def frequencias(tabela: pd.DataFrame, coluna: str, n=10) -> pd.DataFrame:
    """Os n valores mais frequentes da coluna (listas contam cada item). Colunas: [coluna, artigos]."""
    valores = tabela[coluna].explode().dropna()
    contagem = valores.value_counts().head(n)
    return pd.DataFrame({coluna: contagem.index, "artigos": contagem.values})


def grafico_frequencias(tabela: pd.DataFrame, coluna: str, n=10):
    """Barras horizontais com os n periódicos, autores ou palavras-chave mais frequentes."""
    contagem = frequencias(tabela, coluna, n).iloc[::-1]
    figura, eixo = plt.subplots(figsize=(8, 0.4 * len(contagem) + 1.5))
    eixo.barh(contagem[coluna].astype(str), contagem["artigos"])
    eixo.set_title(f"{ROTULOS.get(coluna, coluna)} mais frequentes")
    eixo.set_xlabel("Número de artigos")
    figura.tight_layout()
    return figura


def grafico_anos(tabela: pd.DataFrame):
    """Barras com o número de artigos por ano de publicação."""
    contagem = tabela["ano"].dropna().astype(int).value_counts().sort_index()
    figura, eixo = plt.subplots(figsize=(8, 4))
    eixo.bar(contagem.index.astype(str), contagem.values)
    eixo.set_title("Artigos por ano de publicação")
    eixo.set_xlabel("Ano de publicação")
    eixo.set_ylabel("Número de artigos")
    figura.tight_layout()
    return figura

