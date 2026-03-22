# Com o Middleware

import pika
import json
import time
from relogios import RelogioLamport, RelogioVetorial
# Consumidor

AMQP_URL = ''

class Cor:
    RESET = '\033[0m'
    VERDE = '\033[92m'
    AZUL = '\033[94m'
    VERMELHO = '\033[91m'
    AMARELO = '\033[93m'
    NEGRITO = '\033[1m'

lamport = RelogioLamport()
vetor = RelogioVetorial("apurador")
total_votos = {}

def processar_voto(ch, method, properties, body):
    try:
        msg = json.loads(body.decode('utf-8'))
        
        # Destaque
        tempo_recebido = msg.get("lamport", 0)
        vetor_recebido = msg.get("vetor", {})
        lamport.atualizar(tempo_recebido)
        vetor.atualizar(vetor_recebido)
        
        candidato = msg["dados"]["candidato"]
        origem = msg["origem_id"]
        
        total_votos[candidato] = total_votos.get(candidato, 0) + 1
        
        print(f"{Cor.VERDE}[✓] Voto processado da Urna {origem} para {candidato}{Cor.RESET}")
        print(f"    {Cor.AZUL}Relógio Lamport Atualizado:{Cor.RESET} L={lamport.pegar_valor()}")
        print(f"    {Cor.AMARELO}Vetor Causal:{Cor.RESET} {vetor.pegar_copia()}")
        print(f"    {Cor.NEGRITO}Apuração Parcial:{Cor.RESET} {total_votos}\n")
        
        time.sleep(1)

        # Destaque consistência
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        print(f"{Cor.VERMELHO}Erro ao processar: {e}{Cor.RESET}")
        ch.basic_nack(delivery_tag=method.delivery_tag)

def iniciar_consumidor():
    print(f"{Cor.NEGRITO}=== APURADOR CONECTANDO AO MIDDLEWARE RABBITMQ ==={Cor.RESET}")
    try:
        parameters = pika.URLParameters(AMQP_URL)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        channel.queue_declare(queue='fila_votos', durable=True)
        
        # Destaque exclusão mútua
        channel.basic_qos(prefetch_count=1)
        
        channel.basic_consume(queue='fila_votos', on_message_callback=processar_voto)
        
        print(f"{Cor.VERDE}Conectado com sucesso! A aguardar votos na fila...{Cor.RESET}\n")
        channel.start_consuming()
        
    except Exception as e:
        print(f"{Cor.VERMELHO}Erro de conexão: Verifique a sua AMQP_URL.{Cor.RESET}")
        print(e)

if __name__ == "__main__":
    iniciar_consumidor()