"""Deduplicação com fusão entre bases (A4) e sobreposição entre bases (A2, etapa 5)."""

import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process

from curso_proknowc import esquema
from curso_proknowc.tratamento import normalizar_titulo

LIMIAR_TITULO = 90  # % mínimo de semelhança entre títulos normalizados
DIFERENCA_ANOS = 1  # versões do mesmo artigo podem sair com um ano de diferença entre bases

COLUNAS_UNIAO = ["bases_origem", "arquivos_origem", "palavras_chave", "palavras_chave_autor", "palavras_chave_indexadas"]
COLUNAS_RELATORIO = ["id_mantido", "id_removido", "criterio", "titulo_removido", "base_removido"]


def _vazio(valor) -> bool:
    if isinstance(valor, (list, dict, str)):
        return len(valor) == 0
    return valor is None or pd.isna(valor)


def _sobrenome(autores):
    if not isinstance(autores, list) or not autores:
        return None
    return normalizar_titulo(autores[0].split(",")[0])


def _compativeis(a: dict, b: dict) -> bool:
    """Ano até DIFERENCA_ANOS, primeiro autor igual (ou ausente) e DOIs que não se contradizem."""
    if abs(a["ano"] - b["ano"]) > DIFERENCA_ANOS:
        return False
    if a["sobrenome"] and b["sobrenome"] and a["sobrenome"] != b["sobrenome"]:
        return False
    return not (a["doi"] and b["doi"] and a["doi"] != b["doi"])


def _pares_por_doi(tabela: pd.DataFrame):
    for _, grupo in tabela[tabela["doi"].notna()].groupby("doi", sort=False):
        primeiro = grupo.index[0]
        for outro in grupo.index[1:]:
            yield primeiro, outro, "DOI"


def _pares_por_titulo(tabela: pd.DataFrame, limiar: float):
    """Compara títulos só entre anos próximos (blocos por ano), com rapidfuzz.process.cdist."""
    candidatos = tabela[tabela["titulo_norm"].notna() & tabela["ano"].notna()]
    info = {
        i: {"ano": int(l["ano"]), "sobrenome": _sobrenome(l["autores"]), "doi": l["doi"] if pd.notna(l["doi"]) else None}
        for i, l in candidatos.iterrows()
    }
    por_ano = {ano: grupo for ano, grupo in candidatos.groupby("ano")}
    for ano, grupo in por_ano.items():
        for outro_ano in range(int(ano), int(ano) + DIFERENCA_ANOS + 1):
            if outro_ano not in por_ano:
                continue
            outro = por_ano[outro_ano]
            notas = process.cdist(
                grupo["titulo_norm"].tolist(), outro["titulo_norm"].tolist(),
                scorer=fuzz.ratio, score_cutoff=limiar, workers=-1,
            )
            for a, b in zip(*np.nonzero(notas)):
                i, j = grupo.index[a], outro.index[b]
                if (outro_ano == ano and i >= j) or not _compativeis(info[i], info[j]):
                    continue
                yield i, j, f"título semelhante ({notas[a, b]:.0f}%)"


def _completude(linha: pd.Series) -> int:
    return sum(not _vazio(linha[c]) for c in esquema.COLUNAS)


def _fundir(mantido: pd.Series, outro: pd.Series) -> pd.Series:
    """Preenche os campos vazios do mantido com os do outro e une bases, arquivos, palavras-chave e citações por base."""
    mantido = mantido.copy()
    for coluna in mantido.index:
        if coluna in COLUNAS_UNIAO:
            atual = list(mantido[coluna]) if not _vazio(mantido[coluna]) else []
            novos = list(outro[coluna]) if not _vazio(outro[coluna]) else []
            mantido[coluna] = atual + [v for v in novos if v not in atual]
        elif coluna == "citacoes_por_base":
            if not _vazio(outro[coluna]):
                mantido[coluna] = {**outro[coluna], **(mantido[coluna] if not _vazio(mantido[coluna]) else {})}
        elif _vazio(mantido[coluna]) and not _vazio(outro[coluna]):
            mantido[coluna] = outro[coluna]
    return mantido


def _raiz(pais: dict, i):
    while pais[i] != i:
        pais[i] = pais[pais[i]]
        i = pais[i]
    return i


def deduplicar(tabela: pd.DataFrame, limiar: float = LIMIAR_TITULO):
    """Funde registros duplicados (1º por DOI, 2º por título semelhante) e devolve (tabela, relatório).

    Em cada grupo de duplicados fica o registro mais completo, com os campos vazios preenchidos
    pelos outros. O relatório tem uma linha por registro fundido, com o id mantido e o critério.
    """
    tabela = tabela.reset_index(drop=True)
    pais = {i: i for i in tabela.index}
    criterio = {}
    for i, j, motivo in list(_pares_por_doi(tabela)) + list(_pares_por_titulo(tabela, limiar)):
        criterio.setdefault(i, motivo)
        criterio.setdefault(j, motivo)
        pais[_raiz(pais, j)] = _raiz(pais, i)

    grupos = {}
    for i in tabela.index:
        grupos.setdefault(_raiz(pais, i), []).append(i)

    linhas, relatorio = [], []
    for membros in grupos.values():
        ordem = sorted(membros, key=lambda i: (-_completude(tabela.loc[i]), i))
        fundido = tabela.loc[ordem[0]]
        for i in ordem[1:]:
            removido = tabela.loc[i]
            fundido = _fundir(fundido, removido)
            relatorio.append([fundido["id"], removido["id"], criterio[i], removido["titulo"], removido["base_origem"]])
        linhas.append((min(membros), fundido))

    resultado = pd.DataFrame([linha for _, linha in sorted(linhas, key=lambda par: par[0])], columns=tabela.columns)
    resultado["etapa_atual"] = "deduplicado"
    resultado = esquema.completar(resultado.reset_index(drop=True))
    return resultado, pd.DataFrame(relatorio, columns=COLUNAS_RELATORIO)


def sobreposicao(tabela: pd.DataFrame) -> pd.DataFrame:
    """Por base: artigos encontrados nela, exclusivos dela e em comum com outra base (usar após deduplicar)."""
    bases = tabela["bases_origem"].map(set)
    nomes = sorted(set().union(*bases)) if len(bases) else []
    linhas = []
    for base in nomes:
        dela = bases.map(lambda b: base in b)
        exclusivos = int((dela & (bases.map(len) == 1)).sum())
        linhas.append({"base": base, "registros": int(dela.sum()), "exclusivos": exclusivos,
                       "em_comum": int(dela.sum()) - exclusivos})
    return pd.DataFrame(linhas, columns=["base", "registros", "exclusivos", "em_comum"])
