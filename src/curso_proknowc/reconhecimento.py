"""Reconhecimento científico (A6).

Citações de uma única fonte, o OpenAlex (consulta pelo DOI), porque os valores das bases não
são comparáveis entre si; curva de citações acumuladas; divisão em "acima do corte" e
"abaixo do corte" pelo percentual acumulado escolhido pelo pesquisador.
"""

from datetime import date

import matplotlib.pyplot as plt
import pandas as pd
import requests

from curso_proknowc.tratamento import normalizar_doi

OPENALEX = "https://api.openalex.org"
LOTE_OPENALEX = 50  # máximo de DOIs por consulta com filtro


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


def atualizar_citacoes(tabela: pd.DataFrame, email=None, chave=None):
    """Preenche `citacoes` com o `cited_by_count` do OpenAlex, `citacoes_fonte`="openalex" e
    `citacoes_data` (hoje). `citacoes_por_base` não é alterado. Devolve (tabela, avisos).

    Fonte única: artigos sem DOI, não encontrados ou cuja consulta falhou ficam sem contagem
    (citacoes vazia), em vez de manter a contagem de uma base, e são listados nos avisos.
    """
    tabela = tabela.copy()
    base = _parametros(email, chave) | {"select": "doi,cited_by_count", "per_page": LOTE_OPENALEX}
    avisos = [f"O artigo '{t}' está sem DOI; ficou sem contagem de citações."
              for t in tabela.loc[tabela["doi"].isna(), "titulo"]]
    dois = list(dict.fromkeys(tabela["doi"].dropna()))
    contagens, consultados = {}, set()
    for inicio in range(0, len(dois), LOTE_OPENALEX):
        lote = dois[inicio : inicio + LOTE_OPENALEX]
        try:
            resultado = _obter_json(f"{OPENALEX}/works", base | {"filter": "doi:" + "|".join(lote)})
        except (requests.RequestException, ValueError) as erro:
            avisos.append(f"Não foi possível consultar {len(lote)} DOI(s) no OpenAlex ({erro}); "
                          "esses artigos ficaram sem contagem de citações. Tente de novo mais tarde.")
            continue
        consultados.update(lote)
        for obra in resultado.get("results", []):
            doi = normalizar_doi(obra.get("doi"))
            if doi in lote:
                contagens[doi] = obra.get("cited_by_count")
    for doi in dois:
        if doi in consultados and doi not in contagens:
            avisos.append(f"DOI {doi} não encontrado no OpenAlex; ficou sem contagem de citações.")

    achados = tabela["doi"].isin(list(contagens))
    tabela["citacoes"] = tabela["doi"].map(contagens).astype("Int64")
    tabela["citacoes_fonte"] = ["openalex" if a else None for a in achados]
    tabela["citacoes_data"] = [date.today().isoformat() if a else None for a in achados]
    return tabela, avisos


def curva_citacoes(tabela: pd.DataFrame) -> pd.DataFrame:
    """Artigos ordenados por citações, com `posicao` e `percentual_acumulado` (inclui o próprio artigo).

    Citações ausentes contam como 0.
    """
    citacoes = pd.to_numeric(tabela["citacoes"], errors="coerce").fillna(0)
    curva = tabela.assign(citacoes=citacoes).sort_values("citacoes", ascending=False, kind="stable")
    curva = curva.reset_index(drop=True)
    curva["posicao"] = range(1, len(curva) + 1)
    total = curva["citacoes"].sum()
    curva["percentual_acumulado"] = curva["citacoes"].cumsum() / total * 100 if total else 0.0
    return curva


def dividir_por_corte(tabela: pd.DataFrame, percentual: float = 80):
    """Devolve (acima, abaixo) do corte do ProKnow-C.

    Ordena por citações e mantém acima do corte os artigos que começam abaixo do percentual
    acumulado (o artigo que cruza o corte entra). Sem nenhuma citação, todos ficam abaixo.
    """
    citacoes = pd.to_numeric(tabela["citacoes"], errors="coerce").fillna(0)
    ordenada = tabela.assign(_c=citacoes).sort_values("_c", ascending=False, kind="stable")
    total = ordenada["_c"].sum()
    if total == 0:
        entra = pd.Series(False, index=ordenada.index)
    else:
        entra = (ordenada["_c"].cumsum() - ordenada["_c"]) / total * 100 < percentual
    ordenada = ordenada.drop(columns="_c")
    return ordenada[entra].reset_index(drop=True), ordenada[~entra].reset_index(drop=True)


def corte_citacoes(tabela: pd.DataFrame, percentual: float = 80) -> pd.DataFrame:
    """Só os artigos acima do corte (veja `dividir_por_corte`)."""
    return dividir_por_corte(tabela, percentual)[0]


def artigos_por_corte(tabela: pd.DataFrame, percentuais=(70, 75, 80, 85, 90)) -> pd.DataFrame:
    """Quantos artigos ficam acima do corte em cada percentual."""
    return pd.DataFrame(
        {
            "corte (%)": list(percentuais),
            "artigos acima do corte": [len(corte_citacoes(tabela, p)) for p in percentuais],
        }
    )


def grafico_curva(tabela: pd.DataFrame, percentual: float = 80):
    """Curva de citações acumuladas com a linha do corte e quantos artigos ficam acima dele."""
    curva = curva_citacoes(tabela)
    acima = len(corte_citacoes(tabela, percentual))
    figura, eixo = plt.subplots(figsize=(8, 4.5))
    eixo.plot(curva["posicao"], curva["percentual_acumulado"], marker="o", markersize=3)
    eixo.axhline(percentual, color="gray", linestyle="--", label=f"Corte em {percentual:g}%")
    if acima:
        eixo.axvline(acima, color="gray", linestyle=":", label=f"{acima} artigo(s) acima do corte")
    eixo.set_title("Citações acumuladas dos artigos")
    eixo.set_xlabel("Artigos, do mais para o menos citado")
    eixo.set_ylabel("Citações acumuladas (%)")
    eixo.set_ylim(0, 105)
    eixo.legend()
    figura.tight_layout()
    return figura
