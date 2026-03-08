import socket
import threading
import json
import time
import heapq
from relogios import RelogioLamport, RelogioVetorial

class Cor:
    RESET = '\033[0m'
    VERDE = '\033[92m'    
    AMARELO = '\033[93m'  
    AZUL = '\033[94m'     
    MAGENTA = '\033[95m'  
    VERMELHO = '\033[91m' 
    CINZA = '\033[90m'   
    NEGRITO = '\033[1m'

HOST = 'localhost'
PORTA = 5000 
NS_IP = 'localhost'
NS_PORTA = 8000

fila_mutex = []
mutex_lock = threading.Lock()
recurso_ocupado = False

lamport = RelogioLamport()
vetor = RelogioVetorial("apurador")

def log_mutex(acao, msg, detalhes=""):
    cor = Cor.RESET
    if acao == "REQUEST": cor = Cor.AMARELO
    elif acao == "GRANT": cor = Cor.VERDE
    elif acao == "RELEASE": cor = Cor.MAGENTA
    elif acao == "VOTO": cor = Cor.AZUL
    
    print(f"{cor}[{acao:<7}]{Cor.RESET} {msg} {Cor.CINZA}{detalhes}{Cor.RESET}")

def registrar_no_ns():
    print(f"{Cor.CINZA}A tentar registar no Servidor de Nomes...{Cor.RESET}")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((NS_IP, NS_PORTA))
        msg = {"comando": "REGISTRAR", "servico": "apurador_votos", "porta": PORTA}
        sock.send(json.dumps(msg).encode('utf-8'))
        resp = json.loads(sock.recv(1024).decode('utf-8'))
        print(f"{Cor.VERDE}[NS] Estado: {resp['status']}{Cor.RESET}")
        sock.close()
    except Exception as e:
        print(f"{Cor.AMARELO}[AVISO] Sem Servidor de Nomes: {e}{Cor.RESET}")

def processar_fila():
    global recurso_ocupado
    with mutex_lock:
        if not recurso_ocupado and fila_mutex:
            tempo, id_origem, conn_cliente = heapq.heappop(fila_mutex)
            recurso_ocupado = True
            log_mutex("GRANT", f"Concedido para Urna {id_origem}", f"(T_Lamport={tempo})")
            msg_grant = {
                "tipo": "COMANDO", "acao": "GRANT",
                "lamport": lamport.incrementar(), "vetor": vetor.incrementar()
            }
            try:
                conn_cliente.send(json.dumps(msg_grant).encode('utf-8'))
            except:
                log_mutex("ERRO", f"Falha ao enviar GRANT para Urna {id_origem}", "", Cor.VERMELHO)
                recurso_ocupado = False

def lidar_com_urna(conn, endereco):
    global recurso_ocupado
    print(f"{Cor.CINZA}[CONEXÃO] {endereco} conectada.{Cor.RESET}")
    while True:
        try:
            dados = conn.recv(4096)
            if not dados: break

            try:
                msg = json.loads(dados.decode('utf-8'))
                tempo_recebido = msg.get("lamport", 0)
                vetor_recebido = msg.get("vetor", {})
                lamport.atualizar(tempo_recebido)
                vetor.atualizar(vetor_recebido)
                tipo = msg.get("tipo")
                acao = msg.get("acao")
                origem = msg.get("origem_id")
                if tipo == "COMANDO" and acao == "REQUEST":
                    log_mutex("REQUEST", f"Recebido de Urna {origem}", f"| L: {tempo_recebido}")
                    with mutex_lock:
                        heapq.heappush(fila_mutex, (tempo_recebido, origem, conn))
                    processar_fila()
                elif tipo == "COMANDO" and acao == "VOTAR":
                    candidato = msg["dados"]["candidato"]
                    log_mutex("VOTO", f"{candidato} (Urna {origem})", f"| Vetor: {vetor.pegar_copia()}")
                    resp = {
                        "tipo": "EVENTO", "evento": "VOTO_PROCESSADO",
                        "lamport": lamport.incrementar(), "vetor": vetor.incrementar()
                    }
                    conn.send(json.dumps(resp).encode('utf-8'))
                elif tipo == "COMANDO" and acao == "RELEASE":
                    log_mutex("RELEASE", f"Urna {origem} libertou.", "Recurso livre.")
                    with mutex_lock:
                        recurso_ocupado = False
                    processar_fila()

            except json.JSONDecodeError:
                pass

        except Exception:
            break

    conn.close()

if __name__ == "__main__":
    print(f"{Cor.NEGRITO}--- APURADOR INICIADO (PORTA {PORTA}) ---{Cor.RESET}")
    registrar_no_ns()
    try:
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.bind((HOST, PORTA))
        servidor.listen()
        while True:
            conn, endereco = servidor.accept()
            t = threading.Thread(target=lidar_com_urna, args=(conn, endereco))
            t.daemon = True
            t.start()
    except OSError as e:
        print(f"{Cor.VERMELHO}ERRO CRÍTICO: Porta ocupada ou erro de rede: {e}{Cor.RESET}")