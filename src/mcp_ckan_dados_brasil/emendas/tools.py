import pandas as pd

from mcp_server import DataToolOutput
from mcp_server.results import text_result

from mcp_ckan_dados_brasil.emendas.load_db import db_connect


SOURCE_URL = (
    "https://portaldatransparencia.gov.br/download-de-dados/emendas-parlamentares/UNICO"
)


def query_df(sql: str, params=()) -> pd.DataFrame:
    """Run a SQL query against the emendas SQLite DB and return a DataFrame."""
    with db_connect() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def build_bar_chart(title: str, labels: list, datasets: list[dict],
                    index_axis: str | None = None, begin_at_zero: bool = True) -> dict:
    """Build a chart dict with sensible defaults."""
    chart = {
        "type": "bar",
        "title": title,
        "labels": labels,
        "datasets": datasets,
        "beginAtZero": begin_at_zero,
    }
    if index_axis:
        chart["indexAxis"] = index_axis
    return chart


def find_author(autor: str, table: str = "emendas") -> tuple[list[str] | None, DataToolOutput | None]:
    """Find matching authors via case-insensitive LIKE search.

    Args:
        autor: Author name to search for.
        table: Table to query -"emendas" or "emendas_por_favorecido".

    Returns:
        (matched_names, None) on success, or (None, error_result) on failure.
    """
    autor_upper = autor.strip().upper()
    autor_like = f"%{autor_upper}%"
    col = "nome_do_autor_da_emenda"

    df = query_df(
        f"SELECT DISTINCT {col} FROM {table} "
        f"WHERE UPPER({col}) LIKE ? ORDER BY {col}",
        (autor_like,),
    )
    if not df.empty:
        return df[col].tolist(), None

    # Suggest similar authors using first 3 chars
    df2 = query_df(
        f"SELECT DISTINCT {col} FROM {table} "
        f"WHERE {col} LIKE ? ORDER BY {col} LIMIT 10",
        (f"%{autor_upper[:3]}%",),
    )
    if not df2.empty:
        names = ", ".join(df2[col])
        msg = (
            f"Nenhum autor encontrado para '{autor}'. "
            f"Autores sugeridos: {names}"
        )
    else:
        msg = f"Nenhum autor encontrado para '{autor}'."
    return None, text_result(msg, source_url=SOURCE_URL, force=msg)


def validate_municipio(municipio: str) -> tuple[str | None, list[str] | None, DataToolOutput | None]:
    """Check that a municipio exists in the emendas table.

    Returns:
        (municipio_upper, uf_list, None) on success, or
        (None, None, error_result) on failure.
    """
    municipio_upper = municipio.strip().upper()
    df = query_df(
        "SELECT DISTINCT uf FROM emendas WHERE municipio = ? ORDER BY uf",
        (municipio_upper,),
    )
    if df.empty:
        msg = f"Nenhuma emenda encontrada para o município '{municipio}'."
        return None, None, text_result(msg, source_url=SOURCE_URL, force=msg)
    return municipio_upper, df["uf"].tolist(), None


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
    municipio_upper, _, err = validate_municipio(municipio)
    if err:
        return err

    # Fetch yearly aggregates across all matching UFs
    df = query_df(
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
    )
    for col in ["total_empenhado", "total_liquidado", "total_pago"]:
        df[col] = df[col].fillna(0.0)

    lines = [f"Emendas parlamentares para {municipio_upper}:", ""]
    table_rows = [["Ano", "UF", "Nº Emendas", "Empenhado (R$)", "Liquidado (R$)", "Pago (R$)"]]

    for _, r in df.iterrows():
        ano = r["ano_da_emenda"]
        uf = r["uf"]
        n = int(r["num_emendas"])
        emp, liq, pago = r["total_empenhado"], r["total_liquidado"], r["total_pago"]
        lines.append(
            f"  {ano} | {uf} | {n} emendas | "
            f"Empenhado: R$ {emp:,.2f} | "
            f"Liquidado: R$ {liq:,.2f} | "
            f"Pago: R$ {pago:,.2f}"
        )
        table_rows.append([ano, uf, n, f"R$ {emp:,.2f}", f"R$ {liq:,.2f}", f"R$ {pago:,.2f}"])

    # One chart per UF
    charts = []
    for uf, group in df.groupby("uf"):
        charts.append(build_bar_chart(
            f"Emendas Parlamentares - {municipio_upper} ({uf})",
            group["ano_da_emenda"].astype(str).tolist(),
            [
                {"label": "Empenhado (R$)", "data": group["total_empenhado"].round(2).tolist()},
                {"label": "Liquidado (R$)", "data": group["total_liquidado"].round(2).tolist()},
                {"label": "Pago (R$)", "data": group["total_pago"].round(2).tolist()},
            ],
        ))

    return text_result("\n".join(lines), source_url=SOURCE_URL, table=table_rows, charts=charts)


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
    municipio_upper, uf_list, err = validate_municipio(municipio)
    if err:
        return err

    df = query_df(
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
    )
    for col in ["total_empenhado", "total_liquidado", "total_pago"]:
        df[col] = df[col].fillna(0.0)

    ufs = ", ".join(uf_list)
    lines = [f"Autores de emendas para {municipio_upper} ({ufs}):", ""]
    table_rows = [["Autor", "Nº Emendas", "Empenhado (R$)", "Liquidado (R$)", "Pago (R$)"]]

    for _, r in df.iterrows():
        autor = r["nome_do_autor_da_emenda"]
        n = int(r["num_emendas"])
        emp, liq, pago = r["total_empenhado"], r["total_liquidado"], r["total_pago"]
        lines.append(
            f"  {autor} | {n} emendas | "
            f"Empenhado: R$ {emp:,.2f} | "
            f"Liquidado: R$ {liq:,.2f} | "
            f"Pago: R$ {pago:,.2f}"
        )
        table_rows.append([autor, n, f"R$ {emp:,.2f}", f"R$ {liq:,.2f}", f"R$ {pago:,.2f}"])

    chart = build_bar_chart(
        f"Autores de Emendas - {municipio_upper}",
        df["nome_do_autor_da_emenda"].tolist(),
        [
            {"label": "Empenhado (R$)", "data": df["total_empenhado"].round(2).tolist()},
            {"label": "Pago (R$)", "data": df["total_pago"].round(2).tolist()},
        ],
        index_axis="y",
    )
    return text_result("\n".join(lines), source_url=SOURCE_URL, table=table_rows, charts=[chart])


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
    df = query_df(
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
    )
    if df.empty:
        msg = "Nenhum favorecido encontrado na base de dados."
        return text_result(msg, source_url=SOURCE_URL, force=msg)

    df["total_recebido"] = df["total_recebido"].fillna(0.0)
    df["natureza_juridica"] = df["natureza_juridica"].fillna("")
    df["tipo_favorecido"] = df["tipo_favorecido"].fillna("")

    lines = [f"Top {len(df)} favorecidos por valor recebido em emendas:", ""]
    table_rows = [["#", "Favorecido", "Natureza Jurídica", "Tipo", "Nº Emendas", "Total Recebido (R$)"]]

    for i, (_, r) in enumerate(df.iterrows(), start=1):
        favorecido = r["favorecido"]
        natureza = r["natureza_juridica"]
        tipo = r["tipo_favorecido"]
        n = int(r["num_emendas"])
        total = r["total_recebido"]
        lines.append(
            f"  {i}. {favorecido} | {natureza} | {tipo} | "
            f"{n} emendas | Recebido: R$ {total:,.2f}"
        )
        table_rows.append([i, favorecido, natureza, tipo, n, f"R$ {total:,.2f}"])

    chart = build_bar_chart(
        f"Top {len(df)} Favorecidos por Valor Recebido",
        df["favorecido"].tolist(),
        [{"label": "Total Recebido (R$)", "data": df["total_recebido"].round(2).tolist()}],
        index_axis="y",
    )
    return text_result("\n".join(lines), source_url=SOURCE_URL, table=table_rows, charts=[chart])


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
    municipio_upper, uf_list, err = validate_municipio(municipio)
    if err:
        return err
    funcao_upper = funcao.strip().upper()

    # Check available funcoes for this municipio
    funcao_df = query_df(
            "SELECT DISTINCT nome_funcao FROM emendas WHERE municipio = ? ORDER BY nome_funcao",
            (municipio_upper,),
        )

    available_funcoes = funcao_df["nome_funcao"].tolist()
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
    df = query_df(
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
    )
    for col in ["total_empenhado", "total_liquidado", "total_pago"]:
        df[col] = df[col].fillna(0.0)
    df["nome_subfuncao"] = df["nome_subfuncao"].fillna("-")

    ufs = ", ".join(uf_list)
    lines = [
        f"Emendas parlamentares para {municipio_upper} ({ufs}) -Função: {matched_funcao}:",
        "",
    ]
    table_rows = [["Ano", "UF", "Subfunção", "Nº Emendas", "Empenhado (R$)", "Liquidado (R$)", "Pago (R$)"]]

    for _, r in df.iterrows():
        ano = r["ano_da_emenda"]
        uf = r["uf"]
        subfuncao = r["nome_subfuncao"]
        n = int(r["num_emendas"])
        emp, liq, pago = r["total_empenhado"], r["total_liquidado"], r["total_pago"]
        lines.append(
            f"  {ano} | {uf} | {subfuncao} | {n} emendas | "
            f"Empenhado: R$ {emp:,.2f} | "
            f"Liquidado: R$ {liq:,.2f} | "
            f"Pago: R$ {pago:,.2f}"
        )
        table_rows.append([ano, uf, subfuncao, n, f"R$ {emp:,.2f}", f"R$ {liq:,.2f}", f"R$ {pago:,.2f}"])

    # Aggregate by year for chart (across all subfunções)
    yearly = df.groupby("ano_da_emenda")[["total_empenhado", "total_liquidado", "total_pago"]].sum()
    yearly = yearly.sort_index()

    chart = build_bar_chart(
        f"Emendas -{municipio_upper} -{matched_funcao}",
        yearly.index.astype(str).tolist(),
        [
            {"label": "Empenhado (R$)", "data": yearly["total_empenhado"].round(2).tolist()},
            {"label": "Liquidado (R$)", "data": yearly["total_liquidado"].round(2).tolist()},
            {"label": "Pago (R$)", "data": yearly["total_pago"].round(2).tolist()},
        ],
    )

    return text_result("\n".join(lines), source_url=SOURCE_URL, table=table_rows, charts=[chart])


def list_funcao() -> DataToolOutput:
    """Return a table listing all available funcao (government functions) in the
    emendas dataset.

    Returns:
        A table of all distinct funcao values available in the parliamentary amendments
        (emendas parlamentares) dataset, with the number of emendas and total
        valor_empenhado per funcao.
    """
    df = query_df(
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
    )
    if df.empty:
        msg = "Nenhuma função encontrada na base de dados."
        return text_result(msg, source_url=SOURCE_URL, force=msg)

    for col in ["total_empenhado", "total_liquidado", "total_pago"]:
        df[col] = df[col].fillna(0.0)

    lines = [f"Funções disponíveis nas emendas parlamentares ({len(df)} funções):", ""]
    table_rows = [["Função", "Nº Emendas", "Empenhado (R$)", "Liquidado (R$)", "Pago (R$)"]]

    for _, r in df.iterrows():
        funcao = r["nome_funcao"]
        n = int(r["num_emendas"])
        emp, liq, pago = r["total_empenhado"], r["total_liquidado"], r["total_pago"]
        lines.append(
            f"  {funcao} | {n} emendas | "
            f"Empenhado: R$ {emp:,.2f} | "
            f"Liquidado: R$ {liq:,.2f} | "
            f"Pago: R$ {pago:,.2f}"
        )
        table_rows.append([funcao, n, f"R$ {emp:,.2f}", f"R$ {liq:,.2f}", f"R$ {pago:,.2f}"])

    chart = build_bar_chart(
        "Funções das Emendas Parlamentares por Valor Empenhado",
        df["nome_funcao"].tolist(),
        [{"label": "Empenhado (R$)", "data": df["total_empenhado"].round(2).tolist()}],
        index_axis="y",
    )
    return text_result("\n".join(lines), source_url=SOURCE_URL, table=table_rows, charts=[chart])


def list_subfuncao() -> DataToolOutput:
    """Return a table listing all available subfuncao (government sub functions) in the
    emendas dataset.

    Returns:
        A table of all distinct subfuncao values available in the parliamentary amendments
        (emendas parlamentares) dataset, with the number of emendas and total
        valor_empenhado per funcao.
    """
    df = query_df(
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
    )
    if df.empty:
        msg = "Nenhuma subfunção encontrada na base de dados."
        return text_result(msg, source_url=SOURCE_URL, force=msg)

    for col in ["total_empenhado", "total_liquidado", "total_pago"]:
        df[col] = df[col].fillna(0.0)

    lines = [f"Subfunções disponíveis nas emendas parlamentares ({len(df)} subfunções):", ""]
    table_rows = [["Subfunção", "Nº Emendas", "Empenhado (R$)", "Liquidado (R$)", "Pago (R$)"]]

    for _, r in df.iterrows():
        subfuncao = r["nome_subfuncao"]
        n = int(r["num_emendas"])
        emp, liq, pago = r["total_empenhado"], r["total_liquidado"], r["total_pago"]
        lines.append(
            f"  {subfuncao} | {n} emendas | "
            f"Empenhado: R$ {emp:,.2f} | "
            f"Liquidado: R$ {liq:,.2f} | "
            f"Pago: R$ {pago:,.2f}"
        )
        table_rows.append([subfuncao, n, f"R$ {emp:,.2f}", f"R$ {liq:,.2f}", f"R$ {pago:,.2f}"])

    chart = build_bar_chart(
        "Subfunções das Emendas Parlamentares por Valor Empenhado",
        df["nome_subfuncao"].tolist(),
        [{"label": "Empenhado (R$)", "data": df["total_empenhado"].round(2).tolist()}],
        index_axis="y",
    )
    return text_result("\n".join(lines), source_url=SOURCE_URL, table=table_rows, charts=[chart])




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
    matched_authors, err = find_author(autor)
    if err:
        return err
    placeholders = ",".join("?" for _ in matched_authors)

    # Fetch yearly aggregates per municipality
    df = query_df(
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
    )
    for col in ["total_empenhado", "total_liquidado", "total_pago"]:
        df[col] = df[col].fillna(0.0)
    df["municipio"] = df["municipio"].fillna("-")
    df["uf"] = df["uf"].fillna("-")

    authors_str = ", ".join(matched_authors)
    lines = [f"Emendas parlamentares de {authors_str}:", ""]
    table_rows = [["Autor", "Ano", "Município", "UF", "Nº Emendas", "Empenhado (R$)", "Liquidado (R$)", "Pago (R$)"]]

    for _, r in df.iterrows():
        autor_name = r["nome_do_autor_da_emenda"]
        ano = r["ano_da_emenda"]
        mun = r["municipio"]
        uf = r["uf"]
        n = int(r["num_emendas"])
        emp, liq, pago = r["total_empenhado"], r["total_liquidado"], r["total_pago"]
        lines.append(
            f"  {autor_name} | {ano} | {mun}/{uf} | {n} emendas | "
            f"Empenhado: R$ {emp:,.2f} | "
            f"Liquidado: R$ {liq:,.2f} | "
            f"Pago: R$ {pago:,.2f}"
        )
        table_rows.append([autor_name, ano, mun, uf, n, f"R$ {emp:,.2f}", f"R$ {liq:,.2f}", f"R$ {pago:,.2f}"])

    # Aggregate by year for chart using pandas groupby
    yearly = df.groupby("ano_da_emenda")[["total_empenhado", "total_liquidado", "total_pago"]].sum()
    yearly = yearly.sort_index()

    chart = build_bar_chart(
        f"Emendas Parlamentares -{authors_str}",
        yearly.index.astype(str).tolist(),
        [
            {"label": "Empenhado (R$)", "data": yearly["total_empenhado"].round(2).tolist()},
            {"label": "Liquidado (R$)", "data": yearly["total_liquidado"].round(2).tolist()},
            {"label": "Pago (R$)", "data": yearly["total_pago"].round(2).tolist()},
        ],
    )

    return text_result("\n".join(lines), source_url=SOURCE_URL, table=table_rows, charts=[chart])


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
    matched_authors, err = find_author(autor, table="emendas_por_favorecido")
    if err:
        return err
    placeholders = ",".join("?" for _ in matched_authors)

    df = query_df(
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
    )
    df["total_recebido"] = df["total_recebido"].fillna(0.0)
    df["natureza_juridica"] = df["natureza_juridica"].fillna("")
    df["tipo_favorecido"] = df["tipo_favorecido"].fillna("")
    df["municipio_favorecido"] = df["municipio_favorecido"].fillna("")
    df["uf_favorecido"] = df["uf_favorecido"].fillna("")

    authors_str = ", ".join(matched_authors)
    lines = [f"Top {len(df)} favorecidos das emendas de {authors_str}:", ""]
    table_rows = [["#", "Favorecido", "Natureza Jurídica", "Tipo", "Município", "UF", "Nº Emendas", "Total Recebido (R$)"]]

    for i, (_, r) in enumerate(df.iterrows(), start=1):
        favorecido = r["favorecido"]
        natureza = r["natureza_juridica"]
        tipo = r["tipo_favorecido"]
        mun = r["municipio_favorecido"]
        uf = r["uf_favorecido"]
        n = int(r["num_emendas"])
        total = r["total_recebido"]
        lines.append(
            f"  {i}. {favorecido} | {natureza} | {tipo} | "
            f"{mun}/{uf} | {n} emendas | Recebido: R$ {total:,.2f}"
        )
        table_rows.append([i, favorecido, natureza, tipo, mun, uf, n, f"R$ {total:,.2f}"])

    chart = build_bar_chart(
        f"Top Favorecidos -Emendas de {authors_str}",
        df["favorecido"].tolist(),
        [{"label": "Total Recebido (R$)", "data": df["total_recebido"].round(2).tolist()}],
        index_axis="y",
    )
    return text_result("\n".join(lines), source_url=SOURCE_URL, table=table_rows, charts=[chart])


def buscar_favorecido(nome_favorecido: str, limit: int = 10) -> DataToolOutput:
    """Search for favorecidos (recipients) by approximate name using partial match.

    Use this when the exact favorecido name is unknown or misspelled, to find the
    correct name before calling other tools.

    Args:
        nome: Name (or partial name) to search for, e.g. "BANCO DO BRASIL" or "FUNDO MUNICIPAL".
              Case-insensitive partial match supported.
        limit: Maximum number of results to return. Defaults to 10.

    Returns:
        A table of favorecidos matching the (possibly partial) name, each with its
        natureza_juridica, tipo_favorecido, municipio, UF, number of emendas and
        total valor_recebido.
        If no results are found, returns a force message.
    """
    nome_upper = nome_favorecido.strip().upper()
    nome_like = f"%{nome_upper}%"

    df = query_df(
        """
        SELECT favorecido,
               natureza_juridica,
               tipo_favorecido,
               municipio_favorecido,
               uf_favorecido,
               COUNT(*) as num_emendas,
               SUM(valor_recebido) as total_recebido
        FROM emendas_por_favorecido
        WHERE UPPER(favorecido) LIKE ?
        GROUP BY favorecido
        ORDER BY total_recebido DESC
        LIMIT ?
        """,
        (nome_like, limit),
    )
    if df.empty:
        msg = f"Nenhum favorecido encontrado para '{nome_favorecido}'."
        return text_result(msg, source_url=SOURCE_URL, force=msg)

    df["total_recebido"] = df["total_recebido"].fillna(0.0)
    df["natureza_juridica"] = df["natureza_juridica"].fillna("")
    df["tipo_favorecido"] = df["tipo_favorecido"].fillna("")
    df["municipio_favorecido"] = df["municipio_favorecido"].fillna("")
    df["uf_favorecido"] = df["uf_favorecido"].fillna("")

    lines = [f"Favorecidos encontrados para '{nome_favorecido}' ({len(df)} resultados):", ""]
    table_rows = [["#", "Favorecido", "Natureza Jurídica", "Tipo", "Município", "UF", "Nº Emendas", "Total Recebido (R$)"]]

    for i, (_, r) in enumerate(df.iterrows(), start=1):
        favorecido = r["favorecido"]
        natureza = r["natureza_juridica"]
        tipo = r["tipo_favorecido"]
        mun = r["municipio_favorecido"]
        uf = r["uf_favorecido"]
        n = int(r["num_emendas"])
        total = r["total_recebido"]
        lines.append(
            f"  {i}. {favorecido} | {natureza} | {tipo} | "
            f"{mun}/{uf} | {n} emendas | Recebido: R$ {total:,.2f}"
        )
        table_rows.append([i, favorecido, natureza, tipo, mun, uf, n, f"R$ {total:,.2f}"])

    return text_result("\n".join(lines), source_url=SOURCE_URL, table=table_rows)


def detalhe_emendas_por_autor(autor: str, ano: int | None = None, limit: int = 30) -> DataToolOutput:
    """Returns the individual emenda records for a given author (nome_do_autor_da_emenda),
    showing full detail per emenda including funcao, subfuncao, programa, acao,
    municipio, and all valor columns.

    Unlike emendas_por_autor which aggregates by year/municipio, this tool shows
    each individual emenda with its complete detail.

    Args:
        autor: Author name to filter by, e.g. "ABILIO SANTANA" or "ABEL MESQUITA JR.".
               Case-insensitive, matched with LIKE for partial/fuzzy matching.
        ano: Optional year to filter by, e.g. 2024. If None, returns all years.
        limit: Maximum number of emenda records to return. Defaults to 30.

    Returns:
        A detailed list of individual parliamentary amendments for the given author,
        with columns: Codigo, Ano, Tipo, Municipio, UF, Funcao, Subfuncao, Programa,
        Acao, Empenhado (R$), Liquidado (R$), Pago (R$).
        If no author is found, returns a force message with suggestions.
    """
    matched_authors, err = find_author(autor)
    if err:
        return err
    placeholders = ",".join("?" for _ in matched_authors)
    params = list(matched_authors)

    ano_filter = ""
    if ano is not None:
        ano_filter = " AND ano_da_emenda = ?"
        params.append(ano)

    params.append(limit)

    df = query_df(
        f"""
        SELECT codigo_da_emenda,
               ano_da_emenda,
               tipo_de_emenda,
               municipio,
               uf,
               nome_funcao,
               nome_subfuncao,
               nome_programa,
               nome_acao,
               valor_empenhado,
               valor_liquidado,
               valor_pago
        FROM emendas
        WHERE nome_do_autor_da_emenda IN ({placeholders}){ano_filter}
        ORDER BY ano_da_emenda DESC, valor_empenhado DESC
        LIMIT ?
        """,
        params,
    )
    for col in ["valor_empenhado", "valor_liquidado", "valor_pago"]:
        df[col] = df[col].fillna(0.0)
    df["tipo_de_emenda"] = df["tipo_de_emenda"].fillna("")
    df["municipio"] = df["municipio"].fillna("-")
    df["uf"] = df["uf"].fillna("-")
    df["nome_funcao"] = df["nome_funcao"].fillna("")
    df["nome_subfuncao"] = df["nome_subfuncao"].fillna("")
    df["nome_programa"] = df["nome_programa"].fillna("")
    df["nome_acao"] = df["nome_acao"].fillna("")

    authors_str = ", ".join(matched_authors)
    ano_label = f" (ano {ano})" if ano else ""
    lines = [f"Detalhe das emendas de {authors_str}{ano_label} ({len(df)} registros):", ""]
    table_rows = [["Código", "Ano", "Tipo", "Município", "UF", "Função", "Subfunção", "Programa", "Ação", "Empenhado (R$)", "Liquidado (R$)", "Pago (R$)"]]

    for _, r in df.iterrows():
        codigo = r["codigo_da_emenda"]
        ano_emenda = r["ano_da_emenda"]
        tipo = r["tipo_de_emenda"]
        mun = r["municipio"]
        uf = r["uf"]
        funcao = r["nome_funcao"]
        subfuncao = r["nome_subfuncao"]
        programa = r["nome_programa"]
        acao = r["nome_acao"]
        emp, liq, pago = r["valor_empenhado"], r["valor_liquidado"], r["valor_pago"]
        lines.append(
            f"  {codigo} | {ano_emenda} | {tipo[:40]} | {mun}/{uf} | "
            f"{funcao} / {subfuncao} | {programa[:30]} | {acao[:30]} | "
            f"Empenhado: R$ {emp:,.2f} | Liquidado: R$ {liq:,.2f} | Pago: R$ {pago:,.2f}"
        )
        table_rows.append([codigo, ano_emenda, tipo, mun, uf, funcao, subfuncao, programa, acao, f"R$ {emp:,.2f}", f"R$ {liq:,.2f}", f"R$ {pago:,.2f}"])

    return text_result("\n".join(lines), source_url=SOURCE_URL, table=table_rows)


if __name__ == "__main__":
    print(list_subfuncao())
