"""
2_transformar.py  -  FASE 2: Transformacao e Camada SILVER
----------------------------------------------------------
Pega os dados "sujos" da camada RAW (tudo texto) e preenche as tabelas SILVER
(ja criadas, com PK/FK, pelo 0_criar_banco.txt) com os dados limpos e tipados."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import banco

# Esvaziar as tabelas SILVER (idempotencia).
LIMPAR_SILVER = [
    'DELETE FROM silver_pagamento',
    'DELETE FROM silver_passagem',
    'DELETE FROM silver_trecho',
    'DELETE FROM silver_viagem'
]


# Copiar RAW -> SILVER convertendo os tipos.
SQL_VIAGEM = """
    INSERT INTO silver_viagem (
        id_viagem, num_proposta, situacao, viagem_urgente, cod_orgao_superior,
        nome_orgao_superior, nome_viajante, cargo, data_inicio, data_fim,
        destinos, motivo, valor_diarias, valor_passagens, valor_devolucao, valor_outros_gastos
    )
    SELECT
        id_viagem,
        num_proposta,
        situacao,
        viagem_urgente,
        cod_orgao_superior,
        nome_orgao_superior,
        nome_viajante,
        cargo,
        STR_TO_DATE(NULLIF(TRIM(data_inicio), ''), '%d/%m/%Y'),
        STR_TO_DATE(NULLIF(TRIM(data_fim), ''), '%d/%m/%Y'),
        destinos,
        motivo,
        CAST(REPLACE(REPLACE(NULLIF(TRIM(valor_diarias),''),'.',''),',','.') AS DECIMAL(10,2)),
        CAST(REPLACE(REPLACE(NULLIF(TRIM(valor_passagens),''),'.',''),',','.') AS DECIMAL(10,2)),
        CAST(REPLACE(REPLACE(NULLIF(TRIM(valor_devolucao),''),'.',''),',','.') AS DECIMAL(10,2)),
        CAST(REPLACE(REPLACE(NULLIF(TRIM(valor_outros_gastos),''),'.',''),',','.') AS DECIMAL(10,2))
    FROM raw_viagem;
"""

# Calcular colunas derivadas.
SQL_VIAGEM_CALCULOS = """
    UPDATE silver_viagem
    SET valor_total = COALESCE(valor_diarias, 0)
                     + COALESCE(valor_passagens, 0)
                     + COALESCE(valor_outros_gastos, 0)
                     - COALESCE(valor_devolucao, 0),
        duracao_dias = DATEDIFF(data_fim, data_inicio);
"""


SQL_PAGAMENTO = """
    INSERT INTO silver_pagamento (
        id_viagem, num_proposta, nome_orgao_pagador, nome_ug_pagadora, tipo_pagamento, valor
    )
    SELECT
        id_viagem,
        num_proposta,
        nome_orgao_pagador,
        nome_ug_pagadora,
        tipo_pagamento,
        CAST(REPLACE(REPLACE(NULLIF(TRIM(valor),''),'.',''),',','.') AS DECIMAL(10,2))
    FROM raw_pagamento
    WHERE id_viagem IN (SELECT id_viagem FROM silver_viagem);
"""


SQL_PASSAGEM = """
    INSERT INTO silver_passagem (
        id_viagem, meio_transporte, pais_origem_ida, uf_origem_ida, cidade_origem_ida, pais_destino_ida,
        uf_destino_ida, cidade_destino_ida, valor_passagem, taxa_servico, data_emissao
    )
    SELECT    
        id_viagem,
        meio_transporte,
        pais_origem_ida,
        uf_origem_ida,
        cidade_origem_ida,
        pais_destino_ida,
        uf_destino_ida,
        cidade_destino_ida,
        CAST(REPLACE(REPLACE(NULLIF(TRIM(valor_passagem),''),'.',''),',','.') AS DECIMAL(10,2)),
        CAST(REPLACE(REPLACE(NULLIF(TRIM(taxa_servico),''),'.',''),',','.') AS DECIMAL(10,2)),
        STR_TO_DATE(NULLIF(TRIM(data_emissao), ''), '%d/%m/%Y')
    FROM raw_passagem
    WHERE id_viagem IN (SELECT id_viagem FROM silver_viagem);           
"""


SQL_TRECHO = """
    INSERT INTO silver_trecho (
        id_viagem, sequencia_trecho, origem_data, origem_uf, origem_cidade, destino_data,
        destino_uf, destino_cidade, meio_transporte, numero_diarias
    )   
    SELECT 
        id_viagem,
        CAST(NULLIF(TRIM(sequencia_trecho), '') AS UNSIGNED), 
        STR_TO_DATE(NULLIF(TRIM(origem_data), ''), '%d/%m/%Y'),
        origem_uf,
        origem_cidade,
        STR_TO_DATE(NULLIF(TRIM(destino_data), ''), '%d/%m/%Y'),
        destino_uf,
        destino_cidade,
        meio_transporte,
        CAST(REPLACE(REPLACE(NULLIF(TRIM(numero_diarias),''),'.',''),',','.') AS DECIMAL(10,2))
    FROM raw_trecho
    WHERE id_viagem IN (SELECT id_viagem FROM silver_viagem);  
"""

# Executar tudo na ordem certa.

def main():
    print("=== FASE 2: TRANSFORMACAO + CAMADA SILVER ===")
    try:
        conexao = banco.conectar()

        print("[1/2] Esvaziando as tabelas SILVER...")
        for comando in LIMPAR_SILVER:
            banco.executar(conexao, comando)

        print("[2/2] Copiando e convertendo RAW -> SILVER...")
        banco.executar(conexao, SQL_VIAGEM)
        banco.executar(conexao, SQL_VIAGEM_CALCULOS)
        print("      silver_viagem  OK")
        banco.executar(conexao, SQL_PAGAMENTO)
        print("      silver_pagamento  OK")
        banco.executar(conexao, SQL_PASSAGEM)
        print("      silver_passagem  OK")
        banco.executar(conexao, SQL_TRECHO)
        print("      silver_trecho  OK")

        conexao.close()
        print("=== Camada SILVER concluida com sucesso! ===")
    except Exception as erro:
        print("[ERRO] Algo deu errado:", erro)
        raise


if __name__ == "__main__":
    main()