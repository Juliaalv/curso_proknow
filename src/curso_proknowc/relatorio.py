"""Relatório de qualidade da leitura (A2, etapa 5), com avisos legíveis para leigos."""

import pandas as pd

# coluna: como o campo ausente aparece no aviso
CAMPOS_VERIFICADOS = {
    "ano": "sem ano",
    "doi": "sem DOI",
    "resumo": "sem resumo",
    "palavras_chave": "sem palavras-chave",
    "citacoes": "sem contagem de citações",
}
LIMITE_AVISO = 20  # % de campos vazios a partir do qual o relatório avisa


def _vazio(valor) -> bool:
    if isinstance(valor, list):
        return len(valor) == 0
    return valor is None or pd.isna(valor)


def _percentual_vazio(linhas: pd.DataFrame, coluna: str) -> float:
    if len(linhas) == 0:
        return 0.0
    return 100 * linhas[coluna].map(_vazio).mean()


def relatorio_qualidade(tabela: pd.DataFrame, excluidos: pd.DataFrame, arquivos: pd.DataFrame):
    """Devolve (uma linha por arquivo, lista de avisos).

    tabela: registros aproveitados; excluidos: registros retirados; arquivos: resumo de `ler_pasta`.
    """
    origem = tabela["arquivos_origem"].map(lambda a: a[0])
    linhas = []
    for _, arquivo in arquivos.iterrows():
        do_arquivo = tabela[origem == arquivo["arquivo"]]
        linha = arquivo.to_dict()
        linha["linhas_aproveitadas"] = len(do_arquivo)
        for coluna in CAMPOS_VERIFICADOS:
            linha[f"% {coluna} vazio"] = round(_percentual_vazio(do_arquivo, coluna), 1)
        linhas.append(linha)
    por_arquivo = pd.DataFrame(linhas)

    avisos = [
        f"O arquivo {a['arquivo']} foi ignorado: {a['motivo']}."
        for _, a in arquivos[arquivos["situacao"] == "ignorado"].iterrows()
    ]
    for base, da_base in tabela.groupby("base_origem"):
        for coluna, descricao in CAMPOS_VERIFICADOS.items():
            percentual = _percentual_vazio(da_base, coluna)
            if percentual >= LIMITE_AVISO:
                avisos.append(f"{percentual:.0f}% dos registros da base {base} vieram {descricao}.")
    for motivo, quantidade in excluidos["motivo_exclusao"].value_counts().items():
        avisos.append(f"{quantidade} registro(s) retirado(s) por: {motivo}.")
    return por_arquivo, avisos
