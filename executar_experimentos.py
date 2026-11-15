"""Executa os cenários isoladamente e salva evidências reais, sem dependências."""
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import sys

RAIZ = Path(__file__).resolve().parent
LOGS = RAIZ / "evidencias"


def anonimizar(texto):
    return texto.replace(str(RAIZ), ".").replace(sys.prefix, "<python>")


def rodar(arquivo, argumentos, nome, impasse=False):
    comando = [sys.executable, "-X", "utf8", "-u", str(RAIZ / arquivo), *argumentos]
    expirou = False
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace",
                                   timeout=4 if impasse else 180)
        texto = resultado.stdout + resultado.stderr
        assert resultado.returncode == 0, texto
    except subprocess.TimeoutExpired as erro:
        expirou = True
        def decodificar(dados):
            return dados.decode("utf-8", errors="replace") if isinstance(dados, bytes) else (dados or "")
        texto = decodificar(erro.stdout) + decodificar(erro.stderr)
    texto = anonimizar(texto)
    (LOGS / nome).write_text(texto, encoding="utf-8")
    if impasse:
        assert expirou and "DEADLOCK:" in texto, texto
        texto += "\nSupervisor: processo encerrado por timeout após diagnóstico de deadlock.\n"
        (LOGS / nome).write_text(texto, encoding="utf-8")
    else:
        assert not expirou, f"Timeout inesperado: {nome}"
    print(f"OK {nome}", flush=True)
    return texto


def main():
    LOGS.mkdir(exist_ok=True)
    ambiente = dict(python=sys.version, plataforma=platform.platform(),
                    executado_em_utc=datetime.now(timezone.utc).isoformat(),
                    threads=8, incrementos_por_thread=200_000, ceder_cada=1000,
                    repeticoes_por_modo=3,
                    nota="Horário do relógio de execução; não determina o prazo do Canvas.")
    (LOGS / "ambiente.json").write_text(json.dumps(ambiente, indent=2), encoding="utf-8")
    rodar("parte1-filosofos/filosofos.py", ["ingenua"], "filosofos-ingenua.log", True)
    rodar("parte1-filosofos/filosofos.py", ["corrigida"], "filosofos-corrigida.log")
    rodar("parte3-deadlock/deadlock.py", ["trava"], "deadlock-trava.log", True)
    rodar("parte3-deadlock/deadlock.py", ["corrigida"], "deadlock-corrigida.log")
    linhas = []
    # Alterna modos para reduzir o efeito da ordem (não elimina ruído do sistema).
    for repeticao in range(1, 4):
        for modo in ("sem", "com"):
            texto = rodar("parte2-semaforo/contador.py", [modo], f"contador-{modo}-{repeticao}.log")
            linhas.append(dict(execucao=repeticao, **json.loads(texto)))
    with (LOGS / "resultados.csv").open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)
    tabela = ["| Execução | Modo | Esperado | Obtido | Perdidos | Tempo (s) |",
              "|---|---|---:|---:|---:|---:|"]
    for r in linhas:
        tabela.append(f"| {r['execucao']} | {r['modo']} | {r['esperado']} | {r['obtido']} | {r['perdidos']} | {r['segundos']:.6f} |")
    (LOGS / "resultados.md").write_text("\n".join(tabela) + "\n", encoding="utf-8")
    print("Experimentos concluídos. Resultados reais em evidencias/.")


if __name__ == "__main__":
    main()
