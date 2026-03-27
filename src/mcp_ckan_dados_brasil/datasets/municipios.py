import json
import logging
import difflib
import unicodedata
from pathlib import Path


log = logging.getLogger(__name__)
MUNICIPIOS_PATH = Path(__file__).parent / "municipios" / "municipios.json"
MUNICIPIOS = None


def normalize(text):
    """Lowercase and strip accents for matching."""
    text = text.lower().strip()
    nfkd = unicodedata.normalize("NFKD", text)
    ret = "".join(c for c in nfkd if not unicodedata.combining(c))
    return ret


def load_municipios():
    """ Load municipios JSON and build lookup dicts.
        Note: UF means state (e.g. RO, SP) and is included in the display string but not required for matching.
        We ensure load this data structure only once with MUNICIPIOS global variable, since it's used for every query.

    Returns two dicts:
        name_to_code: normalized_name -> 6-digit IBGE code
        name_to_display: normalized_name -> display string "Nome/UF (codigo)"
    """
    global MUNICIPIOS
    if MUNICIPIOS is not None:
        log.info("Municipios already loaded, using cached data.")
        return MUNICIPIOS
    log.info(f"Loading municipios from {MUNICIPIOS_PATH}")
    with open(MUNICIPIOS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    name_to_code = {}
    name_to_display = {}
    for m in data:
        codigo_6 = m["id"] // 10
        nome = m["nome"]
        try:
            uf = m["microrregiao"]["mesorregiao"]["UF"]["sigla"]
        except (TypeError, KeyError):
            uf = None

        if uf:
            key_with_uf = normalize(f"{nome}/{uf}")
            name_to_code[key_with_uf] = codigo_6
            name_to_display[key_with_uf] = f"{nome}/{uf} ({codigo_6})"

        key_plain = normalize(nome)
        name_to_code[key_plain] = codigo_6
        display = f"{nome}/{uf} ({codigo_6})" if uf else f"{nome} ({codigo_6})"
        name_to_display[key_plain] = display

    MUNICIPIOS = {
        "name_to_code": name_to_code,
        "name_to_display": name_to_display
    }
    return MUNICIPIOS


def resolve_municipio(municipio):
    """Resolve a municipality name (with optional /UF) to a 6-digit IBGE code."""
    key = normalize(municipio)
    munis = load_municipios()
    codigo = munis["name_to_code"].get(key)
    if codigo is None:
        return None, f"Município '{municipio}' não encontrado. Use buscar_municipio('{municipio}') para nomes similares."
    return codigo, None


def buscar_municipio(nome: str, limit: int = 10) -> str:
    """ Search for municipalities by approximate name using fuzzy matching.
        We can get the IBGE (Instituto Brasileiro de Geografia e Estatística) code for a municipality.
        Also, we can get the UF (state) if available, which is helpful for disambiguation.
        The display format is "Nome/UF (codigo)".
        The search supports both plain names and "Name/UF" formats.

    Args:
        nome: Name (or partial/misspelled name) to search for.
        limit: Max suggestions to return. Defaults to 10.

    Returns:
        Boolean indicating if a match was found, and either the IBGE code or an error message with suggestions.
        Formatted list of matching municipality names with IBGE codes.
    """
    key = normalize(nome)
    munis = load_municipios()
    all_keys = list(munis["name_to_display"].keys())
    matches = difflib.get_close_matches(key, all_keys, n=limit, cutoff=0.5)

    if not matches:
        force = (
            "<force>"
            f"No municipality found similar to '{nome}'."
            "</force>"
        )
        return False, f"{force} Nenhum município encontrado similar a '{nome}'."

    # deduplicate by display string (plain name and name/UF keys can both match)
    seen = set()
    lines = []
    # Also, expose this similarities in a <table> like bolsa familia
    table_rows = [["Nome/UF", "Código"]]
    munis = load_municipios()
    for m in matches:
        display = munis["name_to_display"][m]
        if display not in seen:
            seen.add(display)
            lines.append(display)
            table_rows.append([display, munis["name_to_code"][m]])

    table_rows_str = json.dumps(table_rows, ensure_ascii=False)
    table = f"<table>{table_rows_str}</table>"
    header = f"Municípios similares a '{nome}':"
    return True, header + "\n" + "\n".join(f"  - {line}" for line in lines) + table
