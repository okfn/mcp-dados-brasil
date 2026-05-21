import sqlite3

from contextlib import contextmanager

from mcp_server import DataToolOutput
from mcp_server.results import text_result


from mcp_ckan_dados_brasil.emendas.load_db import get_db_path

SOURCE_URL = (
    "https://portaldatransparencia.gov.br/download-de-dados/emendas-parlamentares/UNICO"
)


@contextmanager
def _db_connect():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


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

    with _db_connect() as conn:
        uf_rows = conn.execute(
            "SELECT DISTINCT uf FROM emendas WHERE municipio = ? ORDER BY uf",
            (municipio_upper,),
        ).fetchall()

    if not uf_rows:
        msg = f"Nenhuma emenda encontrada para o município '{municipio}'."
        return text_result(msg, source_url=SOURCE_URL)

    # Fetch yearly aggregates across all matching UFs
    with _db_connect() as conn:
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

    # Check that the municipio exists
    with _db_connect() as conn:
        uf_rows = conn.execute(
            "SELECT DISTINCT uf FROM emendas WHERE municipio = ? ORDER BY uf",
            (municipio_upper,),
        ).fetchall()

    if not uf_rows:
        msg = f"Nenhuma emenda encontrada para o município '{municipio}'."
        return text_result(msg, source_url=SOURCE_URL, force=msg)

    with _db_connect() as conn:
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
    with _db_connect() as conn:
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


def emendas_a_municipio_por_funcao(municipio: str, funcao: str) -> DataToolOutput:
    """Returns the amounts of emendas for a given municipality filtered by a specific
    funcao (government function), grouped by subfuncao and year.

    Args:
        municipio: Municipality name to filter by, e.g. "Pilar" or "São Paulo".
        funcao: Government function name to filter by, e.g. "Saúde", "Educação",
                "Assistência Social". Case-insensitive match.

    Returns:
        A breakdown of parliamentary amendments (emendas parlamentares) for the given
        municipality and function, grouped by subfunction and year. Shows
        valor_empenhado, valor_liquidado and valor_pago totals.
        If the municipality or function is not found, returns a force message with
        suggestions.
    """
    municipio_upper = municipio.strip().upper()
    funcao_upper = funcao.strip().upper()

    with _db_connect() as conn:
        # Check that the municipio exists
        uf_rows = conn.execute(
            "SELECT DISTINCT uf FROM emendas WHERE municipio = ? ORDER BY uf",
            (municipio_upper,),
        ).fetchall()

    if not uf_rows:
        msg = f"Nenhuma emenda encontrada para o município '{municipio}'."
        return text_result(msg, source_url=SOURCE_URL, force=msg)

    with _db_connect() as conn:
        # Check available funcoes for this municipio
        funcao_rows = conn.execute(
            "SELECT DISTINCT nome_funcao FROM emendas WHERE municipio = ? ORDER BY nome_funcao",
            (municipio_upper,),
        ).fetchall()

    available_funcoes = [r["nome_funcao"] for r in funcao_rows]
    matched_funcao = None
    for f in available_funcoes:
        if f.upper() == funcao_upper:
            matched_funcao = f
            break

    if matched_funcao is None:
        funcoes_list = ", ".join(available_funcoes)
        msg = (
            f"Função '{funcao}' não encontrada para o município '{municipio}'. "
            f"Funções disponíveis: {funcoes_list}"
        )
        return text_result(msg, source_url=SOURCE_URL, force=msg)

    # Fetch subfunction breakdown
    with _db_connect() as conn:
        rows = conn.execute(
            """
            SELECT ano_da_emenda,
                   municipio,
                   uf,
                   nome_funcao,
                   nome_subfuncao,
                   COUNT(*) as num_emendas,
                   SUM(valor_empenhado) as total_empenhado,
                   SUM(valor_liquidado) as total_liquidado,
                   SUM(valor_pago) as total_pago
            FROM emendas
            WHERE municipio = ? AND nome_funcao = ?
            GROUP BY uf, ano_da_emenda, nome_subfuncao
            ORDER BY uf, ano_da_emenda, nome_subfuncao
            """,
            (municipio_upper, matched_funcao),
        ).fetchall()

    ufs = ", ".join(r["uf"] for r in uf_rows)

    lines = [
        f"Emendas parlamentares para {municipio_upper} ({ufs}) — Função: {matched_funcao}:",
        "",
    ]
    table_rows = [
        [
            "Ano",
            "UF",
            "Subfunção",
            "Nº Emendas",
            "Empenhado (R$)",
            "Liquidado (R$)",
            "Pago (R$)",
        ]
    ]

    for row in rows:
        ano = row["ano_da_emenda"]
        uf = row["uf"]
        subfuncao = row["nome_subfuncao"] or "—"
        n = row["num_emendas"]
        emp = row["total_empenhado"] or 0.0
        liq = row["total_liquidado"] or 0.0
        pago = row["total_pago"] or 0.0
        lines.append(
            f"  {ano} | {uf} | {subfuncao} | {n} emendas | "
            f"Empenhado: R$ {emp:,.2f} | "
            f"Liquidado: R$ {liq:,.2f} | "
            f"Pago: R$ {pago:,.2f}"
        )
        table_rows.append(
            [
                ano,
                uf,
                subfuncao,
                n,
                f"R$ {emp:,.2f}",
                f"R$ {liq:,.2f}",
                f"R$ {pago:,.2f}",
            ]
        )

    # Aggregate by year for chart (across all subfunções)
    yearly_data = {}
    for row in rows:
        ano = str(row["ano_da_emenda"])
        if ano not in yearly_data:
            yearly_data[ano] = {"empenhado": 0.0, "liquidado": 0.0, "pago": 0.0}
        yearly_data[ano]["empenhado"] += row["total_empenhado"] or 0.0
        yearly_data[ano]["liquidado"] += row["total_liquidado"] or 0.0
        yearly_data[ano]["pago"] += row["total_pago"] or 0.0

    chart_labels = sorted(yearly_data.keys())
    chart_empenhado = [round(yearly_data[y]["empenhado"], 2) for y in chart_labels]
    chart_liquidado = [round(yearly_data[y]["liquidado"], 2) for y in chart_labels]
    chart_pago = [round(yearly_data[y]["pago"], 2) for y in chart_labels]

    chart = {
        "type": "bar",
        "title": f"Emendas — {municipio_upper} — {matched_funcao}",
        "labels": chart_labels,
        "datasets": [
            {"label": "Empenhado (R$)", "data": chart_empenhado},
            {"label": "Liquidado (R$)", "data": chart_liquidado},
            {"label": "Pago (R$)", "data": chart_pago},
        ],
        "beginAtZero": True,
    }

    text = "\n".join(lines)

    return text_result(text, source_url=SOURCE_URL, table=table_rows, charts=[chart])


def list_funcao() -> DataToolOutput:
    """Return a table listing all available funcao (government functions) in the
    emendas dataset.

    Returns:
        A table of all distinct funcao values available in the parliamentary amendments
        (emendas parlamentares) dataset, with the number of emendas and total
        valor_empenhado per funcao.
    """
    with _db_connect() as conn:
        rows = conn.execute(
            """
            SELECT nome_funcao,
                   COUNT(*) as num_emendas,
                   SUM(valor_empenhado) as total_empenhado,
                   SUM(valor_liquidado) as total_liquidado,
                   SUM(valor_pago) as total_pago
            FROM emendas
            GROUP BY nome_funcao
            ORDER BY total_empenhado DESC
            """
        ).fetchall()

    if not rows:
        msg = "Nenhuma função encontrada na base de dados."
        return text_result(msg, source_url=SOURCE_URL, force=msg)

    lines = [f"Funções disponíveis nas emendas parlamentares ({len(rows)} funções):", ""]
    table_rows = [
        [
            "Função",
            "Nº Emendas",
            "Empenhado (R$)",
            "Liquidado (R$)",
            "Pago (R$)",
        ]
    ]
    chart_labels = []
    chart_empenhado = []

    for row in rows:
        funcao = row["nome_funcao"]
        n = row["num_emendas"]
        emp = row["total_empenhado"] or 0.0
        liq = row["total_liquidado"] or 0.0
        pago = row["total_pago"] or 0.0
        lines.append(
            f"  {funcao} | {n} emendas | "
            f"Empenhado: R$ {emp:,.2f} | "
            f"Liquidado: R$ {liq:,.2f} | "
            f"Pago: R$ {pago:,.2f}"
        )
        table_rows.append(
            [
                funcao,
                n,
                f"R$ {emp:,.2f}",
                f"R$ {liq:,.2f}",
                f"R$ {pago:,.2f}",
            ]
        )
        chart_labels.append(funcao)
        chart_empenhado.append(round(emp, 2))

    text = "\n".join(lines)

    chart = {
        "type": "bar",
        "indexAxis": "y",
        "title": "Funções das Emendas Parlamentares por Valor Empenhado",
        "labels": chart_labels,
        "datasets": [
            {"label": "Empenhado (R$)", "data": chart_empenhado},
        ],
        "beginAtZero": True,
    }

    return text_result(text, source_url=SOURCE_URL, table=table_rows, charts=[chart])


def list_subfuncao() -> DataToolOutput:
    """Return a table listing all available subfuncao (government sub functions) in the
    emendas dataset.

    Returns:
        A table of all distinct subfuncao values available in the parliamentary amendments
        (emendas parlamentares) dataset, with the number of emendas and total
        valor_empenhado per funcao.
    """
    with _db_connect() as conn:
        rows = conn.execute(
            """
            SELECT nome_subfuncao,
                   COUNT(*) as num_emendas,
                   SUM(valor_empenhado) as total_empenhado,
                   SUM(valor_liquidado) as total_liquidado,
                   SUM(valor_pago) as total_pago
            FROM emendas
            GROUP BY nome_subfuncao
            ORDER BY total_empenhado DESC
            """
        ).fetchall()

    if not rows:
        msg = "Nenhuma subfunção encontrada na base de dados."
        return text_result(msg, source_url=SOURCE_URL, force=msg)

    lines = [f"Subfunções disponíveis nas emendas parlamentares ({len(rows)} funções):", ""]
    table_rows = [
        [
            "Subfunção",
            "Nº Emendas",
            "Empenhado (R$)",
            "Liquidado (R$)",
            "Pago (R$)",
        ]
    ]
    chart_labels = []
    chart_empenhado = []

    for row in rows:
        funcao = row["nome_subfuncao"]
        n = row["num_emendas"]
        emp = row["total_empenhado"] or 0.0
        liq = row["total_liquidado"] or 0.0
        pago = row["total_pago"] or 0.0
        lines.append(
            f"  {funcao} | {n} emendas | "
            f"Empenhado: R$ {emp:,.2f} | "
            f"Liquidado: R$ {liq:,.2f} | "
            f"Pago: R$ {pago:,.2f}"
        )
        table_rows.append(
            [
                funcao,
                n,
                f"R$ {emp:,.2f}",
                f"R$ {liq:,.2f}",
                f"R$ {pago:,.2f}",
            ]
        )
        chart_labels.append(funcao)
        chart_empenhado.append(round(emp, 2))

    text = "\n".join(lines)

    chart = {
        "type": "bar",
        "indexAxis": "y",
        "title": "Subfunções das Emendas Parlamentares por Valor Empenhado",
        "labels": chart_labels,
        "datasets": [
            {"label": "Empenhado (R$)", "data": chart_empenhado},
        ],
        "beginAtZero": True,
    }

    return text_result(text, source_url=SOURCE_URL, table=table_rows, charts=[chart])


def emendas_por_autor(autor: str) -> DataToolOutput:
    """Returns emendas parlamentares authored by the given author (nome_do_autor_da_emenda),
    grouped by year and municipio, sorted by year descending and total empenhado descending.

    Args:
        autor: Author name to filter by, e.g. "ABILIO SANTANA" or "ABEL MESQUITA JR.".
               Case-insensitive, matched with LIKE for partial/fuzzy matching.

    Returns:
        A summary of parliamentary amendments authored by the given author,
        grouped by year and municipality. Shows valor_empenhado, valor_liquidado and
        valor_pago totals per year/municipio.
        If the author name matches multiple authors, returns results for all of them.
        If no results are found, returns a force message with suggestions.
    """
    autor_upper = autor.strip().upper()
    autor_like = f"%{autor_upper}%"

    with _db_connect() as conn:
        # Find matching authors
        author_rows = conn.execute(
            "SELECT DISTINCT nome_do_autor_da_emenda FROM emendas "
            "WHERE UPPER(nome_do_autor_da_emenda) LIKE ? ORDER BY nome_do_autor_da_emenda",
            (autor_like,),
        ).fetchall()

    if not author_rows:
        # Try to suggest similar authors
        with _db_connect() as conn:
            suggestions = conn.execute(
                "SELECT DISTINCT nome_do_autor_da_emenda FROM emendas "
                "WHERE nome_do_autor_da_emenda LIKE ? ORDER BY nome_do_autor_da_emenda LIMIT 10",
                (f"%{autor_upper[:3]}%",),
            ).fetchall()
        if suggestions:
            names = ", ".join(r["nome_do_autor_da_emenda"] for r in suggestions)
            msg = (
                f"Nenhum autor encontrado para '{autor}'. "
                f"Autores sugeridos: {names}"
            )
        else:
            msg = f"Nenhum autor encontrado para '{autor}'."
        return text_result(msg, source_url=SOURCE_URL, force=msg)

    matched_authors = [r["nome_do_autor_da_emenda"] for r in author_rows]
    placeholders = ",".join("?" for _ in matched_authors)

    # Fetch yearly aggregates per municipality
    with _db_connect() as conn:
        rows = conn.execute(
            f"""
            SELECT nome_do_autor_da_emenda,
                   ano_da_emenda,
                   municipio,
                   uf,
                   COUNT(*) as num_emendas,
                   SUM(valor_empenhado) as total_empenhado,
                   SUM(valor_liquidado) as total_liquidado,
                   SUM(valor_pago) as total_pago
            FROM emendas
            WHERE nome_do_autor_da_emenda IN ({placeholders})
            GROUP BY nome_do_autor_da_emenda, ano_da_emenda, municipio, uf
            ORDER BY nome_do_autor_da_emenda, ano_da_emenda DESC, total_empenhado DESC
            """,
            matched_authors,
        ).fetchall()

    # Also get overall totals per year for the chart
    with _db_connect() as conn:
        yearly_rows = conn.execute(
            f"""
            SELECT ano_da_emenda,
                   COUNT(*) as num_emendas,
                   SUM(valor_empenhado) as total_empenhado,
                   SUM(valor_liquidado) as total_liquidado,
                   SUM(valor_pago) as total_pago
            FROM emendas
            WHERE nome_do_autor_da_emenda IN ({placeholders})
            GROUP BY ano_da_emenda
            ORDER BY ano_da_emenda
            """,
            matched_authors,
        ).fetchall()

    authors_str = ", ".join(matched_authors)
    lines = [f"Emendas parlamentares de {authors_str}:", ""]
    table_rows = [
        [
            "Autor",
            "Ano",
            "Município",
            "UF",
            "Nº Emendas",
            "Empenhado (R$)",
            "Liquidado (R$)",
            "Pago (R$)",
        ]
    ]

    for row in rows:
        autor_name = row["nome_do_autor_da_emenda"]
        ano = row["ano_da_emenda"]
        mun = row["municipio"] or "—"
        uf = row["uf"] or "—"
        n = row["num_emendas"]
        emp = row["total_empenhado"] or 0.0
        liq = row["total_liquidado"] or 0.0
        pago = row["total_pago"] or 0.0
        lines.append(
            f"  {autor_name} | {ano} | {mun}/{uf} | {n} emendas | "
            f"Empenhado: R$ {emp:,.2f} | "
            f"Liquidado: R$ {liq:,.2f} | "
            f"Pago: R$ {pago:,.2f}"
        )
        table_rows.append(
            [
                autor_name,
                ano,
                mun,
                uf,
                n,
                f"R$ {emp:,.2f}",
                f"R$ {liq:,.2f}",
                f"R$ {pago:,.2f}",
            ]
        )

    # Build chart from yearly aggregates
    chart_labels = [str(r["ano_da_emenda"]) for r in yearly_rows]
    chart_empenhado = [round(r["total_empenhado"] or 0.0, 2) for r in yearly_rows]
    chart_liquidado = [round(r["total_liquidado"] or 0.0, 2) for r in yearly_rows]
    chart_pago = [round(r["total_pago"] or 0.0, 2) for r in yearly_rows]

    chart = {
        "type": "bar",
        "title": f"Emendas Parlamentares — {authors_str}",
        "labels": chart_labels,
        "datasets": [
            {"label": "Empenhado (R$)", "data": chart_empenhado},
            {"label": "Liquidado (R$)", "data": chart_liquidado},
            {"label": "Pago (R$)", "data": chart_pago},
        ],
        "beginAtZero": True,
    }

    text = "\n".join(lines)

    return text_result(text, source_url=SOURCE_URL, table=table_rows, charts=[chart])


def favorecidos_por_autor(autor: str, limit: int = 20) -> DataToolOutput:
    """Returns the top recipients (favorecidos) of parliamentary amendments from the given
    author (nome_do_autor_da_emenda), ranked by total valor_recebido descending.

    Args:
        autor: Author name to filter by, e.g. "ABILIO SANTANA" or "ABEL MESQUITA JR.".
               Case-insensitive, matched with LIKE for partial/fuzzy matching.
        limit: Maximum number of recipients to return. Defaults to 20.

    Returns:
        A ranking of top recipients of parliamentary amendment funds from the given author,
        showing the favorecido name, natureza_juridica, tipo_favorecido, municipio, UF,
        number of emendas and total valor_recebido. Includes a table and a horizontal bar
        chart.
        If no author is found, returns a force message with suggestions.
    """
    autor_upper = autor.strip().upper()
    autor_like = f"%{autor_upper}%"

    with _db_connect() as conn:
        author_rows = conn.execute(
            "SELECT DISTINCT nome_do_autor_da_emenda FROM emendas_por_favorecido "
            "WHERE UPPER(nome_do_autor_da_emenda) LIKE ? ORDER BY nome_do_autor_da_emenda",
            (autor_like,),
        ).fetchall()

    if not author_rows:
        with _db_connect() as conn:
            suggestions = conn.execute(
                "SELECT DISTINCT nome_do_autor_da_emenda FROM emendas_por_favorecido "
                "WHERE nome_do_autor_da_emenda LIKE ? ORDER BY nome_do_autor_da_emenda LIMIT 10",
                (f"%{autor_upper[:3]}%",),
            ).fetchall()
        if suggestions:
            names = ", ".join(r["nome_do_autor_da_emenda"] for r in suggestions)
            msg = (
                f"Nenhum autor encontrado para '{autor}'. "
                f"Autores sugeridos: {names}"
            )
        else:
            msg = f"Nenhum autor encontrado para '{autor}'."
        return text_result(msg, source_url=SOURCE_URL, force=msg)

    matched_authors = [r["nome_do_autor_da_emenda"] for r in author_rows]
    placeholders = ",".join("?" for _ in matched_authors)

    with _db_connect() as conn:
        rows = conn.execute(
            f"""
            SELECT favorecido,
                   natureza_juridica,
                   tipo_favorecido,
                   municipio_favorecido,
                   uf_favorecido,
                   COUNT(*) as num_emendas,
                   SUM(valor_recebido) as total_recebido
            FROM emendas_por_favorecido
            WHERE nome_do_autor_da_emenda IN ({placeholders})
            GROUP BY favorecido
            ORDER BY total_recebido DESC
            LIMIT ?
            """,
            (*matched_authors, limit),
        ).fetchall()

    authors_str = ", ".join(matched_authors)
    lines = [f"Top {len(rows)} favorecidos das emendas de {authors_str}:", ""]
    table_rows = [
        [
            "#",
            "Favorecido",
            "Natureza Jurídica",
            "Tipo",
            "Município",
            "UF",
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
        mun = row["municipio_favorecido"] or ""
        uf = row["uf_favorecido"] or ""
        n = row["num_emendas"]
        total = row["total_recebido"] or 0.0
        lines.append(
            f"  {i}. {favorecido} | {natureza} | {tipo} | "
            f"{mun}/{uf} | {n} emendas | Recebido: R$ {total:,.2f}"
        )
        table_rows.append(
            [
                i,
                favorecido,
                natureza,
                tipo,
                mun,
                uf,
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
        "title": f"Top Favorecidos — Emendas de {authors_str}",
        "labels": chart_labels,
        "datasets": [
            {"label": "Total Recebido (R$)", "data": chart_recebido},
        ],
        "beginAtZero": True,
    }

    return text_result(text, source_url=SOURCE_URL, table=table_rows, charts=[chart])


if __name__ == "__main__":
    print(list_subfuncao())
