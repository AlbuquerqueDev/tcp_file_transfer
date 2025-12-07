import socket
import struct
import sys


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


def user_interface(conn: socket):
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


def download_file(conn: socket):
    file_name = input("Informe o nome do arquivo para download: ")
    if not file_name:
        print("Informe um nome!")
        exit(1)

    file_name_length = len(file_name)

    byte_operacao = struct.pack(">B", 10)
    download_signal = conn.send(byte_operacao)

    if download_signal:
        fl_bytes = struct.pack(">I", file_name_length)
        conn.send(fl_bytes)
        print("[-] Enviando o tamanho do nome do arquivo...")

        fn_bytes = file_name.encode("utf-8")
        conn.send(fn_bytes)
        print("[-] Enviando o nome do arquivo...")

    print(f"Arquivo solicitado: {file_name}")

    try:
        status_data = conn.recv(1)
    except socket.timeout:
        print("ERRO: tempo de espera excedido.")
        exit(1)

    status = struct.unpack(">B", status_data)[0]

    if status == 0:
        print("Arquivo não existe.")
        exit(1)
    elif status == 1:
        print("Arquivo encontrado! Iniciando o download.")
    else:
        print("Erro durante a requisição do nome de arquivo.")
        exit(1)
    try:
        file_size_bytes = conn.recv(4)
    except socket.timeout:
        print("ERRO: tempo de espera excedido.")
        exit(1)
    except socket.ConnectionRefusedError:
        print("ERRO: Conexão perdida: porta inacessiva")
        exit(1)

    if len(file_size_bytes) != 4:
        print("tamanho de arquivo inválido.")
        exit(1)

    file_size = struct.unpack(">I", file_size_bytes)[0]

    print(f"Tamanho do arquivo: {file_size} bytes")

    file_data = b""
    bytes_received = 0

    while bytes_received < file_size:
        try:
            chunk = conn.recv(1024)
        except socket.timeout:
            print("ERRO: tempo de espera excedido!")
            exit(1)
        file_data += chunk
        bytes_received += len(chunk)

    output_name = f"baixado_{file_name}"

    with open(output_name, "wb") as f:
        f.write(file_data)


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

    print(f"Conectando ao servidor {HOST}:{PORT}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            print(f"Conectado no host: {HOST}:{PORT}")

            user_interface(s)

        except ConnectionRefusedError:
            print(f"Erro: Não foi possível conectar ao servidor {HOST}:{PORT}")
            print("Verifique se o servidor está acessível.")
            exit(1)
        except KeyboardInterrupt:
            print("\nEncerrando...")
            exit(1)


if __name__ == "__main__":
    main()
