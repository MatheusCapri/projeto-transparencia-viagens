"""
1_extrair.py
---------
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import zipfile

import pandas as pd

import gdown
import config
import banco


# ---------------------------------------------------------------------------
# Download do arquivo do Drive usando 'gdown'
# ---------------------------------------------------------------------------
def baixar_zip():
    """Faz o download do arquivo.zip direto do Drive (so se ainda nao existir em data/)."""
    config.PASTA_DADOS.mkdir(parents=True, exist_ok=True)
    caminho_zip = config.PASTA_DADOS / "dados.zip"

    if caminho_zip.exists():
        print("[1/3] O arquivo ja foi baixado antes - pulando o download.")
        return caminho_zip

    print("[1/3] Baixando o arquivo do Google Drive...")
    try:
        gdown.download(id=config.DRIVE_FILE_ID, output=str(caminho_zip))
    except Exception as erro:
        raise RuntimeError(
            f"Nao foi possivel baixar o arquivo do Google Drive "
            f"(ID: {config.DRIVE_FILE_ID}). Verifique sua conexao com a "
            f"internet e se o ID esta correto no config.py. Detalhe: {erro}"
        )

    return caminho_zip


# ---------------------------------------------------------------------------
# Carregamento do csv
# ---------------------------------------------------------------------------
def carregar_csv(conexao, zip_aberto, nome_csv, tabela):
    """Le um CSV de dentro do zip e insere todas as linhas na tabela do MySQL.

    As colunas do CSV estao na MESMA ordem das colunas da tabela
    (definidas no 0_criar_banco.sql). Por isso conseguimos inserir "na ordem",
    sem precisar escrever o nome de cada coluna.
    """
    print("      Carregando", tabela, "...")

    banco.executar(conexao, f"TRUNCATE TABLE {tabela}")

    total = 0
    with zip_aberto.open(nome_csv) as arquivo:
        pedacos = pd.read_csv(
            arquivo,
            sep=config.CSV_SEPARADOR, 
            encoding=config.CSV_ENCODING, 
            dtype=str,  
            keep_default_na=False, 
            chunksize=config.TAMANHO_BLOCO,
        )
        for pedaco in pedacos:
            linhas = pedaco.values.tolist()
            marcadores = ", ".join(["%s"] * len(pedaco.columns))
            comando = f"INSERT INTO {tabela} VALUES ({marcadores})"
            banco.inserir_em_lote(conexao, comando, linhas)
            total += len(linhas)

    print("      ->", total, "linhas em", tabela)


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------
def main():
    print("=== FASE 1: EXTRACAO + CAMADA RAW ===")
    try:
        conexao = banco.conectar()

        caminho_zip = baixar_zip()
        print("[2/3] Abrindo o arquivo zip...")
        print("[3/3] Carregando as 4 tabelas RAW...")
        with zipfile.ZipFile(caminho_zip) as zip_aberto:
            for arquivo in config.ARQUIVOS.values():
                carregar_csv(conexao, zip_aberto, arquivo["csv"], arquivo["tabela_raw"])

        conexao.close()
        print("=== Camada RAW concluida com sucesso! ===")
    except Exception as erro:
        print("[ERRO] Algo deu errado:", erro)
        raise


if __name__ == "__main__":
    main()
