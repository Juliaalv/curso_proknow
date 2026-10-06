"""Rastreabilidade e relato no estilo PRISMA 2020 (A10).

O histórico das etapas é uma lista de dicionários, um por filtro, na ordem em que foram aplicados:
    {"etapa": nome, "entram": n, "excluidos": n, "motivo": texto}
com a chave opcional "incluidos" (ex.: artigos complementares da representatividade).
`etapa_de_excluidos` monta um desses dicionários a partir da tabela de excluídos (`motivo_exclusao`).
"""

import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from curso_proknowc.tratamento import normalizar_titulo

NOMES_BASES = {"scopus": "Scopus", "ieee": "IEEE", "wos": "Web of Science"}


def registros_por_base(tabela_bruta: pd.DataFrame) -> dict:
    """Número de registros lidos de cada base, para o topo do fluxograma."""
    return {base: int(n) for base, n in tabela_bruta["base_origem"].value_counts().items()}


def etapa_de_excluidos(etapa: str, entram: int, excluidos: pd.DataFrame) -> dict:
    """Uma etapa do histórico, com os motivos de exclusão resumidos como "motivo (n); ..."."""
    motivos = excluidos["motivo_exclusao"].fillna("sem motivo informado").value_counts()
    return {
        "etapa": etapa,
        "entram": entram,
        "excluidos": len(excluidos),
        "motivo": "; ".join(f"{motivo} ({n})" for motivo, n in motivos.items()),
    }


def _final(etapas: list) -> int:
    ultima = etapas[-1]
    return ultima["entram"] - ultima["excluidos"] + ultima.get("incluidos", 0)


def _caixa(eixo, x, y, texto, cor="white"):
    texto = "\n".join(textwrap.fill(linha, 45) for linha in texto.split("\n"))
    return eixo.text(
        x, y, texto, ha="center", va="center", fontsize=9,
        bbox={"boxstyle": "round,pad=0.6", "facecolor": cor, "edgecolor": "black"},
    )


def _seta(eixo, origem, destino):
    eixo.annotate(
        "", xy=destino.get_position(), xytext=origem.get_position(),
        arrowprops={"arrowstyle": "-|>", "color": "black",
                    "patchA": origem.get_bbox_patch(), "patchB": destino.get_bbox_patch()},
    )


def fluxograma(etapas: list, por_base: dict):
    """Fluxograma no estilo PRISMA 2020: registros por base, cada filtro com seus excluídos e o portfólio final."""
    linhas = len(etapas) + 2
    figura, eixo = plt.subplots(figsize=(11, 1.5 * linhas))
    eixo.set_axis_off()
    eixo.set_xlim(0, 1)
    eixo.set_ylim(0, linhas)
    y = linhas - 0.5

    bases = "\n".join(f"{NOMES_BASES.get(b, b)} (n = {n})" for b, n in por_base.items())
    anterior = _caixa(eixo, 0.3, y, f"Registros identificados (n = {sum(por_base.values())})\n{bases}", "#dbe9f6")
    for etapa in etapas:
        y -= 1
        atual = _caixa(eixo, 0.3, y, f"{etapa['etapa']}\n(n = {etapa['entram']})")
        _seta(eixo, anterior, atual)
        lateral = f"Excluídos (n = {etapa['excluidos']})"
        if etapa.get("motivo"):
            lateral += "\n" + etapa["motivo"].replace("; ", "\n")
        if etapa.get("incluidos"):
            lateral = f"Incluídos (n = {etapa['incluidos']})\n" + lateral
        _seta(eixo, atual, _caixa(eixo, 0.78, y, lateral, "#f6e3db"))
        anterior = atual
    final = _caixa(eixo, 0.3, y - 1, f"Portfólio final (n = {_final(etapas)})", "#dcf0d8")
    _seta(eixo, anterior, final)
    eixo.set_title("Fluxograma da seleção do portfólio (estilo PRISMA 2020)")
    return figura


def log_decisoes(excluidos_por_etapa: dict) -> pd.DataFrame:
    """Um registro por artigo excluído: em que etapa saiu e por quê. Recebe {etapa: tabela de excluídos}."""
    colunas = ["id", "doi", "titulo", "motivo_exclusao", "motivo_pesquisador"]
    partes = [
        excluidos.reindex(columns=colunas).assign(etapa=etapa)
        for etapa, excluidos in excluidos_por_etapa.items()
    ]
    if not partes:
        return pd.DataFrame(columns=["etapa"] + colunas)
    return pd.concat(partes, ignore_index=True)[["etapa"] + colunas]


def checklist_prisma(etapas: list, por_base: dict) -> str:
    """Checklist PRISMA 2020 resumido; [x] = preenchido pelo curso, [ ] = o pesquisador completa."""
    bases = ", ".join(f"{b} ({n})" for b, n in por_base.items())
    selecao = "\n".join(
        f"      - {e['etapa']}: entram {e['entram']}, excluídos {e['excluidos']}"
        + (f", incluídos {e['incluidos']}" if e.get("incluidos") else "")
        for e in etapas
    )
    return f"""Checklist PRISMA 2020 (resumido)
[ ] 1. Título: identificar o trabalho como revisão (seleção pelo ProKnow-C).
[ ] 2. Resumo: objetivo, fontes, critérios, número de artigos, principais resultados.
[ ] 3-4. Introdução: justificativa e objetivos da revisão.
[ ] 5. Critérios de elegibilidade: delimitações (anos, tipos, idiomas) e critérios de alinhamento.
[x] 6. Fontes de informação: {bases}. Informe também a data da busca.
[ ] 7. Estratégia de busca: string completa usada em cada base.
[x] 8. Processo de seleção (etapas do ProKnow-C):
{selecao}
      Informe quem leu títulos, resumos e textos e como as divergências foram resolvidas.
[ ] 9-10. Coleta de dados: o que foi extraído de cada artigo e como.
[ ] 13. Métodos de síntese: análise bibliométrica e análise sistêmica.
[x] 16. Resultados da seleção: {sum(por_base.values())} registros identificados, {_final(etapas)} artigos no portfólio final (ver fluxograma).
[ ] 23. Discussão: limitações da busca e da seleção (ex.: bases consultadas, fonte única de citações).
[ ] 27. Disponibilidade: onde estão os dados, as tabelas de cada etapa e o código.
"""


# ---------- Exportação para Zotero e Mendeley ----------

_TIPO_RIS = {"artigo": "JOUR", "revisão": "JOUR", "conferência": "CONF", "capítulo": "CHAP"}
_TIPO_BIBTEX = {"artigo": "article", "revisão": "article", "conferência": "inproceedings", "capítulo": "incollection"}
_CAMPO_FONTE = {"article": "journal", "inproceedings": "booktitle", "incollection": "booktitle"}


def _valor(valor):
    """None para campos vazios (None, NaN, NA, lista vazia); o próprio valor nos demais casos."""
    if isinstance(valor, list):
        return valor or None
    return None if valor is None or pd.isna(valor) else valor


def exportar_ris(tabela: pd.DataFrame, caminho) -> Path:
    """Grava o portfólio em RIS (importável no Zotero e no Mendeley)."""
    registros = []
    for _, artigo in tabela.iterrows():
        a = {campo: _valor(artigo.get(campo)) for campo in tabela.columns}
        linhas = [f"TY  - {_TIPO_RIS.get(a.get('tipo_documento'), 'GEN')}"]
        linhas += [f"AU  - {autor}" for autor in a.get("autores") or []]
        for marca, campo in [("TI", "titulo"), ("T2", "periodico"), ("PY", "ano"), ("DO", "doi"), ("SN", "issn"), ("AB", "resumo")]:
            if a.get(campo) is not None:
                linhas.append(f"{marca}  - {a[campo]}")
        linhas += [f"KW  - {palavra}" for palavra in a.get("palavras_chave") or []]
        linhas.append("ER  - ")
        registros.append("\n".join(linhas))
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text("\n\n".join(registros) + "\n", encoding="utf-8")
    return caminho


def _bibtex_texto(valor) -> str:
    texto = str(valor).replace("{", "").replace("}", "")
    return texto.replace("&", r"\&").replace("%", r"\%")


def _chave(autores, ano, usadas: set) -> str:
    sobrenome = normalizar_titulo(autores[0].split(",")[0]) if autores else None
    base = (sobrenome or "semautor").replace(" ", "") + (str(ano) if ano is not None else "")
    chave, sufixo = base, "b"
    while chave in usadas:
        chave = base + sufixo
        sufixo = chr(ord(sufixo) + 1)
    usadas.add(chave)
    return chave


def exportar_bibtex(tabela: pd.DataFrame, caminho) -> Path:
    """Grava o portfólio em BibTeX (importável no Zotero e no Mendeley)."""
    usadas, entradas = set(), []
    for _, artigo in tabela.iterrows():
        a = {campo: _valor(artigo.get(campo)) for campo in tabela.columns}
        tipo = _TIPO_BIBTEX.get(a.get("tipo_documento"), "misc")
        campos = {
            "author": " and ".join(a["autores"]) if a.get("autores") else None,
            "title": a.get("titulo"),
            _CAMPO_FONTE.get(tipo, "howpublished"): a.get("periodico"),
            "year": a.get("ano"),
            "doi": a.get("doi"),
            "issn": a.get("issn"),
            "abstract": a.get("resumo"),
            "keywords": ", ".join(a["palavras_chave"]) if a.get("palavras_chave") else None,
        }
        linhas = [f"  {nome} = {{{_bibtex_texto(valor)}}}," for nome, valor in campos.items() if valor is not None]
        entradas.append(f"@{tipo}{{{_chave(a.get('autores'), a.get('ano'), usadas)},\n" + "\n".join(linhas) + "\n}")
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text("\n\n".join(entradas) + "\n", encoding="utf-8")
    return caminho
