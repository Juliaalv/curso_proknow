"""Tratamento campo a campo e tradução de um arquivo da base para o esquema comum (A2, etapas 2 e 3)."""

import html
import re
import unicodedata

import pandas as pd

from curso_proknowc import esquema

_DOI = re.compile(r"10\.\d{4,9}/\S+")
_TAG_HTML = re.compile(r"<[^>]+>")
_ESPACOS = re.compile(r"\s+")

_MARCADORES_SEM_RESUMO = {"[no abstract available]", "no abstract available"}

_IDIOMAS = {
    "english": "en",
    "portuguese": "pt",
    "spanish": "es",
    "chinese": "zh",
    "french": "fr",
    "german": "de",
    "russian": "ru",
    "japanese": "ja",
    "korean": "ko",
    "italian": "it",
    "turkish": "tr",
    "persian": "fa",
    "arabic": "ar",
}


def _texto(valor) -> str:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    return str(valor).strip()


def _sem_html(texto: str) -> str:
    texto = html.unescape(_TAG_HTML.sub("", texto))
    return _ESPACOS.sub(" ", texto).strip()


def normalizar_doi(valor):
    achado = _DOI.search(_texto(valor).lower())
    return achado.group(0).rstrip(".") if achado else None


def limpar_titulo(valor):
    titulo = _sem_html(_texto(valor)).rstrip(".").strip()
    return titulo or None


def normalizar_titulo(valor):
    sem_acento = unicodedata.normalize("NFKD", _texto(valor))
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return _ESPACOS.sub(" ", re.sub(r"[^a-z0-9]+", " ", sem_acento.lower())).strip() or None


def _separar(texto: str, separador: str = ";") -> list:
    return [parte.strip() for parte in texto.split(separador) if parte.strip()]


def autores_scopus(valor) -> list:
    """"Silva J.; da Costa M.A." (ou o formato antigo "Silva J., Costa M.") -> ["Silva, J.", "da Costa, M.A."]."""
    texto = _texto(valor)
    nomes = _separar(texto, ";") if ";" in texto else _separar(texto, ",")
    autores = []
    for nome in nomes:
        if "," in nome:
            autores.append(nome)
            continue
        partes = nome.split()
        autores.append(f"{' '.join(partes[:-1])}, {partes[-1]}" if len(partes) > 1 else nome)
    return autores


def _iniciais(prenome: str) -> str:
    return "-".join(f"{parte[0].upper()}." for parte in prenome.split("-") if parte)


def autores_ieee(valor) -> list:
    """"Maria A. Santos; Jean-Pierre Dupont" -> ["Santos, M.A.", "Dupont, J.-P."]."""
    autores = []
    for nome in _separar(_texto(valor), ";"):
        partes = nome.split()
        if len(partes) == 1:
            autores.append(nome)
        else:
            autores.append(f"{partes[-1]}, {''.join(_iniciais(p) for p in partes[:-1])}")
    return autores


def inteiro(valor):
    try:
        return int(float(_texto(valor)))
    except ValueError:
        return None


def lista_palavras(valor) -> list:
    palavras = []
    for palavra in _separar(_texto(valor).lower(), ";"):
        if palavra not in palavras:
            palavras.append(palavra)
    return palavras


def limpar_resumo(valor):
    resumo = _sem_html(_texto(valor))
    if not resumo or resumo.lower() in _MARCADORES_SEM_RESUMO:
        return None
    return resumo


def tipo_documento(valor):
    tipo = _texto(valor).lower()
    if not tipo:
        return None
    if "conference review" in tipo:
        return "outro"
    if "review" in tipo:
        return "revisão"
    if "conference" in tipo:
        return "conferência"
    if "chapter" in tipo or "book" in tipo:
        return "capítulo"
    if any(chave in tipo for chave in ("article", "journal", "magazine", "early access")):
        return "artigo"
    return "outro"


def idioma(valor):
    primeiro = _separar(_texto(valor), ";")
    if not primeiro:
        return None
    nome = primeiro[0].lower()
    return _IDIOMAS.get(nome, nome)


_AUTORES = {"scopus": autores_scopus, "ieee": autores_ieee}


def padronizar(bruto: pd.DataFrame, perfil: dict, base: str, arquivo: str) -> pd.DataFrame:
    """Traduz as linhas de um arquivo da base para o esquema comum, já com os campos tratados."""
    colunas = perfil["colunas"]
    ler_autores = _AUTORES[perfil["formato_autores"]]

    def campo(linha, nome):
        coluna = colunas.get(nome)
        return linha.get(coluna, "") if coluna else ""

    registros = []
    for _, linha in bruto.iterrows():
        citacoes = inteiro(campo(linha, "citacoes"))
        if citacoes is None and perfil.get("citacao_vazia_e_zero") and not _texto(campo(linha, "citacoes")):
            citacoes = 0
        chave_autor = lista_palavras(campo(linha, "palavras_chave_autor"))
        chave_indexada = lista_palavras(campo(linha, "palavras_chave_indexadas"))
        titulo = limpar_titulo(campo(linha, "titulo"))
        registros.append(
            {
                "doi": normalizar_doi(campo(linha, "doi")),
                "titulo": titulo,
                "titulo_norm": normalizar_titulo(titulo),
                "resumo": limpar_resumo(campo(linha, "resumo")),
                "autores": ler_autores(campo(linha, "autores")),
                "autores_ids": _separar(_texto(campo(linha, "autores_ids")), ";"),
                "ano": inteiro(campo(linha, "ano")),
                "periodico": _texto(campo(linha, "periodico")) or None,
                "issn": _texto(campo(linha, "issn")) or None,
                "tipo_documento": tipo_documento(campo(linha, "tipo_documento")),
                "idioma": idioma(campo(linha, "idioma")),
                "palavras_chave_autor": chave_autor,
                "palavras_chave_indexadas": chave_indexada,
                "palavras_chave": chave_autor + [p for p in chave_indexada if p not in chave_autor],
                "citacoes": citacoes,
                "citacoes_fonte": base if citacoes is not None else None,
                "citacoes_por_base": {base: citacoes} if citacoes is not None else None,
                "referencias_texto": _texto(campo(linha, "referencias_texto")) or None,
                "base_origem": base,
                "bases_origem": [base],
                "arquivos_origem": [arquivo],
                "etapa_atual": "padronizado",
            }
        )
    return esquema.completar(pd.DataFrame(registros, columns=list(registros[0]) if registros else None))
