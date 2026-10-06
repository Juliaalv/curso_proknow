"""Perfis de colunas das bases: um arquivo YAML por base, com o nome da subpasta de entrada."""

from pathlib import Path

import yaml

PASTA = Path(__file__).parent


def carregar_perfis() -> dict:
    """Devolve {nome da subpasta: perfil}, por exemplo {"scopus": {...}, "ieee": {...}}."""
    return {
        arquivo.stem: yaml.safe_load(arquivo.read_text(encoding="utf-8"))
        for arquivo in sorted(PASTA.glob("*.yaml"))
    }
