"""
Glosarry Tool.

A tool used to answer questions regarding concepts and terms of the datasets.
"""

from mcp_server import DataToolOutput
from mcp_server.results import text_result

SOURCE = "https://portaldatransparencia.gov.br/dicionario-de-dados/emendas-parlamentares"

GLOSSARY = {
    "codigo_da_emenda": {
        "name": "Código da Emenda",
        "definition": (
            "Identificador da emenda parlamentar, composto por 12 dígitos: 4 do ano da "
            "emenda + 4 do código do autor + 4 do número da emenda do autor."
        ),
    },
    "ano_da_emenda": {
        "name": "Ano da Emenda",
        "definition": "Ano em que emenda foi proposta.",
    },
    "tipo_da_emenda": {
        "name": "Tipo da Emenda",
        "definition": "Descreve o tipo de emenda parlamentar.",
    },
    "codigo_do_autor_da_emenda": {
        "name": "Código do Autor da Emenda",
        "definition": (
            "Código do autor da emenda parlamentar, conforme registrado no Sistema de "
            "Administração Financeira do Governo Federal - SIAFI."
            ),
    },
    "nome_do_autor_da_emenda": {
        "name": "Nome do Autor da Emenda",
        "definition": (
            "Nome do autor da emenda parlamentar, conforme registrado no Sistema "
            "de Administração Financeira do Governo Federal - SIAFI."
            ),
    },
    "numero_da_emenda": {
        "name": "Número da Emenda",
        "definition": (
            "Número da emenda parlamentar, conforme registrado no Sistema de Administração "
            "Financeira do Governo Federal - SIAFI."
            ),
    },
    "localidade_do_gasto": {
        "name": "Localidade do Gasto",
        "definition": (
            "Atributo do Plano de Trabalho que indica, durante a execução da despesa, a "
            "região onde a despesa ocorre."
            "Para municípios, o formato é 'NOME DO MUNICÍPIO - UF' (ex: 'PILAR - PB'). "
            "Para aplicações em nível estadual, o formato é 'NOME DO ESTADO (UF)' (ex: 'SERGIPE (UF)'). "
            "Este campo está sempre preenchido, ao contrário do campo 'municipio' que pode estar em branco "
            "para aplicações de escopo estadual ou regional."
            ),
    },
    "codigo_municipio_ibge": {
        "name": "Código Município IBGE",
        "definition": (
            "Código IBGE do município de destinação do recurso. Este campo poderá estar em branco, "
            "a depender da localidade de aplicação."
            ),
    },
    "municipio": {
        "name": "Município",
        "definition": (
            "Nome do município de destinação do recurso. Este campo poderá estar em branco, a "
            "depender da localidade de aplicação."
            ),
    },
    "codigo_uf_ibge": {
        "name": "Código UF IBGE",
        "definition": (
            "Código IBGE do estado de destinação do recurso. Este campo poderá estar em branco, "
            "a depender da localidade de aplicação."
            ),
    },
    "uf": {
        "name": "UF",
        "definition": (
            "Nome do estado de destinação do recurso. Este campo poderá estar sem informação, a "
            "depender da localidade de aplicação."
            ),
    },
    "regiao": {"name": "Região", "definition": "Região de destinação do recurso."},
    "codigo_funcao": {
        "name": "Código Função",
        "definition": (
            "Código da Função em que foi classificada a despesa associada à emenda parlamentar. "
            "Função - Representa o maior nível de agregação das diversas áreas de atuação do setor público. "
            "Reflete a competência institucional do órgão, como, por exemplo, cultura, educação, saúde, defesa, "
            "que guarda relação com os respectivos Ministérios. Fonte: Manual Técnico do Orçamento."
            ),
    },
    "nome_funcao": {
        "name": "Nome Função",
        "definition": "Nome da Função em que foi classificada a despesa associada à emenda parlamentar.",
    },
    "codigo_subfuncao": {
        "name": "Código Subfunção",
        "definition": (
            "Código da Subfunção em que foi classificada a despesa associada à emenda parlamentar. "
            "Subfunção - representa um nível de agregação imediatamente inferior à função e deve evidenciar "
            "a natureza da atuação governamental. De acordo com a Portaria no 42, de 14 de abril de 1999, "
            "é possível combinar as subfunções a funções diferentes daquelas a elas diretamente relacionadas, "
            "o que se denomina matricialidade. Fonte: Manual Técnico do Orçamento."
            ),
    },
    "nome_subfuncao": {
        "name": "Nome Subfunção",
        "definition": "Nome da subfunção em que foi classificada a despesa associada à emenda parlamentar.",
    },
    "codigo_programa": {
        "name": "Código Programa",
        "definition": (
            "Código do Programa em que foi classificada a despesa. Toda ação do Governo está estruturada "
            "em programas orientados para a realização dos objetivos estratégicos definidos para o período "
            "do PPA, ou seja, quatro anos. Programa Temático: aquele que expressa e orienta a ação governamental "
            "para a entrega de bens e serviços à sociedade. Programa de Gestão, Manutenção e Serviços ao Estado: "
            "aquele que expressa e orienta as ações destinadas ao apoio, à gestão e à manutenção da atuação "
            "governamental. Fonte: Manual Técnico do Orçamento."
            ),
    },
    "nome_programa": {
        "name": "Nome Programa",
        "definition": "Nome do Programa em que foi classificada a despesa. Fonte: Manual Técnico do Orçamento.",
    },
    "codigo_acao": {
        "name": "Código Ação",
        "definition": (
            "Código da Ação Orçamentária em que foi classificada a despesa. Ação Orçamentária: Operação da qual "
            "resultam produtos (bens ou serviços) que contribuem para atender ao objetivo de um programa. "
            "Incluem-se também no conceito de ação as transferências obrigatórias ou voluntárias a outros entes "
            "da Federação e a pessoas físicas e jurídicas, na forma de subsídios, subvenções, auxílios, contribuições, "
            "entre outros, e os financiamentos. Fonte: Manual Técnico do Orçamento."
            ),
    },
    "nome_acao": {
        "name": "Nome Ação",
        "definition": "Nome da ação orçamentária em que foi classificada a despesa.",
    },
    "codigo_plano_orcamentario": {
        "name": "Código Plano Orçamentário",
        "definition": (
            "Código do Plano Orçamentário (PO). O PO é uma identificação orçamentária, de caráter gerencial "
            "(não constante da LOA), vinculada à ação orçamentária, que tem por finalidade permitir que, tanto a "
            "elaboração do orçamento quanto o acompanhamento físico e financeiro da execução, ocorram num nível mais "
            "detalhado do que o do subtítulo/localizador de gasto. Fonte: Manual Técnico do Orçamento."
            ),
    },
    "nome_plano_orcamentario": {
        "name": "Nome Plano Orçamentário",
        "definition": "Descrição do Plano Orçamentário.",
    },
    "valor_empenhado": {
        "name": "Valor Empenhado",
        "definition": (
            "Valor resultante da fase de empenho, que é o primeiro estágio da despesa. Consiste na reserva de dotação "
            "orçamentária, ou seja, reserva de valores monetários autorizados para atender um fim específico. O empenho "
            "é registrado no momento da contratação do serviço, aquisição do material ou bem, obra ou amortização da dívida"
            ),
    },
    "valor_liquidado": {
        "name": "Valor Liquidado",
        "definition": (
            "Valor resultante da fase de liquidação, segundo estágio da execução da despesa. Consiste na verificação do "
            "direito adquirido pelo credor, tendo por base os títulos e documentos comprobatórios do respectivo crédito. "
            "É nesse segundo estágio da execução da despesa que será cobrada a prestação dos serviços ou a entrega dos bens, "
            "ou ainda, a realização da obra. Envolve, portanto, todos os atos de verificação e conferência, desde a entrega "
            "do material ou a prestação do serviço até o reconhecimento da despesa"
        ),
    },
    "valor_pago": {
        "name": "Valor Pago",
        "definition": (
            "Valor resultante da fase de pagamento, último estágio da execução da despesa. "
            "É o valor efetivamente entregue ao credor. "
            "Esse pagamento normalmente é efetuado por meio de crédito em conta bancária do favorecido."
        ),
    },
    "valor_restos_a_pagar_inscritos": {
        "name": "Valor Restos A Pagar Inscritos",
        "definition": "Valor inscrito em restos a pagar para a emenda.",
    },
    "valor_restos_a_pagar_cancelados": {
        "name": "Valor Restos A Pagar Cancelados",
        "definition": "Valor cancelado das inscrições em restos a pagar para a emenda.",
    },
    "valor_restos_a_pagar_pagos": {
        "name": "Valor Restos A Pagar Pagos",
        "definition": "Valor pago em restos a pagar para a emenda.",
    },
    "data_publicacao_convenio": {
        "name": "Data Publicação Convênio",
        "definition": "Data de Publicação do convênio.",
    },
    "convenente": {
        "name": "Convenente",
        "definition": (
            "Órgão da administração direta, autárquica ou fundacional, empresa pública ou sociedade de economia mista, "
            "de qualquer esfera de governo, ou organização particular com a qual a administração federal pactua a execução "
            "de programa, projeto ou atividade, ou evento mediante a celebração de convênio. "
            "É quem recebe os recursos do Governo Federal."
            ),
    },
    "objeto_convenio": {
        "name": "Objeto Convênio",
        "definition": "Aquilo pactuado entre o Governo Federal concedente e o convenente beneficiado no município.",
    },
    "numero_convenio": {
        "name": "Número Convênio",
        "definition": "Número que identifica o convênio.",
    },
    "valor_convenio": {
        "name": "Valor Convênio",
        "definition": (
            "É o valor correspondente à participação do concedente. É adicionado ao valor original do convênio a "
            "parcela (999) que corresponde a rendimento de aplicação financeira, quando for o caso."
            ),
    },
    "ano_mes": {
        "name": "Ano/Mês",
        "definition": "Ano e mês em que foi realizado o lançamento.",
    },
    "codigo_do_favorecido": {
        "name": "Código do Favorecido",
        "definition": (
            "Código do favorecido do pagamento realizado. Favorecidos: Entes governamentais, entidades sem fins lucrativos, "
            "demais pessoas jurídicas ou pessoas físicas que receberam transferências de recursos públicos federais, "
            "independentemente da origem desses valores. Fonte: Controladoria-Geral da União."
            ),
    },
    "favorecido": {
        "name": "Favorecido",
        "definition": (
            "Nome do favorecido do pagamento realizado."
            "Serão chamados de Favorecidos os Órgãos ou Empresas Privadas e Pessoas Físicas que receberam "
            "recursos públicos federais."
            ),
    },
    "natureza_juridica": {
        "name": "Natureza Jurídica",
        "definition": "Natureza jurídica do favorecido.",
    },
    "tipo_favorecido": {
        "name": "Tipo Favorecido",
        "definition": "Informa se o favorecido é Pessoa Física ou Pessoa Jurídica.",
    },
    "uf_favorecido": {
        "name": "UF Favorecido",
        "definition": "Unidade Federativa do favorecido do recurso.",
    },
    "municipio_favorecido": {
        "name": "Município Favorecido",
        "definition": "Nome do município do favorecido do recurso.",
    },
    "valor_recebido": {
        "name": "Valor Recebido",
        "definition": "Valor recebido pelo favorecido.",
    },
    "emendas": {
        "name": "Emendas",
        "definition": (
            "As emendas feitas ao Orçamento Geral da União, denominado de Lei Orçamentária Anual (LOA) – "
            "enviada pelo Executivo ao Congresso anualmente –, são propostas por meio das quais os parlamentares "
            "podem opinar ou influir na alocação de recursos públicos em função de compromissos políticos que "
            "assumiram durante seu mandato, tanto junto aos estados e municípios quanto a instituições. Tais emendas "
            "podem acrescentar, suprimir ou modificar determinados itens (rubricas) do projeto de lei orçamentária "
            "enviado pelo Executivo. Fonte: https://www12.senado.leg.br/noticias/glossario-legislativo/emendas-ao-orcamento"
            ),
    },
    "empenho": {
        "name": "Empenho",
        "definition": (
            "Primeiro estágio da despesa. No primeiro estágio, é criada a obrigação de pagamento da despesa pelo governo ao "
            "credor. Consiste na reserva de dotação orçamentária, ou seja, reserva de valores monetários autorizados para "
            "atender um fim específico. O empenho é registrado no momento da contratação do serviço, aquisição do material ou "
            "bem, obra ou amortização da dívida."
            ),
    },
    "liquidacao": {
        "name": "Liquidação",
        "definition": (
            "Segundo estágio da execução da despesa pública. Esse estágio consiste na verificação do direito adquirido "
            "pelo credor, tendo por base os títulos e documentos comprobatórios do respectivo crédito. É nesse segundo "
            "estágio da execução da despesa que será cobrada a prestação dos serviços ou a entrega dos bens, ou ainda, a "
            "realização da obra. Envolve, portanto, todos os atos de verificação e conferência, desde a entrega do material "
            "ou a prestação do serviço até o reconhecimento da despesa."
            ),
    },
    "pagamento": {
        "name": "Pagamento",
        "definition": (
            "O último estágio da despesa pública. Consiste na entrega de numerário ao credor. "
            "Nessa fase, a autoridade competente determina que a despesa que foi liquidada seja paga. "
            "Esse pagamento normalmente é efetuado por meio de crédito em conta bancária do favorecido."
            ),
    },
}


def glossary(concept: str) -> DataToolOutput:
    """Returns the official definition of a concept."""
    d = GLOSSARY.get(concept)
    if d is None:
        available = ", ".join(GLOSSARY.keys())
        texto = f"Não existe uma definição para '{concept}' no glossário.Conceitos disponíveis: {available}."
        return text_result(texto, [SOURCE])

    texto = f"{d['name']}: {d['definition']}:\n\nFonte: {SOURCE})."
    return text_result(texto, [SOURCE])
