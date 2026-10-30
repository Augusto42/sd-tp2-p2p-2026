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

24 configurações x 5 repetições = 120 execuções. Dois/quatro peers, blocos de 1.024/4.096 bytes e arquivos de 10/20 KiB, 1/5/10/20 MiB. Malha completa. Ordem embaralhada por repetição, arquivos pseudoaleatórios replicáveis com seed 2026. Verificação de tamanho, SHA-256, índices, fontes e conexão a todos os vizinhos. Processos independentes em TCP loopback. Comando: python3 executar.py --testes --repeticoes 5 --seed 2026.

Fonte: https://github.com/Augusto42/sd-tp2-p2p-2026

## Slide 6

Médias e desvios calculados automaticamente dos cinco tempos por configuração em resultados/estatisticas.json: [{"peers":2,"block_bytes":1024,"size_bytes":20971520,"repetitions":5,"mean_seconds":4.05026,"std_seconds":0.7943199091046377,"min_seconds":3.3614,"max_seconds":5.141,"seconds":[5.141,3.7553,3.3614,4.616,3.3776],"integrity":"PASS","topology":"mesh"},{"peers":4,"block_bytes":1024,"size_bytes":20971520,"repetitions":5,"mean_seconds":9.61766,"std_seconds":1.6812387941633995,"min_seconds":7.4895,"max_seconds":11.3061,"seconds":[11.3015,11.3061,8.5974,7.4895,9.3938],"integrity":"PASS","topology":"mesh"},{"peers":2,"block_bytes":4096,"size_bytes":20971520,"repetitions":5,"mean_seconds":1.343,"std_seconds":0.19280001296680455,"min_seconds":1.1294,"max_seconds":1.5704,"seconds":[1.1294,1.2537,1.2384,1.5704,1.5231],"integrity":"PASS","topology":"mesh"},{"peers":4,"block_bytes":4096,"size_bytes":20971520,"repetitions":5,"mean_seconds":2.6962,"std_seconds":0.5765892298681965,"min_seconds":2.1876,"max_seconds":3.412,"seconds":[2.4346,3.412,3.2178,2.1876,2.229],"integrity":"PASS","topology":"mesh"}]. Desvio-padrão amostral, denominador n-1. Quatro peers entregam três cópias. Inclui inicialização, logs e contato com todos os vizinhos. Sem inferência de desempenho em LAN/WAN.

Fonte: https://github.com/Augusto42/sd-tp2-p2p-2026

## Slide 7

Cinco sorteios reproduzíveis entre quatro peers, seeds 0 a 4. SIGKILL aplicado enquanto downloads dos sobreviventes ainda estavam incompletos e após observar dados recebidos do peer escolhido. Duas sementes iniciais garantem disponibilidade. Os sobreviventes receberam novos blocos de outras fontes e concluíram sem reiniciar o peer morto. Dados: [{"seed":0,"peer":3,"blocks":{"2":402},"sources":{"2":[38031,43499]},"seconds":0.8297,"hash":"9fd6bacd218559526a9fc1abd35692c465fede0352bc1ce148c8eecce6ec6081"},{"seed":1,"peer":1,"blocks":{"2":488,"3":487},"sources":{"2":[36089,45867],"3":[36089,46947,51943]},"seconds":1.7487,"hash":"6a8529956c7a3c8926785a34bf6e4527a0193725b1aa43e8d96ff26943c9fbfd"},{"seed":2,"peer":0,"blocks":{"2":449,"3":462},"sources":{"2":[45089,60595],"3":[41481,45089,59655]},"seconds":1.3939,"hash":"c1208dd98a06878af2b6d19f1e3ed46275d0af1d3cdcfac5e4436e7a8e73d617"},{"seed":3,"peer":1,"blocks":{"2":475,"3":493},"sources":{"2":[41419,44605],"3":[44605,45605]},"seconds":1.654,"hash":"c068aedf351f92f867fc32fb74552f81b2c1b05711a31ff151a06eeb3f5b86f2"},{"seed":4,"peer":1,"blocks":{"2":472,"3":454},"sources":{"2":[38713,48885],"3":[38713,48055]},"seconds":1.1411,"hash":"bd2b917729e756f7f55137f5ddc52c727f87edca06b9bdf8ef3e0a86593431d0"}]. Também passaram queda temporária da única semente, queda permanente controlada, redistribuição parcial, início tardio e malha completa. Total: 130 integrações e 11 unitários.

Fonte: https://github.com/Augusto42/sd-tp2-p2p-2026

## Slide 8

Executar python3 executar.py na raiz. O programa gera arquivo/metadados, inicia quatro processos em malha, mata e reinicia a única semente no primeiro cenário; no segundo sorteia um peer e mata sem retorno, com duas sementes iniciais. Confere tamanho e SHA-256 e encerra todos os processos automaticamente. Não é preciso abrir terminais adicionais. Para repetir o sorteio usar --demo --seed 0. Logs em resultados/demo. Augusto acompanha por compartilhamento de tela. O peer individual continua servindo para os demais; o executor encerra a rede ao fim. Reiniciar o próprio leecher descarta seu parcial.

Fonte: https://github.com/Augusto42/sd-tp2-p2p-2026
