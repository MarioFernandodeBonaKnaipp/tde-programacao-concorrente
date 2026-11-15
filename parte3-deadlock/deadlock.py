"""Duas threads, dois locks; deadlock determinístico e correção por ordem global."""
import argparse
import faulthandler
import threading
import time


def executar(modo):
    a, b = threading.Lock(), threading.Lock()
    barreira = threading.Barrier(2)
    tentando = [threading.Event(), threading.Event()]
    concluidas = []
    erros = []
    saida = threading.Lock()

    def log(texto):
        with saida:
            print(texto, flush=True)

    def tarefa(numero):
        primeiro, segundo = (b, a) if modo == "trava" and numero == 2 else (a, b)
        nome1, nome2 = ("B", "A") if primeiro is b else ("A", "B")
        try:
            with primeiro:
                log(f"T{numero}: adquiriu {nome1}")
                if modo == "trava":
                    # As duas threads seguram o primeiro lock antes de prosseguir.
                    barreira.wait()
                time.sleep(0.01)
                log(f"T{numero}: aguarda {nome2}")
                tentando[numero-1].set()
                with segundo:
                    log(f"T{numero}: concluiu")
                    concluidas.append(numero)
        except BaseException as erro:
            erros.append(repr(erro))

    threads = [threading.Thread(target=tarefa, args=(i,), name=f"T{i}")
               for i in (1, 2)]
    for t in threads:
        t.start()
    if modo == "trava":
        for evento in tentando:
            evento.wait()
        print("DEADLOCK: T1 retém A e espera B; T2 retém B e espera A.", flush=True)
        faulthandler.dump_traceback()
    for t in threads:
        t.join()
    assert not erros, erros
    assert sorted(concluidas) == [1, 2], concluidas
    assert not a.locked() and not b.locked()
    print("OK: ambas concluíram; locks liberados.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("modo", choices=["trava", "corrigida"])
    executar(p.parse_args().modo)
