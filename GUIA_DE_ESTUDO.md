# Guia de estudo — concorrência

## 1. Comece por três diferenças

**Concorrência:** tarefas avançam em períodos sobrepostos, mesmo se um único núcleo alternar entre elas. **Paralelismo:** tarefas executam ao mesmo tempo em recursos distintos. Uma corrida não exige execução simultânea em dois núcleos; uma interrupção entre leitura e escrita já pode bastar.

**Deadlock:** um conjunto de participantes fica preso em dependências que não consegue satisfazer. **Inanição:** um participante pode ficar sem acesso indefinidamente enquanto outros continuam avançando. **Espera normal:** a thread está temporariamente bloqueada e há uma ação futura que pode liberá-la.

**Segurança:** algo indevido nunca ocorre, por exemplo, dois vizinhos usando o mesmo garfo. **Progresso:** o sistema consegue avançar. **Justiça:** a política evita que uma solicitação seja continuamente ultrapassada. Ausência de deadlock não implica ausência de inanição.

## 2. Entenda a corrida antes de rodar

Imagine contador inicial 7:

| Passo | Thread 1 | Thread 2 | Contador compartilhado |
|---|---|---|---:|
| 1 | Lê 7 | — | 7 |
| 2 | — | Lê 7 | 7 |
| 3 | Calcula e grava 8 | — | 8 |
| 4 | — | Calcula e grava 8 | 8 |

Houve duas tentativas e apenas um incremento preservado. O defeito está na operação composta desprotegida. Proteger só a escrita ainda permite ambas lerem o mesmo valor antigo. A proteção precisa incluir leitura, cálculo e escrita.

Um semáforo com uma permissão deixa passar uma thread por vez. Adquirir consome a permissão; liberar a devolve. Se houver duas permissões para atualizar o mesmo contador, duas threads ainda poderão sobrepor essas operações.

Abra `parte2-semaforo/contador.py` e localize `anterior = contador` e `contador = anterior + 1`. Verifique onde o semáforo começa e termina. A barreira da primeira leitura pertence apenas ao experimento inseguro: colocar uma barreira de oito participantes dentro de uma região que admite uma única thread causaria bloqueio.

## 3. Memorize Coffman usando a mesa

| Condição | Pergunta de diagnóstico | Nos filósofos ingênuos |
|---|---|---|
| Exclusão mútua | O recurso só pode ter um usuário? | Um garfo não pode ser compartilhado ao mesmo tempo |
| Manter-e-esperar | Alguém segura algo enquanto espera mais? | Cada um segura um garfo e pede outro |
| Não preempção | O dono precisa liberar voluntariamente? | Não se arranca o garfo de outro |
| Espera circular | As dependências fecham um ciclo? | Cada um depende de um vizinho até voltar ao primeiro |

As quatro são condições necessárias para o deadlock clássico de recursos modelado aqui. Ver várias threads esperando por alguns instantes não prova impasse. Nestes exemplos há evidência adicional: o estado dos recursos estabelece um ciclo sem nenhum caminho de liberação.

## 4. Compare duas correções diferentes

Na parte dos filósofos, o garçom entrega dois garfos juntos. Quem espera ainda não segura nenhum: quebra manter-e-esperar. A fila limita a ultrapassagem entre pedidos.

Na parte dos dois locks, todas as threads seguem A antes de B. Ninguém forma a dependência inversa B→A: quebra espera circular. Não é preciso abandonar exclusão mútua para impedir deadlock.

**Cuidado com generalizações:** limitar a quatro filósofos ou ordenar garfos pode prevenir deadlock sem garantir, por si só, que um filósofo específico nunca seja preterido. A fila explícita trata essa segunda questão.

## 5. Leia o código nesta ordem

1. `parte3-deadlock/deadlock.py`: desenhe quem possui e quem espera cada lock.
2. `parte2-semaforo/contador.py`: simule duas leituras do mesmo contador no papel.
3. `parte1-filosofos/filosofos.py`: acompanhe um pedido da entrada na fila até a devolução dos dois garfos.
4. `executar_experimentos.py`: entenda por que os exemplos que travam são processos filhos e por que matar o processo serve só para limpar o experimento.
5. Compare cada explicação com os logs reais em `evidencias/`.

## 6. Confira se consegue explicar sem ler

Tente responder primeiro; depois confira a indicação.

| Pergunta | O que uma resposta correta precisa mencionar |
|---|---|
| Por que o GIL não é solução para este contador? | A atualização foi dividida e pode ceder execução entre leitura e escrita |
| Por que a versão errada parece mais rápida? | Ela preserva menos trabalho e não paga a mesma exclusão; a instrumentação também influencia |
| Por que `finally` é necessário? | Devolver a permissão/recursos mesmo quando o corpo lança exceção |
| `notify_all` torna a fila justa? | Não; ele acorda candidatos, mas a condição de cabeça da fila impede ultrapassagens |
| Quem está esperando retém o mutex da condição? | `Condition.wait` libera o mutex e o readquire antes de retornar |
| A fila FIFO aproveita toda oportunidade de comer? | Não; a cabeça pode impedir atendimento de pedido posterior com garfos livres |
| Todos comerem cinco vezes prova ausência de inanição para sempre? | Não; é evidência finita. A prova depende da política e das hipóteses de progresso |
| Um timeout isolado prova deadlock? | Não; pode ser lentidão. Aqui o ciclo de recursos e as pilhas complementam a observação |
| Por que a barreira torna a demonstração determinística? | Todos adquirem o primeiro recurso antes de tentar o segundo |
| Por que não basta inverter a ordem em uma thread qualquer num programa maior? | A regra precisa ser global entre todos os caminhos que usam os recursos envolvidos |

## 7. Exercícios de compreensão

- Desenhe a mesa de cinco lugares e marque por que P0 pode comer junto com P2, mas não com P1 ou P4.
- No papel, faça três threads lerem 10 antes de escrever. Explique por que o resultado pode ser 11 em vez de 13.
- Trace uma fila com pedidos de P0, P1 e P3. Mostre um caso em que o terceiro poderia usar garfos livres, mas precisa aguardar o segundo.
- Explique a diferença entre prevenir deadlock, detectá-lo e encerrar um processo bloqueado.
- Antes de executar cada programa, anote sua previsão. Depois compare com os resultados e identifique o que o teste demonstra e o que depende de argumento lógico.

Referência para conferir as APIs utilizadas: [documentação oficial do módulo threading](https://docs.python.org/3/library/threading.html).
