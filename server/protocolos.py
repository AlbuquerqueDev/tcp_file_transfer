import socket
import struct
import os
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_DIR = os.path.join(SCRIPT_DIR, "arquivos")
BUFSIZE = 1024


def enviar_arquivo(conn: socket, addr: tuple):
    try:
        tamanho_arquivo_bytes = conn.recv(4)

        if not tamanho_arquivo_bytes:
            print(f"Cliente {addr} desonectou.")
            return False

        tamanho_nome_arquivo = struct.unpack(">I", tamanho_arquivo_bytes)[0]
        print(f"[-] Tamanho do nome: {tamanho_nome_arquivo} bytes")

        nome_arquivo_bytes = conn.recv(tamanho_nome_arquivo)
        nome_arquivo = nome_arquivo_bytes.decode("utf-8")
        print(f"[-] Arquivo solicitado: {nome_arquivo}")

        caminho_arquivo = os.path.join(SCRIPT_DIR, nome_arquivo)
        caminho_arquivo = os.path.normpath(caminho_arquivo)

        if not caminho_arquivo.startswith(os.path.abspath(SCRIPT_DIR)):
            print("[!] ATENCAO: Acesso fora do diretório de arquivos negado.")
            status = struct.pack(">B", 1)
            conn.send(status)
            return True

        if not os.path.exists(caminho_arquivo):
            print(f"ERRO: Arquivo não encontrado: {caminho_arquivo}")
            status = struct.pack(">B", 1)
            conn.send(status)
            return True

        status = struct.pack(">B", 0)
        conn.send(status)
        print(f"Arquivo encontrado: {nome_arquivo}")

        tamanho_arquivo = os.path.getsize(caminho_arquivo)
        print(f"[-] Tamanho do arquivo: {tamanho_arquivo} bytes")

        tamanho_bytes = struct.pack(">I", tamanho_arquivo)
        conn.send(tamanho_bytes)

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
        return True
    except UnicodeDecodeError as e:
        print(f"Erro ao decodificar nome do arquivo: {e}")
        try:
            status = struct.pack(">B", 1)
            conn.send(status)
        except:
            pass
        return False
    except Exception as e:
        print(f"Erro durante envio do arquivo: {e}")
        return False


def enviar_listagem(conn: socket.socket, addr: tuple):
    try:
        lista_arquivos = []

        if os.path.exists(SCRIPT_DIR):
            for fn in os.listdir(SCRIPT_DIR):
                file_path = os.path.join(SCRIPT_DIR, fn)

                if os.path.isfile(file_path):
                    tamanho_arquivo = os.path.getsize(file_path)
                    lista_arquivos.append(
                        {"nome": fn, "tamanho": str(tamanho_arquivo)})
        print(f"[-] Total de arquivos encontrados: {len(lista_arquivos)}")

        json_str = json.dumps(lista_arquivos, ensure_ascii=False, indent=2)
        json_bytes = json_str.encode("utf-8")
        json_size = len(json_bytes)

        status = struct.pack(">B", 0)
        conn.send(status)

        tamanho_json_bytes = struct.pack(">I", json_size)
        conn.send(tamanho_json_bytes)

        conn.send(json_bytes)

        print(f"Lista de arquivos enviada com sucesso para {addr}")
        return True
    except Exception as e:
        print(f"Erro ao enviar lista de arquivos: {e}")
        try:
            status = struct.pack(">B", 1)
            conn.send(status)
        except:
            pass
        return False


def receber_arquivo(conn: socket.socket, addr: tuple):
    try:
        tamanho_arquivo_bytes = conn.recv(4)

        if not tamanho_arquivo_bytes:
            print(f"Cliente {addr} desconectou.")
            return False

        tamanho_nome_arquivo = struct.unpack(">I", tamanho_arquivo_bytes)[0]
        print(f"[-] Tamanho do nome: {tamanho_nome_arquivo} bytes")

        nome_arquivo_bytes = conn.recv(tamanho_nome_arquivo)
        nome_arquivo = nome_arquivo_bytes.decode('utf-8')
        print(f"[-] Arquivo a ser recebido {nome_arquivo}")

        caminho_arquivo = os.path.join(SCRIPT_DIR, nome_arquivo)
        caminho_arquivo = os.path.normpath(caminho_arquivo)

        if not caminho_arquivo.startswith(os.path.abspath(SCRIPT_DIR)):
            print("[!] ATENCAO: Acesso fora do diretório de arquivos negado.")
            status = struct.pack(">B", 1)
            conn.send(status)
            return True

        status = struct.pack(">B", 0)
        conn.send(status)
        print("[-] Upload aceito, os bytes serão esperados...")

        tamanho_arquivo_bytes = conn.recv(4)
        if len(tamanho_arquivo_bytes) != 4:
            print("ERRO: tamanho de arquivo inválido.")
            return

        tamanho_arquivo = struct.unpack(">I", tamanho_arquivo_bytes)[0]
        print(f"Tamanho do arquivo: {tamanho_arquivo} bytes")

        arquivo_saida = os.path.join(SCRIPT_DIR, nome_arquivo)

        with open(arquivo_saida, "wb") as f:
            bytes_recebidos = 0
            while bytes_recebidos < tamanho_arquivo:
                chunk = conn.recv(BUFSIZE)
                if not chunk:
                    break
                f.write(chunk)
                bytes_recebidos += len(chunk)
        print(f"Upload concluído! Arquivo salvo em {
              SCRIPT_DIR.split("/")[-1]}/{nome_arquivo}")

        if bytes_recebidos == tamanho_arquivo:
            upload_stauts = struct.pack(">B", 0)
            conn.send(upload_stauts)
            return True
    except UnicodeDecodeError as e:
        print(f"Erro ao decodificar nome do arquivo: {e}")
        try:
            status = struct.pack(">B", 1)
            conn.send(status)
        except:
            pass
        return False
    except Exception as e:
        print(f"Erro durante recebimento do arquivo: {e}")
        return False
