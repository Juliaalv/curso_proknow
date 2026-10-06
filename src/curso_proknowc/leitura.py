"""Leitura da pasta de entrada e concatenação dos arquivos das bases (A2, etapa 1)."""

import io
from pathlib import Path

import pandas as pd

from curso_proknowc import esquema
from curso_proknowc.perfis import carregar_perfis
from curso_proknowc.tratamento import padronizar

EXTENSOES = {".csv"}
SEPARADORES = [",", ";", "\t"]


def criar_pasta_entrada(pasta) -> Path:
    """Cria a pasta de entrada com uma subpasta por base (scopus/, ieee/, ...)."""
    pasta = Path(pasta)
    for base in carregar_perfis():
        (pasta / base).mkdir(parents=True, exist_ok=True)
    return pasta


def _ler_texto(caminho: Path) -> str:
    conteudo = caminho.read_bytes()
    try:
        return conteudo.decode("utf-8-sig")
    except UnicodeDecodeError:
        return conteudo.decode("latin-1")


def ler_arquivo(caminho) -> pd.DataFrame:
    """Lê um CSV detectando codificação e separador; todas as células como texto."""
    texto = _ler_texto(Path(caminho))
    cabecalho = texto.split("\n", 1)[0]
    separador = max(SEPARADORES, key=cabecalho.count)
    return pd.read_csv(io.StringIO(texto), sep=separador, dtype=str, keep_default_na=False)


def _reconhece(colunas, perfil) -> bool:
    return set(perfil["assinatura"]) <= set(colunas)


def ler_pasta(pasta):
    """Lê todos os arquivos de entrada/<base>/ e devolve (tabela padronizada, resumo dos arquivos).

    O resumo tem uma linha por arquivo encontrado, com a situação ("lido" ou "ignorado") e o motivo.
    """
    pasta = Path(pasta)
    if not pasta.is_dir():
        raise FileNotFoundError(f"A pasta de entrada não existe: {pasta}")
    perfis = carregar_perfis()
    partes, arquivos = [], []

    def registrar(caminho, base, situacao, motivo="", linhas=0):
        arquivos.append(
            {
                "arquivo": caminho.relative_to(pasta).as_posix(),
                "base": base,
                "situacao": situacao,
                "motivo": motivo,
                "linhas_lidas": linhas,
            }
        )

    for item in sorted(pasta.iterdir()):
        if item.is_file():
            registrar(item, None, "ignorado", f"está fora das subpastas; mova para uma de: {', '.join(perfis)}")
            continue
        base = item.name
        for caminho in sorted(p for p in item.rglob("*") if p.is_file()):
            if base not in perfis:
                registrar(caminho, None, "ignorado", f"subpasta '{base}' desconhecida; use uma de: {', '.join(perfis)}")
                continue
            if caminho.suffix.lower() not in EXTENSOES:
                registrar(caminho, base, "ignorado", f"formato {caminho.suffix or 'sem extensão'} não suportado; exporte em CSV")
                continue
            try:
                bruto = ler_arquivo(caminho)
            except Exception as erro:
                registrar(caminho, base, "ignorado", f"não foi possível ler o arquivo ({erro})")
                continue
            perfil = perfis[base]
            if not _reconhece(bruto.columns, perfil):
                outras = [nome for nome, p in perfis.items() if nome != base and _reconhece(bruto.columns, p)]
                motivo = f"o cabeçalho não é de um arquivo da {perfil['nome']}"
                if outras:
                    motivo += f"; parece ser da base {outras[0]}: mova para a pasta {outras[0]}/"
                registrar(caminho, base, "ignorado", motivo)
                continue
            partes.append(padronizar(bruto, perfil, base, caminho.relative_to(pasta).as_posix()))
            registrar(caminho, base, "lido", linhas=len(bruto))

    partes = [p for p in partes if len(p)]
    tabela = pd.concat(partes, ignore_index=True) if partes else esquema.completar(pd.DataFrame())
    tabela["id"] = [f"R{n:05d}" for n in range(1, len(tabela) + 1)]
    resumo = pd.DataFrame(arquivos, columns=["arquivo", "base", "situacao", "motivo", "linhas_lidas"])
    return tabela, resumo
