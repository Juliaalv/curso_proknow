"""Executa os notebooks gerados, em sequência, sobre os CSVs de teste (sem rede)."""

import json
import sys
from pathlib import Path

import nbformat

FERRAMENTAS = Path(__file__).resolve().parents[1] / "ferramentas"
sys.path.insert(0, str(FERRAMENTAS))

from executar_notebooks import executar  # noqa: E402
from gerar_notebooks import gerar  # noqa: E402

ENTRADA = Path(__file__).parent / "dados" / "entrada"


def test_toda_celula_de_codigo_e_um_formulario(tmp_path):
    for caminho in gerar(tmp_path):
        for celula in nbformat.read(caminho, as_version=4).cells:
            if celula.cell_type == "code":
                assert celula.source.startswith("#@title"), caminho.name
                assert celula.metadata["cellView"] == "form"


def test_notebooks_rodam_em_sequencia_com_meus_arquivos(tmp_path):
    resultados = executar(ENTRADA, sem_rede=True, trabalho=tmp_path)
    for nome in ["02_padronizado", "03_alinhados_titulo", "04_portfolio", "05_portfolio_final"]:
        assert (resultados / f"{nome}.parquet").exists(), nome
    for arquivo in ["fluxograma.png", "portfolio.ris", "portfolio.bib", "log_exclusoes.csv"]:
        assert (resultados / arquivo).exists(), arquivo

    historico = json.loads((resultados / "historico.json").read_text(encoding="utf-8"))
    assert historico["por_base"] == {"ieee": 2, "scopus": 3}
    assert [e["etapa"] for e in historico["etapas"]] == [
        "Registros incompletos",
        "Delimitações",
        "Duplicados",
        "Alinhamento pelo título",
        "Reconhecimento científico e repescagem",
        "Leitura do resumo",
        "Leitura do texto completo",
        "Teste de representatividade",
    ]
