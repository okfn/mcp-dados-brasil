# Bolsa Família

URL:

Dataset: https://dados.gov.br/dados/conjuntos-dados/bolsa-familia
Resource:
https://aplicacoes.mds.gov.br/sagi/servicos/misocial/?fq=anomes_s:2026*&fl=codigo_ibge%2Canomes_s%2Cqtd_familias_beneficiarias_bolsa_familia_s%2Cvalor_repassado_bolsa_familia_s%2Cpbf_vlr_medio_benef_f&fq=valor_repassado_bolsa_familia_s%3A*&q=*%3A*&rows=100000&sort=anomes_s%20desc%2C%20codigo_ibge%20asc&wt=csv

Resource URL analysis:
<pre>
https://aplicacoes.mds.gov.br/sagi/servicos/misocial/?
    fq=anomes_s:2026*&
    fl=codigo_ibge%2Canomes_s%2Cqtd_familias_beneficiarias_bolsa_familia_s%2Cvalor_repassado_bolsa_familia_s%2Cpbf_vlr_medio_benef_f&
    fq=valor_repassado_bolsa_familia_s%3A*&
    q=*%3A*&
    rows=100000&
    sort=anomes_s%20desc%2C%20codigo_ibge%20asc&
    wt=csv
</pre>

## Info

O Bolsa Família é um programa de transferência direta de renda, direcionado às famílias em situação de pobreza e de extrema pobreza em todo o País, de modo que consigam superar a situação de vulnerabilidade e pobreza. Tem como principal objetivo combater a fome, a pobreza e promover a segurança alimentar e nutricional, retirando as famílias da vulnerabilidade socieconômica por meio da transferência de renda; Além disso, através das condicionalidades, reforçar o acesso aos direitos básicos e aos serviços de saúde, educação, segurança alimentar a assistência social.

### Neste conjunto de dados temos as seguintes variáveis:

A partir de março de 2023:

<pre>
ibge: código ibge do município
anomes: ano e mês de referência
qtd_familias_beneficiarias_bolsa_familia_s: Quantidade de famílias beneficiárias do Programa Bolsa Família
valor_repassado_bolsa_familia_s: Valor repassado para pagamento de benefícios do Programa Bolsa Família
pbf_vlr_medio_benef_f: Valor médio dos benefícios pagos do Programa Bolsa Família
</pre>

De 2004 a 2021:

<pre>
ibge: código ibge do município
anomes: ano e mês de referência
qtd_familias_beneficiarias_bolsa_familia: Quantidade de famílias beneficiárias do Programa Bolsa Família
valor_repassado_bolsa_familia: Valor repassado para pagamento de benefícios do Programa Bolsa Família
</pre>

Esse conjunto de dados informa a quantidade de famílias beneficiárias e o valor repassado através da folha de pagamento do Bolsa Família, assim como o município e ano/mês de referência.

Para saber mais informações sobre os dados do programa no período de Nov/2021 a Fev/2023, consulte os indicadores do Programa Auxílio Brasil (PAB), clique no link: https://dados.gov.br/dados/conjuntos-dados/auxlio-brasil---mi-social

Painel de Análise dos Dados: https://aplicacoes.mds.gov.br/sagi-paineis/analise_dados_abertos/

Idioma: Português (pt-BR)

Soluções utilizadas para abertura deste conjunto de dados:

VIS DATA: é a ferramenta informacional sucessora da Matriz de Informações Sociais concebida em 2005. O VIS DATA se utiliza do conceito de base de dados para armazenar e gerir diversos indicadores e variáveis.

Acesse o VIS DATA

Documenta Wiki: é uma ferramenta online que busca concentrar a documentação e as informações mais detalhadas (os metadados) dos programas e dos indicadores de monitoramento.

Acesse o Documenta Wiki - Bolsa Família


 Licença: Creative Commons Attribution
 Formatos: CSV; JSON; XML; xlm;
 Atualização: Mensal
 Catalogação: 30/11/2017
 Última alteração nos metadados: 17/03/2026
 Última alteração em um arquivo: Indisponível
 Área técnica responsável: Secretaria de Avaliação, Gestão da Informação e Cadastro Único - SAGICAD
 E-mail da área técnica: dgi.sagicad@mds.gov.br
 Objetivos de Desenvolvimento Sustentável (ODS): Fome Zero e Agricultura Sustentável, Saúde e Bem-Estar, Educação de Qualidade
 Raça/etnia: Não
 Gênero: Não
 Versão: 1.1


## TODO

Get the _código ibge do município_ to be able to show and search by city.  
This information is not available in the dataset, but it can be obtained from the [IBGE API](https://servicodados.ibge.gov.br/api/docs/localidades?versao=1#api-Municipios-get_municipios).  

