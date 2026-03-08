import socket
import threading
import json

class Cor:
    RESET = '\033[0m'
    VERDE = '\033[92m'
    CIANO = '\033[96m'
    AMARELO = '\033[93m'
    VERMELHO = '\033[91m'
    NEGRITO = '\033[1m'
    CINZA = '\033[90m'

HOST = 'localhost'
PORTA = 8000 
registro_servicos = {}

def log(tag, mensagem, cor):
    print(f"{cor}[{tag}]{Cor.RESET} {mensagem}")

def lidar_cliente(conn, addr):
    try:
        dados = conn.recv(1024).decode('utf-8')
        if not dados: return
        
        mensagem = json.loads(dados)
        comando = mensagem.get("comando")
        resposta = {}

        if comando == "REGISTRAR":
            servico = mensagem.get("servico")
            porta_alvo = mensagem.get("porta")
            registro_servicos[servico] = (addr[0], porta_alvo)
            log("REGISTO", f"Serviço '{servico}' salvo em {addr[0]}:{porta_alvo}", Cor.VERDE)
            resposta = {"status": "SUCESSO", "msg": "Serviço registado"}
        elif comando == "BUSCAR":
            servico = mensagem.get("servico")
            endereco = registro_servicos.get(servico)
            if endereco:
                log("CONSULTA", f"A enviar endereço de '{servico}' para {addr}", Cor.CIANO)
                resposta = {
                    "status": "ENCONTRADO", 
                    "ip": endereco[0], 
                    "porta": endereco[1]
                }
            else:
                log("ERRO", f"Alguém pediu '{servico}' mas não encontrei no registo.", Cor.AMARELO)
                resposta = {"status": "ERRO", "msg": "Serviço não encontrado"}
        
        conn.send(json.dumps(resposta).encode('utf-8'))
    
    except json.JSONDecodeError:
        log("ERRO", f"Recebi dados inválidos de {addr}", Cor.VERMELHO)
    except Exception as e:
        log("ERRO", f"{e}", Cor.VERMELHO)
    finally:
        conn.close()

def main():
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((HOST, PORTA))
        server.listen()
        
        print(f"{Cor.NEGRITO}--- SERVIDOR DE NOMES INICIADO NA PORTA {PORTA} ---{Cor.RESET}")
        print(f"{Cor.CINZA}A aguardar registos e consultas...{Cor.RESET}")
        
        while True:
            conn, addr = server.accept()
            t = threading.Thread(target=lidar_cliente, args=(conn, addr))
            t.daemon = True
            t.start()
            
    except OSError:
        log("FATAL", "A porta 8000 já está em uso! Verifique se já não tem um terminal aberto.", Cor.VERMELHO)

if __name__ == "__main__":
    main()