from mcp.types import CallToolResult, TextContent
from mcp_server import DataToolOutput

from mcp_dados_brasil.emendas import glossary as emendas_glossary
from mcp_dados_brasil.emendas import tools as emendas


def register_tools(mcp):

    mcp.set_plugin_info(
        description=(
            "Ferramentas sobre dados abertos do Brasil (https://dados.gov.br)"
        ),
        instructions=(
            "Você é um assistente especializado EXCLUSIVAMENTE em emendas "
            "parlamentares do Brasil. Fonte única: o Portal da Transparência "
            "da Controladoria-Geral da União "
            "(https://portaldatransparencia.gov.br), com os dados de emendas "
            "parlamentares (autor da emenda, localidade de aplicação do "
            "recurso, função e subfunção de governo, favorecidos e os valores "
            "empenhado, liquidado e pago).\n"
            "- Responda SOMENTE sobre emendas parlamentares do Brasil e "
            "SOMENTE com os dados destas tools. Nada de outros países, outros "
            "temas, nem conhecimento próprio.\n"
            "- Não confunda os valores: valor_empenhado != valor_liquidado != "
            "valor_pago. Use a tool e a coluna que correspondem ao que foi "
            "perguntado; consulte glossary para a definição exata de cada "
            "termo.\n"
            "- Para perguntas políticas ou sobre decisões de governo que não "
            "se respondem com dados, chame political_questions.\n"
            "- Se a pergunta não for sobre emendas parlamentares do Brasil, "
            "ou se nenhuma tool a cobrir, chame nenhuma_ferramenta_disponivel "
            "com o motivo; não improvise com uma tool que não se aplica."
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
            "Qual foi o total empenhado na ação orçamentária 0EC2 em 2025?",
            "Histórico da ação orçamentária 2E89",
            "Emendas da ação orçamentária 0EC2 para São Paulo",
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

    @mcp.tool()
    def nenhuma_ferramenta_disponivel(motivo: str | None = None) -> DataToolOutput:
        """Chame **apenas** quando nenhuma outra tool puder responder à
            pergunta: temas que não são emendas parlamentares do Brasil
            (outros países, clima, esportes, etc.), ou perguntas fora do
            alcance dos dados de emendas. **Nunca** use se houver uma tool de
            dados que possa contribuir, ainda que parcialmente - prefira
            sempre a tool específica. Para perguntas políticas ou sobre
            decisões de governo que não se respondem com dados use
            political_questions, não esta tool.
            Define o alcance DESTA instância: somente emendas parlamentares do
            Brasil (Portal da Transparência / CGU). Emite uma mensagem padrão
            dizendo ao usuário que o sistema não cobre esse tema.

        Args:
            motivo: Breve explicação (1 frase) de por que nenhuma tool se
                aplica. Ex: "pergunta sobre o Uruguai, não o Brasil", "não é
                um tema de emendas parlamentares". É incluído na mensagem para
                que o usuário entenda o alcance.

        Examples:
            - nenhuma_ferramenta_disponivel(motivo="pergunta sobre clima, não emendas")
            - nenhuma_ferramenta_disponivel(motivo="dados do Uruguai, esta instância é BR")
        """
        msg = (
            "Esta instância responde unicamente sobre emendas parlamentares "
            "do Brasil, com dados do Portal da Transparência da "
            "Controladoria-Geral da União (https://portaldatransparencia.gov.br)."
        )
        if motivo:
            msg += f" Motivo: {motivo}."
        msg += " Para outros temas ou países, consulte outra fonte."
        return CallToolResult(
            content=[TextContent(type="text", text=msg)],
            structuredContent={"sources": []},
        )

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
    def emendas_por_localidade_e_tipo(localidade: str, tipo_de_emenda: str,
                                      ano: int | None = None, historico: bool = False) -> DataToolOutput:
        """Returns the amounts of parliamentary amendments for a given location
            (localidade_de_aplicacao_do_recurso) filtered by a specific tipo_de_emenda
            (amendment type), grouped by year and location.

            Use list_tipo_de_emenda() to discover available tipo_de_emenda values.

            By default returns only the freshest year available for the location+type. The
            response ends with a verbatim note telling the user which year is shown and how to ask
            for history. Pass historico=True (as a follow-up) for the full yearly view, or
            ano=YYYY for a specific year.

        Args:
            localidade: Location name to filter by, e.g. "Pilar", "São Paulo", or "PILAR - PB".
                        Supports partial matching at the start of the name.
            tipo_de_emenda: Amendment type to filter by, e.g. "Emenda Individual - Transferências
                            com Finalidade Definida" or "Emenda de Bancada". Case-insensitive match.
            ano: Year to filter by, e.g. 2024. If None (default), shows the latest year that
                 actually has data for the location+type.
            historico: If True, return ALL years (full history). Overrides `ano`. Use as a
                 follow-up when the user asks for the history.

        Returns:
            A breakdown of parliamentary amendments for the given location and amendment type,
            grouped by year. Shows valor_empenhado, valor_liquidado and valor_pago totals,
            plus a verbatim note about the year shown.
            If the location or amendment type is not found, returns a force message with
            suggestions of available tipos.

        Examples:
            - emendas_por_localidade_e_tipo(localidade="Pilar", tipo_de_emenda="Emenda de Bancada")
            - emendas_por_localidade_e_tipo(localidade="São Paulo", tipo_de_emenda="Emenda de Relator", historico=True)
        """
        return emendas.emendas_por_localidade_e_tipo(localidade, tipo_de_emenda, ano=ano, historico=historico)

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
    def list_tipo_de_emenda() -> DataToolOutput:
        """List all available tipo_de_emenda (amendment types) in the emendas dataset.

        Use this to discover which tipo_de_emenda values can be passed to
        emendas_por_localidade_e_tipo().

        Returns:
            A table of all distinct tipo_de_emenda values in the parliamentary amendments
            dataset, with the number of emendas and total valor_empenhado, valor_liquidado and
            valor_pago per tipo_de_emenda. Includes a horizontal bar chart.

        Examples:
            - list_tipo_de_emenda()
        """
        return emendas.list_tipo_de_emenda()

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
    def list_acao() -> DataToolOutput:
        """List all available acao (ações orçamentárias) in the emendas dataset.

        Use this to discover which codigo_acao (e.g. "0EC2") and nome_acao values can
        be passed to emendas_por_acao().

        Returns:
            A table of all distinct acao values in the parliamentary amendments dataset,
            with the codigo_acao, nome_acao, number of emendas and total
            valor_empenhado, valor_liquidado and valor_pago per acao. Includes a
            horizontal bar chart.

        Examples:
            - list_acao()
        """
        return emendas.list_acao()

    @mcp.tool()
    def emendas_por_acao(acao: str, ano: int | None = None, historico: bool = False) -> DataToolOutput:
        """Returns the amounts of parliamentary amendments (emendas parlamentares) for a
        given ação orçamentária (codigo_acao / nome_acao), grouped by year.

        Use list_acao() to discover available codigo_acao and nome_acao values.

        By default returns only the freshest year available for the ação. The response ends
        with a verbatim note telling the user which year is shown and how to ask for history.
        Pass historico=True (as a follow-up) for the full yearly view, or ano=YYYY for a
        specific year.

        Shows valor_empenhado, valor_liquidado and valor_pago totals.
        Accepts either the codigo_acao (e.g. "0EC2") or the nome_acao
        (e.g. "TRANSFERENCIAS ESPECIAIS"), case-insensitive, with partial name matching.

        Args:
            acao: Ação orçamentária to filter by. Accepts either the codigo_acao
                  (e.g. "0EC2") or the nome_acao (e.g. "TRANSFERENCIAS ESPECIAIS").
                  Case-insensitive; partial name matching supported.
            ano: Year to filter by, e.g. 2025. If None (default), shows the latest year that
                 actually has data for the ação.
            historico: If True, return ALL years (full history). Overrides `ano`. Use as a
                 follow-up when the user asks for the history.

        Returns:
            A summary of parliamentary amendments for the given ação orçamentária, with a
            table and bar chart of empenhado/liquidado/pago, plus a verbatim note about the
            year shown. If the ação is not found, returns a force message with suggestions.

        Examples:
            - emendas_por_acao(acao="0EC2")
            - emendas_por_acao(acao="0EC2", ano=2025)
            - emendas_por_acao(acao="TRANSFERENCIAS ESPECIAIS", historico=True)
        """
        return emendas.emendas_por_acao(acao, ano=ano, historico=historico)

    @mcp.tool()
    def emendas_por_localidade_e_acao(localidade: str, acao: str,
                                      ano: int | None = None, historico: bool = False) -> DataToolOutput:
        """Returns the amounts of parliamentary amendments for a given location
        (localidade_de_aplicacao_do_recurso) filtered by a specific ação orçamentária
        (codigo_acao / nome_acao), grouped by year.

        Use list_acao() to discover available codigo_acao and nome_acao values.

        By default returns only the freshest year available for the location+ação. The
        response ends with a verbatim note telling the user which year is shown and how to
        ask for history. Pass historico=True (as a follow-up) for the full yearly view, or
        ano=YYYY for a specific year.

        Shows valor_empenhado, valor_liquidado and valor_pago totals.
        Accepts either the codigo_acao (e.g. "0EC2") or the nome_acao
        (e.g. "TRANSFERENCIAS ESPECIAIS"), case-insensitive, with partial name matching.

        Args:
            localidade: Location name to filter by, e.g. "Pilar", "São Paulo", or "PILAR - PB".
                        Supports partial matching at the start of the name.
            acao: Ação orçamentária to filter by. Accepts either the codigo_acao
                  (e.g. "0EC2") or the nome_acao (e.g. "TRANSFERENCIAS ESPECIAIS").
                  Case-insensitive; partial name matching supported.
            ano: Year to filter by, e.g. 2025. If None (default), shows the latest year that
                 actually has data for the location+ação.
            historico: If True, return ALL years (full history). Overrides `ano`. Use as a
                 follow-up when the user asks for the history.

        Returns:
            A breakdown of parliamentary amendments for the given location and ação
            orçamentária, grouped by year. Shows valor_empenhado, valor_liquidado and
            valor_pago totals, plus a verbatim note about the year shown.
            If the location or ação is not found, returns a force message with suggestions.

        Examples:
            - emendas_por_localidade_e_acao(localidade="São Paulo", acao="0EC2")
            - emendas_por_localidade_e_acao(localidade="Pilar", acao="0EC2", ano=2024)
            - emendas_por_localidade_e_acao(localidade="Pilar", acao="TRANSFERENCIAS ESPECIAIS", historico=True)
        """
        return emendas.emendas_por_localidade_e_acao(localidade, acao, ano=ano, historico=historico)

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
