import json

class RelogioLamport:
    def __init__(self):
        self.valor = 0

    def incrementar(self):
        self.valor += 1
        return self.valor

    def atualizar(self, tempo_recebido):
        self.valor = max(self.valor, tempo_recebido) + 1
        return self.valor

    def pegar_valor(self):
        return self.valor

class RelogioVetorial:
    def __init__(self, meu_id):
        self.meu_id = meu_id
        self.vetor = {meu_id: 0}

    def incrementar(self):
        self.vetor[self.meu_id] += 1
        return self.vetor

    def atualizar(self, vetor_recebido):
        self.vetor[self.meu_id] += 1
        for id_proc, tempo in vetor_recebido.items():
            tempo_atual = self.vetor.get(id_proc, 0)
            self.vetor[id_proc] = max(tempo_atual, tempo)
        return self.vetor
    
    def pegar_copia(self):
        return self.vetor.copy()