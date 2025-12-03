import socket
import struct
import os

HOST = '10.25.1.115'
PORT = 60000

FILE_NAME = "teste.txt"

def send_file(s, file_name):
    bytes_sent = 0
    with open(file_name, 'rb') as f:
        while True:
            data = f.read(4096)
            if not data:
                break
            s.send(data)
    print(f"Arquivo {file_name} enviado com sucesso.")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    try:

        s.bind((HOST, PORT))
        
        s.listen(1)
        print(f"Aceitando conexões em {HOST}:{PORT}")

        conn, addr = s.accept()
        with conn:
            while True:
                try:
                    file_length_data = conn.recv(1)
                    file_name_length = struct.unpack('>B', file_length_data)[0]

                    file_name_data = conn.recv(file_name_length)
                    file_name = file_name_data.decode()

                    print(f"Arquivo solicitado: {file_name}")

                    if file_name != "teste.txt":
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