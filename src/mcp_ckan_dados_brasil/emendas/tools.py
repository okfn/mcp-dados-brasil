import sqlite3

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
            "UF",
            "Nº Emendas",
            "Empenhado (R$)",
            "Liquidado (R$)",
            "Pago (R$)",
        ]
    ]

    # Group rows by UF for per-UF charts
    uf_data = {}
    for row in rows:
        uf = row["uf"]
        uf_data.setdefault(uf, []).append(row)

    for row in rows:
        ano = row["ano_da_emenda"]
        uf = row["uf"]
        n = row["num_emendas"]
        emp = row["total_empenhado"] or 0.0
        liq = row["total_liquidado"] or 0.0
        pago = row["total_pago"] or 0.0
        lines.append(
            f"  {ano} | {uf} | {n} emendas | "
            f"Empenhado: R$ {emp:,.2f} | "
            f"Liquidado: R$ {liq:,.2f} | "
            f"Pago: R$ {pago:,.2f}"
        )
        table_rows.append(
            [
                ano,
                uf,
                n,
                f"R$ {emp:,.2f}",
                f"R$ {liq:,.2f}",
                f"R$ {pago:,.2f}",
            ]
        )

    # One chart per UF
    charts = []
    for uf, uf_rows in uf_data.items():
        chart_labels = []
        chart_empenhado = []
        chart_liquidado = []
        chart_pago = []
        for row in uf_rows:
            emp = row["total_empenhado"] or 0.0
            liq = row["total_liquidado"] or 0.0
            pago = row["total_pago"] or 0.0
            chart_labels.append(str(row["ano_da_emenda"]))
            chart_empenhado.append(round(emp, 2))
            chart_liquidado.append(round(liq, 2))
            chart_pago.append(round(pago, 2))
        charts.append(
            {
                "type": "bar",
                "title": f"Emendas Parlamentares - {municipio_upper} ({uf})",
                "labels": chart_labels,
                "datasets": [
                    {"label": "Empenhado (R$)", "data": chart_empenhado},
                    {"label": "Liquidado (R$)", "data": chart_liquidado},
                    {"label": "Pago (R$)", "data": chart_pago},
                ],
                "beginAtZero": True,
            }
        )

    text = "\n".join(lines)

    return text_result(text, source_url=SOURCE_URL, table=table_rows, charts=charts)


def quem_envia_emendas(municipio: str) -> DataToolOutput:
    """Returns a list of emenda authors (nome_do_autor_da_emenda) with the total
    valor_empenhado, valor_liquidado and valor_pago for the given municipio,
    sorted by total empenhado descending.

    Args:
        municipio: Municipality name to filter by, e.g. "Pilar" or "São Paulo".

    Returns:
        A ranking of parliamentary amendment authors for the given municipality,
        showing how many emendas each authored and the total empenhado/liquidado/pago.
        Includes a table and a horizontal bar chart.
        If no results are found, returns a force message.
    """
    municipio_upper = municipio.strip().upper()

    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row

    # Check that the municipio exists
    uf_rows = conn.execute(
        "SELECT DISTINCT uf FROM emendas WHERE municipio = ? ORDER BY uf",
        (municipio_upper,),
    ).fetchall()

    if not uf_rows:
        conn.close()
        msg = f"Nenhuma emenda encontrada para o município '{municipio}'."
        return text_result(msg, source_url=SOURCE_URL, force=msg)

    rows = conn.execute(
        """
        SELECT nome_do_autor_da_emenda,
               COUNT(*) as num_emendas,
               SUM(valor_empenhado) as total_empenhado,
               SUM(valor_liquidado) as total_liquidado,
               SUM(valor_pago) as total_pago
        FROM emendas
        WHERE municipio = ?
        GROUP BY nome_do_autor_da_emenda
        ORDER BY total_empenhado DESC
        """,
        (municipio_upper,),
    ).fetchall()
    conn.close()

    ufs = ", ".join(r["uf"] for r in uf_rows)

    lines = [f"Autores de emendas para {municipio_upper} ({ufs}):", ""]
    table_rows = [
        [
            "Autor",
            "Nº Emendas",
            "Empenhado (R$)",
            "Liquidado (R$)",
            "Pago (R$)",
        ]
    ]
    chart_labels = []
    chart_empenhado = []
    chart_pago = []

    for row in rows:
        autor = row["nome_do_autor_da_emenda"]
        n = row["num_emendas"]
        emp = row["total_empenhado"] or 0.0
        liq = row["total_liquidado"] or 0.0
        pago = row["total_pago"] or 0.0
        lines.append(
            f"  {autor} | {n} emendas | "
            f"Empenhado: R$ {emp:,.2f} | "
            f"Liquidado: R$ {liq:,.2f} | "
            f"Pago: R$ {pago:,.2f}"
        )
        table_rows.append(
            [
                autor,
                n,
                f"R$ {emp:,.2f}",
                f"R$ {liq:,.2f}",
                f"R$ {pago:,.2f}",
            ]
        )
        chart_labels.append(autor)
        chart_empenhado.append(round(emp, 2))
        chart_pago.append(round(pago, 2))

    text = "\n".join(lines)

    chart = {
        "type": "bar",
        "indexAxis": "y",
        "title": f"Autores de Emendas - {municipio_upper}",
        "labels": chart_labels,
        "datasets": [
            {"label": "Empenhado (R$)", "data": chart_empenhado},
            {"label": "Pago (R$)", "data": chart_pago},
        ],
        "beginAtZero": True,
    }

    return text_result(text, source_url=SOURCE_URL, table=table_rows, charts=[chart])


def top_favorecidos_das_emendas(limit: int = 10) -> DataToolOutput:
    """Returns which recipients (favorecidos) received the most money from
    parliamentary amendments, ranked by total valor_recebido.

    Args:
        limit: Maximum number of recipients to return (default 10).

    Returns:
        A ranking of top recipients of parliamentary amendment funds,
        showing the total valor_recebido and number of emendas per favorecido.
        Includes a table and a horizontal bar chart.
    """
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT favorecido,
               natureza_juridica,
               tipo_favorecido,
               COUNT(*) as num_emendas,
               SUM(valor_recebido) as total_recebido
        FROM emendas_por_favorecido
        GROUP BY favorecido
        ORDER BY total_recebido DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()

    if not rows:
        msg = "Nenhum favorecido encontrado na base de dados."
        return text_result(msg, source_url=SOURCE_URL, force=msg)

    lines = [f"Top {len(rows)} favorecidos por valor recebido em emendas:", ""]
    table_rows = [
        [
            "#",
            "Favorecido",
            "Natureza Jurídica",
            "Tipo",
            "Nº Emendas",
            "Total Recebido (R$)",
        ]
    ]
    chart_labels = []
    chart_recebido = []

    for i, row in enumerate(rows, start=1):
        favorecido = row["favorecido"]
        natureza = row["natureza_juridica"] or ""
        tipo = row["tipo_favorecido"] or ""
        n = row["num_emendas"]
        total = row["total_recebido"] or 0.0
        lines.append(
            f"  {i}. {favorecido} | {natureza} | {tipo} | "
            f"{n} emendas | Recebido: R$ {total:,.2f}"
        )
        table_rows.append(
            [
                i,
                favorecido,
                natureza,
                tipo,
                n,
                f"R$ {total:,.2f}",
            ]
        )
        chart_labels.append(favorecido)
        chart_recebido.append(round(total, 2))

    text = "\n".join(lines)

    chart = {
        "type": "bar",
        "indexAxis": "y",
        "title": f"Top {len(rows)} Favorecidos por Valor Recebido",
        "labels": chart_labels,
        "datasets": [
            {"label": "Total Recebido (R$)", "data": chart_recebido},
        ],
        "beginAtZero": True,
    }

    return text_result(text, source_url=SOURCE_URL, table=table_rows, charts=[chart])

if __name__ == "__main__":
    print(emendas_por_municipio("PILAR"))
