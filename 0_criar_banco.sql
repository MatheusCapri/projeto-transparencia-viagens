-- criação database
DROP DATABASE IF EXISTS transparencia;
CREATE DATABASE transparencia
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE transparencia;

-- raw_viagem: copia fiel do CSV 2025_Viagem.csv
DROP TABLE IF EXISTS raw_viagem;
CREATE TABLE raw_viagem (
	id_viagem						VARCHAR(20),
    num_proposta					VARCHAR(20),
    situacao						VARCHAR(50),
    viagem_urgente					VARCHAR(5),
    justificativa_urgencia_viagem	TEXT,
    cod_orgao_superior				VARCHAR(20),
    nome_orgao_superior				VARCHAR(255),
    cod_orgao_solicitante			VARCHAR(20),
    nome_orgao_solicitante			VARCHAR(255),
    cpf_viajante					VARCHAR(20),
    nome_viajante					VARCHAR(255),
    cargo							VARCHAR(255),
    funcao							VARCHAR(255),
    descricao_funcao				TEXT,
    data_inicio						VARCHAR(20),
    data_fim						VARCHAR(20),
    destinos						VARCHAR(4000),
    motivo							VARCHAR(4000),
    valor_diarias					VARCHAR(20),
    valor_passagens					VARCHAR(20),
    valor_devolucao					VARCHAR(20),
    valor_outros_gastos				VARCHAR(20)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;

-- raw_pagamento: copia fiel do CSV 2025_Pagamento.csv
DROP TABLE IF EXISTS raw_pagamento;
CREATE TABLE raw_pagamento (
	id_viagem					VARCHAR(20),
    num_proposta				VARCHAR(20),
    cod_orgao_superior			VARCHAR(20),
    nome_orgao_superior			VARCHAR(255),
    cod_orgao_pagador			VARCHAR(20),
    nome_orgao_pagador			VARCHAR(255),
    cod_ug_pagadora				VARCHAR(20),
    nome_ug_pagadora			VARCHAR(255),
    tipo_pagamento				VARCHAR(50),
    valor						VARCHAR(20)
) ENGINE=InnoDB;

-- raw_passagem: copia fiel do CSV 2025_Passagem.csv
DROP TABLE IF EXISTS raw_passagem;
CREATE TABLE raw_passagem (
	id_viagem					VARCHAR(20),
    num_proposta				VARCHAR(20),
    meio_transporte				VARCHAR(50),
    pais_origem_ida				VARCHAR(60),
    uf_origem_ida				VARCHAR(40),
    cidade_origem_ida			VARCHAR(80),
    pais_destino_ida			VARCHAR(60),
    uf_destino_ida				VARCHAR(40),
    cidade_destino_ida			VARCHAR(80),
    pais_origem_volta			VARCHAR(60),
    uf_origem_volta				VARCHAR(40),
    cidade_origem_volta			VARCHAR(80),
    pais_destino_volta			VARCHAR(60),
    uf_destino_volta			VARCHAR(40),
    cidade_destino_volta		VARCHAR(80),
    valor_passagem				VARCHAR(20),
    taxa_servico				VARCHAR(20),
    data_emissao				VARCHAR(20),
    hora_emissao				VARCHAR(20)
) ENGINE=InnoDB;

-- raw_trecho: copia fiel do CSV 2025_Trecho.csv
DROP TABLE IF EXISTS raw_trecho;
CREATE TABLE raw_trecho (
    id_viagem				VARCHAR(20),
    num_proposta			VARCHAR(20),
    sequencia_trecho		VARCHAR(20),
    origem_data				VARCHAR(20),
    origem_pais				VARCHAR(40),
    origem_uf				VARCHAR(40),
    origem_cidade			VARCHAR(80),
    destino_data			VARCHAR(20),
    destino_pais			VARCHAR(40),
    destino_uf				VARCHAR(40),
    destino_cidade			VARCHAR(80),
    meio_transporte			VARCHAR(50),
    numero_diarias			VARCHAR(20),
    missao					VARCHAR(255)
) ENGINE=InnoDB;

-- silver_viagem: criada a partir da raw_viagem
DROP TABLE IF EXISTS silver_viagem;
CREATE TABLE silver_viagem (
	id_viagem						VARCHAR(20)	NOT NULL	PRIMARY KEY,
    num_proposta					VARCHAR(20),
    situacao						VARCHAR(50),
    viagem_urgente					VARCHAR(5),
    cod_orgao_superior				VARCHAR(20),
    nome_orgao_superior				VARCHAR(255) NOT NULL,
    nome_viajante					VARCHAR(255),
    cargo							VARCHAR(255),
    data_inicio						DATE,
    data_fim						DATE,
    destinos						VARCHAR(4000),
    motivo							VARCHAR(4000),
    valor_diarias					DECIMAL(10,2),
    valor_passagens					DECIMAL(10,2),
    valor_devolucao					DECIMAL(10,2),
    valor_outros_gastos				DECIMAL(10,2),
    valor_total						DECIMAL(12,2),
    duracao_dias					INT,
    
    CONSTRAINT chk_valor_diarias      	CHECK (valor_diarias >= 0) 
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;


-- silver_pagamento: criada a partir da raw_pagamento
DROP TABLE IF EXISTS silver_pagamento;
CREATE TABLE silver_pagamento (
	id_pagamento				INT	AUTO_INCREMENT	PRIMARY KEY,
	id_viagem					VARCHAR(20)	NOT NULL,
    num_proposta				VARCHAR(20),
    nome_orgao_pagador			VARCHAR(255),
    nome_ug_pagadora			VARCHAR(255),
    tipo_pagamento				VARCHAR(50)	NOT NULL,
    valor						DECIMAL(10,2),
    
    CONSTRAINT fk_pagamento_viagem
        FOREIGN KEY (id_viagem)
        REFERENCES silver_viagem (id_viagem),
	CONSTRAINT chk_valor_pgto      	CHECK (valor >= 0) 
) ENGINE=InnoDB;


-- silver_passagem: criada a partir da raw_passagem
DROP TABLE IF EXISTS silver_passagem;
CREATE TABLE silver_passagem (
	id_passagem					INT	AUTO_INCREMENT	PRIMARY KEY,
    id_viagem					VARCHAR(20)	NOT NULL,
    meio_transporte				VARCHAR(50),
    pais_origem_ida				VARCHAR(60),
    uf_origem_ida				VARCHAR(40),
    cidade_origem_ida			VARCHAR(80),
    pais_destino_ida			VARCHAR(60),
    uf_destino_ida				VARCHAR(40),
    cidade_destino_ida			VARCHAR(80),
    valor_passagem				DECIMAL(10,2),
    taxa_servico				DECIMAL(10,2),
    data_emissao				DATE,
    
    CONSTRAINT fk_passagem
        FOREIGN KEY (id_viagem)
        REFERENCES silver_viagem (id_viagem),
	CONSTRAINT chk_valor_passagem      	CHECK (valor_passagem >= 0), 
	CONSTRAINT chk_tx_serv		      	CHECK (taxa_servico >= 0) 
) ENGINE=InnoDB;


-- silver_trecho: criada a partir da raw_trecho
DROP TABLE IF EXISTS silver_trecho;
CREATE TABLE silver_trecho (
    id_trecho				INT	AUTO_INCREMENT	PRIMARY KEY,
    id_viagem				VARCHAR(20) NOT NULL,
    sequencia_trecho		INT,
    origem_data				DATE,
    origem_uf				VARCHAR(40),
    origem_cidade			VARCHAR(80),
    destino_data			DATE,
    destino_uf				VARCHAR(40),
    destino_cidade			VARCHAR(80),
    meio_transporte			VARCHAR(50),
    numero_diarias			DECIMAL(10,2),
    
    CONSTRAINT fk_trecho
        FOREIGN KEY (id_viagem)
        REFERENCES silver_viagem (id_viagem),
	CONSTRAINT chk_nro_diarias      	CHECK (numero_diarias >= 0),
	CONSTRAINT uk_trecho_sequencia UNIQUE (id_viagem, sequencia_trecho)	
) ENGINE=InnoDB;