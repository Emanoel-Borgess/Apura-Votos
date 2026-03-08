import pika
import json
import time
import random
import os
from relogios import RelogioLamport, RelogioVetorial

AMQP_URL = 'amqps://byvqrtaq:vzbx1gqhQgU8s-OTsKi1ScdaBK7um0UK@gerbil.rmq.cloudamqp.com/byvqrtaq'

class Cor:
    RESET = '\033[0m'
    CIANO = '\033[96m'
    AMARELO = '\033[93m'
    MAGENTA = '\033[95m'
    NEGRITO = '\033[1m'


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

def iniciar_urna():
    print(f"{Cor.NEGRITO}=== URNA {id_urna} CONECTANDO AO MIDDLEWARE ==={Cor.RESET}")
    try:
        parameters = pika.URLParameters(AMQP_URL)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        
        channel.queue_declare(queue='fila_votos', durable=True)
        print(f"{Cor.CIANO}Urna {id_urna} conectada ao RabbitMQ com sucesso!{Cor.RESET}\n")

        while True:
            time.sleep(random.uniform(2, 5))
            candidato = random.choice(["Candidato_A", "Candidato_B", "Candidato_C"])
            
            
            l_time = lamport.incrementar()
            v_time = vetor.incrementar()
            
            msg = {
                "tipo": "EVENTO",
                "acao": "VOTO",
                "origem_id": id_urna,
                "dados": {"candidato": candidato},
                "lamport": l_time,
                "vetor": v_time
            }
            
            print(f"{Cor.NEGRITO}[AÇÃO] Eleitor a votar em {candidato}...{Cor.RESET}")
            
            channel.basic_publish(
                exchange='',
                routing_key='fila_votos',
                body=json.dumps(msg),
                properties=pika.BasicProperties(
                    delivery_mode=2, 
                )
            )
            
            print(f"{Cor.AMARELO}[PUBLICADO]{Cor.RESET} Voto enviado para a Fila do RabbitMQ.")
            print(f"   {Cor.MAGENTA}Lamport: L={l_time} | Vetor: {v_time}{Cor.RESET}\n")

    except Exception as e:
        print(f"Erro de conexão com o Middleware: {e}")
    finally:
        if 'connection' in locals() and connection.is_open:
            connection.close()

if __name__ == "__main__":
    iniciar_urna()