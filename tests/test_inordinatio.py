import pandas as pd
import pytest

from curso_proknowc.inordinatio import (
    calcular_inordinatio,
    comparar_com_corte,
    corte_citacoes,
    ranking_inordinatio,
)


def _tabela():
    return pd.DataFrame(
        {
            "id": ["a", "b", "c", "d"],
            "titulo": ["A", "B", "C", "D"],
            "ano": [2016, 2020, 2025, 2026],
            "citacoes": [100, 50, 5, 0],
            "sjr": [2000.0, 1000.0, None, 500.0],
        }
    )


def test_formula():
    t = calcular_inordinatio(_tabela(), "sjr", ano_pesquisa=2026, alfa=10)
    # (FI/1000) + α × [10 − (2026 − ano)] + citações
    assert t["inordinatio"].tolist() == pytest.approx([2 + 0 + 100, 1 + 40 + 50, 0 + 90 + 5, 0.5 + 100 + 0])


def test_fi_ausente_vale_zero_com_aviso():
    with pytest.warns(UserWarning, match="1 artigo"):
        t = calcular_inordinatio(_tabela(), "sjr", ano_pesquisa=2026, alfa=1)
    assert t.loc[2, "inordinatio"] == pytest.approx(0 + 9 + 5)


def test_coluna_fi_inexistente_vale_zero_com_aviso():
    with pytest.warns(UserWarning, match="citescore"):
        t = calcular_inordinatio(_tabela(), "citescore", ano_pesquisa=2026, alfa=1)
    assert t.loc[0, "inordinatio"] == pytest.approx(0 + 0 + 100)


def test_citacoes_ausentes_valem_zero():
    tabela = _tabela()
    tabela.loc[0, "citacoes"] = None
    t = calcular_inordinatio(tabela, "sjr", ano_pesquisa=2026, alfa=1)
    assert t.loc[0, "inordinatio"] == pytest.approx(2 + 0 + 0)


@pytest.mark.parametrize("alfa", [0, 11, -1, 10.5])
def test_alfa_fora_de_1_a_10(alfa):
    with pytest.raises(ValueError, match="α"):
        calcular_inordinatio(_tabela(), "sjr", ano_pesquisa=2026, alfa=alfa)


def test_ranking_ordena_e_numera():
    r = ranking_inordinatio(_tabela(), "sjr", ano_pesquisa=2026, alfa=10)
    assert r["id"].tolist() == ["a", "d", "c", "b"]
    assert r["posicao_inordinatio"].tolist() == [1, 2, 3, 4]


def test_corte_citacoes_acumuladas():
    # total 155: a = 64,5% (entra), b chega a 96,8% mas começa abaixo de 80% (entra), c começa acima (sai)
    assert corte_citacoes(_tabela(), percentual=80)["id"].tolist() == ["a", "b"]
    assert corte_citacoes(_tabela(), percentual=50)["id"].tolist() == ["a"]


def test_comparacao_lado_a_lado():
    c = comparar_com_corte(_tabela(), "sjr", ano_pesquisa=2026, alfa=10, percentual=80)
    # top-N padrão = tamanho do portfólio pelo corte (2): d e a
    situacao = dict(zip(c["id"], c["situacao"]))
    assert situacao == {"a": "nos dois", "b": "só no corte de citações", "d": "só no InOrdinatio"}


def test_comparacao_com_top_n():
    c = comparar_com_corte(_tabela(), "sjr", ano_pesquisa=2026, alfa=10, percentual=80, top_n=3)
    situacao = dict(zip(c["id"], c["situacao"]))
    assert situacao == {"a": "nos dois", "b": "só no corte de citações", "c": "só no InOrdinatio", "d": "só no InOrdinatio"}
