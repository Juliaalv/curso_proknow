"""Encadeamento das etapas sobre os CSVs de teste: A2 → A4 → A5 → A6 → A7 → A9 → A10."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from curso_proknowc import bibliometria, esquema, rastreabilidade, triagem
from curso_proknowc.deduplicacao import deduplicar
from curso_proknowc.delimitacoes import remover_incompletos
from curso_proknowc.leitura import ler_pasta
from curso_proknowc.reconhecimento import dividir_por_corte
from curso_proknowc.repescagem import repescar

ENTRADA = Path(__file__).parent / "dados" / "entrada"


def test_fluxo_encadeado(tmp_path):
    bruta, _ = ler_pasta(ENTRADA)
    completos, incompletos = remover_incompletos(bruta)
    portfolio, fundidos = deduplicar(completos)

    lstm = portfolio[portfolio["doi"] == "10.1016/j.renene.2022.01.001"]
    assert len(lstm) == 1
    assert sorted(lstm.iloc[0]["bases_origem"]) == ["ieee", "scopus"]
    assert lstm.iloc[0]["citacoes_por_base"] == {"scopus": 45, "ieee": 50}

    decisoes = tmp_path / "decisoes.csv"
    for id_artigo in portfolio["id"]:
        triagem.registrar(decisoes, id_artigo, "titulo", "aceito")
    triagem.registrar(decisoes, portfolio["id"].iloc[-1], "titulo", "rejeitado", "fora do tema")
    alinhados, nao_alinhados = triagem.aplicar(portfolio, "titulo", decisoes)
    assert list(nao_alinhados["motivo_pesquisador"]) == ["fora do tema"]

    acima, abaixo = dividir_por_corte(alinhados, 80)
    assert len(acima) + len(abaixo) == len(alinhados)
    enviados, descartados = repescar(abaixo, acima, ano_pesquisa=2026)
    assert len(enviados) + len(descartados) == len(abaixo)

    duplicados = completos[completos["id"].isin(fundidos["id_removido"])].assign(motivo_exclusao="duplicado")
    etapas = [
        rastreabilidade.etapa_de_excluidos("Registros incompletos", len(bruta), incompletos),
        rastreabilidade.etapa_de_excluidos("Duplicados", len(completos), duplicados),
        rastreabilidade.etapa_de_excluidos("Alinhamento pelo título", len(portfolio), nao_alinhados),
    ]
    rastreabilidade.fluxograma(etapas, rastreabilidade.registros_por_base(bruta)).savefig(tmp_path / "fluxo.png")
    rastreabilidade.exportar_ris(portfolio, tmp_path / "portfolio.ris")
    assert len(bibliometria.frequencias(portfolio, "periodico")) == len(portfolio)

    esquema.salvar(portfolio, tmp_path / "portfolio.parquet")
    assert len(esquema.carregar(tmp_path / "portfolio.parquet")) == len(portfolio)
