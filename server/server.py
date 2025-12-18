import socket
import os
import struct
import protocolos as p

BUFFSIZE = 1024
FILE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_DIR = os.path.join(FILE_DIR, "files")


def main():

    HOST = ''
    PORT = 20000

    if not os.path.exists(FILE_DIR):
        try:
            print(f"Criando o diretório de arquivos para download: {
                  FILE_DIR}\n")
            os.makedirs(FILE_DIR, exist_ok=True)
            print(f"Diretório {FILE_DIR} criado com sucesso!\n")
        except Exception as e:
            print(f"ERRO: Não foi possível criar o diretório '{
                  FILE_DIR}': {e}\n")
            exit(1)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((HOST, PORT))
        print("Servidor TCP Iniciado!")

        s.listen(5)
        ips = []
        try:
            hostname = socket.gethostname()

            ip_list = socket.gethostbyname_ex(hostname)[2]

            print("Aguardando conexões nos seguintes endereços...")
            print("-" * 20)
            for ip in ip_list:
                if not ip.startswith('127.'):
                    ips.append(ip)
                    print(ip)
            print("-" * 20)
        except socket.error as e:
            print(f'Erro durante obtenção de ips: {e}')
            exit(1)

        while True:
            try:
                conn, addr = s.accept()
                print(f"Cliente {addr} está conectado.")
                with conn:
                    while True:
                        operation_byte = conn.recv(1)

                        if not operation_byte:
                            print(f"Cliente {addr} desconectou.")
                            break

                        signal_code = struct.unpack(">B", operation_byte)[0]
                        print(
                            f"\n[-] Codigo de operacao recebido: {signal_code}")

                        match signal_code:
                            case 10:
                                print("[-] 10 - Download de arquivo")
                                if not p.send_file(conn, addr):
                                    break
                            case 20:
                                print("[-] 20 - Listar arquivos")
                                if not p.send_file_list(conn, addr):
                                    break
                            case 30:
                                print("[-] 30 - Upload de arquivos")
                                if not p.receive_upload(conn, addr):
                                    break
                            case _:
                                print(f"Operacao inválida ({signal_code})")

                                try:
                                    status = struct.pack(">B", 1)
                                    conn.send(status)
                                except:
                                    pass
            except socket.timeout:
                print("ERRO: Tempo de espera excedido.")
            except ConnectionRefusedError:
                print("ERRO: Conexão resetada pelo cliente.")
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
