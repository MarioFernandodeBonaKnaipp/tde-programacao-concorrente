"""Jantar dos Filósofos: versão ingênua e garçom FIFO. Python 3.10+."""
import argparse
from collections import deque
import faulthandler
import threading
import time

N = 5
saida = threading.Lock()


def log(p, mensagem):
    with saida:
        print(f"P{p}: {mensagem}", flush=True)


def ingenua():
    garfos = [threading.Lock() for _ in range(N)]
    barreira = threading.Barrier(N)
    tentando = [threading.Event() for _ in range(N)]

    def filosofo(p):
        log(p, "pensando")
        log(p, "com fome")
        # Garfo p fica entre Pp e P(p+1). Pp usa p e (p-1) mod N.
        with garfos[p]:
            log(p, f"segura garfo {p}")
            barreira.wait()
            log(p, f"aguarda garfo {(p-1) % N}")
            tentando[p].set()
            with garfos[(p-1) % N]:
                log(p, "comendo")

    threads = [threading.Thread(target=filosofo, args=(p,), name=f"P{p}")
               for p in range(N)]
    for t in threads:
        t.start()
    for evento in tentando:
        evento.wait()
    # Os cinco primeiros garfos continuam retidos: ninguém pode obter o segundo.
    print("DEADLOCK: todos retêm um garfo e precisam de outro retido.", flush=True)
    faulthandler.dump_traceback()
    for t in threads:
        t.join()  # intencional: o supervisor externo encerrará este processo


class GarcomFIFO:
    """Reserva os DOIS garfos atomicamente, em ordem de chegada à fila."""
    def __init__(self):
        self.condicao = threading.Condition()
        self.fila = deque()
        self.livres = [True] * N
        self.comendo = set()
        self.max_simultaneos = 0

    def adquirir(self, p):
        a, b = p, (p - 1) % N
        with self.condicao:
            self.fila.append(p)
            while self.fila[0] != p or not (self.livres[a] and self.livres[b]):
                self.condicao.wait()
            self.fila.popleft()
            self.livres[a] = self.livres[b] = False
            assert (p - 1) % N not in self.comendo
            assert (p + 1) % N not in self.comendo
            self.comendo.add(p)
            self.max_simultaneos = max(self.max_simultaneos, len(self.comendo))
            self.condicao.notify_all()

    def liberar(self, p):
        with self.condicao:
            self.comendo.remove(p)
            self.livres[p] = self.livres[(p-1) % N] = True
            self.condicao.notify_all()


def corrigida(refeicoes):
    garcom = GarcomFIFO()
    inicio = threading.Barrier(N)
    contagens = [0] * N
    erros = []

    def filosofo(p):
        try:
            inicio.wait()
            for _ in range(refeicoes):
                log(p, "pensando")
                time.sleep(0.001 * (p + 1))
                log(p, "com fome")
                garcom.adquirir(p)
                try:
                    log(p, "comendo")
                    time.sleep(0.003)
                    contagens[p] += 1
                finally:
                    garcom.liberar(p)
                log(p, "pensando (garfos devolvidos)")
        except BaseException as erro:
            with saida:
                erros.append(repr(erro))

    threads = [threading.Thread(target=filosofo, args=(p,), name=f"P{p}")
               for p in range(N)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not erros, erros
    assert contagens == [refeicoes] * N, contagens
    assert all(garcom.livres) and not garcom.comendo and not garcom.fila
    print(f"OK: refeições por filósofo={contagens}; máximo simultâneo={garcom.max_simultaneos}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("modo", choices=["ingenua", "corrigida"])
    parser.add_argument("--refeicoes", type=int, default=5)
    args = parser.parse_args()
    if args.refeicoes < 1:
        parser.error("refeicoes deve ser positivo")
    ingenua() if args.modo == "ingenua" else corrigida(args.refeicoes)
