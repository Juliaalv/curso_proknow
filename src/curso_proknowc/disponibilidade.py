"""Disponibilidade do texto integral pelo Unpaywall (A8).

Preenche `acesso_aberto` e `url_pdf` e acrescenta duas colunas:
- `buscar_capes`: True quando o texto não foi encontrado em acesso aberto (fechado, sem DOI,
  DOI desconhecido ou falha na consulta) e deve ser procurado no Portal de Periódicos CAPES.
- `obs_disponibilidade`: o motivo, em texto, para o participante conferir.

`acesso_aberto` fica vazio (None) quando não foi possível saber.
"""

import pandas as pd
import requests

URL_UNPAYWALL = "https://api.unpaywall.org/v2/{doi}"


def _consultar_unpaywall(doi: str, email: str) -> dict:
    """Única chamada à rede; os testes a substituem."""
    resposta = requests.get(URL_UNPAYWALL.format(doi=doi), params={"email": email}, timeout=30)
    resposta.raise_for_status()
    return resposta.json()


def _melhor_url(registro: dict):
    """PDF da melhor localização; senão, PDF de outra localização; senão, URL da melhor."""
    melhor = registro.get("best_oa_location") or {}
    if melhor.get("url_for_pdf"):
        return melhor["url_for_pdf"]
    for local in registro.get("oa_locations") or []:
        if local.get("url_for_pdf"):
            return local["url_for_pdf"]
    return melhor.get("url")


def _resultado(acesso_aberto, url_pdf, obs):
    return {
        "acesso_aberto": acesso_aberto,
        "url_pdf": url_pdf,
        "buscar_capes": not acesso_aberto,
        "obs_disponibilidade": obs,
    }


def consultar_doi(doi, email: str) -> dict:
    """Consulta um DOI e devolve as colunas de disponibilidade; nunca levanta erro de rede."""
    if doi is None or pd.isna(doi) or not str(doi).strip():
        return _resultado(None, None, "sem DOI: buscar no Portal de Periódicos CAPES")
    try:
        registro = _consultar_unpaywall(str(doi).strip(), email)
    except requests.HTTPError as erro:
        if getattr(erro.response, "status_code", None) == 404:
            return _resultado(None, None, "DOI não encontrado no Unpaywall: buscar no Portal de Periódicos CAPES")
        return _resultado(None, None, f"falha na consulta ao Unpaywall ({erro}): buscar no Portal de Periódicos CAPES")
    except (requests.RequestException, ValueError) as erro:
        return _resultado(None, None, f"falha na consulta ao Unpaywall ({erro}): buscar no Portal de Periódicos CAPES")
    if not registro.get("is_oa"):
        return _resultado(False, None, "fechado: buscar no Portal de Periódicos CAPES")
    return _resultado(True, _melhor_url(registro), "acesso aberto")


def verificar_disponibilidade(tabela: pd.DataFrame, email: str) -> pd.DataFrame:
    """Consulta cada DOI da tabela; o e-mail do participante é exigido pelo Unpaywall."""
    if not email or "@" not in str(email):
        raise ValueError("Informe seu e-mail: o Unpaywall exige um e-mail válido em cada consulta.")
    email = str(email).strip()
    resultados = pd.DataFrame([consultar_doi(doi, email) for doi in tabela["doi"]], index=tabela.index)
    tabela = tabela.copy()
    for coluna in resultados.columns:
        tabela[coluna] = resultados[coluna].astype(object)
    return tabela
