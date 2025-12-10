import json
import os
import socket
import struct
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_DIR = os.path.join(SCRIPT_DIR, "downloaded_files")
BUFFSIZE = 1024


def validar_ipv4(addr: str) -> bool:
    try:
        socket.inet_pton(socket.AF_INET, addr)
    except AttributeError:
        try:
            socket.inet_aton(addr)
        except socket.error:
            return False
        return addr.count(".") == 3
    except socket.error:
        return False
    return True


def create_file_dir():
    if not os.path.exists(FILE_DIR):
        try:
            print(f"Criando o diretório de arquivos para download: {
                  FILE_DIR}\n")
            os.makedirs(FILE_DIR, exist_ok=True)
            print(f"Diretório {FILE_DIR} criado com sucesso!\n")
        except Exception as e:
            print(f"ERRO: Não foi possível criar o diretório '{
                  FILE_DIR}': {e}\n")


def user_interface(conn: socket):
    while True:
        print("=" * 20)
        print("TCP Fileserver")
        print("=" * 20)

        print("-" * 20)
        print("O que deseja fazer?")
        print("[1] Baixar um arquivo")
        print("[2] Listar arquivos disponíveis")
        print("-" * 20)

        opcao = input("Digite uma opcao: ").strip()

        match opcao:
            case "1":
                download_file(conn)
            case "2":
                list_files(conn)
            case _:
                print("Operacao inválida.")


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

        if status == 0:
            print("ERRO: Arquivo não existe no servidor.")
            return
        elif status == 1:
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

        file_data = b""
        bytes_received = 0

        while bytes_received < file_size:
            chunk = conn.recv(min(BUFFSIZE, file_size - bytes_received))
            if not chunk:
                print("ERRO: Conexão fechada durante download.")
                return
            file_data += chunk
            bytes_received += len(chunk)

        output_name = os.path.join(FILE_DIR, file_name)

        with open(output_name, "wb") as f:
            f.write(file_data)

        print(f"Download concluído! Arquivo salvo em {output_name}")
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

        if status == 0:
            print("Erro durante o envio de listagem.")
            return
        elif status != 1:
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
            chunk = conn.recv(min(BUFFSIZE, list_size - bytes_received))
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


def main():
    if len(sys.argv) != 3:
        print("Exemplo de uso: tcp_client <HOST> <PORTA>")
        exit(1)

    HOST = sys.argv[1]

    if not validar_ipv4(HOST):
        print(f"Erro: '{HOST}' não é um endereço IP válido!")
        exit(1)
    try:
        PORT = int(sys.argv[2])
    except ValueError:
        print("Erro: A porta deve ser um número inteiro.")

    if PORT < 1024 or PORT > 65535:
        print("Erro: A porta deve estar entre 1024 e 65535.")
        exit(1)

    create_file_dir()

    print(f"Conectando ao servidor {HOST}:{PORT}")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            print(f"\nConexão estabelecida com o host: {HOST}:{PORT}")

            user_interface(s)

    except ConnectionRefusedError:
        print(f"Erro: Não foi possível conectar ao servidor {HOST}:{PORT}")
        print("Verifique se o servidor está acessível.")
        exit(1)
    except KeyboardInterrupt:
        print("\nEncerrando...")
        exit(0)
    except Exception as e:
        print(f"ERRO: {e}")


if __name__ == "__main__":
    main()
