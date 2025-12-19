import socket
import os
import struct
import threading
import protocolos as p

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_DIR = os.path.join(FILE_DIR, "arquivos")

print_lock = threading.Lock()

clientes_ativos = 0
cliente_lock = threading.Lock()


def mensagem(msg):
    with print_lock:
        print(msg)


def gerenciar_cliente(conn: socket.socket, addr: tuple):

    global clientes_ativos

    with cliente_lock:
        clientes_ativos += 1
        mensagem("-" * 20)
        mensagem(f"[+] Cliente {addr} está conectado.")
        mensagem(f"[+] Clientes ativos: {clientes_ativos}")
        mensagem("-" * 20)
    try:
        with conn:
            while True:
                byte_operacao = conn.recv(1)

                if not byte_operacao:
                    mensagem(f"[-] Cliente {addr} desconectou.")
                    break

                codigo = struct.unpack(">B", byte_operacao)[0]
                mensagem(
                    f"\n[{addr}] Codigo de operacao recebido: {codigo}")

                match codigo:
                    case 10:
                        mensagem(f"[{addr}] 10 - Download de arquivo")
                        if not p.enviar_arquivo(conn, addr):
                            break
                    case 20:
                        mensagem(f"[{addr}] 20 - Listar arquivos")
                        if not p.enviar_listagem(conn, addr):
                            break
                    case 30:
                        mensagem(f"[{addr}] 30 - Upload de arquivos")
                        if not p.receber_arquivo(conn, addr):
                            break
                    case _:
                        mensagem(
                            f"[{addr}] Operacao inválida ({codigo})")

                        try:
                            status = struct.pack(">B", 1)
                            conn.send(status)
                        except:
                            pass
    except socket.timeout:
        mensagem(f"[{addr}] Tempo de espera excedido.")
    except ConnectionResetError:
        mensagem(f"[{addr}] Conexão resetada pelo cliente.")
    except BrokenPipeError:
        mensagem(f"[{addr}] Pipe quebrado.")
    except Exception as e:
        mensagem(f"[{addr}] Erro durante conexão: {e}")
    finally:

        with cliente_lock:
            clientes_ativos -= 1
            mensagem("-" * 20)
            mensagem(f"[-] Cliente {addr} desconectado.")
            mensagem(f"[-] Clientes ativos: {clientes_ativos}")
            mensagem("-" * 20)


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
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        s.bind((HOST, PORT))
        s.listen(5)

        print("Servidor TCP Iniciado!")

        try:
            hostname = socket.gethostname()
            ips = socket.gethostbyname_ex(hostname)[2]

            print("Aguardando conexões nos seguintes endereços:")
            print("-" * 20)
            for ip in ips:
                print(f"{ip}:20000")
            print("-" * 20)
        except socket.error as e:
            print(f"Erro inesperado: {e}")

        while True:
            try:
                conn, addr = s.accept()
                thread_cliente = threading.Thread(
                    target=gerenciar_cliente, args=(conn, addr), daemon=True)
                thread_cliente.start()
            except KeyboardInterrupt:
                print("\nEncerrando...")
                break
            except Exception as e:
                print(f"Erro durante conexão: {e}")
                continue

    except KeyboardInterrupt:
        print("\nEncerrando...")
    finally:
        print("\nEncerrando servidor...")
        s.close()

        print("Aguardando clientes desconectarem...")
        thread_principal = threading.current_thread()
        for thread in threading.enumerate():
            if thread != thread_principal:
                thread.join(timeout=2)
        print("\nServidor encerrado com sucesso.")


if __name__ == "__main__":
    main()
