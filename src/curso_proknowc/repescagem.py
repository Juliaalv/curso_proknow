"""Repescagem dos artigos abaixo do corte de citações (A7).

- Recentes (publicados há menos de 2 anos em relação ao ano da pesquisa): vão à leitura do resumo.
- Antigos: só vão à leitura do resumo se algum autor estiver no banco de autores do grupo A.
- Demais: excluídos, com o motivo em `motivo_exclusao` (para o fluxograma da A10).

Autores são casados pelo nome normalizado ("Sobrenome, Iniciais" sem acento e em minúsculas);
identificadores de autor não são comparáveis entre bases.
"""

import re
import unicodedata
from collections import Counter

import pandas as pd

MOTIVO_EXCLUSAO = "abaixo do corte, antigo e sem autor do grupo A"


def _nome_norm(nome: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", nome)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acento.lower().replace(". ", ".")).strip()


def _autores(valor) -> list:
    return list(valor) if isinstance(valor, (list, tuple)) else []


def banco_autores(grupo_a: pd.DataFrame) -> pd.DataFrame:
    """Autores do grupo A e em quantos artigos aparecem. Colunas: autor, artigos."""
    contagem, grafia = Counter(), {}
    for autores in grupo_a["autores"]:
        do_artigo = {_nome_norm(a): a for a in _autores(autores)}
        contagem.update(do_artigo.keys())
        for nome, a in do_artigo.items():
            grafia.setdefault(nome, a)
    ordem = sorted(contagem, key=lambda n: (-contagem[n], n))
    return pd.DataFrame({"autor": [grafia[n] for n in ordem], "artigos": [contagem[n] for n in ordem]})


def repescar(abaixo: pd.DataFrame, grupo_a: pd.DataFrame, ano_pesquisa: int):
    """Devolve (enviados, excluidos).

    `enviados` vão à leitura do resumo, com grupo="repescagem", `motivo_repescagem` e
    `autores_grupo_a` (os autores do artigo que estão no banco do grupo A).
    Artigos sem ano não podem ser considerados recentes.
    """
    banco = {_nome_norm(a) for autores in grupo_a["autores"] for a in _autores(autores)}
    tabela = abaixo.copy()
    tabela["autores_grupo_a"] = [[a for a in _autores(v) if _nome_norm(a) in banco] for v in tabela["autores"]]
    recente = (ano_pesquisa - pd.to_numeric(tabela["ano"], errors="coerce") < 2).fillna(False).astype(bool)
    com_autor = tabela["autores_grupo_a"].map(bool)

    tabela["motivo_repescagem"] = None
    tabela.loc[com_autor, "motivo_repescagem"] = tabela.loc[com_autor, "autores_grupo_a"].map(
        lambda autores: "autor do grupo A: " + "; ".join(autores)
    )
    tabela.loc[recente, "motivo_repescagem"] = "recente"

    vai = recente | com_autor
    enviados = tabela[vai].copy()
    enviados["grupo"] = "repescagem"
    excluidos = tabela[~vai].drop(columns=["autores_grupo_a", "motivo_repescagem"])
    excluidos["motivo_exclusao"] = MOTIVO_EXCLUSAO
    return enviados.reset_index(drop=True), excluidos.reset_index(drop=True)
