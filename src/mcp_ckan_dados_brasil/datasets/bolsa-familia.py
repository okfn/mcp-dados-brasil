import json
import difflib
import unicodedata
import pandas as pd
from pathlib import Path

CSV_PATH = Path(__file__).parent / "aplicacoes-bolsa-familia" / "2026-aplicacoes.mds.gov.br.csv"
MUNICIPIOS_PATH = Path(__file__).parent / "aplicacoes-bolsa-familia" / "municipios" / "municipios.json"


def _normalize(text):
    """Lowercase and strip accents for matching."""
    text = text.lower().strip()
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _load_municipios():
    """ Load municipios JSON and build lookup dicts.
        Note: UF means state (e.g. RO, SP) and is included in the display string but not required for matching.

    Returns two dicts:
        name_to_code: normalized_name -> 6-digit IBGE code
        name_to_display: normalized_name -> display string "Nome/UF (codigo)"
    """
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
            key_with_uf = _normalize(f"{nome}/{uf}")
            name_to_code[key_with_uf] = codigo_6
            name_to_display[key_with_uf] = f"{nome}/{uf} ({codigo_6})"

        key_plain = _normalize(nome)
        name_to_code[key_plain] = codigo_6
        display = f"{nome}/{uf} ({codigo_6})" if uf else f"{nome} ({codigo_6})"
        name_to_display[key_plain] = display

    return name_to_code, name_to_display


_NAME_TO_CODE, _NAME_TO_DISPLAY = _load_municipios()


def _resolve_municipio(municipio):
    """Resolve a municipality name (with optional /UF) to a 6-digit IBGE code."""
    key = _normalize(municipio)
    codigo = _NAME_TO_CODE.get(key)
    if codigo is None:
        return None, f"Município '{municipio}' não encontrado. Use buscar_municipio('{municipio}') para encontrar nomes similares."
    return codigo, None


def buscar_municipio(nome: str, limit: int = 10) -> str:
    """ Search for municipalities by approximate name using fuzzy matching.
        We can get the IBGE (Instituto Brasileiro de Geografia e Estatística) code for a municipality.
        Also, we can get the UF (state) if available, which is helpful for disambiguation. The display format is "Nome/UF (codigo)".
        The search supports both plain names and "Name/UF" formats.

    Args:
        nome: Name (or partial/misspelled name) to search for.
        limit: Max suggestions to return. Defaults to 10.

    Returns:
        Boolean indicating if a match was found, and either the IBGE code or an error message with suggestions.
        Formatted list of matching municipality names with IBGE codes.
    """
    key = _normalize(nome)
    all_keys = list(_NAME_TO_DISPLAY.keys())
    matches = difflib.get_close_matches(key, all_keys, n=limit, cutoff=0.5)

    if not matches:
        return False, f"Nenhum município encontrado similar a '{nome}'."

    # deduplicate by display string (plain name and name/UF keys can both match)
    seen = set()
    lines = []
    for m in matches:
        display = _NAME_TO_DISPLAY[m]
        if display not in seen:
            seen.add(display)
            lines.append(display)
    header = f"Municípios similares a '{nome}':"
    return True, header + "\n" + "\n".join(f"  - {line}" for line in lines)


def get_bolsa_familia_rows(municipio: str = None, codigo_ibge: int = None, limit: int = 20) -> str:
    """ Return a simple list of Bolsa Familia rows from the local CSV.
        A Municipality is required.

    Args:
        municipio: Municipality name to filter by, e.g. "Cacoal" or "Porto Velho/RO".
        codigo_ibge: IBGE municipality code to filter by. If None, returns all.
        limit: Max rows to return. Defaults to 20.

    Returns:
        Formatted string with the rows.
    """
    if municipio is None:
        return (
            "Por favor, forneça o nome do município para listar os registros do Bolsa Família. "
        )

    resolved, error = _resolve_municipio(municipio)
    if not resolved:
        found, muni = buscar_municipio(municipio)
        if not found:
            return f"Município '{municipio}' não encontrado. Also, no similar municipalities found. {error}"
        return f"Município '{municipio}' não encontrado. Sugestões:\n{muni}"

    codigo_ibge = resolved

    df = pd.read_csv(CSV_PATH)
    if codigo_ibge is not None:
        df = df[df["codigo_ibge"] == codigo_ibge]
    total = len(df)
    df = df.head(limit)

    lines = []
    for _, row in df.iterrows():
        lines.append(
            f"  - IBGE: {int(row['codigo_ibge'])} | "
            f"Mês: {int(row['anomes_s'])} | "
            f"Famílias: {int(row['qtd_familias_beneficiarias_bolsa_familia_s'])} | "
            f"Valor: R$ {row['valor_repassado_bolsa_familia_s']:,.2f} | "
            f"Média: R$ {row['pbf_vlr_medio_benef_f']:,.2f}"
        )

    label = f" em {municipio}" if municipio else ""
    header = f"Bolsa Família{label} - {len(lines)} registros (de {total} total):"
    return header + "\n" + "\n".join(lines)
