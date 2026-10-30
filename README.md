# Transferência de arquivos P2P

Sistemas Distribuídos — TP2 | CEFET-MG | 2026/2  
Professora: Michelle Hanne  
**Augusto Coelho Fagundes e ADJAILSON FREIRE DE SÁ FILHO**  
Código público: https://github.com/Augusto42/sd-tp2-p2p-2026

## Apresentação: um terminal, um comando

Requisitos: Python 3.10+ em Linux/macOS; no Windows, use WSL. Executar na raiz da pasta extraída:

```bash
python3 executar.py
```

O programa gera o arquivo e os metadados, inicia quatro processos de `src/peer.py` em **malha completa**, provoca quedas durante a transferência, verifica tamanho/SHA-256 e **encerra todos os peers automaticamente**. Não é necessário abrir outros terminais nem configurar portas manualmente.

A primeira demonstração derruba a única semente e a reinicia. A segunda sorteia um peer, encerra-o com SIGKILL e verifica a conclusão dos sobreviventes por outras fontes, sem reiniciar o peer morto. Nesse segundo cenário há duas sementes iniciais, garantindo uma cópia disponível. A semente do sorteio padrão é 2026; para outro sorteio reproduzível:

```bash
python3 executar.py --demo --seed 0
```

Observe `peer_offline`, `peer_reiniciado` e `integridade_confirmada`. Os eventos mostram o peer escolhido, os blocos já recebidos no momento da queda e o hash final. Os logs completos da demonstração ficam em `resultados/demo/`. Augusto pode acompanhar remotamente pelo compartilhamento da tela do terminal.

## Bateria automática e replicável

```bash
python3 executar.py --testes --repeticoes 5 --seed 2026
```

O comando executa os 11 testes unitários e 130 integrações:

- 24 configurações × 5 repetições: 2/4 peers, blocos de 1.024/4.096 bytes e arquivos de 10/20 KiB, 1/5/10/20 MiB.
- 3 cenários: compartilhamento parcial, semente tardia e múltiplas fontes.
- 2 quedas controladas: temporária e permanente.
- 5 quedas de peer sorteado com sementes 0 a 4.

A ordem das configurações é embaralhada de forma reproduzível a cada repetição. Na matriz, a geração dos arquivos é pseudoaleatória e determinística: a mesma semente reproduz os mesmos bytes por tamanho de arquivo. Portas livres são escolhidas automaticamente; tempos e escalonamento variam entre execuções.

`resultados/estatisticas.csv` e `.json` contêm média, **desvio-padrão amostral (n−1)**, mínimo, máximo, quantidade e os cinco tempos de cada configuração. `medicoes.json` associa cada tempo aos logs e metadados; `adicionais.json` contém os dados das falhas, fontes alternativas, blocos recebidos após a queda e tempo até a conclusão. `bateria.json` consolida a aprovação.

Todos os cenários conferem tamanho, SHA-256, índices dos blocos e fontes. A matriz também exige que cada leecher tenha se conectado a **todos** os seus vizinhos. Todos os processos são encerrados em `finally`, inclusive quando um teste falha. A bateria pode levar alguns minutos.

## Arquivos de entrega

- `executar.py`: comando único para demonstração e bateria.
- `src/peer.py`: protocolo TCP, servidor, cliente, fragmentação e montagem.
- `tests/`: testes unitários e executor multiprocessos.
- `docs/relatorio.pdf`: relatório de quatro páginas, com média/desvio e resultados das quedas.
- `docs/apresentacao.pptx` e `.pdf`: slides e notas para apresentação.
- `docs/roteiro_apresentacao.md`: roteiro extraído das notas.
- `docs/protocolo.md`: mensagens e decisões de implementação.
- `docs/gerar_relatorio.py`: gerador do relatório; requer ReportLab apenas para regenerar o PDF.
- `resultados/`: resultados e logs. Manifestos compartilhados ficam em `entradas/`; cada medição aponta para seu manifesto em `metadados_ref.txt`.

No ZIP, os logs estão descompactados. No GitHub, extraia `resultados/evidencias.zip` na raiz para obter os logs detalhados.

## Funcionamento e limites

Com quatro peers, A conhece B/C/D; B conhece A/C/D; C conhece A/B/D; D conhece A/B/C. Cada leecher abre uma tarefa por vizinho. A semente completa atende solicitações sem precisar baixar. As prioridades circulares dos blocos diferem entre peers para favorecer a redistribuição durante o download.

Um peer individual permanece servindo após concluir, pois fechar sua conexão imediatamente poderia impedir a conclusão dos demais. **O executor encerra a rede quando todos os peers ativos concluem.**

A recuperação mantém os leechers sobreviventes ativos. Reiniciar o próprio leecher ainda descarta seu parcial. Se todos os detentores de um bloco saírem definitivamente, não há como recuperar esse bloco sem outra cópia. Metadados são previamente distribuídos e confiáveis; não há tracker, descoberta automática ou autenticação. Ensaios realizados em TCP loopback; não foram medidos em máquinas remotas.
