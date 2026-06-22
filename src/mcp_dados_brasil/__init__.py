from mcp.types import CallToolResult, TextContent
from mcp_server import DataToolOutput

from mcp_dados_brasil.datasets import bolsa_familia, municipios
from mcp_dados_brasil.emendas import tools as emendas
from mcp_dados_brasil.emendas import glossary as emendas_glossary


def register_tools(mcp):

    mcp.set_plugin_info(
        description=(
            "Ferramentas sobre dados abertos do Brasil (https://)dados.gov.br)"
        ),
        sample_questions=[
            "Quais são as emendas parlamentares para Pilar?",
            "Emendas parlamentares para Pilar no ano corrente",
            "Histórico de emendas parlamentares para São Paulo",
            "Quem são os parlamentares que mais enviam emendas para São Paulo?",
            "Top 10 favorecidos das emendas parlamentares",
            "Top 20 favorecidos das emendas parlamentares no ano corrente",
            "Emendas para Saúde em São Paulo",
            "Quanto Belo Horizonte recebeu em emendas de Educação?",
            "Emendas para Assistência Social em Manaus",
            "Quais funções de governo recebem mais recursos de emendas?",
            "Quais subfunções concentram mais valor empenhado em emendas?",
            "Quem destina emendas parlamentares para Salvador?",
            "Quais representantes mais destinaram emendas parlamentares?",
            "Quem deu mais emendas em 2024?",
            "Top 20 autores de emendas parlamentares no ano corrente",
            "Quais emendas o parlamentar ABILIO SANTANA destinou?",
            "Emendas de ABILIO SANTANA no ano corrente",
            "Quais favorecidos receberam emendas de LULA DA FONTE?",
            "Histórico de favorecidos das emendas de LULA DA FONTE",
            "Quanto é que a favorecido 100 Sports LTDA recebeu com as emendas?",
            "Para que serviu o dinheiro enviado pelo deputado ABILIO SANTANA?",
        ],
    )

    # @mcp.tool()
    def bolsa_familia_list(
        municipio: str = None, codigo_ibge: int = None,
        year: int = 2026, limit: int = 20, state: str = None,
        order_by: str = None
    ) -> DataToolOutput:
        """List rows from the Bolsa Família dataset (beneficiary families per municipality).

        Args:
            municipio: Municipality name, e.g. "Cacoal" or "Porto Velho/RO".
            codigo_ibge: IBGE municipality code to filter by, e.g. 110001.
            year: Year to filter the data. Defaults to 2026. We only have data from 2024 to 2026 (inclusive).
            limit: Maximum number of rows to return. Defaults to 20.
            state: Optional state abbreviation to filter results, e.g. "RO". If None, searches all states.
            order_by: Column name to order the results by. This must a valid column +
                      (optionally) "asc" or "desc" for ascending/descending.
                      E.g. "qtd_familias_beneficiarias_bolsa_familia_s desc".
                      If None, defaults to the CSV order.

        Returns:
            Monthly Bolsa Família records for the requested municipality, with a table of
            (IBGE, month, families, value, average) and a bar chart of value over time.
            If `municipio` is missing or cannot be resolved, returns a force message asking
            the user to clarify (or, when fuzzy matches exist, a table of similar-name
            suggestions).

        Examples:
            - bolsa_familia_list(municipio="Porto Velho")
            - bolsa_familia_list(municipio="São Paulo/SP", year=2025)
            - bolsa_familia_list(state="RO", year=2024)
            - bolsa_familia_list(codigo_ibge=110001)
            # To answer things like: "10 most families in a state of RO in 2026"
            - bolsa_familia_list(state="RO", year=2026, limit=10, order_by="qtd_familias_beneficiarias_bolsa_familia_s desc")

        Head file sample:
            codigo_ibge,anomes_s,qtd_familias_beneficiarias_bolsa_familia_s,valor_repassado_bolsa_familia_s,pbf_vlr_medio_benef_f
            110001,202412,1677,1132797.0,679.54
            110002,202412,7710,5247594.0,683.9
        """
        return bolsa_familia.get_bolsa_familia_rows(
            municipio=municipio, codigo_ibge=codigo_ibge, year=year, limit=limit,
            state=state, order_by=order_by
        )

    @mcp.tool()
    def buscar_municipio(nome: str, limit: int = 10) -> DataToolOutput:
        """Search for Brazilian municipalities by approximate name. Use this when the exact
            municipality name is unknown or misspelled, to find the correct name before
            calling bolsa_familia_list.

        Args:
            nome: Name (or partial/misspelled name) to search for, e.g. "Poto Velho".
            limit: Maximum number of suggestions to return. Defaults to 10.

        Returns:
            A table of municipalities matching the (possibly misspelled) name, each with its
            UF and IBGE code. If no similar name is found, returns a force message saying so.

        Examples:
            - buscar_municipio(nome="Poto Velho")
            - buscar_municipio(nome="San Pablo")
        """
        return municipios.buscar_municipio(nome=nome, limit=limit)

    @mcp.tool()
    def political_questions(country=None) -> DataToolOutput:
        """ To anwer when people ask about political questions that are not answerable with data,
            but are common questions about Brasil Government.
            For example: "Why is X data not available?" or "What did the Gobvernment open this data in this way?"

        Returns:
            A message with the canned response. The text is shown to the user verbatim;
            no LLM rewording is needed.

        Examples:
            - political_questions()
        """

        response = (
            "Sinto muito, mas não posso responder a essa pergunta. "
            "As decisões governamentais relativas à divulgação de dados podem "
            "depender de muitos fatores, incluindo considerações de privacidade, "
            "segurança, recursos disponíveis e prioridades políticas. "
            "Se você tiver dúvidas específicas sobre a disponibilidade de "
            "determinados dados, recomendo que entre em contato diretamente "
            "com as autoridades governamentais responsáveis pela gestão de dados "
            "no Brasil para obter informações mais detalhadas."
        )

        return CallToolResult(
            content=[TextContent(type="text", text=response)],
            structuredContent={"sources": [], "force": response},
        )

    @mcp.tool()
    def emendas_por_localidade(localidade: str, ano: int | None = None, historico: bool = False) -> DataToolOutput:
        """Get parliamentary amendments (emendas parlamentares) for a given location
        (localidade_de_aplicacao_do_recurso).

        By default returns only the freshest year available for the location. The response
        ends with a verbatim note telling the user which year is shown and how to ask for
        history. Pass historico=True (as a follow-up) for the full yearly view, or ano=YYYY
        for a specific year.

        Shows valor_empenhado, valor_liquidado and valor_pago totals.
        If the location name matches multiple entries, returns results for all of them.

        Args:
            localidade: Location name to filter by, e.g. "Pilar", "São Paulo", or "PILAR - PB".
                        Supports partial matching at the start of the name.
            ano: Year to filter by, e.g. 2024. If None (default), shows the latest year that
                 actually has data for the location.
            historico: If True, return ALL years (full history). Overrides `ano`. Use as a
                 follow-up when the user asks for the history.

        Returns:
            A summary of parliamentary amendments for the given location, with a table and
            bar chart of empenhado/liquidado/pago, plus a verbatim note about the year shown.
            If no results are found, returns a force message.

        Examples:
            - emendas_por_localidade(localidade="Pilar")
            - emendas_por_localidade(localidade="São Paulo", ano=2024)
            - emendas_por_localidade(localidade="São Paulo", historico=True)
        """
        return emendas.emendas_por_localidade(localidade, ano=ano, historico=historico)

    @mcp.tool()
    def quem_envia_emendas(localidade: str, ano: int | None = None, historico: bool = False) -> DataToolOutput:
        """Returns a ranking of parliamentary amendment authors (nome_do_autor_da_emenda)
        for a given location (localidade_de_aplicacao_do_recurso), sorted by total
        valor_empenhado descending.

        By default returns only the freshest year available for the location. The response
        ends with a verbatim note telling the user which year is shown and how to ask for
        history. Pass historico=True (as a follow-up) for the all-time ranking, or ano=YYYY
        for a specific year.

        Args:
            localidade: Location name to filter by, e.g. "Pilar", "São Paulo", or "PILAR - PB".
                        Supports partial matching at the start of the name.
            ano: Year to filter by, e.g. 2024. If None (default), shows the latest year that
                 actually has data for the location.
            historico: If True, aggregate ALL years (all-time ranking). Overrides `ano`. Use as a
                 follow-up when the user asks for the history.

        Returns:
            A ranking of amendment authors for the given location, showing how many
            emendas each authored and the total empenhado/liquidado/pago. Includes a table
            and a horizontal bar chart, plus a verbatim note about the year shown.
            If no results are found, returns a force message.

        Examples:
            - quem_envia_emendas(localidade="Pilar")
            - quem_envia_emendas(localidade="São Paulo", ano=2024)
            - quem_envia_emendas(localidade="São Paulo", historico=True)
        """
        return emendas.quem_envia_emendas(localidade, ano=ano, historico=historico)

    @mcp.tool()
    def top_favorecidos_das_emendas(limit: int, ano: int | None = None, historico: bool = False) -> DataToolOutput:
        """Returns which recipients (favorecidos) received the most money from parliamentary
        amendments, ranked by total valor_recebido.

        By default returns only the freshest year available. The response ends with a verbatim
        note telling the user which year is shown and how to ask for history. Pass
        historico=True (as a follow-up) for the all-time ranking, or ano=YYYY for a specific year.

        Args:
            limit: Maximum number of recipients to return, e.g. 10.
            ano: Year to filter by, e.g. 2024. If None (default), shows the latest year that
                 actually has data.
            historico: If True, aggregate ALL years (all-time ranking). Overrides `ano`. Use as a
                 follow-up when the user asks for the history.

        Returns:
            A ranking of top recipients of parliamentary amendment funds, showing the
            total valor_recebido, natureza_juridica, tipo_favorecido and number of emendas
            per favorecido. Includes a table and a horizontal bar chart, plus a verbatim note
            about the year shown.

        Examples:
            - top_favorecidos_das_emendas(limit=10)
            - top_favorecidos_das_emendas(limit=20, historico=True)
        """
        return emendas.top_favorecidos_das_emendas(limit, ano=ano, historico=historico)

    @mcp.tool()
    def emendas_por_localidade_e_funcao(localidade: str, funcao: str,
                                        ano: int | None = None, historico: bool = False) -> DataToolOutput:
        """Returns the amounts of parliamentary amendments for a given location
        (localidade_de_aplicacao_do_recurso) filtered by a specific funcao (government
        function), grouped by subfuncao and year.

        Use list_funcao() to discover available funcao values.

        By default returns only the freshest year available for the location+function. The
        response ends with a verbatim note telling the user which year is shown and how to ask
        for history. Pass historico=True (as a follow-up) for the full yearly view, or
        ano=YYYY for a specific year.

        Args:
            localidade: Location name to filter by, e.g. "Pilar", "São Paulo", or "PILAR - PB".
                        Supports partial matching at the start of the name.
            funcao: Government function name to filter by, e.g. "Saúde", "Educação",
                    "Assistência Social". Case-insensitive match.
            ano: Year to filter by, e.g. 2024. If None (default), shows the latest year that
                 actually has data for the location+function.
            historico: If True, return ALL years (full history). Overrides `ano`. Use as a
                 follow-up when the user asks for the history.

        Returns:
            A breakdown of parliamentary amendments for the given location and function,
            grouped by subfunction and year. Shows valor_empenhado, valor_liquidado and
            valor_pago totals, plus a verbatim note about the year shown.
            If the location or function is not found, returns a force message with
            suggestions of available funcoes.

        Examples:
            - emendas_por_localidade_e_funcao(localidade="Pilar", funcao="Saúde")
            - emendas_por_localidade_e_funcao(localidade="São Paulo", funcao="Educação", historico=True)
        """
        return emendas.emendas_por_localidade_e_funcao(localidade, funcao, ano=ano, historico=historico)

    @mcp.tool()
    def list_funcao() -> DataToolOutput:
        """List all available funcao (government functions) in the emendas dataset.

        Use this to discover which funcao values can be passed to
        emendas_por_localidade_e_funcao().

        Returns:
            A table of all distinct funcao values in the parliamentary amendments dataset,
            with the number of emendas and total valor_empenhado, valor_liquidado and
            valor_pago per funcao. Includes a horizontal bar chart.

        Examples:
            - list_funcao()
        """
        return emendas.list_funcao()

    @mcp.tool()
    def emendas_por_autor(autor: str, ano: int | None = None, historico: bool = False) -> DataToolOutput:
        """Returns parliamentary amendments (emendas parlamentares) authored by a given
        author (nome_do_autor_da_emenda), grouped by year and municipality.

        By default returns only the freshest year available for the author. The response
        ends with a verbatim note telling the user which year is shown and how to ask for
        history. Pass historico=True (as a follow-up) for the full yearly view, or ano=YYYY
        for a specific year.

        Shows valor_empenhado, valor_liquidado and valor_pago totals per year/municipio.
        Uses case-insensitive partial matching for the author name.

        Args:
            autor: Author name to filter by, e.g. "ABILIO SANTANA" or "ABEL MESQUITA".
                   Case-insensitive partial match supported.
            ano: Year to filter by, e.g. 2024. If None (default), shows the latest year that
                 actually has data for the author.
            historico: If True, return ALL years (full history). Overrides `ano`. Use as a
                 follow-up when the user asks for the history.

        Returns:
            A summary of parliamentary amendments authored by the given author,
            grouped by year and municipality, with a table and bar chart of
            empenhado/liquidado/pago, plus a verbatim note about the year shown.
            If no results are found, returns a force message with suggestions.

        Examples:
            - emendas_por_autor(autor="ABILIO SANTANA")
            - emendas_por_autor(autor="ABEL MESQUITA", ano=2022)
            - emendas_por_autor(autor="ABEL MESQUITA", historico=True)
        """
        return emendas.emendas_por_autor(autor, ano=ano, historico=historico)

    @mcp.tool()
    def list_subfuncao() -> DataToolOutput:
        """List all available subfuncao (government sub-functions) in the emendas dataset.

        Returns:
            A table of all distinct subfuncao values in the parliamentary amendments dataset,
            with the number of emendas and total valor_empenhado, valor_liquidado and
            valor_pago per subfuncao. Includes a horizontal bar chart.

        Examples:
            - list_subfuncao()
        """
        return emendas.list_subfuncao()

    @mcp.tool()
    def favorecidos_por_autor(autor: str, limit: int = 20,
                              ano: int | None = None, historico: bool = False) -> DataToolOutput:
        """Returns the top recipients (favorecidos) of parliamentary amendments from a given
        author (nome_do_autor_da_emenda), ranked by total valor_recebido descending.

        Uses case-insensitive partial matching for the author name.

        By default returns only the freshest year available for the author. The response ends
        with a verbatim note telling the user which year is shown and how to ask for history.
        Pass historico=True (as a follow-up) for the all-time ranking, or ano=YYYY for a
        specific year.

        Args:
            autor: Author name to filter by, e.g. "ABILIO SANTANA" or "ABEL MESQUITA".
                   Case-insensitive partial match supported.
            limit: Maximum number of recipients to return. Defaults to 20.
            ano: Year to filter by, e.g. 2024. If None (default), shows the latest year that
                 actually has data for the author.
            historico: If True, aggregate ALL years (all-time ranking). Overrides `ano`. Use as a
                 follow-up when the user asks for the history.

        Returns:
            A ranking of top recipients of amendment funds from the given author, showing
            the favorecido name, natureza_juridica, tipo_favorecido, municipio, UF,
            number of emendas and total valor_recebido. Includes a table and a horizontal
            bar chart, plus a verbatim note about the year shown.
            If no author is found, returns a force message with suggestions.

        Examples:
            - favorecidos_por_autor(autor="ABILIO SANTANA")
            - favorecidos_por_autor(autor="LULA DA FONTE", limit=10, historico=True)
        """
        return emendas.favorecidos_por_autor(autor, limit, ano=ano, historico=historico)

    @mcp.tool()
    def buscar_favorecido(nome_favorecido: str, limit: int = 10) -> DataToolOutput:
        """Search for favorecidos (recipients of parliamentary amendments) by approximate name.

        Use this when the exact favorecido name is unknown or misspelled, to find the
        correct name before calling other tools.

        Args:
            nome: Name (or partial name) to search for, e.g. "BANCO DO BRASIL"
                  or "FUNDO MUNICIPAL". Case-insensitive partial match supported.
            limit: Maximum number of results to return. Defaults to 10.

        Returns:
            A table of favorecidos matching the (possibly partial) name, each with its
            natureza_juridica, tipo_favorecido, municipio, UF, number of emendas and
            total valor_recebido.
            If no results are found, returns a force message.

        Examples:
            - buscar_favorecido(nome_favorecido="BANCO DO BRASIL")
            - buscar_favorecido(nome_favorecido="FUNDO MUNICIPAL DE SAUDE")
        """
        return emendas.buscar_favorecido(nome_favorecido, limit)

    @mcp.tool()
    def top_autores_das_emendas(limit: int = 10, ano: int | None = None,
                                historico: bool = False) -> DataToolOutput:
        """Returns the top authors (nome_do_autor_da_emenda) of parliamentary amendments,
        ranked by total valor_empenhado descending.

        This answers questions like "which representative allocated the most in amendments?"
        or "who are the top emenda authors?".

        By default returns only the freshest year available. The response ends with a verbatim
        note telling the user which year is shown and how to ask for history. Pass
        historico=True (as a follow-up) for the all-time ranking, or ano=YYYY for a specific year.

        Args:
            limit: Maximum number of authors to return, e.g. 10.
            ano: Year to filter by, e.g. 2024. If None (default), shows the latest year that
                 actually has data.
            historico: If True, aggregate ALL years (all-time ranking). Overrides `ano`. Use as a
                 follow-up when the user asks for the history.

        Returns:
            A ranking of top parliamentary amendment authors, showing the author name,
            number of emendas, total valor_empenhado, valor_liquidado and valor_pago.
            Includes a table and a horizontal bar chart, plus a verbatim note about the year
            shown.

        Examples:
            - top_autores_das_emendas(limit=10)
            - top_autores_das_emendas(limit=20, historico=True)
            - top_autores_das_emendas(limit=20, ano=2024)
        """
        return emendas.top_autores_das_emendas(limit, ano, historico)

    @mcp.tool()
    def detalhe_emendas_por_autor(autor: str, ano: int | None = None, limit: int = 30,
                                  historico: bool = False) -> DataToolOutput:
        """Returns individual emenda records for a given author with full detail (funcao,
        subfuncao, programa, acao, municipio, and all valor columns).

        Unlike emendas_por_autor which aggregates by year/municipio, this shows each
        individual emenda with its complete detail.

        By default returns only the freshest year available for the author. The response ends
        with a verbatim note telling the user which year is shown and how to ask for history.
        Pass historico=True (as a follow-up) to see records across all years, or ano=YYYY for
        a specific year.

        Args:
            autor: Author name to filter by, e.g. "ABILIO SANTANA" or "ABEL MESQUITA".
                   Case-insensitive partial match supported.
            ano: Year to filter by, e.g. 2024. If None (default), shows the latest year that
                 actually has data for the author.
            limit: Maximum number of emenda records to return. Defaults to 30.
            historico: If True, return records from ALL years (ordered by most recent).
                 Overrides `ano`. Use as a follow-up when the user asks for the history.

        Returns:
            A detailed list of individual parliamentary amendments for the given author,
            with full detail columns, plus a verbatim note about the year shown.
            Returns a table of results.
            If no author is found, returns a force message with suggestions.

        Examples:
            - detalhe_emendas_por_autor(autor="ABILIO SANTANA")
            - detalhe_emendas_por_autor(autor="LULA DA FONTE", ano=2025, limit=10)
            - detalhe_emendas_por_autor(autor="LULA DA FONTE", historico=True)
        """
        return emendas.detalhe_emendas_por_autor(autor, ano, limit, historico)

    @mcp.tool()
    def glossary(concept: str) -> DataToolOutput:
        """Returns the official definition of a concept.

        This tool contains all the relevant concepts and metadata required to understand
        the information returned by the other tools.

        Args:
            concept: The key of a specific term or concept, e.g. "natureza_juridica" or "valor_liquidado".

        Returns:
            A definition of the concept. If no concept is found, it returns a list of all
            available concepts.

        Examples:
            - glossary("natureza_juridica")
            - glossary("valor_liquidado")
        """
        return emendas_glossary.glossary(concept)


def main() -> None:
    print("Hello from mcp-dados-brasil")
