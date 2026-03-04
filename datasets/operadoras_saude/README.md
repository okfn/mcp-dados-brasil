# Operadoras de Planos de Saúde Ativas

## Organization

A Agência Nacional de Saúde Suplementar (ANS) é a agência reguladora vinculada ao Ministério da Saúde responsável pelo setor de planos de saúde no Brasil.  

## Dataset
Dataset: https://dados.gov.br/dados/conjuntos-dados/operadoras-de-planos-de-saude-ativas

## Resource

Dados cadastrais das Operadoras Ativas na ANS.  
Trata-se de conjunto de dados com relação de operadoras com registro ativo na ANS (autorizadas a vender planos de saúde no Brasil), elaborada a partir de informações fornecidas pelas próprias empresas.

## Data file

The actual link to the file data is https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/Relatorio_cadop.csv  

## Notes

This is a dataset from the Brazilian government's open data portal containing the registration data of all active health insurance operators in Brazil.  
Organization: It is published by the Agência Nacional de Saúde Suplementar (ANS), which is the national regulatory agency for private health insurance and plans in Brazil.  
Content: The dataset is a list of all companies currently authorized by the ANS to sell health plans. The information is provided by the companies themselves.  

Sample data


```
REGISTRO_OPERADORA;CNPJ;Razao_Social;Nome_Fantasia;Modalidade;Logradouro;Numero;Complemento;Bairro;Cidade;UF;CEP;DDD;Telefone;Fax;Endereco_eletronico;Representante;Cargo_Representante;Regiao_de_Comercializacao;Data_Registro_ANS
"419761";"19541931000125";"18 DE JULHO ADMINISTRADORA DE BENEFÍCIOS LTDA";;"Administradora de Benefícios";"RUA CAPITÃO MEDEIROS DE REZENDE";"274";;"PRAÇA DA BANDEIRA";"Além Paraíba";"MG";"36660000";"32";"34624649";;"contabilidade@cbnassessoria.com.br";"LUIZ HENRIQUE MARENDINO GONÇALVES";"SÓCIO ADMINISTRADOR";6;"2015-05-19"
"421545";"22869997000153";"2B ODONTOLOGIA OPERADORA DE PLANOS ODONTOLÓGICOS LTDA";;"Odontologia de Grupo";"RUA CATÃO";"128";"SALA 126";"VILA ROMANA";"São Paulo";"SP";"05049000";"11";"34415852";;"labmarisol@gmail.com";"MARISOL BECHELLI";"SÓCIO ADMINISTRADORA";4;"2019-06-13"
"421421";"27452545000195";"2CARE OPERADORA DE SAÚDE LTDA.";;"Medicina de Grupo";"RUA: BERNARDINO DE CAMPOS";"230";"1º ANDAR";"CENTRO";"Campinas";"SP";"13010151";"19";"37901224";;"ans.plano@hospitalcare.com.br";"RODRIGO PINHO RIBEIRO";"REPRESENTANTE";5;"2018-10-09"
```

On the structure of the file each row is representing a different health operator and columns containing specific information. Here is what the main fields mean:

REGISTRO_OPERADORA: Operator's registration number with ANS
CNPJ: Brazilian National Registry of Legal Entities (tax ID)
Razao_Social: Legal Company Name
Nome_Fantasia: Trade Name / Brand Name
Modalidade: Business Modality (e.g., "Administradora de Benefícios" = Benefits Administrator, "Odontologia de Grupo" = Group Dentistry)
Logradouro, Numero, etc.: Full address (Street, Number, Neighborhood, City, State, Zip Code)
DDD, Telefone, Fax: Area code and phone/fax numbers
Endereco_eletronico: Email address
Representante: Legal Representative's name
Cargo_Representante: Representative's job title
Regiao_de_Comercializacao: Commercialization region code
Data_Registro_ANS: Date of registration with ANS

In short, this is a directory of all legally authorized health plan operators in Brazil, useful for research, market analysis, or regulatory compliance.  
