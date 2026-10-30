# Roteiro de apresentação

## Slide 1

Apresentar o objetivo: cada processo recebe e envia blocos do mesmo arquivo. A ilustração representa o conceito de rede P2P. Fonte técnica: enunciado SD_TP2_2_2026.pdf, seções 1 e 2.

## Slide 2

Cada peer configura os outros três como vizinhos. Cada leecher inicia uma tarefa cliente por vizinho e continua tentando o primeiro contato mesmo se concluir o arquivo rapidamente. A semente completa aceita conexões sem precisar baixar. O servidor serve blocos já verificados enquanto o cliente baixa.

Fonte: https://github.com/Augusto42/sd-tp2-p2p-2026

## Slide 3

O metadado contém tamanho do arquivo, tamanho de bloco, hashes individuais e hash completo. O último bloco pode ser menor. A escrita usa offset no arquivo parcial. have é atualizado somente após a validação e escrita. busy evita solicitações duplicadas. Fonte: src/peer.py, put e finish.

Fonte: https://github.com/Augusto42/sd-tp2-p2p-2026

## Slide 4

Cada frame começa com quatro bytes big-endian contendo o tamanho do corpo. readexactly reconstrói mensagens mesmo quando TCP as divide. Um pedido por conexão fica em voo. Timeout de conexão: 2 s. Resposta: 5 s. Nova tentativa: 100 ms. Fonte: docs/protocolo.md e src/peer.py.

Fonte: https://github.com/Augusto42/sd-tp2-p2p-2026

## Slide 5

24 combinações: 2/4 peers, blocos de 1.024/4.096 bytes e arquivos de 10/20 KiB, 1/5/10/20 MiB. Todos os ensaios usam malha completa. Os logs verificam que cada leecher se conectou a todos os vizinhos, e que índices, fontes, tamanho e SHA-256 estão corretos. Processos independentes em TCP loopback; uma execução por configuração.

Fonte: https://github.com/Augusto42/sd-tp2-p2p-2026

## Slide 6

Dados da execução de 30/10/2026 em resultados/resumo.json. [{"peers":2,"block":1024,"seconds":3.1995},{"peers":4,"block":1024,"seconds":10.2469},{"peers":2,"block":4096,"seconds":1.5319},{"peers":4,"block":4096,"seconds":5.0194}]. Quatro peers entregam três cópias em malha completa. Os tempos incluem inicialização, logs e espera pelo contato com todos os vizinhos; uma medição por caso, sem inferir desempenho em LAN/WAN.

Fonte: https://github.com/Augusto42/sd-tp2-p2p-2026

## Slide 7

Os dois testes usam SIGKILL real durante downloads incompletos, com quatro peers em malha. No temporário, a única semente cai, os leechers preservam seus blocos em memória/disco e reconectam quando ela reinicia. No permanente, há duas sementes iniciais; uma cai e os três processos restantes concluem sem seu retorno. Ter cópias disponíveis é necessário para tolerar perda permanente. Tamanho e SHA-256 conferidos em todos os arquivos dos processos ativos; índices sem duplicação. Também passaram compartilhamento parcial, seeder tardio e múltiplas fontes. Evidência: resultados/queda_temporaria e resultados/queda_permanente.

Fonte: https://github.com/Augusto42/sd-tp2-p2p-2026

## Slide 8

Na raiz do projeto, executar python3 tests/integration.py --demo. O comando abre quatro processos, mostra portas e progresso no momento da queda e executa dois cenários. Primeiro: única semente morta e reiniciada. Segundo: uma de duas sementes morta sem retorno. Observar peer_offline, peer_reiniciado e integridade_confirmada. O comando valida os arquivos automaticamente e encerra os processos. Logs em resultados/demo. Augusto pode acompanhar o terminal por compartilhamento de tela. Ensaio entre máquinas remotas não foi realizado. Reiniciar um leecher ainda descarta o parcial; o teste mantém os leechers ativos.

Fonte: https://github.com/Augusto42/sd-tp2-p2p-2026
