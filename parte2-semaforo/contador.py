"""Corrida controlada e exclusão mútua com Semaphore(1). Python 3.10+."""
import argparse
import json
import threading
import time


def executar(modo, total_threads, incrementos, ceder_cada):
    contador = 0
    semaforo = threading.Semaphore(1)
    inicio = threading.Barrier(total_threads + 1)
    # Apenas na corrida: todos leem o primeiro valor antes de qualquer escrita.
    primeira_leitura = threading.Barrier(total_threads)
    erros = []
    mutex_erros = threading.Lock()

    def incrementar(i):
        nonlocal contador
        anterior = contador
        if modo == "sem" and i == 0:
            primeira_leitura.wait()
        # Mesma cessão periódica em ambos os modos, dentro do read/modify/write.
        # Na versão protegida o semáforo continua retido durante a cessão.
        if i % ceder_cada == 0:
            time.sleep(0)
        contador = anterior + 1

    def tarefa():
        try:
            inicio.wait()
            for i in range(incrementos):
                if modo == "com":
                    semaforo.acquire()
                    try:
                        incrementar(i)
                    finally:
                        semaforo.release()
                else:
                    incrementar(i)
        except BaseException as erro:
            with mutex_erros:
                erros.append(repr(erro))

    threads = [threading.Thread(target=tarefa) for _ in range(total_threads)]
    for t in threads:
        t.start()
    t0 = time.perf_counter()
    inicio.wait()
    for t in threads:
        t.join()
    segundos = time.perf_counter() - t0
    assert not erros, erros
    esperado = total_threads * incrementos
    if modo == "com":
        assert contador == esperado, (contador, esperado)
    else:
        assert contador < esperado, "A corrida controlada deveria perder incrementos"
    return dict(modo=modo, threads=total_threads, incrementos=incrementos,
                ceder_cada=ceder_cada, esperado=esperado, obtido=contador,
                perdidos=esperado-contador, segundos=round(segundos, 6),
                tentativas_por_segundo=round(esperado/segundos, 2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("modo", choices=["sem", "com"])
    p.add_argument("--threads", type=int, default=8)
    p.add_argument("--incrementos", type=int, default=200_000)
    p.add_argument("--ceder-cada", type=int, default=1000)
    a = p.parse_args()
    if a.threads < 2 or a.incrementos < 1 or a.ceder_cada < 1:
        p.error("Use threads >= 2 e demais parâmetros positivos")
    print(json.dumps(executar(a.modo, a.threads, a.incrementos, a.ceder_cada)))
