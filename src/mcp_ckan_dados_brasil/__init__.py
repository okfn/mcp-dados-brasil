

def register_tools(mcp):

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
