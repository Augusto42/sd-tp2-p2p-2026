# Protocolo v1 e decisões

## Metadado JSON

`version=1`, `name` (informativo), `size` em bytes, `block_size` em bytes, `sha256` do arquivo e `blocks` com hashes SHA-256 na ordem dos blocos. O número de blocos é ceil(size / block_size); o último pode ser menor. Arquivo vazio tem zero blocos e hash SHA-256 do conteúdo vazio. O nome recebido nunca vira caminho de escrita; a saída é sempre `arquivo_final.bin` na pasta local configurada.

## Enquadramento sobre TCP

Cada frame começa com quatro bytes unsigned big-endian de comprimento, seguidos exatamente por essa quantidade de bytes. Limite: 8 MiB. `readexactly` trata fragmentação/coalescência TCP; encerramento prematuro descarta a resposta e aciona reconexão.

Requisições são JSON UTF-8:

```json
{"op":"have","file":"SHA256_HEXADECIMAL_DO_ARQUIVO"}
{"op":"get","file":"SHA256_HEXADECIMAL_DO_ARQUIVO","index":0}
```

Respostas são binárias com discriminador no primeiro byte:

- `J` seguido de JSON com índices disponíveis, por exemplo `J[0,1,4]`.
- `B` seguido de bytes crus do bloco, sem base64.
- `E` seguido de erro ASCII: `wrong_file` ou `not_available`.

Uma conexão persistente por vizinho; um pedido em voo por conexão. Não é necessário ID de correlação porque o cliente espera a resposta antes do próximo pedido. Servidor atende conexões simultâneas em tarefas distintas. Deadline de conexão: 2 s; resposta: 5 s; o servidor encerra conexão ociosa após 15 s. Após falha, nova tentativa em 100 ms; sem blocos novos, consulta após 20 ms. Estes valores são escolhas didáticas para LAN, não ajustes universais.

## Estado e concorrência

`have` contém apenas blocos com tamanho e hash válidos já escritos e descarregados do buffer Python. `busy` contém reservas temporárias para evitar duplicação entre tarefas. A gravação e atualização de `have` não têm `await`, portanto são indivisíveis em relação às outras tarefas desse event loop. A leitura do bloco no servidor também ocorre antes de qualquer espera. Isso evita uma corrida no ponteiro do arquivo compartilhado. `flush` não equivale a persistência garantida contra queda de energia; não há `fsync` por bloco.

Após validar o SHA-256 final, o arquivo parcial é renomeado na mesma pasta; a publicação do nome final ocorre apenas depois da validação. O descritor permanece aberto para servir blocos. Um leecher consulta todos os vizinhos configurados e pode atendê-los enquanto baixa. Um seeder completo não precisa iniciar downloads, mas aceita solicitações.

## Por que estas escolhas

1. Python/biblioteca padrão: instalação simples e código pequeno, priorizando conceitos de SD.
2. `asyncio` e TCP: sockets não bloqueantes e multiplexação sem uma thread por peer; TCP oferece fluxo confiável, mas ainda exige enquadramento de mensagens.
3. Vizinhos estáticos: atendem ao enunciado e evitam tracker opcional.
4. JSON para controle e metadados: fácil inspeção; bytes crus para blocos evitam expansão de base64.
5. SHA-256 por bloco e arquivo: rejeitar corrupção cedo e confirmar montagem inteira. Metadado deve vir de fonte confiável; hash não autentica remetente.
6. Arquivo parcial em disco: evita manter o arquivo todo em RAM; escrita por offset permite chegada fora de ordem.
7. Inventário consultado periodicamente: implementação direta e adequada aos tamanhos de teste; listas completas custam O(n) e não são ideais em grande escala.
8. Malha completa: cada peer configura todos os demais como vizinhos. Os testes verificam conexão de cada leecher com todos os vizinhos, incluindo arquivos pequenos. Caminhos alternativos permitem continuar usando fontes ainda disponíveis.
9. Seleção circular: a prioridade de índices depende da porta local; isso evita que todos os leechers escolham sempre a mesma frente de blocos e favorece o repasse parcial. Não é rarest-first.
10. Logs JSONL: um registro por evento, analisável automaticamente, com fonte, índice e contagem recebida; medição inclui seu custo.
11. Saída com nome fixo: elimina uso de nomes do metadado como caminhos arbitrários.

## Garantias e limites de recuperação

Blocos já validados permanecem disponíveis enquanto o processo vive. Falha de conexão, indisponibilidade inicial, resposta inválida e corrupção provocam nova tentativa; reservas são liberadas em `finally`. Não há limite total de download: se nenhuma fonte oferece um bloco necessário, o peer espera indefinidamente. Reiniciar um leecher descarta o parcial; retomada persistente não foi implementada. O teste `seeder_tardio` cobre indisponibilidade inicial. `queda_temporaria` mata a única semente durante o download e comprova reconexão após seu retorno, sem reiniciar os leechers. `queda_permanente` inicia duas sementes, mata uma durante o download e verifica a conclusão dos peers restantes sem seu retorno. Em ambos, há SIGKILL real, logs de retry, blocos recebidos após a queda e verificação final de tamanho/SHA-256. Corrupção é exercitada em teste unitário do armazenamento, não por injeção na rede.

## Execução automática

`executar.py` inicia os processos de `src/peer.py`, cria dados e metadados, monitora os arquivos, valida integridade e encerra os processos em `finally`. Sem argumentos, faz a demonstração; com `--testes`, executa os unitários e cinco repetições por configuração, calculando média e desvio-padrão amostral. O peer individual continua servindo até o executor encerrar a rede, evitando perder fontes necessárias a outros downloads.

Nos testes `queda_aleatoria_N`, o peer é sorteado uniformemente entre os quatro IDs com `random.Random(N).randrange(4)`. A falha só é injetada depois de observar dados recebidos desse peer e downloads sobreviventes ainda incompletos. Registra-se SIGKILL, novas fontes e blocos após a queda. Duas sementes iniciais garantem disponibilidade mesmo se uma delas for escolhida.
