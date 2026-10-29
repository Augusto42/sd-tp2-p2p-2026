# Roteiro de apresentação (8 a 10 minutos)

## Slide 1: Um peer baixa e compartilha

- Transferência de arquivos P2P - TP2 / CEFET-MG
- Python + asyncio + TCP
- Augusto Coelho Fagundes<br/>ADJAILSON FREIRE DE SÁ FILHO

**Fala sugerida:** Abrir explicando que a função de cliente e servidor existe no mesmo processo. Material preparado com Codex, assistente de IA da OpenAI.

## Slide 2: A cadeia comprova o repasse

- A (semente)  >  B  >  C  >  D
- B e C servem blocos antes de completar o arquivo.
- Vizinhos estáticos; um processo por peer.

**Fala sugerida:** Mostrar o desenho. D não conhece A; portanto a chegada dos dados exige redistribuição pelos intermediários.

## Slide 3: Do arquivo aos blocos verificados

- Metadado: tamanho + hashes por bloco + SHA-256 final
- Receber > verificar > gravar > anunciar no inventário
- Ao completar: verificar o todo e publicar arquivo_final.bin

**Fala sugerida:** Explicar bloco final menor, arquivo parcial em disco e dois conjuntos have/busy. Hash identifica corrupção; não autentica o remetente.

## Slide 4: TCP precisa de enquadramento

- 4 bytes de comprimento + corpo da mensagem
- have / get: JSON | inventário: J | bloco: B | erro: E
- Conexões persistentes, deadlines e novas tentativas

**Fala sugerida:** TCP não preserva fronteiras de mensagens. readexactly reconstrói frames. Uma tarefa por vizinho permite receber e enviar simultaneamente.

## Slide 5: A matriz cobriu 24 combinações

- 2 e 4 processos; blocos de 1 e 4 KiB
- 10/20 KiB e 1/5/10/20 MiB
- 24/24: SHA-256, tamanho e fontes corretos

**Fala sugerida:** Todos os testes usaram processos reais e loopback. Explicar unidades binárias. Cada caso foi executado uma vez; dados aleatórios são regenerados.

## Slide 6: Blocos maiores reduziram o tempo em 20 MiB

- 2 peers: 2,5323 s (1 KiB) > 0,9107 s (4 KiB)
- 4 peers: 4,6279 s (1 KiB) > 3,4303 s (4 KiB)
- Medição inclui inicialização e logs; não representa WAN.

**Fala sugerida:** Mais peers na cadeia também significam mais cópias entregues. Não concluir que quatro peers aceleram ou pioram universalmente P2P.

## Slide 7: As evidências vão além do arquivo final

- 216 envios durante download no caso com atraso
- Seeder tardio: 7 tentativas, recuperação correta
- Malha: múltiplas fontes | 10 testes unitários aprovados

**Fala sugerida:** Abrir verificacao.json e um log received/sent. Mostrar complete=false. O teste de recuperação é de indisponibilidade inicial.

## Slide 8: Demonstração e próximos passos

- Gerar metadado; iniciar A e B; comparar SHA-256
- Limites: sem retomada persistente, TLS ou tracker
- Código, testes, logs e relatório acompanham a entrega.

**Fala sugerida:** Executar os comandos do README. Concluir explicando as escolhas e limites. Repositório público: Augusto42/sd-tp2-p2p-2026.

## Perguntas prováveis

- Por que TCP? Confiabilidade de transporte, com protocolo de frames próprio.
- Como comprovar P2P? Cadeia força repasse e logs registram envio antes de completar.
- O que ocorre se um peer cair? Reconexão e nova busca, se existir fonte; reinício do leecher não retoma estado.
- SHA-256 garante segurança? Detecta divergência frente a metadado confiável; não autentica a origem.
- Qual a limitação dos tempos? Uma execução por caso em loopback, incluindo custos de inicialização e logs.
