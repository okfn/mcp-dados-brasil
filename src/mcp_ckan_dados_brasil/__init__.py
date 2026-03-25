from mcp_ckan_dados_brasil.datasets import bolsa_familia
from mcp_ckan_dados_brasil.datasets import municipios


def register_tools(mcp):

    @mcp.tool()
    def bolsa_familia_list(
        municipio: str = None, codigo_ibge: int = None,
        year: int = 2026, limit: int = 20, state: str = None,
        order_by: str = None
    ) -> str:
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
            str: Formatted list of Bolsa Família records.

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
    def buscar_municipio(nome: str, limit: int = 10):
        """Search for Brazilian municipalities by approximate name. Use this when the exact
            municipality name is unknown or misspelled, to find the correct name before
            calling bolsa_familia_list.

        Args:
            nome: Name (or partial/misspelled name) to search for, e.g. "Poto Velho".
            limit: Maximum number of suggestions to return. Defaults to 10.

        Returns:
            str: List of matching municipality names with UF and IBGE codes.

        Examples:
            - buscar_municipio(nome="Poto Velho")
            - buscar_municipio(nome="San Pablo")
        """
        return municipios.buscar_municipio(nome=nome, limit=limit)

    @mcp.tool()
    def political_questions(country=None):
        """ To anwer when people ask about political questions that are not answerable with data,
            but are common questions about Brasil Government.
            For example: "Why is X data not available?" or "What did the Gobvernment open this data in this way?"

        Returns:
            str: A formatted response

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

        return response


def main() -> None:
    print("Hello from mcp-ckan-dados-brasil")
