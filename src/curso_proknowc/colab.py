"""Estrutura comum dos notebooks (seção 8 do plano): pastas, entrada, salvamento e histórico.

Cada notebook é independente: começa por `preparar`, carrega a entrada (o exemplo do curso ou a
tabela que o próprio aluno salvou antes), executa a etapa e salva o resultado em `resultados/`.
O histórico de etapas (`historico.json` + tabelas de excluídos) alimenta o fluxograma da A10.
"""

import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from curso_proknowc import esquema, rastreabilidade, triagem
from curso_proknowc.leitura import criar_pasta_entrada
from curso_proknowc.tratamento import normalizar_titulo

EXEMPLO = "exemplo do curso"
MEUS_ARQUIVOS = "meus arquivos"

DRIVE = Path("/content/drive")
REPO = Path(__file__).resolve().parents[2]


@dataclass
class Pastas:
    raiz: Path
    entrada: Path
    resultados: Path
    exemplo: Path  # dados/ do repositório: exemplo_bruto/ e exemplo_processado/


def no_colab() -> bool:
    return "google.colab" in sys.modules


def preparar(raiz=None, exemplo=None) -> Pastas:
    """Cria a pasta do curso (no Google Drive, quando no Colab) com entrada/<base>/ e resultados/."""
    if raiz is None:
        if no_colab():
            from google.colab import drive

            drive.mount(str(DRIVE))
            raiz = DRIVE / "MyDrive" / "curso_proknowc"
        else:
            raiz = Path.cwd() / "curso_proknowc"
    raiz = Path(raiz)
    pastas = Pastas(
        raiz=raiz,
        entrada=criar_pasta_entrada(raiz / "entrada"),
        resultados=raiz / "resultados",
        exemplo=Path(exemplo) if exemplo else REPO / "dados",
    )
    pastas.resultados.mkdir(parents=True, exist_ok=True)
    return pastas


def ler_eixos(pares) -> dict:
    """[(nome do eixo, "termo; termo"), ...] digitados no formulário -> {eixo: [termos]}; eixos sem nome saem."""
    return {
        nome.strip(): [t.strip() for t in termos.split(";") if t.strip()]
        for nome, termos in pares
        if nome.strip()
    }


def pasta_entrada(pastas: Pastas, fonte: str) -> Path:
    """Pasta com os CSVs das bases: a do aluno ou a de reserva do curso."""
    return pastas.exemplo / "exemplo_bruto" if fonte == EXEMPLO else pastas.entrada


def _pasta_resultados(pastas: Pastas, fonte: str) -> Path:
    return pastas.exemplo / "exemplo_processado" if fonte == EXEMPLO else pastas.resultados


def _texto_csv(valor):
    if isinstance(valor, list):
        return "; ".join(map(str, valor))
    if isinstance(valor, dict):
        return json.dumps(valor, ensure_ascii=False)
    return valor


def salvar(pastas: Pastas, tabela: pd.DataFrame, nome: str, baixar: bool = False) -> Path:
    """Grava resultados/<nome>.parquet e uma cópia .csv para abrir em planilha."""
    caminho = pastas.resultados / f"{nome}.parquet"
    esquema.salvar(tabela, caminho)
    tabela.apply(lambda coluna: coluna.map(_texto_csv)).to_csv(
        caminho.with_suffix(".csv"), index=False, encoding="utf-8-sig"
    )
    if baixar and no_colab():
        from google.colab import files

        files.download(str(caminho.with_suffix(".csv")))
    return caminho


def carregar(pastas: Pastas, fonte: str, nome: str, notebook: str) -> pd.DataFrame:
    """Carrega a tabela de entrada do notebook.

    Com o exemplo, o histórico das etapas anteriores ao notebook também vem do exemplo,
    substituindo o do aluno, para o fluxograma corresponder à cadeia realmente usada.
    """
    caminho = _pasta_resultados(pastas, fonte) / f"{nome}.parquet"
    if not caminho.exists():
        raise FileNotFoundError(
            f"Não encontrei {caminho.name} em {caminho.parent}. Rode antes o notebook anterior "
            f"(e confira se ele salvou o resultado) ou escolha a entrada '{EXEMPLO}'."
        )
    if fonte == EXEMPLO:
        _copiar_historico_do_exemplo(pastas, notebook)
    return esquema.carregar(caminho)


# --- Triagem (A5) ---

# Só o gerador do conjunto de exemplo liga isto: artigos sem decisão contam como aceitos.
ACEITAR_PENDENTES = False


def arquivo_decisoes(pastas: Pastas, fonte: str) -> Path:
    """Arquivo de decisões da triagem em resultados/. Com o exemplo, começa com as decisões do curso."""
    arquivo = pastas.resultados / "decisoes.csv"
    do_exemplo = pastas.exemplo / "exemplo_processado" / "decisoes.csv"
    if fonte == EXEMPLO and not arquivo.exists() and do_exemplo.exists():
        shutil.copy(do_exemplo, arquivo)
    return arquivo


def aplicar_triagem(tabela: pd.DataFrame, etapa: str, arquivo: Path):
    """`triagem.aplicar`, aceitando os pendentes quando ACEITAR_PENDENTES estiver ligado."""
    if ACEITAR_PENDENTES:
        while (artigo := triagem.proximo(tabela, etapa, arquivo)) is not None:
            triagem.registrar(arquivo, artigo["id"], etapa, "aceito")
    return triagem.aplicar(tabela, etapa, arquivo)


# --- Histórico de etapas (para a A10) ---

def _arquivo_historico(pasta: Path) -> Path:
    return pasta / "historico.json"


def _ler_historico(pasta: Path) -> dict:
    arquivo = _arquivo_historico(pasta)
    if not arquivo.exists():
        return {"por_base": {}, "etapas": []}
    return json.loads(arquivo.read_text(encoding="utf-8"))


def _gravar_historico(pasta: Path, historico: dict) -> None:
    _arquivo_historico(pasta).write_text(json.dumps(historico, ensure_ascii=False, indent=2), encoding="utf-8")


def _arquivo_excluidos(pasta: Path, notebook: str, etapa: str) -> Path:
    return pasta / "excluidos" / f"{notebook}_{normalizar_titulo(etapa).replace(' ', '_')}.parquet"


def registrar_bases(pastas: Pastas, por_base: dict) -> None:
    """Guarda quantos registros cada base trouxe (primeira caixa do fluxograma)."""
    historico = _ler_historico(pastas.resultados)
    historico["por_base"] = {base: int(n) for base, n in por_base.items()}
    _gravar_historico(pastas.resultados, historico)


def registrar_etapa(pastas: Pastas, notebook: str, etapa: str, entram: int, excluidos: pd.DataFrame, incluidos: int = 0) -> None:
    """Acrescenta (ou substitui, se rodada de novo) uma etapa do histórico e guarda seus excluídos."""
    registro = rastreabilidade.etapa_de_excluidos(etapa, int(entram), excluidos)
    registro["notebook"] = notebook
    if incluidos:
        registro["incluidos"] = int(incluidos)
    historico = _ler_historico(pastas.resultados)
    historico["etapas"] = [e for e in historico["etapas"] if e["etapa"] != etapa] + [registro]
    _gravar_historico(pastas.resultados, historico)
    esquema.salvar(excluidos, _arquivo_excluidos(pastas.resultados, notebook, etapa))


def historico(pastas: Pastas, fonte: str):
    """Devolve (registros por base, etapas em ordem, {etapa: tabela de excluídos})."""
    pasta = _pasta_resultados(pastas, fonte)
    dados = _ler_historico(pasta)
    excluidos = {}
    for etapa in dados["etapas"]:
        arquivo = _arquivo_excluidos(pasta, etapa["notebook"], etapa["etapa"])
        excluidos[etapa["etapa"]] = esquema.carregar(arquivo) if arquivo.exists() else pd.DataFrame()
    return dados["por_base"], dados["etapas"], excluidos


def _copiar_historico_do_exemplo(pastas: Pastas, notebook: str) -> None:
    origem = pastas.exemplo / "exemplo_processado"
    dados = _ler_historico(origem)
    dados["etapas"] = [e for e in dados["etapas"] if e["notebook"] < notebook]
    shutil.rmtree(pastas.resultados / "excluidos", ignore_errors=True)
    for etapa in dados["etapas"]:
        arquivo = _arquivo_excluidos(origem, etapa["notebook"], etapa["etapa"])
        if arquivo.exists():
            destino = _arquivo_excluidos(pastas.resultados, etapa["notebook"], etapa["etapa"])
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(arquivo, destino)
    _gravar_historico(pastas.resultados, dados)
