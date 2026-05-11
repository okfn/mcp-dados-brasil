import sqlite3

from mcp.types import CallToolResult, TextContent
from mcp_server import DataToolOutput
from mcp_server.results import text_result


from mcp_ckan_dados_brasil.emendas.load_db import get_db_path

SOURCE_URL = (
    "https://portaldatransparencia.gov.br/download-de-dados/emendas-parlamentares/UNICO"
)


def emendas_por_municipio(municipio: str) -> DataToolOutput:
    """Get the valor_empenhado, valor_liquidado and valor_pago of emendas for the given
    municipio, grouped by year, from the emendas table.

    Args:
        municipio: Municipality name to filter by, e.g. "Pilar" or "São Paulo".

    Returns:
        A summary of parliamentary amendments (emendas parlamentares) for the given
        municipality, grouped by year. Shows valor_empenhado, valor_liquidado and
        valor_pago totals per year.
        If the municipality name matches multiple states, returns results for all of them.
        If no results are found, returns a force message.
    """
    municipio_upper = municipio.strip().upper()

    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row

    # Check how many UF matches we have
    uf_rows = conn.execute(
        "SELECT DISTINCT uf FROM emendas WHERE municipio = ? ORDER BY uf",
        (municipio_upper,),
    ).fetchall()

    if not uf_rows:
        conn.close()
        msg = f"Nenhuma emenda encontrada para o município '{municipio}'."
        return text_result(msg, source_url=SOURCE_URL)

    # Fetch yearly aggregates across all matching UFs
    rows = conn.execute(
        """
        SELECT ano_da_emenda,
               municipio,
               uf,
               COUNT(*) as num_emendas,
               SUM(valor_empenhado) as total_empenhado,
               SUM(valor_liquidado) as total_liquidado,
               SUM(valor_pago) as total_pago
        FROM emendas
        WHERE municipio = ?
        GROUP BY uf, ano_da_emenda
        ORDER BY uf, ano_da_emenda
        """,
        (municipio_upper,),
    ).fetchall()
    conn.close()

    lines = [f"Emendas parlamentares para {municipio_upper}:", ""]
    table_rows = [
        [
            "Ano",
            "Municipio",
            "UF",
            "Nº Emendas",
            "Empenhado (R$)",
            "Liquidado (R$)",
            "Pago (R$)",
        ]
    ]
    chart_labels = []
    chart_empenhado = []
    chart_liquidado = []
    chart_pago = []

    for row in rows:
        ano = row["ano_da_emenda"]
        mun = row["municipio"]
        uf = row["uf"]
        n = row["num_emendas"]
        emp = row["total_empenhado"] or 0.0
        liq = row["total_liquidado"] or 0.0
        pago = row["total_pago"] or 0.0
        lines.append(
            f"  {ano} | {n} emendas | {municipio} | {uf} | "
            f"Empenhado: R$ {emp:,.2f} | "
            f"Liquidado: R$ {liq:,.2f} | "
            f"Pago: R$ {pago:,.2f}"
        )
        table_rows.append(
            [
                ano,
                n,
                mun,
                uf,
                f"R$ {emp:,.2f}",
                f"R$ {liq:,.2f}",
                f"R$ {pago:,.2f}",
            ]
        )
        chart_labels.append(str(ano))
        chart_empenhado.append(round(emp, 2))
        chart_liquidado.append(round(liq, 2))
        chart_pago.append(round(pago, 2))

    text = "\n".join(lines)

    return text_result(text, source_url=SOURCE_URL, table=table_rows)


if __name__ == "__main__":
    print(emendas_por_municipio("PILAR"))
