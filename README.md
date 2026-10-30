# Transferência de arquivos P2P

Sistemas Distribuídos - TP2 | CEFET-MG | 2026/2

**Integrantes:** Augusto Coelho Fagundes e ADJAILSON FREIRE DE SÁ FILHO.

**Professora:** Michelle Hanne.

**Código-fonte:** https://github.com/Augusto42/sd-tp2-p2p-2026

## Requisitos e execução

Linux/macOS, Python 3.10 ou superior; nenhuma dependência externa para executar peers e testes. Validado em Linux; o tratamento de sinais usa `loop.add_signal_handler`, não suportado pelo loop padrão do Windows (usar WSL).

Execute os comandos na raiz desta pasta. Use uma pasta de saída exclusiva para cada processo; iniciar um peer recria seu arquivo parcial. O metadado deve ser distribuído previamente a todos os nós.

```bash
python3 -c "from pathlib import Path; import os; Path('origem.bin').write_bytes(os.urandom(1048576))"
python3 src/peer.py manifest origem.bin arquivo.json --block-size 1024
```

Em quatro terminais, use malha completa (cada peer conhece os outros três):

```bash
# A — semente
python3 src/peer.py run --meta arquivo.json --dir dados_a --port 9001 --neighbor 127.0.0.1:9002 --neighbor 127.0.0.1:9003 --neighbor 127.0.0.1:9004 --seed origem.bin --log a.jsonl
# B
python3 src/peer.py run --meta arquivo.json --dir dados_b --port 9002 --neighbor 127.0.0.1:9001 --neighbor 127.0.0.1:9003 --neighbor 127.0.0.1:9004 --log b.jsonl
# C
python3 src/peer.py run --meta arquivo.json --dir dados_c --port 9003 --neighbor 127.0.0.1:9001 --neighbor 127.0.0.1:9002 --neighbor 127.0.0.1:9004 --log c.jsonl
# D
python3 src/peer.py run --meta arquivo.json --dir dados_d --port 9004 --neighbor 127.0.0.1:9001 --neighbor 127.0.0.1:9002 --neighbor 127.0.0.1:9003 --log d.jsonl
```

A conecta-se a B/C/D quando atua como leecher; B a A/C/D; C a A/B/D; D a A/B/C. A semente completa atende conexões e não precisa baixar. O resultado fica em `dados_b/arquivo_final.bin` e nas outras pastas. Os processos continuam compartilhando depois de completar; encerre com Ctrl+C. Em máquinas distintas, use `--host` com o IP local e os IPs reais nos vizinhos.

### Demonstração ao vivo com um comando

```bash
python3 tests/integration.py --demo
```

O comando inicia quatro processos em malha e mostra os eventos `malha_iniciada`, `peer_offline`, `peer_reiniciado` e `integridade_confirmada`. Primeiro mata a única semente durante o download e a reinicia; depois mata uma das duas sementes e comprova que os peers restantes concluem sem seu retorno. Todos os arquivos finais ativos são conferidos por tamanho e SHA-256. Os logs ficam em `resultados/demo/`, separados da matriz oficial. Atrasos artificiais tornam a queda observável. É possível acompanhar remotamente pelo compartilhamento de tela do terminal; não exige quatro computadores.

Se o único peer que possui certos blocos sair definitivamente, esses blocos deixam de estar disponíveis: é necessário seu retorno ou outra cópia. O leecher que permanece ativo conserva os blocos já recebidos; reiniciar esse leecher ainda descarta seu parcial.

```bash
sha256sum origem.bin dados_b/arquivo_final.bin
python3 -m unittest discover -s tests -v
python3 tests/integration.py          # matriz completa + 5 cenários
python3 tests/integration.py --quick  # quatro combinações pequenas + 5 cenários
```

Os testes de integração geram novos dados aleatórios a cada execução; preservam os hashes, metadados, logs completos, resultados CSV/JSON e ambiente, mas apagam os arquivos binários temporários para reduzir o pacote. Reproduz-se o procedimento, não os mesmos bytes aleatórios. Uma nova execução substitui os resultados dos cenários executados. Os tempos incluem inicialização, criação da cópia do seeder, polling e gravação de logs.

## Organização

- `src/peer.py`: protocolo, servidor, cliente, fragmentação e montagem.
- `tests/`: testes unitários e cenários multiprocessos.
- `resultados/`: evidência real da execução; `resumo.csv`/`resumo.json` consolidam 29 cenários.
- `docs/relatorio.pdf`: relatório de até cinco páginas.
- `docs/apresentacao.pptx`: apresentação editável com notas do apresentador.
- `docs/apresentacao.pdf`: apresentação pronta para projeção.
- `docs/roteiro_apresentacao.md`: fala sugerida e demonstração.
- `docs/protocolo.md`: especificação de mensagens, decisões e limites.
- `docs/gerar_relatorio.py`: fonte do relatório, requer ReportLab.

No ZIP de entrega, os logs estão descompactados. No GitHub, os logs completos estão em `resultados/evidencias.zip`; extraia esse arquivo na raiz do projeto para obter as pastas de cada cenário.

## Limites

Vizinhos estáticos, um arquivo por execução, metadado local confiável, ambiente cooperativo. Não há tracker, descoberta, TLS, autenticação, retomada após reinício do processo nem controle de congestionamento no nível da aplicação. TCP cuida da ordenação e retransmissão de bytes; a aplicação verifica hashes e tenta novamente após falhas. O conjunto `busy` evita pedidos simultâneos do mesmo bloco, mas não implementa rarest-first nem justiça garantida entre fontes. O frame tem limite de 8 MiB; os inventários dos tamanhos do trabalho cabem nesse limite. Os dados no disco usam operações síncronas curtas dentro do loop assíncrono. Os testes locais não permitem inferir ganhos em WAN ou resultados estatísticos.
