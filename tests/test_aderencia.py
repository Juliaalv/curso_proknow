from pathlib import Path

import pandas as pd
import pytest

from curso_proknowc import aderencia as a
from curso_proknowc.leitura import ler_pasta

ENTRADA = Path(__file__).parent / "dados" / "entrada"

EIXOS = {
    "Wind Speed": ["wind speed", "wind velocity"],
    "Forecasting": ["forecast*", "prediction"],
}


def test_curinga_cobre_continuacao_da_palavra():
    assert a.cobre("forecast*", "forecasting")
    assert a.cobre("forecast*", "forecast")
    assert not a.cobre("forecast*", "nowcasting")


def test_sem_curinga_exige_palavra_inteira():
    assert a.cobre("prediction", "wind power prediction")
    assert not a.cobre("prediction", "predictions")
    assert not a.cobre("wind", "windmill")


def test_termo_composto_cobre_se_aparece_dentro_da_palavra_chave():
    assert a.cobre("wind speed", "short-term wind speed")
    assert not a.cobre("wind speed", "speed of wind")


def test_comparacao_ignora_maiusculas_acentos_e_aspas():
    assert a.cobre('"Previsão"', "previsao de vento")
    assert a.cobre("previs*", "PREVISÃO")


def test_palavras_digitadas_em_lista_ou_texto_com_ponto_e_virgula():
    tabela, _, _ = a.testar_aderencia(
        EIXOS,
        {"Artigo 1": "Wind Speed; LSTM", "Artigo 2": ["wind power forecasting", "deep learning"]},
    )
    assert list(tabela.columns) == ["artigo", "palavra_chave", "situacao", "termo"]
    assert tabela.to_dict("records") == [
        {"artigo": "Artigo 1", "palavra_chave": "wind speed", "situacao": "contemplada", "termo": "wind speed"},
        {"artigo": "Artigo 1", "palavra_chave": "lstm", "situacao": "ausente", "termo": ""},
        {"artigo": "Artigo 2", "palavra_chave": "wind power forecasting", "situacao": "contemplada", "termo": "forecast*"},
        {"artigo": "Artigo 2", "palavra_chave": "deep learning", "situacao": "ausente", "termo": ""},
    ]


def test_sugestoes_sao_as_ausentes_sem_repeticao():
    _, sugestoes, mensagem = a.testar_aderencia(EIXOS, {"A": "lstm; wind speed", "B": "LSTM; deep learning"})
    assert sugestoes == ["lstm", "deep learning"]
    assert "não passou" in mensagem
    assert "3 de 4" in mensagem
    assert "busque de novo" in mensagem


def test_mensagem_quando_falta_palavra_sugere_curinga_para_plural():
    _, _, mensagem = a.testar_aderencia(
        {"Previsão": ["prediction"]}, {"A": ["predictions"], "B": ["prediction"]}
    )
    assert "*" in mensagem and "plural" in mensagem


def test_mensagem_quando_a_busca_passa():
    _, sugestoes, mensagem = a.testar_aderencia(EIXOS, {"A": "wind speed", "B": "forecasting"})
    assert sugestoes == []
    assert "passou no teste" in mensagem
    assert "não passou" not in mensagem


def test_exige_pelo_menos_dois_artigos_semente():
    with pytest.raises(ValueError, match="2 artigos"):
        a.testar_aderencia(EIXOS, {"A": "wind speed"})


TABELA = pd.DataFrame(
    {
        "id": ["R00001", "R00002", "R00003"],
        "titulo": ["Wind speed forecasting with LSTM", "Hybrid deep learning for wind", "Previsão de vento"],
        "palavras_chave_autor": [["lstm", "wind speed"], ["deep learning"], []],
        "palavras_chave": [["lstm", "wind speed", "forecasting"], ["deep learning"], ["vento", "previsão"]],
    }
)


def test_sementes_da_tabela_por_id_ou_trecho_do_titulo():
    sementes = a.sementes_da_tabela(TABELA, ["R00002", "wind speed FORECASTING"])
    assert sementes == {
        "Hybrid deep learning for wind": ["deep learning"],
        "Wind speed forecasting with LSTM": ["lstm", "wind speed"],
    }


def test_sem_palavras_do_autor_usa_todas_as_palavras_chave():
    assert a.sementes_da_tabela(TABELA, ["previsao"]) == {"Previsão de vento": ["vento", "previsão"]}


def test_escolha_sem_artigo_correspondente_avisa():
    with pytest.raises(ValueError, match="Nenhum artigo"):
        a.sementes_da_tabela(TABELA, ["solar"])


def test_escolha_ambigua_pede_o_id():
    with pytest.raises(ValueError, match="R00001.*R00002"):
        a.sementes_da_tabela(TABELA, ["wind"])


def test_fluxo_com_a_tabela_padronizada_da_a2():
    tabela, _ = ler_pasta(ENTRADA)
    sementes = a.sementes_da_tabela(tabela, ["R00001", "hybrid deep learning"])
    resultado, sugestoes, _ = a.testar_aderencia(EIXOS, sementes)
    assert len(resultado) == 4
    assert sugestoes == ["lstm", "deep learning", "wind"]
