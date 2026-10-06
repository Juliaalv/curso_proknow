"""Executa os notebooks em sequência, como um aluno que escolhe "meus arquivos".

Serve para testar os notebooks e para gerar o conjunto de exemplo a partir dos CSVs reais:

    python ferramentas/executar_notebooks.py --entrada dados/exemplo_bruto --saida dados/exemplo_processado \
        --decisoes minhas_decisoes.csv --email voce@exemplo.org

As decisões de triagem vêm do arquivo --decisoes (formato do triagem.py); artigos sem decisão
contam como aceitos. Com --sem-rede, as consultas ao OpenAlex e ao Unpaywall são puladas.
"""

import argparse
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

import nbformat
from nbclient import NotebookClient

PROJETO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from gerar_notebooks import gerar  # noqa: E402


def _definir(codigo: str, nome: str, valor) -> str:
    """Troca o valor de um campo de formulário (`NOME = ... #@param ...`)."""
    return re.sub(rf"^{nome} = .*?(#@param.*)$", lambda m: f"{nome} = {valor!r} {m.group(1)}", codigo, flags=re.M)


def executar(entrada, decisoes=None, email="", sem_rede=False, trabalho=None, saida=None) -> Path:
    """Roda os notebooks numa pasta de trabalho e devolve a pasta resultados/ produzida."""
    trabalho = Path(trabalho or tempfile.mkdtemp())
    raiz = trabalho / "curso_proknowc"
    shutil.copytree(entrada, raiz / "entrada", dirs_exist_ok=True)
    (raiz / "resultados").mkdir(parents=True, exist_ok=True)
    if decisoes:
        shutil.copy(decisoes, raiz / "resultados" / "decisoes.csv")

    valores = {"FONTE": "meus arquivos", "EMAIL": email}
    if sem_rede:
        valores |= {"ATUALIZAR_CITACOES": False, "BUSCAR_REFERENCIAS": False}
    os.environ["PYTHONPATH"] = os.pathsep.join([str(PROJETO / "src"), os.environ.get("PYTHONPATH", "")])

    for caminho in gerar(trabalho / "notebooks"):
        caderno = nbformat.read(caminho, as_version=4)
        for celula in caderno.cells:
            if celula.cell_type == "code":
                for nome, valor in valores.items():
                    celula.source = _definir(celula.source, nome, valor)
        caderno.cells.insert(2, nbformat.v4.new_code_cell("colab.ACEITAR_PENDENTES = True"))
        print("Executando", caminho.name)
        NotebookClient(caderno, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(trabalho)}}).execute()
        nbformat.write(caderno, caminho)

    if saida:
        shutil.copytree(raiz / "resultados", saida, dirs_exist_ok=True)
    return raiz / "resultados"


if __name__ == "__main__":
    argumentos = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    argumentos.add_argument("--entrada", required=True, help="pasta com scopus/ e ieee/")
    argumentos.add_argument("--saida", help="para onde copiar resultados/ (ex.: dados/exemplo_processado)")
    argumentos.add_argument("--decisoes", help="CSV de decisões de triagem")
    argumentos.add_argument("--email", default="", help="e-mail para o OpenAlex e o Unpaywall")
    argumentos.add_argument("--sem-rede", action="store_true")
    argumentos.add_argument("--trabalho", help="pasta de trabalho (padrão: temporária)")
    a = argumentos.parse_args()
    resultados = executar(a.entrada, a.decisoes, a.email, a.sem_rede, a.trabalho, a.saida)
    print("Resultados em", resultados)
