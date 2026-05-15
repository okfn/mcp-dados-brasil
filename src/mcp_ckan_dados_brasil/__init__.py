from mcp.types import CallToolResult, TextContent
from mcp_server import DataToolOutput

from mcp_ckan_dados_brasil.datasets import bolsa_familia
from mcp_ckan_dados_brasil.datasets import municipios
from mcp_ckan_dados_brasil.emendas import tools as emendas


def register_tools(mcp):

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

    # @mcp.tool()
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
    def emendas_por_municipio(municipio: str) -> DataToolOutput:
        """Get parliamentary amendments (emendas parlamentares) for a given municipality,
        grouped by year.

        Shows valor_empenhado, valor_liquidado and valor_pago totals per year.
        If the municipality name matches multiple states, returns results for all of them.

        Args:
            municipio: Municipality name to filter by, e.g. "Pilar" or "São Paulo".

        Returns:
            A summary of parliamentary amendments for the given municipality, grouped by
            year, with a table and bar chart of empenhado/liquidado/pago per year.
            If no results are found, returns a force message.

        Examples:
            - emendas_por_municipio(municipio="Pilar")
            - emendas_por_municipio(municipio="São Paulo")
        """
        return emendas.emendas_por_municipio(municipio)

    @mcp.tool()
    def quem_envia_emendas(municipio: str) -> DataToolOutput:
        """Returns a ranking of parliamentary amendment authors (nome_do_autor_da_emenda)
        for a given municipality, sorted by total valor_empenhado descending.

        Args:
            municipio: Municipality name to filter by, e.g. "Pilar" or "São Paulo".

        Returns:
            A ranking of amendment authors for the given municipality, showing how many
            emendas each authored and the total empenhado/liquidado/pago. Includes a table
            and a horizontal bar chart.
            If no results are found, returns a force message.

        Examples:
            - quem_envia_emendas(municipio="Pilar")
            - quem_envia_emendas(municipio="São Paulo")
        """
        return emendas.quem_envia_emendas(municipio)

    @mcp.tool()
    def top_favorecidos_das_emendas(limit: int) -> DataToolOutput:
        """Returns which recipients (favorecidos) received the most money from parliamentary
        amendments, ranked by total valor_recebido.

        Args:
            limit: Maximum number of recipients to return, e.g. 10.

        Returns:
            A ranking of top recipients of parliamentary amendment funds, showing the
            total valor_recebido, natureza_juridica, tipo_favorecido and number of emendas
            per favorecido. Includes a table and a horizontal bar chart.

        Examples:
            - top_favorecidos_das_emendas(limit=10)
            - top_favorecidos_das_emendas(limit=20)
        """
        return emendas.top_favorecidos_das_emendas(limit)

    @mcp.tool()
    def emendas_a_municipio_por_funcao(municipio: str, funcao: str) -> DataToolOutput:
        """Returns the amounts of parliamentary amendments for a given municipality filtered
        by a specific funcao (government function), grouped by subfuncao and year.

        Use list_funcao() to discover available funcao values.

        Args:
            municipio: Municipality name to filter by, e.g. "Pilar" or "São Paulo".
            funcao: Government function name to filter by, e.g. "Saúde", "Educação",
                    "Assistência Social". Case-insensitive match.

        Returns:
            A breakdown of parliamentary amendments for the given municipality and function,
            grouped by subfunction and year. Shows valor_empenhado, valor_liquidado and
            valor_pago totals.
            If the municipality or function is not found, returns a force message with
            suggestions of available funcoes.

        Examples:
            - emendas_a_municipio_por_funcao(municipio="Pilar", funcao="Saúde")
            - emendas_a_municipio_por_funcao(municipio="São Paulo", funcao="Educação")
        """
        return emendas.emendas_a_municipio_por_funcao(municipio, funcao)

    @mcp.tool()
    def list_funcao() -> DataToolOutput:
        """List all available funcao (government functions) in the emendas dataset.

        Use this to discover which funcao values can be passed to
        emendas_a_municipio_por_funcao().

        Returns:
            A table of all distinct funcao values in the parliamentary amendments dataset,
            with the number of emendas and total valor_empenhado, valor_liquidado and
            valor_pago per funcao. Includes a horizontal bar chart.

        Examples:
            - list_funcao()
        """
        return emendas.list_funcao()

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


def main() -> None:
    print("Hello from mcp-ckan-dados-brasil")
