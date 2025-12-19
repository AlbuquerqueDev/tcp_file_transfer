import os
import socket
import sys
import protocolos as p


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


def main():
    if len(sys.argv) != 3:
        print("Exemplo de uso: tcp_client <HOST> <PORTA>")
        exit(1)

    HOST = sys.argv[1]

    if not validar_ipv4(HOST):
        print(f"Erro: '{HOST}' não é um endereço IP válido!")
        exit(1)
    try:
        PORTA = int(sys.argv[2])
    except ValueError:
        print("Erro: A porta deve ser um número inteiro.")

    if PORTA < 1024 or PORTA > 65535:
        print("Erro: A porta deve estar entre 1024 e 65535.")
        exit(1)

    FILE_DIR = os.path.dirname(os.path.abspath(__file__))
    FILE_DIR = os.path.join(FILE_DIR, "arquivos_baixados")

    if not os.path.exists(FILE_DIR):
        try:
            print(f"Criando o diretório de arquivos para download: {
                  FILE_DIR}\n")
            os.makedirs(FILE_DIR, exist_ok=True)
            print(f"Diretório {FILE_DIR} criado com sucesso!\n")
        except Exception as e:
            print(f"ERRO: Não foi possível criar o diretório '{
                  FILE_DIR}': {e}\n")

    print(f"Conectando ao servidor {HOST}:{PORTA}")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORTA))
            print(f"\nConexão estabelecida com o host: {HOST}:{PORTA}")

            while True:
                print("=" * 20)
                print("TCP Fileserver")
                print("=" * 20)

                print("-" * 20)
                print("O que deseja fazer?")
                print("[1] Baixar um arquivo")
                print("[2] Listar arquivos disponíveis")
                print("[3] Fazer um upload de arquivo")
                print("[0] Encerrar cliente")
                print("-" * 20)

                opcao = input("Digite uma opcao: ").strip()

                match opcao:
                    case "1":
                        p.baixar_arquivo(s)
                    case "2":
                        p.listar_arquivos(s)
                    case "3":
                        p.upload_arquivo(s)
                    case "0":
                        break
                    case _:
                        print("Operacao inválida.")

    except ConnectionRefusedError:
        print(f"Erro: Não foi possível conectar ao servidor {HOST}:{PORTA}")
        print("Verifique se o servidor está acessível.")
        exit(1)
    except KeyboardInterrupt:
        print("\nEncerrando...")
        exit(0)
    except Exception as e:
        print(f"ERRO: {e}")


if __name__ == "__main__":
    main()
