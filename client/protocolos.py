import socket
import struct
import os
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_DIR = os.path.join(SCRIPT_DIR, "downloaded_files")

BUFSIZE = 1024


def download_file(conn: socket.socket):
    file_name = input("Informe o nome do arquivo para download: ")
    if not file_name:
        print("Informe um nome!")
        exit(1)

    file_name_length = len(file_name)
    try:
        byte_operacao = struct.pack(">B", 10)
        conn.send(byte_operacao)
        print("Enviando código de operacao 10 (download)...")

        fl_bytes = struct.pack(">I", file_name_length)
        conn.send(fl_bytes)
        print("[-] Enviando o tamanho do nome do arquivo...")

        fn_bytes = file_name.encode("utf-8")
        conn.send(fn_bytes)
        print("[-] Enviando o nome do arquivo...")

        print(f"Arquivo {file_name} solicitado com sucesso.")

        status_data = conn.recv(1)
        if not status_data:
            print("ERRO: Conexao fechada pelo servidor.")
            return

        status = struct.unpack(">B", status_data)[0]

        if status == 1:
            print("ERRO: Arquivo não existe no servidor.")
            return
        elif status == 0:
            print("Arquivo encontrado! Iniciando o download...")
        else:
            print(f"ERRO: Status desconhecido {status}")
            return

        file_size_bytes = conn.recv(4)
        if len(file_size_bytes) != 4:
            print("ERRO: tamanho de arquivo inválido.")
            return

        file_size = struct.unpack(">I", file_size_bytes)[0]
        print(f"Tamanho do arquivo: {file_size} bytes")

        output_name = os.path.join(SCRIPT_DIR, file_name)

        with open(output_name, "wb") as f:
            bytes_received = 0
            while bytes_received < file_size:
                chunk = conn.recv(BUFSIZE)
                if not chunk:
                    break
                f.write(chunk)
                bytes_received += len(chunk)

        print(f"Download concluído! Arquivo salvo em {
              SCRIPT_DIR.split("/")[-1]}/{file_name}")
    except socket.timeout:
        print("ERRO: Tempo de espera excedido.")
    except ConnectionRefusedError:
        print("ERRO: Conexão resetada pelo servidor.")
    except Exception as e:
        print(f"Erro durante download: {e}")


def list_files(conn: socket.socket):
    try:
        byte_operacao = struct.pack(">B", 20)
        conn.send(byte_operacao)
        print("Enviando código de operacao 20 (listagem de arquivos)")

        status_data = conn.recv(1)
        if not status_data:
            print("ERRO: Conexão f3chada pelo servidor.")
            return

        status = struct.unpack(">B", status_data)[0]

        if status == 1:
            print("Erro durante o envio de listagem.")
            return
        elif status != 0:
            print(f"ERRO: Status desconhecido: {(status)}")
            return
        print("[-] Recebendo lista de arquivos...")

        list_size_data = conn.recv(4)
        if len(list_size_data) != 4:
            print("ERRO: Tamanho de lista inválido.")
            return

        list_size = struct.unpack(">I", list_size_data)[0]
        print(f"[-] Tamanho da lista: {list_size} bytes")

        list_data = b""
        bytes_received = 0

        while bytes_received < list_size:
            chunk = conn.recv(min(BUFSIZE, list_size - bytes_received))
            if not chunk:
                print("ERRO: Conexão fechada durante recebimento da lista.")
                return
            list_data += chunk
            bytes_received += len(chunk)
        try:
            file_list = list_data.decode("utf-8")

            print("=" * 20)
            print("Arquivos disponíveis para download: ")
            print("=" * 20)
            print(file_list)
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


def upload_file(conn: socket.socket):

    file_name = input("Informe o nome do arquivo para upload: ")
    if not file_name:
        print("Informe um nome!")
        exit(1)

    file_name_length = len(file_name)

    try:
        byte_operacao = struct.pack(">B", 30)
        conn.send(byte_operacao)
        print("Enviando código de operacao 30 (upload)...")

        fl_bytes = struct.pack(">I", file_name_length)
        conn.send(fl_bytes)
        print("[-] Tamanho do nome do arquivo enviado.")

        file_name_data = file_name.encode('utf-8')
        conn.send(file_name_data)
        print("[-] Nome do arquivo enviado.")

        status_data = conn.recv(1)
        status = struct.unpack(">B", status_data)[0]

        if status == 1:
            print("Erro não identificado, os bytes não serão esperados.")
            return
        elif status == 0:
            print("O upload foi aceito, os bytes serão esperados...")
        else:
            print(f"ERRO: Status desconhecido {status}")
            return

        full_file_path = os.path.join(SCRIPT_DIR, file_name)
        full_file_path = os.path.normpath(full_file_path)

        file_size = os.path.getsize(full_file_path)
        print(f"[-] Tamanho do arquivo: {file_size} bytes")

        size_bytes = struct.pack(">I", file_size)
        conn.send(size_bytes)

        if not full_file_path.startswith(os.path.abspath(SCRIPT_DIR)):
            print("[!] ATENCAO: Acesso fora do diretório de arquivos negado.")
            status = struct.pack(">B", 0)
            conn.send(status)
            return True

        bytes_sent = 0
        with open(full_file_path, "rb") as f:
            while True:
                data = f.read(BUFSIZE)
                if not data:
                    break
                conn.sendall(data)
                bytes_sent += len(data)
        print(f"{file_name} enviado com sucesso. ({bytes_sent}) bytes enviados")

        final_status_data = conn.recv(1)
        if final_status_data:
            final_status = struct.unpack(">B", final_status_data)[0]
            if final_status == 0:
                print("Servidor confirmou o recebimento com sucesso.")

        return True
        print(f"{file_name} enviado com sucesso. ({bytes_sent}) bytes enviados")
        return True
    except socket.timeout:
        print("ERRO: Tempo de espera excedido.")
    except ConnectionRefusedError:
        print("ERRO: Conexão resetada pelo servidor.")
    except Exception as e:
        print(f"Erro durante download: {e}")
