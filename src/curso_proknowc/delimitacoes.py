"""Filtragem preliminar e delimitações do pesquisador (A2, etapa 4).

Cada função devolve (mantidos, excluidos); os excluídos levam o motivo em `motivo_exclusao`,
para o fluxograma da A10.
"""

import pandas as pd


def _separar(tabela: pd.DataFrame, sai: pd.Series, motivo: str):
    excluidos = tabela[sai].copy()
    excluidos["motivo_exclusao"] = motivo
    return tabela[~sai].reset_index(drop=True), excluidos.reset_index(drop=True)


def remover_incompletos(tabela: pd.DataFrame):
    """Retira registros sem título, ou sem ano e sem DOI."""
    sai = tabela["titulo"].isna() | (tabela["ano"].isna() & tabela["doi"].isna())
    return _separar(tabela, sai, "informação ausente")


def aplicar_delimitacoes(tabela: pd.DataFrame, anos=None, tipos=None, idiomas=None):
    """Aplica os filtros opcionais do pesquisador.

    anos: (inicial, final), inclusivo. tipos e idiomas: listas de valores aceitos.
    Registros que não informam o campo são mantidos, porque não há como julgá-los.
    """
    filtros = []
    if anos:
        inicio, fim = anos
        filtros.append(("ano", lambda c: c.notna() & ((c < inicio) | (c > fim)), "fora do intervalo de anos"))
    if tipos:
        filtros.append(("tipo_documento", lambda c: c.notna() & ~c.isin(tipos), "tipo de documento fora da delimitação"))
    if idiomas:
        filtros.append(("idioma", lambda c: c.notna() & ~c.isin(idiomas), "idioma fora da delimitação"))

    todos_excluidos = []
    for coluna, regra, motivo in filtros:
        tabela, excluidos = _separar(tabela, regra(tabela[coluna]).fillna(False).astype(bool), motivo)
        todos_excluidos.append(excluidos)
    excluidos = pd.concat(todos_excluidos, ignore_index=True) if todos_excluidos else tabela.iloc[0:0].copy()
    return tabela, excluidos
