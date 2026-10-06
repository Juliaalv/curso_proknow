import shutil
from pathlib import Path

import pytest

from curso_proknowc import esquema
from curso_proknowc.delimitacoes import aplicar_delimitacoes, remover_incompletos
from curso_proknowc.leitura import ler_pasta
from curso_proknowc.relatorio import relatorio_qualidade

ENTRADA = Path(__file__).parent / "dados" / "entrada"
SCOPUS = ENTRADA / "scopus" / "scopus.csv"
IEEE = ENTRADA / "ieee" / "export2025.10.05.csv"


@pytest.fixture
def entrada(tmp_path):
    destino = tmp_path / "entrada"
    shutil.copytree(ENTRADA, destino)
    return destino


def test_le_e_concatena_as_duas_bases(entrada):
    tabela, arquivos = ler_pasta(entrada)
    assert len(tabela) == 5
    assert sorted(tabela["base_origem"].unique()) == ["ieee", "scopus"]
    assert set(esquema.COLUNAS) <= set(tabela.columns)
    assert tabela["id"].is_unique
    assert list(arquivos["situacao"]) == ["lido", "lido"]


def test_campos_mapeados_e_tratados(entrada):
    tabela, _ = ler_pasta(entrada)
    lstm_scopus = tabela[(tabela["base_origem"] == "scopus") & (tabela["ano"] == 2022)].iloc[0]
    assert lstm_scopus["titulo"] == "Short-term wind speed forecasting using LSTM networks"
    assert lstm_scopus["autores"] == ["Silva, J.", "Santos, M.A."]
    assert lstm_scopus["doi"] == "10.1016/j.renene.2022.01.001"
    assert lstm_scopus["palavras_chave"] == ["wind speed", "lstm", "forecasting", "wind power", "neural networks"]
    assert lstm_scopus["palavras_chave_autor"] == ["wind speed", "lstm", "forecasting"]
    assert lstm_scopus["citacoes_por_base"] == {"scopus": 45}
    assert lstm_scopus["arquivos_origem"] == ["scopus/scopus.csv"]

    lstm_ieee = tabela[(tabela["base_origem"] == "ieee") & (tabela["ano"] == 2022)].iloc[0]
    assert lstm_ieee["autores"] == ["Silva, J.", "Santos, M.A."]
    assert lstm_ieee["doi"] == "10.1016/j.renene.2022.01.001"
    assert lstm_ieee["tipo_documento"] == "artigo"


def test_citacao_vazia_vale_zero(entrada):
    tabela, _ = ler_pasta(entrada)
    revisao = tabela[tabela["tipo_documento"] == "revisão"].iloc[0]
    assert revisao["citacoes_por_base"] == {"scopus": 0}
    assert revisao["resumo"] is None


def test_varios_arquivos_da_mesma_base_sao_concatenados(entrada):
    shutil.copy(SCOPUS, entrada / "scopus" / "scopus_lote2.csv")
    tabela, arquivos = ler_pasta(entrada)
    assert (tabela["base_origem"] == "scopus").sum() == 6
    assert len(arquivos) == 3


def test_arquivo_na_pasta_errada_e_ignorado_com_aviso(entrada):
    shutil.copy(IEEE, entrada / "scopus" / "ieee_por_engano.csv")
    tabela, arquivos = ler_pasta(entrada)
    assert len(tabela) == 5
    ignorado = arquivos[arquivos["arquivo"] == "scopus/ieee_por_engano.csv"].iloc[0]
    assert ignorado["situacao"] == "ignorado"
    assert "ieee" in ignorado["motivo"]


def test_detecta_ponto_e_virgula_e_latin1(entrada):
    texto = SCOPUS.read_text(encoding="utf-8-sig")
    import csv, io
    linhas = list(csv.reader(io.StringIO(texto)))
    saida = io.StringIO()
    csv.writer(saida, delimiter=";").writerows(linhas)
    (entrada / "scopus" / "scopus.csv").write_bytes(saida.getvalue().replace("João", "Joãozinho").encode("latin-1"))
    tabela, _ = ler_pasta(entrada)
    assert (tabela["base_origem"] == "scopus").sum() == 3


def test_pasta_vazia_e_arquivos_fora_do_padrao(tmp_path):
    entrada = tmp_path / "entrada"
    (entrada / "scopus").mkdir(parents=True)
    (entrada / "ieee").mkdir()
    (entrada / "solto.csv").write_text("a,b\n1,2\n")
    (entrada / "scopus" / "notas.txt").write_text("oi")
    tabela, arquivos = ler_pasta(entrada)
    assert len(tabela) == 0
    assert set(arquivos["situacao"]) == {"ignorado"}


def test_remove_incompletos_com_motivo(entrada):
    tabela, _ = ler_pasta(entrada)
    mantidos, excluidos = remover_incompletos(tabela)
    assert len(mantidos) == 4
    assert list(excluidos["motivo_exclusao"]) == ["informação ausente"]


def test_delimitacoes_registram_motivo(entrada):
    tabela, _ = ler_pasta(entrada)
    tabela, _ = remover_incompletos(tabela)
    mantidos, excluidos = aplicar_delimitacoes(tabela, anos=(2020, 2026), tipos=["artigo", "conferência"])
    assert len(mantidos) == 3
    assert list(excluidos["motivo_exclusao"]) == ["fora do intervalo de anos"]


def test_delimitacao_de_idioma_mantem_quem_nao_informa_idioma(entrada):
    tabela, _ = ler_pasta(entrada)
    tabela, _ = remover_incompletos(tabela)
    mantidos, excluidos = aplicar_delimitacoes(tabela, idiomas=["en"])
    assert len(mantidos) == 4  # o registro em português já saiu por estar incompleto; IEEE não informa idioma


def test_relatorio_por_arquivo_e_avisos(entrada):
    tabela, arquivos = ler_pasta(entrada)
    mantidos, excluidos = remover_incompletos(tabela)
    por_arquivo, avisos = relatorio_qualidade(mantidos, excluidos, arquivos)
    scopus = por_arquivo[por_arquivo["arquivo"] == "scopus/scopus.csv"].iloc[0]
    assert scopus["linhas_lidas"] == 3
    assert scopus["linhas_aproveitadas"] == 2
    assert any("sem resumo" in a and "scopus" in a for a in avisos)


def test_salvar_e_carregar_parquet(entrada, tmp_path):
    tabela, _ = ler_pasta(entrada)
    caminho = tmp_path / "tabela.parquet"
    esquema.salvar(tabela, caminho)
    lida = esquema.carregar(caminho)
    assert len(lida) == len(tabela)
    assert lida.iloc[0]["autores"] == tabela.iloc[0]["autores"]
    assert lida.iloc[0]["citacoes_por_base"] == tabela.iloc[0]["citacoes_por_base"]
