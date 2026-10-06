"""InOrdinatio (Methodi Ordinatio, Pagani, Kovaleski e Resende, 2015) e comparação com o corte do ProKnow-C (B2).

InOrdinatio = (FI / 1000) + α × [10 − (ano da pesquisa − ano de publicação)] + citações

Adaptação do curso: o FI (JCR) é substituído por uma coluna escolhida pelo participante
(SJR, CiteScore ou a citação média de dois anos do OpenAlex).
"""

import warnings

import pandas as pd

from curso_proknowc.reconhecimento import corte_citacoes  # regra do corte do ProKnow-C (A6)


def _validar_alfa(alfa) -> None:
    if not 1 <= alfa <= 10:
        raise ValueError(f"α deve estar entre 1 e 10 (recebido: {alfa}).")


def _fator_impacto(tabela: pd.DataFrame, coluna_fi: str) -> pd.Series:
    """Coluna do substituto do FI; valores ausentes viram 0, com aviso."""
    if coluna_fi not in tabela.columns:
        warnings.warn(f"Coluna '{coluna_fi}' não existe na tabela: FI considerado 0 para todos os artigos.")
        return pd.Series(0.0, index=tabela.index)
    fi = pd.to_numeric(tabela[coluna_fi], errors="coerce")
    ausentes = int(fi.isna().sum())
    if ausentes:
        warnings.warn(f"{ausentes} artigo(s) sem valor em '{coluna_fi}': FI considerado 0.")
    return fi.fillna(0.0)


def calcular_inordinatio(tabela: pd.DataFrame, coluna_fi: str, ano_pesquisa: int, alfa: float) -> pd.DataFrame:
    """Devolve uma cópia da tabela com a coluna `inordinatio` (vazia se o ano faltar)."""
    _validar_alfa(alfa)
    fi = _fator_impacto(tabela, coluna_fi)
    citacoes = pd.to_numeric(tabela["citacoes"], errors="coerce").fillna(0)
    ano = pd.to_numeric(tabela["ano"], errors="coerce")
    tabela = tabela.copy()
    tabela["inordinatio"] = (fi / 1000 + alfa * (10 - (ano_pesquisa - ano)) + citacoes).astype(float)
    return tabela


def ranking_inordinatio(tabela: pd.DataFrame, coluna_fi: str, ano_pesquisa: int, alfa: float) -> pd.DataFrame:
    """Tabela ordenada pelo InOrdinatio, do maior para o menor, com `posicao_inordinatio`."""
    tabela = calcular_inordinatio(tabela, coluna_fi, ano_pesquisa, alfa)
    tabela = tabela.sort_values("inordinatio", ascending=False, kind="stable").reset_index(drop=True)
    tabela["posicao_inordinatio"] = range(1, len(tabela) + 1)
    return tabela


def comparar_com_corte(
    tabela: pd.DataFrame,
    coluna_fi: str,
    ano_pesquisa: int,
    alfa: float,
    percentual: float = 80,
    top_n: int | None = None,
) -> pd.DataFrame:
    """Lado a lado: portfólio pelo corte de citações e top-N do InOrdinatio.

    Sem `top_n`, usa o tamanho do portfólio pelo corte, para comparar conjuntos do mesmo tamanho.
    Devolve só os artigos que entram em pelo menos um dos dois, com a coluna `situacao`.
    """
    ranking = ranking_inordinatio(tabela, coluna_fi, ano_pesquisa, alfa)
    pelo_corte = set(corte_citacoes(tabela, percentual)["id"])
    if top_n is None:
        top_n = len(pelo_corte)
    pelo_inordinatio = set(ranking["id"].head(top_n))

    ranking["no_corte_citacoes"] = ranking["id"].isin(pelo_corte)
    ranking["no_top_inordinatio"] = ranking["id"].isin(pelo_inordinatio)
    ranking = ranking[ranking["no_corte_citacoes"] | ranking["no_top_inordinatio"]].copy()
    ranking["situacao"] = "nos dois"
    ranking.loc[~ranking["no_top_inordinatio"], "situacao"] = "só no corte de citações"
    ranking.loc[~ranking["no_corte_citacoes"], "situacao"] = "só no InOrdinatio"
    colunas = ["id", "titulo", "ano", "citacoes", "inordinatio", "posicao_inordinatio",
               "no_corte_citacoes", "no_top_inordinatio", "situacao"]
    return ranking[[c for c in colunas if c in ranking.columns]].reset_index(drop=True)
