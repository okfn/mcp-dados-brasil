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
        return emendas.emendas_por_municipio(municipio)

    @mcp.tool()
    def quem_envia_emendas(municipio: str) -> DataToolOutput:
        return emendas.quem_envia_emendas(municipio)

    @mcp.tool()
    def top_favorecidos_das_emendas(limit: int) -> DataToolOutput:
        return emendas.top_favorecidos_das_emendas(limit)

    @mcp.tool()
    def emendas_a_municipio_por_funcao(municipio: str, funcao: str) -> DataToolOutput:
        return emendas.emendas_a_municipio_por_funcao(municipio, funcao)

    @mcp.tool()
    def list_funcao() -> DataToolOutput:
        return emendas.list_funcao()

    @mcp.tool()
    def list_subfuncao() -> DataToolOutput:
        return emendas.list_subfuncao()

def main() -> None:
    print("Hello from mcp-ckan-dados-brasil")
