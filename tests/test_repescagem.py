import pandas as pd

from curso_proknowc import esquema, repescagem


def _grupo_a():
    return esquema.completar(
        pd.DataFrame(
            {
                "id": ["a1", "a2"],
                "titulo": ["A1", "A2"],
                "autores": [["Conceição, M.", "Silva, J."], ["Lima, P."]],
                "ano": [2018, 2020],
                "grupo": ["A", "A"],
            }
        )
    )


def _abaixo():
    return esquema.completar(
        pd.DataFrame(
            {
                "id": ["r1", "r2", "v1", "v2", "v3"],
                "titulo": ["Recente 2026", "Recente 2025", "Antigo com autor", "Antigo sem autor", "Sem ano"],
                "autores": [["Outro, X."], None, ["CONCEICAO, M.", "Novo, Y."], ["Costa, R."], None],
                "ano": [2026, 2025, 2015, 2024, None],
            }
        )
    )


def test_recentes_vao_para_leitura_do_resumo():
    enviados, _ = repescagem.repescar(_abaixo(), _grupo_a(), ano_pesquisa=2026)
    recentes = enviados[enviados["motivo_repescagem"] == "recente"]
    assert recentes["id"].tolist() == ["r1", "r2"]


def test_antigo_com_autor_do_grupo_a_e_repescado_mostrando_o_autor():
    enviados, _ = repescagem.repescar(_abaixo(), _grupo_a(), ano_pesquisa=2026)
    linha = enviados[enviados["id"] == "v1"].iloc[0]
    assert linha["autores_grupo_a"] == ["CONCEICAO, M."]
    assert "autor do grupo A" in linha["motivo_repescagem"]
    assert set(enviados["grupo"]) == {"repescagem"}


def test_demais_sao_excluidos_com_motivo():
    _, excluidos = repescagem.repescar(_abaixo(), _grupo_a(), ano_pesquisa=2026)
    assert excluidos["id"].tolist() == ["v2", "v3"]
    assert set(excluidos["motivo_exclusao"]) == {"abaixo do corte, antigo e sem autor do grupo A"}


def test_banco_de_autores():
    banco = repescagem.banco_autores(_grupo_a())
    assert banco.to_dict("list") == {"autor": ["Conceição, M.", "Lima, P.", "Silva, J."], "artigos": [1, 1, 1]}
