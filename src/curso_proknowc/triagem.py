"""Triagem assistida por título, resumo e texto completo (A5).

A ferramenta não decide: só mostra um artigo por vez e grava a decisão do pesquisador.

Cada clique acrescenta uma linha a um CSV de decisões (id, etapa, decisao, motivo, data_hora).
Acrescentar uma linha é rápido e não reescreve o que já foi gravado; se a sessão do Colab cair
no meio de uma gravação, no máximo a última linha fica incompleta e é ignorada na leitura.
Um Parquet teria de ser reescrito inteiro a cada clique. Para uma mesma etapa e artigo vale a
última linha, então decidir de novo substitui a decisão anterior.
"""

import html
import os
from datetime import datetime
from pathlib import Path

import pandas as pd

ETAPAS = {"titulo": "pelo título", "resumo": "pelo resumo", "texto": "pelo texto completo"}
DECISOES = ["aceito", "rejeitado"]
CAMPOS = ["id", "etapa", "decisao", "motivo", "data_hora"]


def _conferir_etapa(etapa):
    if etapa not in ETAPAS:
        raise ValueError(f"Etapa desconhecida: {etapa!r}. Use uma de: {', '.join(ETAPAS)}.")


def _ler(caminho) -> pd.DataFrame:
    caminho = Path(caminho)
    if not caminho.exists():
        return pd.DataFrame(columns=CAMPOS)
    linhas = pd.read_csv(caminho, dtype=str, keep_default_na=False, encoding="utf-8")
    return linhas[linhas["decisao"].isin(DECISOES)].reset_index(drop=True)


def registrar(caminho, id_artigo, etapa, decisao, motivo="") -> None:
    """Grava a decisão no arquivo imediatamente."""
    _conferir_etapa(etapa)
    if decisao not in DECISOES:
        raise ValueError(f"Decisão desconhecida: {decisao!r}. Use 'aceito' ou 'rejeitado'.")
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    linha = pd.DataFrame(
        [[str(id_artigo), etapa, decisao, motivo or "", datetime.now().isoformat(timespec="seconds")]],
        columns=CAMPOS,
    )
    linha.to_csv(caminho, mode="a", header=not caminho.exists(), index=False, encoding="utf-8")


def carregar_decisoes(caminho, etapa) -> pd.DataFrame:
    """Decisões válidas da etapa, uma por artigo (a mais recente), na ordem em que foram tomadas."""
    _conferir_etapa(etapa)
    linhas = _ler(caminho)
    linhas = linhas[linhas["etapa"] == etapa]
    return linhas.drop_duplicates("id", keep="last").reset_index(drop=True)


def desfazer(caminho, etapa):
    """Apaga a última decisão da etapa e devolve o id do artigo, ou None se não houver nenhuma."""
    _conferir_etapa(etapa)
    linhas = _ler(caminho)
    da_etapa = linhas.index[linhas["etapa"] == etapa]
    if len(da_etapa) == 0:
        return None
    id_artigo = linhas.loc[da_etapa[-1], "id"]
    caminho = Path(caminho)
    temporario = caminho.with_name(caminho.name + ".tmp")
    linhas.drop(index=da_etapa[-1]).to_csv(temporario, index=False, encoding="utf-8")
    os.replace(temporario, caminho)
    return id_artigo


def _decididos(tabela, etapa, caminho):
    ids = set(carregar_decisoes(caminho, etapa)["id"])
    return tabela["id"].astype(str).isin(ids)


def progresso(tabela, etapa, caminho):
    """(quantos artigos da tabela já têm decisão nesta etapa, total de artigos)."""
    return int(_decididos(tabela, etapa, caminho).sum()), len(tabela)


def proximo(tabela, etapa, caminho):
    """Primeiro artigo da tabela ainda sem decisão nesta etapa, ou None se todos foram decididos."""
    pendentes = tabela[~_decididos(tabela, etapa, caminho)]
    return None if pendentes.empty else pendentes.iloc[0]


def aplicar(tabela, etapa, caminho):
    """Preenche `decisao_<etapa>` e devolve (aceitos, rejeitados).

    Os rejeitados levam `motivo_exclusao` = "não alinhado pelo <etapa>" (categoria usada no
    fluxograma da A10) e, em `motivo_pesquisador`, o motivo escrito pelo pesquisador, quando houver.
    """
    decisoes = carregar_decisoes(caminho, etapa).set_index("id")
    ids = tabela["id"].astype(str)
    faltam = int((~ids.isin(decisoes.index)).sum())
    if faltam:
        raise ValueError(f"Ainda há {faltam} artigo(s) sem decisão na etapa '{etapa}'. Termine a triagem antes.")

    tabela = tabela.copy()
    tabela[f"decisao_{etapa}"] = ids.map(decisoes["decisao"]).values
    rejeitado = (tabela[f"decisao_{etapa}"] == "rejeitado").values

    motivos = ids.map(decisoes["motivo"])
    rejeitados = tabela[rejeitado].copy()
    rejeitados["motivo_exclusao"] = f"não alinhado {ETAPAS[etapa]}"
    rejeitados["motivo_pesquisador"] = [m or None for m in motivos[rejeitado]]
    return tabela[~rejeitado].reset_index(drop=True), rejeitados.reset_index(drop=True)


def ordenar_por_similaridade(tabela, descricao):
    """Ordena pela semelhança (TF-IDF) entre título + resumo e a descrição do tema.

    Serve só para priorizar a leitura: não exclui nenhum artigo.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    textos = (tabela["titulo"].fillna("") + " " + tabela["resumo"].fillna("")).tolist()
    matriz = TfidfVectorizer().fit_transform(textos + [descricao])
    notas = cosine_similarity(matriz[:-1], matriz[-1]).ravel()
    ordem = pd.Series(notas).sort_values(ascending=False, kind="stable").index
    return tabela.iloc[ordem].reset_index(drop=True)


def _texto(artigo, etapa):
    if artigo is None:
        return "<p><b>Triagem concluída: todos os artigos têm decisão nesta etapa.</b></p>"
    partes = [f"<h3>{html.escape(str(artigo['titulo']))}</h3>"]
    if etapa == "resumo":
        resumo = artigo.get("resumo")
        resumo = "(sem resumo)" if resumo is None or pd.isna(resumo) else str(resumo)
        partes.append(f"<p>{html.escape(resumo)}</p>")
    return "".join(partes)


def interface(tabela, etapa, caminho):
    """Monta a tela de triagem (ipywidgets). No Colab, basta deixá-la como última linha da célula."""
    import ipywidgets as widgets

    _conferir_etapa(etapa)
    total = len(tabela)
    por_id = tabela.assign(_id=tabela["id"].astype(str)).set_index("_id")

    artigo_html = widgets.HTML()
    contagem = widgets.Label()
    barra = widgets.IntProgress(min=0, max=max(total, 1), description="Progresso:")
    motivo = widgets.Text(placeholder="Motivo (opcional)", description="Motivo:")
    aceitar = widgets.Button(description="Aceitar", button_style="success")
    rejeitar = widgets.Button(description="Rejeitar", button_style="danger")
    voltar = widgets.Button(description="Voltar", tooltip="Desfaz a última decisão")
    estado = {"atual": None}

    def mostrar(artigo):
        estado["atual"] = artigo
        feitos, _ = progresso(tabela, etapa, caminho)
        barra.value = feitos
        contagem.value = f"{feitos} de {total} artigos decididos (leitura {ETAPAS[etapa]})"
        artigo_html.value = _texto(artigo, etapa)
        aceitar.disabled = rejeitar.disabled = artigo is None
        motivo.value = ""

    def decidir(decisao):
        if estado["atual"] is not None:
            registrar(caminho, estado["atual"]["id"], etapa, decisao, motivo.value.strip())
        mostrar(proximo(tabela, etapa, caminho))

    def desfazer_ultima(_):
        id_artigo = desfazer(caminho, etapa)
        if id_artigo is not None and id_artigo in por_id.index:
            mostrar(por_id.loc[id_artigo])
        else:
            mostrar(proximo(tabela, etapa, caminho))

    aceitar.on_click(lambda _: decidir("aceito"))
    rejeitar.on_click(lambda _: decidir("rejeitado"))
    voltar.on_click(desfazer_ultima)
    mostrar(proximo(tabela, etapa, caminho))

    tela = widgets.VBox([barra, contagem, artigo_html, motivo, widgets.HBox([aceitar, rejeitar, voltar])])
    tela.aceitar, tela.rejeitar, tela.voltar, tela.motivo, tela.barra = aceitar, rejeitar, voltar, motivo, barra
    return tela
