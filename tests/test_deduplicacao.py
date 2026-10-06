import time
from pathlib import Path

import pandas as pd

from curso_proknowc import esquema
from curso_proknowc.deduplicacao import deduplicar, sobreposicao
from curso_proknowc.delimitacoes import remover_incompletos
from curso_proknowc.leitura import ler_pasta

ENTRADA = Path(__file__).parent / "dados" / "entrada"


def _registro(id, titulo, ano=2020, autor="Silva, J.", base="scopus", doi=None, **outros):
    from curso_proknowc.tratamento import normalizar_titulo

    registro = {
        "id": id,
        "doi": doi,
        "titulo": titulo,
        "titulo_norm": normalizar_titulo(titulo),
        "autores": [autor] if autor else [],
        "ano": ano,
        "base_origem": base,
        "bases_origem": [base],
        "arquivos_origem": [f"{base}/{base}.csv"],
        "etapa_atual": "padronizado",
    }
    registro.update(outros)
    return registro


def _tabela(*registros):
    return esquema.completar(pd.DataFrame(list(registros)))


def _exemplo():
    tabela, _ = ler_pasta(ENTRADA)
    tabela, _ = remover_incompletos(tabela)
    return tabela


def test_funde_o_lstm_das_duas_bases_pelo_doi():
    tabela = _exemplo()
    sem_dup, relatorio = deduplicar(tabela)
    assert len(sem_dup) == len(tabela) - 1
    assert len(relatorio) == 1
    assert relatorio.iloc[0]["criterio"] == "DOI"
    lstm = sem_dup[sem_dup["doi"] == "10.1016/j.renene.2022.01.001"].iloc[0]
    assert lstm["bases_origem"] == ["scopus", "ieee"]
    assert lstm["arquivos_origem"] == ["scopus/scopus.csv", "ieee/export2025.10.05.csv"]
    assert lstm["citacoes_por_base"] == {"scopus": 45, "ieee": 50}
    assert {relatorio.iloc[0]["id_mantido"], relatorio.iloc[0]["id_removido"]} == set(
        tabela.loc[tabela["doi"] == "10.1016/j.renene.2022.01.001", "id"]
    )
    assert lstm["id"] == relatorio.iloc[0]["id_mantido"]
    assert (sem_dup["etapa_atual"] == "deduplicado").all()


def test_mantem_o_mais_completo_e_preenche_vazios():
    tabela = _tabela(
        _registro("R1", "Wind forecasting with LSTM", doi="10.1/a", base="ieee", issn="1234-5678",
                  citacoes=50, citacoes_fonte="ieee", citacoes_por_base={"ieee": 50}),
        _registro("R2", "Wind forecasting with LSTM", doi="10.1/a", resumo="Um resumo.",
                  palavras_chave=["lstm"], referencias_texto="Ref A", periodico="Energy",
                  citacoes=45, citacoes_fonte="scopus", citacoes_por_base={"scopus": 45}),
    )
    sem_dup, relatorio = deduplicar(tabela)
    assert len(sem_dup) == 1
    fundido = sem_dup.iloc[0]
    assert fundido["id"] == "R2"
    assert relatorio.iloc[0]["id_removido"] == "R1"
    assert fundido["resumo"] == "Um resumo."
    assert fundido["issn"] == "1234-5678"
    assert fundido["citacoes"] == 45 and fundido["citacoes_fonte"] == "scopus"
    assert fundido["citacoes_por_base"] == {"scopus": 45, "ieee": 50}
    assert fundido["bases_origem"] == ["scopus", "ieee"]


def test_palavras_chave_das_duas_bases_sao_unidas():
    sem_dup, _ = deduplicar(_exemplo())
    lstm = sem_dup[sem_dup["doi"] == "10.1016/j.renene.2022.01.001"].iloc[0]
    assert lstm["palavras_chave"] == ["wind speed", "lstm", "forecasting", "wind power", "neural networks", "wind forecasting"]
    assert lstm["palavras_chave_indexadas"] == ["wind power", "neural networks", "forecasting", "wind forecasting"]


def test_funde_por_titulo_semelhante_com_ano_e_autor_compativeis():
    tabela = _tabela(
        _registro("R1", "Short-term wind speed forecasting using LSTM networks", ano=2022, doi="10.1/a"),
        _registro("R2", "Short term wind speed forecasting using LSTM network", ano=2023, base="ieee"),
    )
    sem_dup, relatorio = deduplicar(tabela)
    assert len(sem_dup) == 1
    assert relatorio.iloc[0]["criterio"].startswith("título semelhante (")
    assert relatorio.iloc[0]["criterio"].endswith("%)")
    assert sem_dup.iloc[0]["bases_origem"] == ["scopus", "ieee"]


def test_titulo_semelhante_nao_funde_se_ano_autor_ou_doi_divergem():
    titulo = "Short-term wind speed forecasting using LSTM networks"
    tabela = _tabela(
        _registro("R1", titulo, ano=2020),
        _registro("R2", titulo, ano=2022),  # ano distante
        _registro("R3", titulo, ano=2020, autor="Wang, Y."),  # outro primeiro autor
        _registro("R4", "A review of wind power prediction methods", ano=2020, doi="10.1/x"),
        _registro("R5", "A review of wind power prediction methods", ano=2020, doi="10.1/y"),  # DOIs diferentes
    )
    sem_dup, relatorio = deduplicar(tabela)
    assert len(sem_dup) == 5
    assert relatorio.empty
    assert list(relatorio.columns[:3]) == ["id_mantido", "id_removido", "criterio"]


def test_limiar_ajustavel():
    tabela = _tabela(
        _registro("R1", "Wind speed forecasting using LSTM"),
        _registro("R2", "Wind speed prediction using LSTM"),
    )
    assert len(deduplicar(tabela)[0]) == 2
    assert len(deduplicar(tabela, limiar=70)[0]) == 1


def test_duplicados_dentro_da_mesma_base():
    tabela = _tabela(
        _registro("R1", "Wind forecasting", doi="10.1/a", citacoes_por_base={"scopus": 3}),
        _registro("R2", "Wind forecasting", doi="10.1/a", arquivos_origem=["scopus/lote2.csv"],
                  citacoes_por_base={"scopus": 3}),
    )
    sem_dup, relatorio = deduplicar(tabela)
    assert len(sem_dup) == 1
    assert sem_dup.iloc[0]["bases_origem"] == ["scopus"]
    assert sem_dup.iloc[0]["arquivos_origem"] == ["scopus/scopus.csv", "scopus/lote2.csv"]


def test_sobreposicao_entre_bases():
    sem_dup, _ = deduplicar(_exemplo())
    tabela = sobreposicao(sem_dup).set_index("base")
    assert tabela.loc["scopus", "registros"] == 2
    assert tabela.loc["scopus", "exclusivos"] == 1
    assert tabela.loc["ieee", "registros"] == 2
    assert tabela.loc["ieee", "exclusivos"] == 1
    assert tabela.loc["scopus", "em_comum"] == 1


def test_rapido_para_milhares_de_registros():
    palavras = "wind speed power forecasting lstm neural hybrid model deep learning solar grid".split()
    registros = []
    for n in range(4000):
        titulo = " ".join(palavras[(n * k) % len(palavras)] for k in range(1, 8)) + f" study {n}"
        registros.append(_registro(f"R{n}", titulo, ano=2010 + n % 15, autor=f"Autor{n % 50}, A.",
                                   doi=f"10.1/{n % 3500}"))
    tabela = _tabela(*registros)
    inicio = time.perf_counter()
    sem_dup, relatorio = deduplicar(tabela)
    assert time.perf_counter() - inicio < 10
    assert len(sem_dup) + len(relatorio) == 4000
