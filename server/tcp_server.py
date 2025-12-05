import socket
import struct
import os
import sys


def validar_ipv4(addr: str) -> bool:
    try:
        socket.inet_pton(socket.AF_INET, addr)
    except AttributeError:
        try:
            socket.inet_aton(addr)
        except socket.error:
            return False
        return addr.count('.') == 3
    except socket.error:
        return False
    return True


FILE_NAME = "lorem_ipsum.txt"


def send_file(s, file_name):
    bytes_sent = 0
    with open(file_name, 'rb') as f:
        while True:
            data = f.read(4096)
            if not data:
                break
            s.send(data)
    print(f"Arquivo {file_name} enviado com sucesso.")


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

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((HOST, PORT))
            s.listen(1)
            print(f"Servidor iniciado em {HOST}:{PORT}")
            print("Aguardando conexões...\n")

            while True:
                conn, addr = s.accept()
                print(f"\nNova conexão: {addr}")
                with conn:
                    while True:
                        try:
                            file_length_data = conn.recv(1)

                            if not file_length_data:
                                print(f"Cliente {addr} desonectou.")
                                break

                            file_name_length = struct.unpack(
                                '>B', file_length_data)[0]

                            file_name_data = conn.recv(file_name_length)
                            file_name = file_name_data.decode()

                            print(f"Arquivo solicitado: {file_name}")

                            if file_name != "lorem_ipsum.txt":
                                status = struct.pack('>B', 0)
                                conn.send(status)

                            status = struct.pack('>B', 1)
                            conn.send(status)
                            print(f"Arquivo encontrado: {FILE_NAME}")

                            file_size = os.path.getsize(FILE_NAME)
                            print(f"Tamanho do arquivo: {file_size} bytes")

                            size_bytes = struct.pack('>I', file_size)
                            conn.send(size_bytes)
                            send_file(conn, FILE_NAME)
                        except socket.timeout:
                            print("Timeout ao aguardar dados do cliente.")
                            continue
                        except UnicodeDecodeError as e:
                            print(f"Erro ao decodificar nome do arquivo: {e}")
                            try:
                                status = struct.pack('>B', 1)
                                conn.send(status)
                            except:
                                pass
                            continue
        except KeyboardInterrupt:
            print("\nEncerrando...")


if __name__ == "__main__":
    main()
