# Pipeline de Viagens a Serviço - Arquitetura Medallion

Projeto desenvolvido com o objetivo de construir um pipeline de dados completo, desde a extração de dados públicos até a análise final, usando a base de Viagens a Serviço do Portal da Transparência (Governo Federal).

---

## Objetivo

Construir um pipeline automatizado que baixa, limpa, organiza e analisa os dados de viagens a serviço do governo federal, seguindo a Arquitetura Medallion (Raw, Silver e Gold). A análise busca responder perguntas como:

- Quais os 5 órgãos com maior custo total em viagens?
- Quais os 3 destinos com maior custo médio por viagem?
- Qual foi a viagem de maior duração e quanto ela custou?
- Qual tipo de pagamento tem o maior valor médio?
- Qual o meio de transporte mais usado nos trechos?
- Qual UF de destino aparece em mais trechos?
- Qual órgão pagou mais no total?

---

## Base de Dados

- **Fonte:** [Portal da Transparência - Viagens a Serviço](https://portaldatransparencia.gov.br)
- **Período:** recorte de 6 meses de 2025
- **Arquivos:** 4 CSVs (Viagem, Pagamento, Passagem e Trecho), baixados automaticamente de um link do Google Drive
- **Volume:** mais de 1,8 milhão de linhas somando as 4 tabelas Raw

---

## Ferramentas Utilizadas

- Python (Pandas, Matplotlib)
- MySQL
- Jupyter Notebook
- Git/GitHub
- Bibliotecas: gdown, mysql-connector-python

---

## Arquitetura do Pipeline (Medallion)

O projeto segue a Arquitetura Medallion, dividida em 3 camadas, organizadas em pastas separadas por responsabilidade (ingestão, pipeline de transformação, SQL e análise). Essa estrutura segue o modelo de Engenharia de Dados fornecido como referência, já que esse projeto é um pipeline automatizado de ponta a ponta, e não uma análise pontual.

### `sql/0_criar_banco.sql`
Cria o banco de dados e as 8 tabelas: 4 na camada Raw (cópia fiel dos CSVs, tudo texto) e 4 na camada Silver (dados já limpos e tipados, com chave primaria, chave estrangeira e restrições).

### `ingestion/1_extrair.py` - Camada Raw
Baixa o arquivo zip do Google Drive automaticamente (usando a biblioteca gdown), le os 4 CSVs de dentro do zip e carrega tudo nas tabelas Raw, sem alteração no dado original.

### `pipelines/2_transformar.py` - Camada Silver
Copia os dados da Raw para a Silver, convertendo texto para os tipos corretos, respeitando as chaves estrangeiras e calculando as colunas `valor_total` e `duracao_dias`.

### `notebooks/3_analise.ipynb` - Camada Gold
Responde as perguntas de negócio com consultas SQL, tabelas e gráficos. Também cria uma camada Gold agregada (com JOIN e GROUP BY), salva como tabela e como VIEW no MySQL.

---

## Como Executar o Projeto

1. Clone este repositório
2. Instale as dependências: `pip install -r requirements.txt`
3. Copie o arquivo `.env.example` para `.env` e preencha com as suas credenciais do MySQL
4. Rode o script `sql/0_criar_banco.sql` no MySQL Workbench (ou outro de sua preferência)
5. Rode `python ingestion/1_extrair.py` no terminal
6. Rode `python pipelines/2_transformar.py` no terminal
7. Abra o `notebooks/3_analise.ipynb` no VS Code (ou Jupyter) e execute as células em ordem

---

## Principais Insights

- O Ministério da Justiça e Segurança Pública lidera o custo total de viagens (quase R$ 487 milhões no período), o que provavelmente reflete a natureza operacional da pasta (Policia Federal, Policia Rodoviária Federal, fiscalizações).
- Esse mesmo órgão concentra 40,9% de todo o valor pago em viagens no periodo, quase metade do total, sozinho, na frente de todos os outros órgãos do governo federal juntos.
- A viagem de maior duração (383 dias) apresenta `valor_total` igual a zero, porque os campos de valor dessa viagem vieram vazios no CSV original. Evidenciando inconsistências nos dados do Governo.
- Os destinos com maior custo médio por viagem (considerando só viagens de trecho único) são Washington/EUA, Brasília/DF e Londrina/PR, com Washington na frente por ser destino internacional.
- A categoria "Inválido" aparece 26.659 vezes no campo de meio de transporte, provavelmente por inconsistência de preenchimento na fonte original.
- O órgão que mais gastou em viagens (Pergunta 1) não é exatamente o mesmo órgão que mais pagou no total (Pergunta 7), porque as duas perguntas usam fontes de calculo um pouco diferentes (uma usa o valor calculado da viagem, a outra usa a soma dos pagamentos de fato realizados).

---

## Decisões técnicas e limitações encontradas

Durante o desenvolvimento, algumas decisões precisaram ser tomadas e documentadas:

- **Tamanho das colunas de texto na Raw:** ao criar a tabela `raw_viagem` com todas as colunas em VARCHAR (como pede o padrão do projeto), o MySQL retornou o erro "row size too large", porque várias colunas de texto longo somadas ultrapassaram o limite do banco. A solução foi usar `TEXT` nas duas colunas exclusivas da Raw que guardam texto livre mais longo, mantendo o restante das colunas em VARCHAR, além de aplicar `ROW_FORMAT=DYNAMIC` nas tabelas que guardam texto mais longo.

- **Cálculo do custo médio por destino (Pergunta 2):** essa pergunta passou por algumas tentativas até chegar numa resposta que fizesse sentido. A primeira tentativa (agrupar pelo campo de texto livre destinos) trazia destinos que apareciam só uma vez, pois juntava várias cidades nesse campo, o que deixava o valor muito alto e a "média" sem sentido estatístico real. Pra tentar corrigir isso, foi adicionado um filtro de mínimo de registros (HAVING COUNT(*) >= 30), mas o resultado continuou estranho, porque o campo destinos ainda concatena vários locais numa única viagem, e o topo do ranking ficou cheio de combinações repetidas do mesmo lugar, tipo "Brasília/DF, Brasília/DF, Brasília/DF...". A segunda tentativa de verdade foi usar a tabela de trechos, que já tem os destinos separados um por linha, o que melhorou bastante, mas viagens com vários trechos ainda acabavam "herdando" o custo total inteiro em cada destino visitado. A versão final considera apenas viagens de trecho único, garantindo que o valor de cada viagem reflete o custo daquele destino específico.

- **Camada Gold única:** o projeto pede a criação de uma camada Gold agregada (com JOIN e GROUP BY, salva como tabela e VIEW). Como as perguntas de negócio do bloco Gold usam dimensões diferentes (uma sobre pagamento, duas sobre trecho), decidimos criar só uma tabela/VIEW Gold oficial (para a pergunta sobre tipo de pagamento), e usar consultas com JOIN separadas para as outras duas perguntas, evitando misturar tabelas de naturezas diferentes num único JOIN, o que inflaria os números.

---

## Diferenciais do Projeto

- Pipeline completo, do download automático até a análise final, sem intervenção manual
- Extração e transformação idempotentes (podem ser executadas várias vezes sem duplicar dados)
- Camada Raw preservada fielmente, mesmo quando o dado original é estranho ou incompleto
- Todo o caminho até chegar nas respostas certas ficou documentado, incluindo os erros e ajustes no meio do processo

---

## Melhorias Futuras

- Trocar a conexão usada pelo Pandas (`mysql-connector-python`) por `SQLAlchemy`, que é a forma recomendada oficialmente e evita um aviso (warning) que aparece hoje ao rodar as consultas
- Adicionar um arquivo de log com o histórico de execuções e possíveis erros
- Criar tabelas/VIEWs Gold também para as perguntas de transporte e UF de destino, caso seja necessário reaproveitar essas consultas em outros projetos

---

## Aprendizados

Durante o desenvolvimento deste projeto, foram aplicados e reforçados conceitos como:

- Construção de um pipeline de dados completo com Arquitetura Medallion (Raw, Silver, Gold)
- Download e extração automatizada de dados (gdown, zipfile)
- Modelagem de banco de dados com chave primaria, chave estrangeira e restrições (CHECK, NOT NULL, UNIQUE)
- Conversão de tipos de dados via SQL (texto para DECIMAL e DATE)
- Idempotência em scripts de ETL
- Consultas SQL com JOIN, GROUP BY e subconsultas
- Criação de tabelas agregadas e VIEWs no MySQL
- Visualização de dados com Matplotlib
- Refinamento iterativo de perguntas de negócio a partir de problemas encontrados nos dados
- Versionamento com Git e organização de commits por funcionalidade

---

## Fonte dos Dados

Dados públicos do [Portal da Transparência](https://portaldatransparencia.gov.br), disponibilizados pelo Governo Federal, utilizados como desafio do curso SC TEC (SENAI Santa Catarina).

---

## Autor

**Matheus Capri**
Profissional em transição para a área de Dados, com experiência em gestão e análise de operações.

🔗 [LinkedIn](https://www.linkedin.com/in/matheus-capri-nery-215a3737)
💻 [GitHub](https://github.com/MatheusCapri)

---
