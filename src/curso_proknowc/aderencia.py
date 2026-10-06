"""Teste de aderência das palavras-chave dos artigos-semente à busca (A3)."""

import re

import pandas as pd

from curso_proknowc.tratamento import lista_palavras, normalizar_titulo

# Regra de "cobre": termo e palavra-chave são comparados em minúsculas, sem acentos e
# com pontuação trocada por espaço. O termo cobre a palavra-chave se aparece dentro dela
# como palavra(s) inteira(s): "wind speed" cobre "short-term wind speed", mas "wind" não
# cobre "windmill". O curinga * vale por qualquer continuação: "forecast*" cobre "forecasting".


def _normalizar(texto: str) -> str:
    return normalizar_titulo(texto) or ""


def cobre(termo: str, palavra_chave: str) -> bool:
    """True se o termo da busca contempla a palavra-chave (regra acima)."""
    partes = [_normalizar(parte) for parte in termo.split("*")]
    padrao = r"\w*".join(re.escape(parte) for parte in partes)
    return bool(re.search(rf"(?<!\w){padrao}(?!\w)", _normalizar(palavra_chave)))


def _termo_que_cobre(eixos: dict, palavra_chave: str) -> str:
    termos = [t.strip() for ts in eixos.values() for t in ts if _normalizar(t)]
    return next((t for t in termos if cobre(t, palavra_chave)), "")


def _palavras(valor) -> list:
    """Aceita lista ou texto separado por ";"."""
    return lista_palavras(valor if isinstance(valor, str) else ";".join(valor))


def sementes_da_tabela(tabela: pd.DataFrame, escolhas: list) -> dict:
    """Artigos-semente escolhidos por id ou trecho do título -> {título: palavras-chave}.

    Usa as palavras-chave do autor; se o artigo não tiver, usa todas as palavras-chave.
    """
    titulos = tabela["titulo"].map(_normalizar)
    sementes = {}
    for escolha in escolhas:
        achados = tabela[tabela["id"] == escolha]
        if achados.empty:
            achados = tabela[titulos.str.contains(_normalizar(escolha), regex=False)]
        if achados.empty:
            raise ValueError(f'Nenhum artigo encontrado com o id ou trecho do título "{escolha}".')
        if len(achados) > 1:
            opcoes = "; ".join(f"{linha.id} ({linha.titulo})" for linha in achados.itertuples())
            raise ValueError(f'Mais de um artigo corresponde a "{escolha}": {opcoes}. Escolha pelo id.')
        linha = achados.iloc[0]
        sementes[linha["titulo"]] = list(linha["palavras_chave_autor"]) or list(linha["palavras_chave"])
    return sementes


def _mensagem(total: int, ausentes: int) -> str:
    if not ausentes:
        return (
            f"A busca passou no teste de aderência: todas as {total} palavras-chave dos "
            "artigos-semente estão contempladas pelos termos da busca."
        )
    return (
        f"A busca não passou no teste de aderência: {ausentes} de {total} palavras-chave "
        "dos artigos-semente não estão contempladas. Veja as sugestões: inclua no eixo adequado "
        "as que forem do seu tema (a decisão é sua), gere a string de novo e busque de novo nas bases. "
        'Dica: sem curinga, o plural não é contemplado ("prediction" não cobre "predictions"); '
        "use * para incluir o plural (ex.: prediction*)."
    )


def testar_aderencia(eixos: dict, sementes: dict):
    """Marca cada palavra-chave dos artigos-semente como "contemplada" ou "ausente" na busca.

    `sementes` é {artigo: palavras-chave}, com as palavras em lista ou em texto separado por ";".
    Devolve (tabela, sugestões de termos a incluir, mensagem).
    """
    if len(sementes) < 2:
        raise ValueError("O teste de aderência precisa de pelo menos 2 artigos-semente.")
    linhas = []
    for artigo, palavras in sementes.items():
        for palavra in _palavras(palavras):
            termo = _termo_que_cobre(eixos, palavra)
            situacao = "contemplada" if termo else "ausente"
            linhas.append({"artigo": artigo, "palavra_chave": palavra, "situacao": situacao, "termo": termo})
    tabela = pd.DataFrame(linhas, columns=["artigo", "palavra_chave", "situacao", "termo"])
    ausentes = tabela.loc[tabela["situacao"] == "ausente", "palavra_chave"]
    sugestoes = []
    for palavra in ausentes:
        if _normalizar(palavra) not in map(_normalizar, sugestoes):
            sugestoes.append(palavra)
    return tabela, sugestoes, _mensagem(len(tabela), len(ausentes))
