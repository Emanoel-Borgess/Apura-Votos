import socket
import time
import random
import json
import os
from relogios import RelogioLamport, RelogioVetorial

class Cor:
    RESET = '\033[0m'
    VERDE = '\033[92m'    
    AMARELO = '\033[93m'  
    AZUL = '\033[94m'     
    MAGENTA = '\033[95m'  
    VERMELHO = '\033[91m' 
    CIANO = '\033[96m'    
    CINZA = '\033[90m'   
    NEGRITO = '\033[1m'

NS_IP = 'localhost'
NS_PORTA = 8000
ARQUIVO_CONFIG = 'contador_urnas.txt'

id_urna = 1
if os.path.exists(ARQUIVO_CONFIG):
    try:
        with open(ARQUIVO_CONFIG, 'r') as f:
            id_urna = int(f.read().strip()) + 1
    except: pass
with open(ARQUIVO_CONFIG, 'w') as f: f.write(str(id_urna))

lamport = RelogioLamport()
vetor = RelogioVetorial(f"urna_{id_urna}")

def log_etapa(etapa, msg, cor, extra=""):
    print(f"{cor}{etapa:<12}{Cor.RESET} {msg} {Cor.CINZA}{extra}{Cor.RESET}")

def descobrir_apurador():
    print(f"{Cor.CINZA}A consultar Servidor de Nomes...{Cor.RESET}")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((NS_IP, NS_PORTA))
        s.send(json.dumps({"comando": "BUSCAR", "servico": "apurador_votos"}).encode('utf-8'))
        resp = json.loads(s.recv(1024).decode('utf-8'))
        s.close()
        if resp["status"] == "ENCONTRADO": return resp["ip"], resp["porta"]
    except: pass
    return None, None

def iniciar_urna():
    print(f"{Cor.NEGRITO}=== URNA {id_urna} (ETAPA 4: MUTEX & RELÓGIOS) ==={Cor.RESET}")
    
    ip, porta = descobrir_apurador()
    if not ip:
        print(f"{Cor.VERMELHO}ERRO: Apurador não encontrado.{Cor.RESET}")
        return

    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((ip, porta))
        print(f"{Cor.CIANO}Conectado ao Apurador em {ip}:{porta}{Cor.RESET}")
        print(f"Relógio Inicial: {lamport.pegar_valor()}")

        while True:
            time.sleep(random.uniform(2, 5)) 
            candidato = random.choice(["Candidato_A", "Candidato_B", "Candidato_C"])
            
            print(f"\n{Cor.NEGRITO}[AÇÃO] Eleitor a tentar votar em {candidato}...{Cor.RESET}")

            req_msg = {
                "tipo": "COMANDO", "acao": "REQUEST", "origem_id": id_urna,
                "lamport": lamport.incrementar(), "vetor": vetor.incrementar()
            }
            client.send(json.dumps(req_msg).encode('utf-8'))
            log_etapa("1. [REQUEST]", "Enviado. A aguardar GRANT...", Cor.AMARELO, f"(L={lamport.pegar_valor()})")

            while True:
                dados = client.recv(4096)
                if not dados: raise Exception("Conexão perdida")
                resp = json.loads(dados.decode('utf-8'))
                
                lamport.atualizar(resp.get("lamport", 0))
                vetor.atualizar(resp.get("vetor", {}))

                if resp.get("acao") == "GRANT":
                    log_etapa("2. [GRANT]", "Permissão recebida! A entrar na Secção Crítica.", Cor.VERDE)
                    break
            
            time.sleep(1)
            voto_msg = {
                "tipo": "COMANDO", "acao": "VOTAR", "origem_id": id_urna,
                "dados": {"candidato": candidato},
                "lamport": lamport.incrementar(), "vetor": vetor.incrementar()
            }
            client.send(json.dumps(voto_msg).encode('utf-8'))
            log_etapa("3. [VOTO]", f"Enviado: {candidato}", Cor.AZUL, f"Vetor: {vetor.pegar_copia()}")

            dados_conf = client.recv(4096)
            if dados_conf:
                resp_conf = json.loads(dados_conf.decode('utf-8'))
                lamport.atualizar(resp_conf.get("lamport", 0))
                vetor.atualizar(resp_conf.get("vetor", {}))
            rel_msg = {
                "tipo": "COMANDO", "acao": "RELEASE", "origem_id": id_urna,
                "lamport": lamport.incrementar(), "vetor": vetor.incrementar()
            }
            client.send(json.dumps(rel_msg).encode('utf-8'))
            log_etapa("4. [RELEASE]", "Enviado. Recurso libertado.", Cor.MAGENTA)
            
    except Exception as e:
        print(f"{Cor.VERMELHO}Erro: {e}{Cor.RESET}")
    finally:
        client.close()

if __name__ == "__main__":
    iniciar_urna()