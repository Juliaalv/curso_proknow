import matplotlib

matplotlib.use("Agg")

import pandas as pd

from curso_proknowc import esquema, rastreabilidade


def _excluidos(titulos, motivos):
    return pd.DataFrame(
        {"id": [f"R{n}" for n in range(len(titulos))], "doi": None, "titulo": titulos, "motivo_exclusao": motivos}
    )


def _etapas():
    return [
        {"etapa": "Remoção de incompletos e duplicados", "entram": 200, "excluidos": 50, "motivo": "duplicado (45); informação ausente (5)"},
        {"etapa": "Alinhamento pelo título", "entram": 150, "excluidos": 110, "motivo": "título não alinhado (110)"},
        {"etapa": "Representatividade", "entram": 40, "excluidos": 0, "motivo": "", "incluidos": 3},
    ]


def test_registros_por_base():
    bruta = pd.DataFrame({"base_origem": ["scopus", "scopus", "ieee"]})
    assert rastreabilidade.registros_por_base(bruta) == {"scopus": 2, "ieee": 1}


def test_etapa_de_excluidos_resume_motivos():
    excluidos = _excluidos(["a", "b", "c"], ["duplicado", "duplicado", "informação ausente"])
    etapa = rastreabilidade.etapa_de_excluidos("Remoção de incompletos e duplicados", 10, excluidos)
    assert etapa == {
        "etapa": "Remoção de incompletos e duplicados",
        "entram": 10,
        "excluidos": 3,
        "motivo": "duplicado (2); informação ausente (1)",
    }


def test_fluxograma_mostra_bases_etapas_e_portfolio():
    figura = rastreabilidade.fluxograma(_etapas(), {"scopus": 120, "ieee": 80})
    textos = " ".join(t.get_text() for t in figura.axes[0].texts)
    assert "Scopus (n = 120)" in textos
    assert "IEEE (n = 80)" in textos
    assert "Alinhamento pelo título" in textos
    assert "n = 110" in textos
    assert "título não alinhado (110)" in textos
    assert "Portfólio final (n = 43)" in textos


def test_log_decisoes():
    log = rastreabilidade.log_decisoes(
        {
            "Delimitações": _excluidos(["a"], ["fora do intervalo de anos"]),
            "Título": _excluidos(["b", "c"], ["título não alinhado", "título não alinhado"]),
        }
    )
    assert list(log.columns) == ["etapa", "id", "doi", "titulo", "motivo_exclusao", "motivo_pesquisador"]
    assert len(log) == 3
    assert log.iloc[0]["etapa"] == "Delimitações"
    assert log.iloc[2]["titulo"] == "c"


def test_checklist_preenche_contagens():
    texto = rastreabilidade.checklist_prisma(_etapas(), {"scopus": 120, "ieee": 80})
    assert "Fontes de informação" in texto
    assert "scopus (120), ieee (80)" in texto
    assert "200 registros" in texto
    assert "43 artigos" in texto


def _portfolio():
    return esquema.completar(
        pd.DataFrame(
            {
                "id": ["R00001", "R00002"],
                "doi": ["10.1/a", None],
                "titulo": ["Wind & LSTM {forecasting}", "Outro artigo"],
                "resumo": ["Resumo A", None],
                "autores": [["Silva, J.", "Santos, M."], ["Silva, J."]],
                "ano": [2022, 2022],
                "periodico": ["Energy", "Proc. Conference"],
                "tipo_documento": ["artigo", "conferência"],
                "palavras_chave": [["lstm", "wind speed"], []],
            }
        )
    )


def test_exportar_ris(tmp_path):
    caminho = rastreabilidade.exportar_ris(_portfolio(), tmp_path / "portfolio.ris")
    texto = caminho.read_text(encoding="utf-8")
    registros = texto.strip().split("ER  - ")
    assert len([r for r in registros if r.strip()]) == 2
    assert "TY  - JOUR" in texto
    assert "TY  - CONF" in texto
    assert "AU  - Silva, J.\nAU  - Santos, M." in texto
    assert "DO  - 10.1/a" in texto
    assert "KW  - wind speed" in texto
    assert "PY  - 2022" in texto


def test_exportar_bibtex(tmp_path):
    caminho = rastreabilidade.exportar_bibtex(_portfolio(), tmp_path / "portfolio.bib")
    texto = caminho.read_text(encoding="utf-8")
    assert "@article{silva2022," in texto
    assert "@inproceedings{silva2022b," in texto
    assert "author = {Silva, J. and Santos, M.}" in texto
    assert "title = {Wind \\& LSTM forecasting}" in texto
    assert "doi = {10.1/a}" in texto
    assert "booktitle = {Proc. Conference}" in texto
