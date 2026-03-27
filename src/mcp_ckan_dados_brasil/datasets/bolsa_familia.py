import json
import logging
import pandas as pd
from pathlib import Path
from mcp_ckan_dados_brasil.datasets.municipios import resolve_municipio, buscar_municipio


log = logging.getLogger(__name__)


def get_csv_data(year=2026, limit=100000):
    """ Helper function to download the CSV data for a given year. Not used in the main code since we load from local CSV,
        but can be used to refresh the data.
        The URL top get the data allows filtering by year
        https://aplicacoes.mds.gov.br/sagi/servicos/misocial/?
            fq=anomes_s:2026*&
            fl=codigo_ibge%2Canomes_s%2Cqtd_familias_beneficiarias_bolsa_familia_s%2Cvalor_repassado_bolsa_familia_s%2Cpbf_vlr_medio_benef_f&
            fq=valor_repassado_bolsa_familia_s%3A*&
            q=*%3A*&
            rows=100000&
            sort=anomes_s%20desc%2C%20codigo_ibge%20asc&
            wt=csv
        We save the file once donwloaded to avoid hitting the remote URL.
    """
    file_path = Path(__file__).parent / "aplicacoes-bolsa-familia" / f"bolsa_familia_{year}.csv"
    if file_path.exists():
        log.info(f"Loading Bolsa Família data for {year} from local CSV.")
        return pd.read_csv(file_path)
    # From 2023-03 the data columns are only in the format we expect so we only allow fetching from 2024
    # onwards to avoid issues with older formats.
    fl = (
        "codigo_ibge%2C"
        "anomes_s%2C"
        "qtd_familias_beneficiarias_bolsa_familia_s%2C"
        "valor_repassado_bolsa_familia_s%2C"
        "pbf_vlr_medio_benef_f"
    )
    url = (
        "https://aplicacoes.mds.gov.br/sagi/servicos/misocial/?"
        f"fq=anomes_s:{year}*&"
        f"fl={fl}&"
        "fq=valor_repassado_bolsa_familia_s%3A*&"
        "q=*%3A*&"
        f"rows={limit}&"
        "sort=anomes_s%20desc%2C%20codigo_ibge%20asc&"
        "wt=csv"
    )
    log.info(f"Downloading Bolsa Família data for {year} from URL: {url}")
    df = pd.read_csv(url)
    df.to_csv(file_path, index=False)
    return df


def get_bolsa_familia_rows(
        municipio: str = None, codigo_ibge: int = None,
        year: int = 2026,
        limit: int = 20,
        state: str = None,
        order_by: str = None
) -> str:
    """ Return a simple list of Bolsa Familia rows from the local CSV.
        A Municipality is required.

    Args:
        municipio: Municipality name to filter by, e.g. "Cacoal" or "Porto Velho/RO".
        codigo_ibge: IBGE municipality code to filter by. If None, returns all.
        year: Year to filter the data. Defaults to 2026.
        limit: Max rows to return. Defaults to 20.
        state: State abbreviation to filter by, e.g. "RO". If None, returns all.
        order_by: Column name to order the results by. This must be pandas sort valid.
                  If None, defaults to the CSV order.

    Returns:
        Formatted string with the rows.
    """
    if municipio is None:
        return (
            "Por favor, forneça o nome do município para listar os registros do Bolsa Família. "
        )

    resolved, _ = resolve_municipio(municipio)
    if not resolved:
        found, msg = buscar_municipio(municipio)
        if not found:
            return msg
        return f"Município '{municipio}' não encontrado. Sugestões:\n{msg}"

    codigo_ibge = resolved

    df = get_csv_data(year=year, limit=100000)
    if codigo_ibge is not None:
        df = df[df["codigo_ibge"] == codigo_ibge]
    if state is not None:
        df = df[df["estado"] == state]
    if order_by is not None:
        order_parts = order_by.split()
        if len(order_parts) == 2 and order_parts[1].lower() in ["asc", "desc"]:
            order_col = order_parts[0]
            ascending = order_parts[1].lower() == "asc"
        else:
            order_col = order_by
            ascending = True
        df = df.sort_values(by=order_col, ascending=ascending)
    total = len(df)
    df = df.head(limit)

    table_rows = [
        ["IBGE", "Mês", "Famílias", "Valor", "Média"]
    ]
    lines = []
    for _, row in df.iterrows():
        lines.append(
            f"  - IBGE: {int(row['codigo_ibge'])} | "
            f"Mês: {int(row['anomes_s'])} | "
            f"Famílias: {int(row['qtd_familias_beneficiarias_bolsa_familia_s'])} | "
            f"Valor: R$ {row['valor_repassado_bolsa_familia_s']:,.2f} | "
            f"Média: R$ {row['pbf_vlr_medio_benef_f']:,.2f}"
        )
        table_rows.append([
            row['codigo_ibge'],
            row['anomes_s'],
            row['qtd_familias_beneficiarias_bolsa_familia_s'],
            f"R$ {row['valor_repassado_bolsa_familia_s']:,.2f}",
            f"R$ {row['pbf_vlr_medio_benef_f']:,.2f}"
        ])

    table_rows_str = json.dumps(table_rows, ensure_ascii=False)
    table = f"<table>{table_rows_str}</table>"
    label = f" em {municipio}" if municipio else ""
    if state is not None:
        label += f" - {state}"
    header = f"Bolsa Família{label} - {len(lines)} registros (de {total} total):"
    return header + "\n" + "\n".join(lines) + table
