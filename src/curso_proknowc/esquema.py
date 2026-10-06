"""Esquema da tabela única de artigos (seção 7 do plano) e gravação em Parquet."""

import json
from pathlib import Path

import pandas as pd

COLUNAS = [
    "id",
    "doi",
    "titulo",
    "resumo",
    "autores",
    "autores_ids",
    "ano",
    "periodico",
    "issn",
    "tipo_documento",
    "idioma",
    "palavras_chave",
    "palavras_chave_autor",
    "palavras_chave_indexadas",
    "titulo_norm",
    "citacoes",
    "citacoes_fonte",
    "citacoes_data",
    "citacoes_por_base",
    "referencias",
    "referencias_texto",
    "base_origem",
    "bases_origem",
    "arquivos_origem",
    "acesso_aberto",
    "url_pdf",
    "buscar_capes",
    "obs_disponibilidade",
    "etapa_atual",
    "decisao_titulo",
    "decisao_resumo",
    "decisao_texto",
    "motivo_exclusao",
    "grupo",
]

COLUNAS_LISTA = [
    "autores",
    "autores_ids",
    "palavras_chave",
    "palavras_chave_autor",
    "palavras_chave_indexadas",
    "referencias",
    "bases_origem",
    "arquivos_origem",
]

# Dicionários com chaves que variam de linha para linha: guardados como JSON no Parquet.
COLUNAS_DICIONARIO = ["citacoes_por_base"]

COLUNAS_INTEIRAS = ["ano", "citacoes"]


def completar(tabela: pd.DataFrame) -> pd.DataFrame:
    """Garante todas as colunas do esquema, na ordem do esquema, com as extras no fim."""
    for coluna in COLUNAS:
        if coluna not in tabela.columns:
            tabela[coluna] = None
    extras = [c for c in tabela.columns if c not in COLUNAS]
    tabela = tabela[COLUNAS + extras]
    for coluna in COLUNAS_INTEIRAS:
        tabela[coluna] = tabela[coluna].astype("Int64")
    return tabela


def salvar(tabela: pd.DataFrame, caminho) -> None:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    copia = tabela.copy()
    for coluna in COLUNAS_DICIONARIO:
        copia[coluna] = copia[coluna].map(lambda v: None if v is None else json.dumps(v))
    copia.to_parquet(caminho, index=False)


def carregar(caminho) -> pd.DataFrame:
    tabela = pd.read_parquet(caminho)
    for coluna in COLUNAS_LISTA:
        if coluna in tabela.columns:
            tabela[coluna] = tabela[coluna].map(lambda v: None if v is None else list(v))
    for coluna in COLUNAS_DICIONARIO:
        if coluna in tabela.columns:
            tabela[coluna] = tabela[coluna].map(lambda v: None if v is None else json.loads(v))
    return tabela
