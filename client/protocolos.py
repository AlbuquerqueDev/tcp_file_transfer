import socket
import struct
import os
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_DIR = os.path.join(SCRIPT_DIR, "arquivos_baixados")

BUFSIZE = 1024


def baixar_arquivo(conn: socket.socket):
    nome_arquivo = input("Informe o nome do arquivo para download: ")
    if not nome_arquivo:
        print("Informe um nome!")
        return

    tamanho_nome_arquivo = len(nome_arquivo)
    try:
        byte_operacao = struct.pack(">B", 10)
        conn.send(byte_operacao)
        print("Enviando código de operacao 10 (download)...")

        tam_bytes = struct.pack(">I", tamanho_nome_arquivo)
        conn.send(tam_bytes)
        print("[-] Enviando o tamanho do nome do arquivo...")

        nome_bytes = nome_arquivo.encode("utf-8")
        conn.send(nome_bytes)
        print("[-] Enviando o nome do arquivo...")

        print(f"Arquivo {nome_arquivo} solicitado com sucesso.")

        bytes_status = conn.recv(1)
        if not bytes_status:
            print("ERRO: Conexao fechada pelo servidor.")
            return

        status = struct.unpack(">B", bytes_status)[0]

        if status == 1:
            print("ERRO: Arquivo não existe no servidor.")
            return
        elif status == 0:
            print("Arquivo encontrado! Iniciando o download...")
        else:
            print(f"ERRO: Status desconhecido {status}")
            return

        tamanho_arquivo_bytes = conn.recv(4)
        if len(tamanho_arquivo_bytes) != 4:
            print("ERRO: tamanho de arquivo inválido.")
            return

        tamanho_arquivo = struct.unpack(">I", tamanho_arquivo_bytes)[0]
        print(f"Tamanho do arquivo: {tamanho_arquivo} bytes")

        nome_saida = os.path.join(SCRIPT_DIR, nome_arquivo)

        with open(nome_saida, "wb") as f:
            bytes_recebidos = 0
            while bytes_recebidos < tamanho_arquivo:
                chunk = conn.recv(BUFSIZE)
                if not chunk:
                    break
                f.write(chunk)
                bytes_recebidos += len(chunk)

        print(f"Download concluído! Arquivo salvo em {
              SCRIPT_DIR.split("/")[-1]}/{nome_arquivo}")
    except socket.timeout:
        print("ERRO: Tempo de espera excedido.")
    except ConnectionRefusedError:
        print("ERRO: Conexão resetada pelo servidor.")
    except Exception as e:
        print(f"Erro durante download: {e}")


def listar_arquivos(conn: socket.socket):
    try:
        byte_operacao = struct.pack(">B", 20)
        conn.send(byte_operacao)
        print("Enviando código de operacao 20 (listagem de arquivos)")

        bytes_status = conn.recv(1)
        if not bytes_status:
            print("ERRO: Conexão f3chada pelo servidor.")
            return

        status = struct.unpack(">B", bytes_status)[0]

        if status == 1:
            print("Erro durante o envio de listagem.")
            return
        elif status != 0:
            print(f"ERRO: Status desconhecido: {(status)}")
            return
        print("[-] Recebendo lista de arquivos...")

        tamanho_lista_bytes = conn.recv(4)
        if len(tamanho_lista_bytes) != 4:
            print("ERRO: Tamanho de lista inválido.")
            return

        tamanho_lista = struct.unpack(">I", tamanho_lista_bytes)[0]
        print(f"[-] Tamanho da lista: {tamanho_lista} bytes")

        lista_bytes = b""
        bytes_recebidos = 0

        while bytes_recebidos < tamanho_lista:
            chunk = conn.recv(min(BUFSIZE, tamanho_lista - bytes_recebidos))
            if not chunk:
                print("ERRO: Conexão fechada durante recebimento da lista.")
                return
            lista_bytes += chunk
            bytes_recebidos += len(chunk)
        try:
            lista_arquivos = lista_bytes.decode("utf-8")

            print("=" * 20)
            print("Arquivos disponíveis para download: ")
            print("=" * 20)
            print(lista_arquivos)
            print("=" * 20)
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON: {e}")
        except Exception as e:
            print(f"Erro ao processar a listagem: {e}")
    except socket.timeout:
        print("ERRO: Tempo de espera excedido.")
    except ConnectionRefusedError:
        print("ERRO: Conexão resetada pelo servidor.")
    except Exception as e:
        print(f"Erro durante download: {e}")


def upload_arquivo(conn: socket.socket):

    nome_arquivo = input("Informe o nome do arquivo para upload: ")
    if not nome_arquivo:
        print("Informe um nome!")
        return

    caminho_arquivo = os.path.join(SCRIPT_DIR, nome_arquivo)
    caminho_arquivo = os.path.normpath(caminho_arquivo)

    if not os.path.exists(caminho_arquivo):
        print(f"ERRO: Arquivo não encontrado: {caminho_arquivo}")
        return

    tamanho_nome_arquivo = len(nome_arquivo)

    try:
        byte_operacao = struct.pack(">B", 30)
        conn.send(byte_operacao)
        print("Enviando código de operacao 30 (upload)...")

        tam_bytes = struct.pack(">I", tamanho_nome_arquivo)
        conn.send(tam_bytes)
        print("[-] Tamanho do nome do arquivo enviado.")

        nome_arquivo_bytes = nome_arquivo.encode('utf-8')
        conn.send(nome_arquivo_bytes)
        print("[-] Nome do arquivo enviado.")

        bytes_status = conn.recv(1)
        status = struct.unpack(">B", bytes_status)[0]

        if status == 1:
            print("Erro não identificado, os bytes não serão esperados.")
            return
        elif status == 0:
            print("O upload foi aceito, os bytes serão esperados...")
        else:
            print(f"ERRO: Status desconhecido {status}")
            return

        tamanho_arquivo = os.path.getsize(caminho_arquivo)
        print(f"[-] Tamanho do arquivo: {tamanho_arquivo} bytes")

        tamanho_bytes = struct.pack(">I", tamanho_arquivo)
        conn.send(tamanho_bytes)

        if not caminho_arquivo.startswith(os.path.abspath(SCRIPT_DIR)):
            print("[!] ATENCAO: Acesso fora do diretório de arquivos negado.")
            status = struct.pack(">B", 0)
            conn.send(status)
            return True

        bytes_enviados = 0
        with open(caminho_arquivo, "rb") as f:
            while True:
                dados = f.read(BUFSIZE)
                if not dados:
                    break
                conn.sendall(dados)
                bytes_enviados += len(dados)
        print(f"{nome_arquivo} enviado com sucesso. ({
              bytes_enviados}) bytes enviados")

        status_final_byte = conn.recv(1)
        if status_final_byte:
            status_final = struct.unpack(">B", status_final_byte)[0]
            if status_final == 0:
                print("Servidor confirmou o recebimento com sucesso.")

        return True
        print(f"{nome_arquivo} enviado com sucesso. ({
              bytes_enviados}) bytes enviados")
        return True
    except socket.timeout:
        print("ERRO: Tempo de espera excedido.")
    except ConnectionRefusedError:
        print("ERRO: Conexão resetada pelo servidor.")
    except Exception as e:
        print(f"Erro durante download: {e}")
