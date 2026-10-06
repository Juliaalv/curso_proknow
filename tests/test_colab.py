import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

from curso_proknowc import colab, esquema

RAIZ_TESTES = Path(__file__).parent / "dados"


def _tabela(ids):
    return esquema.completar(pd.DataFrame({"id": ids, "titulo": [f"Artigo {i}" for i in ids], "autores": [["Silva, J."]] * len(ids)}))


@pytest.fixture
def pastas(tmp_path):
    exemplo = tmp_path / "repo" / "dados"
    shutil.copytree(RAIZ_TESTES / "entrada", exemplo / "exemplo_bruto")
    (exemplo / "exemplo_processado").mkdir(parents=True)
    return colab.preparar(raiz=tmp_path / "drive" / "curso_proknowc", exemplo=exemplo)


def test_preparar_cria_entrada_com_subpastas_e_resultados(pastas):
    assert (pastas.entrada / "scopus").is_dir()
    assert (pastas.entrada / "ieee").is_dir()
    assert pastas.resultados.is_dir()


def test_pasta_de_entrada_conforme_a_fonte(pastas):
    assert colab.pasta_entrada(pastas, colab.MEUS_ARQUIVOS) == pastas.entrada
    assert colab.pasta_entrada(pastas, colab.EXEMPLO) == pastas.exemplo / "exemplo_bruto"


def test_salvar_e_carregar_dos_meus_arquivos(pastas):
    colab.salvar(pastas, _tabela(["R1", "R2"]), "02_padronizado")
    assert (pastas.resultados / "02_padronizado.parquet").exists()
    csv = pd.read_csv(pastas.resultados / "02_padronizado.csv")
    assert csv.loc[0, "autores"] == "Silva, J."
    lida = colab.carregar(pastas, colab.MEUS_ARQUIVOS, "02_padronizado", notebook="03")
    assert list(lida["id"]) == ["R1", "R2"]


def test_carregar_arquivo_que_nao_existe_explica_o_que_fazer(pastas):
    with pytest.raises(FileNotFoundError, match="notebook anterior"):
        colab.carregar(pastas, colab.MEUS_ARQUIVOS, "02_padronizado", notebook="03")


def test_historico_registra_e_substitui_etapa_rodada_de_novo(pastas):
    colab.registrar_bases(pastas, {"scopus": 3, "ieee": 2})
    colab.registrar_etapa(pastas, "02", "Registros incompletos", 5, _tabela(["R9"]).assign(motivo_exclusao="informação ausente"))
    colab.registrar_etapa(pastas, "02", "Registros incompletos", 5, _tabela([]).assign(motivo_exclusao=None))
    por_base, etapas, excluidos = colab.historico(pastas, colab.MEUS_ARQUIVOS)
    assert por_base == {"scopus": 3, "ieee": 2}
    assert [e["etapa"] for e in etapas] == ["Registros incompletos"]
    assert etapas[0]["excluidos"] == 0
    assert len(excluidos["Registros incompletos"]) == 0


def test_usar_o_exemplo_traz_o_historico_das_etapas_anteriores(pastas):
    # Monta um "exemplo" com etapas dos notebooks 02 e 03.
    exemplo = colab.Pastas(raiz=pastas.exemplo, entrada=None, resultados=pastas.exemplo / "exemplo_processado", exemplo=pastas.exemplo)
    colab.registrar_bases(exemplo, {"scopus": 3})
    colab.registrar_etapa(exemplo, "02", "Registros incompletos", 3, _tabela(["R9"]).assign(motivo_exclusao="informação ausente"))
    colab.registrar_etapa(exemplo, "03", "Duplicados", 2, _tabela(["R2"]).assign(motivo_exclusao="duplicado"))
    colab.salvar(exemplo, _tabela(["R1", "R2"]), "02_padronizado")

    # O aluno tinha um histórico próprio, que deixa de valer ao escolher o exemplo.
    colab.registrar_etapa(pastas, "02", "Delimitações", 9, _tabela([]).assign(motivo_exclusao=None))

    colab.carregar(pastas, colab.EXEMPLO, "02_padronizado", notebook="03")
    por_base, etapas, _ = colab.historico(pastas, colab.MEUS_ARQUIVOS)
    assert por_base == {"scopus": 3}
    assert [e["etapa"] for e in etapas] == ["Registros incompletos"]


def test_decisoes_do_exemplo_sao_copiadas_uma_vez(pastas):
    from curso_proknowc import triagem

    exemplo = pastas.exemplo / "exemplo_processado" / "decisoes.csv"
    triagem.registrar(exemplo, "R1", "titulo", "aceito")
    arquivo = colab.arquivo_decisoes(pastas, colab.EXEMPLO)
    assert arquivo == pastas.resultados / "decisoes.csv"
    triagem.registrar(arquivo, "R2", "titulo", "rejeitado")
    colab.arquivo_decisoes(pastas, colab.EXEMPLO)  # não sobrescreve o que o aluno decidiu
    assert len(triagem.carregar_decisoes(arquivo, "titulo")) == 2


def test_decisoes_dos_meus_arquivos_comecam_vazias(pastas):
    assert not colab.arquivo_decisoes(pastas, colab.MEUS_ARQUIVOS).exists()


def test_aplicar_triagem_com_pendentes(pastas, monkeypatch):
    from curso_proknowc import triagem

    arquivo = pastas.resultados / "decisoes.csv"
    triagem.registrar(arquivo, "R1", "titulo", "rejeitado")
    with pytest.raises(ValueError, match="sem decisão"):
        colab.aplicar_triagem(_tabela(["R1", "R2"]), "titulo", arquivo)
    monkeypatch.setattr(colab, "ACEITAR_PENDENTES", True)
    aceitos, rejeitados = colab.aplicar_triagem(_tabela(["R1", "R2"]), "titulo", arquivo)
    assert list(aceitos["id"]) == ["R2"] and list(rejeitados["id"]) == ["R1"]


def test_ler_eixos_do_formulario():
    eixos = colab.ler_eixos([("Wind Speed", "wind speed; wind velocity ;"), ("Forecasting", "forecast*"), ("", "")])
    assert eixos == {"Wind Speed": ["wind speed", "wind velocity"], "Forecasting": ["forecast*"]}


def test_texto_de_lista_e_dicionario_no_csv(pastas):
    tabela = _tabela(["R1"])
    tabela.at[0, "citacoes_por_base"] = {"scopus": 4}
    colab.salvar(pastas, tabela, "x")
    csv = pd.read_csv(pastas.resultados / "x.csv")
    assert json.loads(csv.loc[0, "citacoes_por_base"]) == {"scopus": 4}
