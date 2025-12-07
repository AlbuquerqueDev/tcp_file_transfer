import json
import os
import socket
import struct
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_DIR = os.path.join(SCRIPT_DIR, "files")
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
            print(f"Criando o diretório de arquivos para download: {FILE_DIR}\n")
            os.makedirs(FILE_DIR, exist_ok=True)
            print(f"Diretório {FILE_DIR} criado com sucesso!\n")
        except Exception as e:
            print(f"ERRO: Não foi possível criar o diretório '{FILE_DIR}': {e}\n")
            exit(1)


def send_file(conn: socket, addr: tuple):
    try:
        file_length_data = conn.recv(4)

        if not file_length_data:
            print(f"Cliente {addr} desonectou.")
            return False

        file_name_length = struct.unpack(">I", file_length_data)[0]
        print(f"[-] Tamanho do nome: {file_name_length} bytes")

        file_name_data = conn.recv(file_name_length)
        file_name = file_name_data.decode("utf-8")
        print(f"[-] Arquivo solicitado: {file_name}")

        full_file_path = os.path.join(FILE_DIR, file_name)
        full_file_path = os.path.normpath(full_file_path)

        if not full_file_path.startswith(os.path.abspath(FILE_DIR)):
            print("[!] ATENCAO: Acesso fora do diretório de arquivos negado.")
            status = struct.pack(">B", 0)
            conn.send(status)
            return True

        if not os.path.exists(full_file_path):
            print(f"ERRO: Arquivo não encontrado: {full_file_path}")
            status = struct.pack(">B", 0)
            conn.send(status)
            return True

        status = struct.pack(">B", 1)
        conn.send(status)
        print(f"Arquivo encontrado: {file_name}")

        file_size = os.path.getsize(full_file_path)
        print(f"[-] Tamanho do arquivo: {file_size} bytes")

        size_bytes = struct.pack(">I", file_size)
        conn.send(size_bytes)

        bytes_sent = 0
        with open(full_file_path, "rb") as f:
            while True:
                data = f.read(BUFFSIZE)
                if not data:
                    break
                conn.send(data)
                bytes_sent += len(data)

        print(f"{file_name} enviado com sucesso. ({bytes_sent}) bytes enviados")
        return True
    except UnicodeDecodeError as e:
        print(f"Erro ao decodificar nome do arquivo: {e}")
        try:
            status = struct.pack(">B", 0)
            conn.send(status)
        except:
            pass
        return False
    except Exception as e:
        print(f"Erro durante envio do arquivo: {e}")
        return False


def send_file_list(conn: socket.socket, addr: tuple):
    try:
        file_list = []

        if os.path.exists(FILE_DIR):
            for fn in os.listdir(FILE_DIR):
                file_path = os.path.join(FILE_DIR, fn)

                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    file_list.append({"nome": fn, "tamanho": str(file_size)})
        print(f"[-] Total de arquivos encontrados: {len(file_list)}")

        json_data = json.dumps(file_list, ensure_ascii=False, indent=2)
        json_bytes = json_data.encode("utf-8")
        json_size = len(json_bytes)

        status = struct.pack(">B", 1)
        conn.send(status)

        json_size_data = struct.pack(">I", json_size)
        conn.send(json_size_data)

        conn.send(json_bytes)

        print(f"Lista de arquivos enviada com sucesso para {addr}")
        return True
    except Exception as e:
        print(f"Erro ao enviar lista de arquivos: {e}")
        try:
            status = struct.pack(">B", 0)
            conn.send(status)
        except:
            pass
        return False


def gerenciar_client(conn: socket.socket, addr: tuple):
    try:
        while True:
            operation_byte = conn.recv(1)

            if not operation_byte:
                print(f"Cliente {addr} desconectou.")
                break

            signal_code = struct.unpack(">B", operation_byte)[0]
            print(f"\n[-] Codigo de operacao recebido: {signal_code}")

            match signal_code:
                case 10:
                    print("[-] 10 - Download de arquivo")
                    if not send_file(conn, addr):
                        break
                case 20:
                    print("[-] 20 - Listar arquivos")
                    if not send_file_list(conn, addr):
                        break
                case _:
                    print(f"Operacao inválida ({signal_code})")

                    try:
                        status = struct.pack(">B", 0)
                        conn.send(status)
                    except:
                        pass
    except socket.timeout:
        print("ERRO: Tempo de espera excedido.")
    except ConnectionRefusedError:
        print("ERRO: Conexão resetada pelo cliente.")


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

    if PORT < 1 or PORT > 65535:
        print("Erro: A porta deve estar entre 1 e 65535.")
        exit(1)

    # inicia o diretório de arquivos
    create_file_dir()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((HOST, PORT))
        s.listen(5)

        print(f"Servidor iniciado em {HOST}:{PORT}")
        print(f"Diretório de arquivos: {FILE_DIR}")
        print("Aguardando conexões...\n")

        while True:
            try:
                conn, addr = s.accept()
                with conn:
                    gerenciar_client(conn, addr)

            except KeyboardInterrupt:
                print("\nEncerrando...")
                break
            except Exception as e:
                print(f"Erro durante conexão: {e}")
                continue
    except KeyboardInterrupt:
        print("\nEncerrando...")

    print("\nEncerrando servidor...")
    s.close()


if __name__ == "__main__":
    main()
