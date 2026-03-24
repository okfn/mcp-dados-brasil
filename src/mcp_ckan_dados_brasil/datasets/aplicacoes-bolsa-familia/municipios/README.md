# Municipios do Brasil

URL: https://servicodados.ibge.gov.br/api/v1/localidades/municipios
ID: Código IBGE (Instituto Brasileiro de Geografia e Estatística ) do município.  

 - IBGE assigns a 7-digit code to each município
 - The first 2 digits = state (UF), next 4 = municipality, last 1 = check digit
 - Many government datasets drop the check digit and use only 6 digits

The IBGE code lives in the id field of each municipality entry in the JSON:

```json
  {  
"id": 1100015,
"nome": "Alta Floresta D'Oeste",
"microrregiao": { ... } 
  }
```

  This is a 7-digit code. But the CSV (2026-aplicacoes.mds.gov.br.csv) uses 6-digit codes:  

<pre>
  codigo_ibge,anomes_s,...
  110001,202603,... 
</pre>
