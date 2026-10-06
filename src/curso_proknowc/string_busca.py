"""Gerador de string de busca a partir dos eixos e palavras-chave (A1)."""

# IEEE Xplore: usa a "Command Search", repetindo cada termo nos campos de título,
# resumo e "Index Terms" (que reúne as palavras-chave do autor e as indexadas).
# Não aplicamos um campo a um grupo inteiro, ex. "Abstract":(a OR b), porque
# não há garantia de que a IEEE aceite essa forma.
_CAMPOS_IEEE = ("Document Title", "Abstract", "Index Terms")

_RAIZ_MINIMA = 4


def _limpar(termo: str) -> str:
    return termo.strip().strip('"').strip()


def preparar_termo(termo: str, curinga: bool = True) -> str:
    """Tira espaços e aspas, remove o * se curinga=False e põe aspas em termos compostos."""
    termo = _limpar(termo)
    if not curinga:
        termo = termo.replace("*", "")
    return f'"{termo}"' if " " in termo else termo


def _eixos_preparados(eixos: dict, curinga: bool) -> list:
    preparados = [[preparar_termo(t, curinga) for t in termos if _limpar(t)] for termos in eixos.values()]
    return [termos for termos in preparados if termos]


def _juntar(eixos: list) -> str:
    return " AND ".join(f"({' OR '.join(termos)})" for termos in eixos)


def string_generica(eixos: dict, curinga: bool = True) -> str:
    """OR entre os termos de um eixo, AND entre os eixos."""
    return _juntar(_eixos_preparados(eixos, curinga))


def string_scopus(eixos: dict, curinga: bool = True) -> str:
    return f"TITLE-ABS-KEY({string_generica(eixos, curinga)})"


def string_wos(eixos: dict, curinga: bool = True) -> str:
    return f"TS=({string_generica(eixos, curinga)})"


def string_ieee(eixos: dict, curinga: bool = True) -> str:
    eixos_ieee = [
        [f'"{campo}":{termo}' for termo in termos for campo in _CAMPOS_IEEE]
        for termos in _eixos_preparados(eixos, curinga)
    ]
    return f"({_juntar(eixos_ieee)})"


def gerar_strings(eixos: dict, curinga: bool = True) -> dict:
    """A mesma busca na sintaxe de cada base."""
    return {
        "generica": string_generica(eixos, curinga),
        "scopus": string_scopus(eixos, curinga),
        "web_of_science": string_wos(eixos, curinga),
        "ieee": string_ieee(eixos, curinga),
    }


def avisos(eixos: dict) -> list:
    """Mensagens sobre eixos vazios e termos amplos demais."""
    mensagens = []
    todos = [_limpar(t).lower() for termos in eixos.values() for t in termos if _limpar(t)]
    compostos = [t for t in todos if " " in t]
    for nome, termos in eixos.items():
        limpos = [_limpar(t) for t in termos if _limpar(t)]
        if not limpos:
            mensagens.append(f'O eixo "{nome}" está vazio e será ignorado na busca.')
        for termo in limpos:
            palavra = termo.lower()
            if " " not in palavra and any(palavra in c.split() for c in compostos):
                mensagens.append(
                    f'O termo "{termo}" (eixo "{nome}") é amplo demais: sozinho, ele traz qualquer texto '
                    f"que tenha essa palavra, e não só o que os termos compostos já buscam. Considere removê-lo."
                )
            elif "*" in palavra and len(palavra.split("*")[0]) < _RAIZ_MINIMA:
                mensagens.append(
                    f'O termo "{termo}" (eixo "{nome}") é amplo demais: o curinga * depois de uma raiz tão curta '
                    f"pega muitas palavras sem relação com o tema. Use uma raiz com pelo menos {_RAIZ_MINIMA} letras."
                )
    return mensagens
