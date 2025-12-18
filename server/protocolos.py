import socket
import struct
import os
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_DIR = os.path.join(SCRIPT_DIR, "files")
BUFFSIZE = 1024


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

        full_file_path = os.path.join(SCRIPT_DIR, file_name)
        full_file_path = os.path.normpath(full_file_path)

        if not full_file_path.startswith(os.path.abspath(SCRIPT_DIR)):
            print("[!] ATENCAO: Acesso fora do diretório de arquivos negado.")
            status = struct.pack(">B", 1)
            conn.send(status)
            return True

        if not os.path.exists(full_file_path):
            print(f"ERRO: Arquivo não encontrado: {full_file_path}")
            status = struct.pack(">B", 1)
            conn.send(status)
            return True

        status = struct.pack(">B", 0)
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
                conn.sendall(data)
                bytes_sent += len(data)

        print(f"{file_name} enviado com sucesso. ({bytes_sent}) bytes enviados")
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


def send_file_list(conn: socket.socket, addr: tuple):
    try:
        file_list = []

        if os.path.exists(SCRIPT_DIR):
            for fn in os.listdir(SCRIPT_DIR):
                file_path = os.path.join(SCRIPT_DIR, fn)

                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    file_list.append({"nome": fn, "tamanho": str(file_size)})
        print(f"[-] Total de arquivos encontrados: {len(file_list)}")

        json_data = json.dumps(file_list, ensure_ascii=False, indent=2)
        json_bytes = json_data.encode("utf-8")
        json_size = len(json_bytes)

        status = struct.pack(">B", 0)
        conn.send(status)

        json_size_data = struct.pack(">I", json_size)
        conn.send(json_size_data)

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


def receive_upload(conn: socket.socket, addr: tuple):
    try:
        file_length_data = conn.recv(4)

        if not file_length_data:
            print(f"Cliente {addr} desconectou.")
            return False

        file_name_length = struct.unpack(">I", file_length_data)[0]
        print(f"[-] Tamanho do nome: {file_name_length} bytes")

        file_name_data = conn.recv(file_name_length)
        file_name = file_name_data.decode('utf-8')
        print(f"[-] Arquivo a ser recebido {file_name}")

        full_file_path = os.path.join(SCRIPT_DIR, file_name)
        full_file_path = os.path.normpath(full_file_path)

        if not full_file_path.startswith(os.path.abspath(SCRIPT_DIR)):
            print("[!] ATENCAO: Acesso fora do diretório de arquivos negado.")
            status = struct.pack(">B", 1)
            conn.send(status)
            return True

        status = struct.pack(">B", 0)
        conn.send(status)
        print("[-] Upload aceito, os bytes serão esperados...")

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
                chunk = conn.recv(BUFFSIZE)
                if not chunk:
                    break
                f.write(chunk)
                bytes_received += len(chunk)
        print(f"Upload concluído! Arquivo salvo em {
              SCRIPT_DIR.split("/")[-1]}/{file_name}")

        if bytes_received == file_size:
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
