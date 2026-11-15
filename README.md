# Programação Concorrente — Filósofos, Semáforos e Deadlock

**Vídeo da apresentação:** [Assistir no YouTube](https://youtu.be/bW6B_y30O-I?si=D5wO3CIVQqYy7tWc)

## Identificação

- **Integrante e apresentador:** Mario Fernando de Bona Knaipp.
- **Composição:** individual, com um único integrante.
- **GitHub:** [MarioFernandodeBonaKnaipp](https://github.com/MarioFernandodeBonaKnaipp).
- **Vídeo:** disponível no link acima.

## Situação do material

- As três partes estão implementadas em Python, somente com biblioteca padrão.
- Os experimentos foram executados; logs e resultados estão em `evidencias/`.
- Repositório: https://github.com/MarioFernandodeBonaKnaipp/tde-programacao-concorrente.
- O nome do grupo no AVA ainda não foi informado; o único integrante está identificado acima.

## Ambiente e execução

Requisito: **Python 3.10 ou superior**, sem instalação de pacotes. Validado em CPython 3.12.14 no Windows; detalhes em `evidencias/ambiente.json`. Os comandos abaixo são executados na pasta deste README, usando uma instalação funcional de Python:

```text
python executar_experimentos.py
```

O supervisor executa cada cenário em um processo separado, registra as saídas e encerra somente os processos das demonstrações de deadlock após quatro segundos. Esse encerramento é limpeza do experimento: não é uma solução para o deadlock. Nos demais cenários, timeout ou retorno diferente de zero é erro. A bateria leva alguns segundos, variando com a máquina.

No computador desta sessão, `python` e `py` não encontraram uma instalação funcional no PATH. A validação usou o Python empacotado com o aplicativo. Em uma instalação pessoal, use o comando que corresponde ao seu Python, por exemplo `py -3` no lugar de `python`.

Execuções individuais:

```text
python parte1-filosofos/filosofos.py ingenua
python parte1-filosofos/filosofos.py corrigida --refeicoes 5
python parte2-semaforo/contador.py sem --threads 8 --incrementos 200000
python parte2-semaforo/contador.py com --threads 8 --incrementos 200000
python parte3-deadlock/deadlock.py trava
python parte3-deadlock/deadlock.py corrigida
```

As versões `ingenua` e `trava`, se executadas diretamente, ficam bloqueadas de propósito; interrompa com Ctrl+C. Prefira o supervisor para capturar os diagnósticos e encerrar os processos automaticamente.

## Parte 1 — Jantar dos Filósofos

### Modelo e protocolo ingênuo

Há cinco filósofos e cinco garfos. O garfo `p` fica entre `Pp` e `P(p+1) mod 5`; cada filósofo usa os garfos `p` e `(p-1) mod 5`. Um `Lock` representa cada garfo na versão ingênua. Os logs registram pensando, com fome, primeiro garfo adquirido e espera pelo segundo. Na versão corrigida também registram comendo e devolução dos garfos.

A versão ingênua pega primeiro o garfo `p`. Uma barreira permite que todos adquiram esse primeiro garfo antes de tentarem o outro. Isso escolhe de forma reprodutível um escalonamento que também pode ocorrer sem a barreira. A barreira não resolve nem substitui o problema: depois de liberada, o ciclo de dependência permanece.

```text
P0 segura G0 e espera G4
P4 segura G4 e espera G3
P3 segura G3 e espera G2
P2 segura G2 e espera G1
P1 segura G1 e espera G0
```

As quatro condições de Coffman coexistem: os garfos são exclusivos; cada participante mantém um recurso enquanto pede outro; ninguém toma o garfo de outro à força; e existe o ciclo acima. Nenhum filósofo chega a comer. O log `evidencias/filosofos-ingenua.log` contém o diagnóstico e as pilhas das threads; o supervisor confirma que o processo não termina.

### Correção: garçom com fila FIFO e reserva conjunta

O garçom representa o estado dos garfos com cinco indicadores de disponibilidade, protegidos por uma `Condition`. Não usa uma solução pronta do problema. A fila contém os filósofos na ordem de entrada nessa região protegida. Cada pedido só é atendido se estiver na cabeça e seus dois garfos estiverem livres. A reserva dos dois ocorre dentro da mesma região crítica. Ao terminar a refeição, o filósofo devolve ambos em `finally`.

```text
REPETIR a quantidade de refeições:
    pensar; registrar "com fome"
    entrar na região protegida do garçom
    adicionar pedido ao fim da fila
    ENQUANTO não for a cabeça OU algum dos dois garfos estiver ocupado:
        esperar na condição (libera o mutex enquanto espera)
    remover pedido da cabeça
    reservar os dois garfos juntos
    avisar os demais; sair da região protegida
    TENTAR:
        registrar "comendo"; comer por tempo finito
    FINALMENTE:
        entrar na região protegida
        devolver os dois garfos; avisar os demais
        sair da região protegida
```

**Condição quebrada: manter-e-esperar pelos garfos.** Quem espera ainda não recebeu garfo algum. Quem recebeu os dois não pede outro garfo. Assim, não se forma um ciclo de filósofos segurando um garfo e esperando outro. O mutex do garçom não fica retido durante espera na condição nem durante a refeição.

**Justiça e progresso:** um pedido novo não ultrapassa um pedido já enfileirado. Se a cabeça espera por garfos, quem os possui já está comendo e termina sem pedir recursos adicionais. Assumindo refeições finitas, liberação correta e que threads prontas eventualmente sejam escalonadas, a cabeça avança. Cada pedido tem um número finito de pedidos à frente; logo será atendido. `notify_all` sozinho não garante justiça: a regra da fila é que impede ultrapassagem.

A garantia começa na entrada na fila; não é uma garantia absoluta de escalonamento do sistema operacional. FIFO estrito pode bloquear temporariamente um pedido posterior cujos garfos estejam livres, reduzindo concorrência em troca de uma política simples de justiça. Dois filósofos não vizinhos ainda podem comer juntos quando a ordem da fila permite.

Na execução registrada todos fizeram cinco refeições: `[5, 5, 5, 5, 5]`; houve até dois comendo simultaneamente. O código verifica a ausência de vizinhos comendo ao mesmo tempo e a devolução de todos os garfos. Esses testes verificam as execuções observadas; a justificativa de ausência de inanição é o argumento da fila, sob as hipóteses declaradas.

## Parte 2 — Contador com threads e semáforo

Parâmetros: oito threads, 200.000 incrementos por thread, esperado de **1.600.000**. A operação foi escrita explicitamente como ler o contador, calcular e escrever. Sem exclusão mútua, duas threads podem ler o mesmo valor e ambas gravar o mesmo sucessor: uma atualização se perde.

Para tornar isso observável em Python, a versão sem sincronização do **contador** contém uma barreira após a primeira leitura e antes da primeira escrita. Há também `sleep(0)` entre leitura e escrita a cada mil incrementos nas duas versões. Essa instrumentação induz interleavings; não se pressupõe que uma expressão curta como `count += 1` necessariamente manifeste corrida em qualquer versão do CPython. A barreira organiza o experimento, mas não protege o contador. O GIL não torna uma sequência arbitrária de operações uma transação indivisível.

Na versão correta, `Semaphore(1)` envolve toda a leitura/modificação/escrita. Uma thread só começa a atualização quando a anterior devolve a permissão, inclusive quando esta cede a execução. `finally` devolve a permissão. O programa principal usa `join` e só lê o resultado depois que todas terminam.

### Resultados reais

Os modos foram alternados: sem/com, três vezes. Tempos medidos com `perf_counter` a partir da liberação inicial até os joins; criação das threads fica fora. A tabela é atualizada pelo supervisor ao executar novamente.

<!-- RESULTADOS_INICIO -->
| Execução | Modo | Esperado | Obtido | Perdidos | Tempo (s) |
|---|---|---:|---:|---:|---:|
| 1 | sem | 1600000 | 200000 | 1400000 | 0.140717 |
| 1 | com | 1600000 | 1600000 | 0 | 1.100700 |
| 2 | sem | 1600000 | 200000 | 1400000 | 0.127880 |
| 2 | com | 1600000 | 1600000 | 0 | 1.047787 |
| 3 | sem | 1600000 | 200000 | 1400000 | 0.135158 |
| 3 | com | 1600000 | 1600000 | 0 | 1.041429 |
<!-- RESULTADOS_FIM -->

Dados em formato tabular: [resultados.csv](evidencias/resultados.csv). Cada saída original está em `contador-sem-*.log` ou `contador-com-*.log`.

### Interpretação e limites

A versão desprotegida pode sobrescrever atualizações recentes com valores calculados a partir de leituras antigas. A versão protegida serializa a operação completa e preserva todos os incrementos. O semáforo tem custo de aquisição, liberação e espera; threads também disputam escalonamento. Neste experimento o modo protegido foi mais lento, mas produziu o resultado correto.

O campo `tentativas_por_segundo` do CSV mede operações tentadas, não atualizações úteis preservadas. O cenário é didático e inclui cessões de execução e uma barreira adicional no modo inseguro; não é um benchmark puro de custo do semáforo. Os tempos não provam uma proporção universal de desempenho.

**Justiça:** não se deve presumir FIFO para `threading.Semaphore`. A solução demonstra exclusão mútua e término observado; não oferece a mesma garantia formal de ausência de inanição do garçom com fila explícita. Em cargas finitas, todas as threads terminaram nos experimentos registrados.

**Visibilidade e ordenação:** o contador é compartilhado, mas o protocolo correto exige acesso sob o mesmo semáforo; o resultado final é inspecionado após os joins. A sincronização define a passagem entre regiões críticas. Não se deve usar o GIL ou uma hipótese de flush de cache como justificativa de correção. A terminologia formal de `happens-before` citada no enunciado pertence ao modelo de memória Java; este trabalho está em Python e não transfere esse contrato literalmente.

## Parte 3 — Dois locks e deadlock

Na versão `trava`, T1 pega A e depois pede B; T2 pega B e depois pede A. Uma barreira garante que ambas detenham o primeiro lock antes de prosseguir. O pequeno sono facilita acompanhar os logs, mas não é a garantia de reprodução. O diagnóstico inclui as pilhas produzidas por `faulthandler`.

```text
T1: adquiriu A
T2: adquiriu B
T1: aguarda B
T2: aguarda A
DEADLOCK: T1 retém A e espera B; T2 retém B e espera A.
```

A ordem de impressão pode variar. Logs reais completos: [deadlock-trava.log](evidencias/deadlock-trava.log).

| Condição de Coffman | Manifestação |
|---|---|
| Exclusão mútua | Cada lock pertence a no máximo uma thread |
| Manter-e-esperar | Cada thread mantém o primeiro e pede o segundo |
| Não preempção | O protocolo não toma o lock da outra thread |
| Espera circular | T1 espera B de T2; T2 espera A de T1 |

A versão corrigida impõe a ordem **A antes de B** para ambas as threads. Com os blocos `with` aninhados, a liberação ocorre em ordem inversa, mesmo em exceções.

```text
T1 e T2:
    adquirir A
    adquirir B
    executar seção crítica
    liberar B
    liberar A
```

Isso quebra **espera circular**: uma thread que espera A não segura B; quem segura A pode adquirir B porque ninguém pode segurar B sem ter adquirido A primeiro. A exclusão mútua permanece. Nenhuma thread precisa adquirir locks em ordem decrescente; por isso não se pode fechar o ciclo. A prova vale para este conjunto de recursos e para threads que respeitem a mesma regra global.

Resultado observado: as duas threads concluíram e os locks ficaram livres. Evidência: [deadlock-corrigida.log](evidencias/deadlock-corrigida.log). Ordem global previne deadlock; isoladamente não estabelece uma política FIFO entre todos os competidores.

## Pendências de entrega

Para concluir a entrega:

- Conferir o vínculo ao grupo no AVA; Mario Fernando de Bona Knaipp é o único integrante.
- Manter os códigos, as instruções e as evidências de execução no repositório público.
- Conferir no vídeo publicado: duração de até dez minutos, visibilidade pública ou não listada, explicações das três partes, demonstrações, áudio claro e ao menos 720p.
- Link do vídeo visível no README; grupo corretamente formado no AVA.
- Submissão dos links do repositório e do vídeo no Canvas até 15/11/2026 às 23h59, conforme prazo exibido na atividade.

A publicação no GitHub não representa submissão ao Canvas. Os caminhos locais das pilhas foram substituídos por `.` e `<python>` antes da publicação; os resultados numéricos não foram alterados.

## Referências oficiais para estudo

- [Python: threading — threads, Lock, Condition, Semaphore, Barrier e join](https://docs.python.org/3/library/threading.html).
- [Python: time — perf_counter e sleep](https://docs.python.org/3/library/time.html).
- [Python: faulthandler — diagnóstico de pilhas](https://docs.python.org/3/library/faulthandler.html).

Consulte também o enunciado e os materiais da disciplina.
