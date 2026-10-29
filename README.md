# TP2 - Transferência de arquivos P2P

Implementação preparada por Codex (assistente de IA da OpenAI), a pedido de Augusto Coelho Fagundes. Material para estudo, revisão e apresentação. Enunciado: Sistemas Distribuídos, CEFET-MG, professora Michelle Hanne, 2026/2.

## Requisitos e execução

Linux/macOS, Python 3.10 ou superior; nenhuma dependência externa para executar peers e testes. Validado em Linux; o tratamento de sinais usa `loop.add_signal_handler`, não suportado pelo loop padrão do Windows (usar WSL).

Execute os comandos na raiz desta pasta. Use uma pasta de saída exclusiva para cada processo; iniciar um peer recria seu arquivo parcial. O metadado deve ser distribuído previamente a todos os nós.

```bash
python3 -c "from pathlib import Path; import os; Path('origem.bin').write_bytes(os.urandom(1048576))"
python3 src/peer.py manifest origem.bin arquivo.json --block-size 1024
```

Terminal A (seeder):
```bash
python3 src/peer.py run --meta arquivo.json --dir dados_a --port 9001 --neighbor 127.0.0.1:9002 --seed origem.bin --log a.jsonl
```
Terminal B (leecher e servidor ao mesmo tempo):
```bash
python3 src/peer.py run --meta arquivo.json --dir dados_b --port 9002 --neighbor 127.0.0.1:9001 --log b.jsonl
```

O resultado fica em `dados_b/arquivo_final.bin`. O processo continua compartilhando depois de completar; encerre com Ctrl+C. Para quatro nós em cadeia, configure C na porta 9003 com vizinho B:9002 e D na porta 9004 com vizinho C:9003. Para malha completa, repita `--neighbor` para cada vizinho. Em máquinas distintas, use `--host` com o IP local e os IPs reais nos vizinhos.

```bash
sha256sum origem.bin dados_b/arquivo_final.bin
python3 -m unittest discover -s tests -v
python3 tests/integration.py          # matriz completa + 3 cenários
python3 tests/integration.py --quick  # quatro combinações pequenas + 3 cenários
```

Os testes de integração geram novos dados aleatórios a cada execução; preservam os hashes, metadados, logs completos, resultados CSV/JSON e ambiente, mas apagam os arquivos binários temporários para reduzir o pacote. Reproduz-se o procedimento, não os mesmos bytes aleatórios. Uma nova execução substitui os resultados dos cenários executados. Os tempos incluem inicialização, criação da cópia do seeder, polling e gravação de logs.

## Organização

- `src/peer.py`: protocolo, servidor, cliente, fragmentação e montagem.
- `tests/`: testes unitários e cenários multiprocessos.
- `resultados/`: evidência real da execução; `resumo.csv`/`resumo.json` consolidam 27 cenários.
- `docs/relatorio.pdf`: relatório de até cinco páginas.
- `docs/rascunho_apresentacao.pdf`: rascunho visual para uma apresentação de 8 a 10 minutos.
- `docs/roteiro_apresentacao.md`: fala sugerida e demonstração.
- `docs/protocolo.md`: especificação de mensagens, decisões e limites.
- `docs/gerar_documentos.py`: fonte dos PDFs, requer ReportLab.

## Limites

Vizinhos estáticos, um arquivo por execução, metadado local confiável, ambiente cooperativo. Não há tracker, descoberta, TLS, autenticação, retomada após reinício do processo nem controle de congestionamento no nível da aplicação. TCP cuida da ordenação e retransmissão de bytes; a aplicação verifica hashes e tenta novamente após falhas. O conjunto `busy` evita pedidos simultâneos do mesmo bloco, mas não implementa rarest-first nem justiça garantida entre fontes. O frame tem limite de 8 MiB; os inventários dos tamanhos do trabalho cabem nesse limite. Os dados no disco usam operações síncronas curtas dentro do loop assíncrono. Os testes locais não permitem inferir ganhos em WAN ou resultados estatísticos.

## Repositório

https://github.com/Augusto42/sd-tp2-p2p-2026 (público; acesso livre pelo link). Os logs completos estão no ZIP de entrega.

O repositório foi tornado público em 29/10/2026 após o envio inicial. As menções a repositório privado nos PDFs e no e-mail original descrevem o estado anterior; não é mais necessário solicitar acesso.
