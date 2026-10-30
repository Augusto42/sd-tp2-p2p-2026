"""Gera o relatório com ReportLab."""
from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.pagesizes import A4
ROOT=Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'resultados/estatisticas.json').read_text())
extra=json.loads((ROOT/'resultados/adicionais.json').read_text())
repo='https://github.com/Augusto42/sd-tp2-p2p-2026'
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyPT',fontName='Helvetica',fontSize=10,leading=14,spaceAfter=9))
styles.add(ParagraphStyle(name='TitlePT',fontName='Helvetica-Bold',fontSize=23,leading=28,spaceAfter=18,textColor=HexColor('#133749')))
story=[]
def title(t):story.append(Paragraph(t,styles['TitlePT']))
def p(t):story.append(Paragraph(t,styles['BodyPT']))
def table(data,widths=None):
 t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#133749')),('TEXTCOLOR',(0,0),(-1,0),white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('ROWBACKGROUNDS',(0,1),(-1,-1),[HexColor('#edf3f4'),white])]))
 story.append(t);story.append(Spacer(1,12))
def page():story.append(PageBreak())
title('Transferência de arquivos P2P')
p('<b>Sistemas Distribuídos - TP2 | CEFET-MG | 2026/2</b><br/>Professora: Michelle Hanne.<br/><b>Integrantes: Augusto Coelho Fagundes e ADJAILSON FREIRE DE SÁ FILHO.</b><br/>30/10/2026.')
p(f'<b>Código-fonte:</b> <link href="{repo}" color="blue">{repo}</link>')
title('1. Arquitetura e decisões')
p('Cada peer é um processo Python com um servidor TCP e tarefas clientes no mesmo event loop asyncio. Ele atende solicitações enquanto baixa de seus vizinhos. A biblioteca padrão reduz dependências e permite concentrar o trabalho em protocolo, concorrência e integridade.')
p('Os vizinhos são estáticos, configurados por IP e porta. Não foi usado tracker, pois é opcional. A matriz usa malha completa: com quatro peers, cada um configura os outros três como vizinhos. Cada leecher estabelece contato com todos, mesmo se um download curto concluir antes da conexão com um vizinho que iniciou depois.')
p('O arquivo é dividido logicamente em blocos de 1.024 ou 4.096 bytes. O metadado JSON informa versão, tamanho, tamanho de bloco, nome informativo, hashes por bloco e hash completo. Todos recebem esse metadado previamente; ele é considerado confiável.')
p('Os blocos ficam em um arquivo parcial em disco, gravados por offset, evitando carregar todo o arquivo em memória. O conjunto have registra blocos verificados; busy reserva pedidos em voo. Prioridades circulares de índices, baseadas na porta local, favorecem blocos diferentes entre leechers e seu compartilhamento.')
p('Após cada bloco passar na checagem de tamanho e SHA-256, ele fica disponível para upload. Ao concluir, verifica-se o SHA-256 completo e renomeia-se o parcial para arquivo_final.bin. O peer continua servindo; executar.py encerra automaticamente todos os processos quando os downloads ativos terminam, inclusive na demonstração em um único terminal.')
page();title('2. Protocolo e implementação')
p('TCP fornece um fluxo de bytes, não mensagens. Por isso cada frame usa prefixo de comprimento de 4 bytes big-endian e corpo de até 8 MiB. readexactly trata frames divididos em múltiplas leituras. Conexões persistentes evitam reconectar a cada bloco.')
table([['Mensagem','Conteúdo / função'],['have (JSON)','Pedir lista dos índices disponíveis'],['get (JSON)','Pedir índice de bloco e identificar arquivo pelo hash'],['J + JSON','Responder inventário de blocos'],['B + bytes','Entregar bloco binário sem base64'],['E + texto','Indicar arquivo incorreto ou bloco indisponível']],[120,360])
p('Um pedido fica em voo por conexão, dispensando identificador de correlação. Cada vizinho possui sua própria tarefa de download. O servidor mantém uma tarefa por conexão recebida. Gravação/atualização do conjunto e leitura do bloco não contêm await; assim, outras tarefas não alteram o ponteiro compartilhado entre seek e read/write.')
p('Conexão tem timeout de 2 s; resposta, 5 s; servidor ocioso, 15 s. Falhas liberam reservas e tentam novamente após 100 ms; falta de blocos novos gera nova consulta após 20 ms. Estes valores privilegiam uma demonstração em rede local. Não há limite global de espera.')
p('Hashes por bloco rejeitam dados corrompidos antes de publicá-los. O hash final confirma remontagem. O nome do metadado é informativo: a saída usa nome local fixo, evitando usar dados remotos como caminho de escrita.')
title('3. Procedimento experimental')
p('Executaram-se 24 configurações, com cinco repetições cada (120 transferências): 2/4 peers x 1.024/4.096 bytes x 10/20 KiB, 1/5/10/20 MiB. KB e MB foram interpretados como unidades binárias. Todos usam processos independentes, malha completa e TCP loopback.')
p('A bateria é automática: <b>python3 executar.py --testes --repeticoes 5 --seed 2026</b>. Geração pseudoaleatória reproduz os mesmos bytes por tamanho; a ordem dos casos é embaralhada por repetição com semente registrada. Cada caso verifica tamanho, SHA-256, índices, fontes e conexão a todos os vizinhos. Logs e metadados são preservados; binários temporários são descartados.')
p('Média aritmética e desvio-padrão amostral (denominador n - 1) são calculados dos cinco tempos. O intervalo medido vai da inicialização até arquivos completos e contato com todos os vizinhos, incluindo logs. Portas, caches e escalonamento variam; os números não representam capacidade de enlace nem desempenho em LAN/WAN.')
page();title('4. Resultados da matriz completa')
data=[['Arquivo','2 peers / 1 KiB','2 peers / 4 KiB','4 peers / 1 KiB','4 peers / 4 KiB']]
for size,label in [(10240,'10 KiB'),(20480,'20 KiB'),(1048576,'1 MiB'),(5242880,'5 MiB'),(10485760,'10 MiB'),(20971520,'20 MiB')]:
 vals=[]
 for n,b in [(2,1024),(2,4096),(4,1024),(4,4096)]:
  x=next(x for x in r if x['size_bytes']==size and x['peers']==n and x['block_bytes']==b)
  vals.append(f"{x['mean_seconds']:.3f} ± {x['std_seconds']:.3f}")
 data.append([label,*vals])
table(data,[65,105,105,105,105])
p('<b>Tempo em segundos: média ± desvio-padrão amostral; n = 5 em cada célula.</b> Cada configuração representa cinco execuções completas, com os mesmos critérios de conclusão.')
p('<b>Integridade: 120/120 execuções aprovadas.</b> Todos os arquivos finais tiveram tamanho e SHA-256 iguais ao original. Os logs confirmam que cada leecher se conectou a todos os vizinhos configurados. Cada bloco foi recebido uma única vez e sua fonte pertence à lista de vizinhos.')
p('Os valores acima são medições da malha completa. Quatro peers entregam três cópias em paralelo, com possibilidade de redistribuição entre leechers. Os tempos incluem inicialização, cópia da semente, espera pelo contato com todos os vizinhos, polling e logs; não medem apenas transmissão de bytes.')
p('Dados individuais em resultados/medicoes.json; estatísticas em resultados/estatisticas.csv e .json; ambiente e sementes em resultados/ambiente.json. Cada linha aponta para logs e manifesto compartilhado, permitindo conferir os cinco valores e recalcular média/desvio. Nenhum tempo de cenário com atraso artificial integra a tabela acima.')
p('Os cenários adicionais comprovam redistribuição antes da conclusão, início tardio da semente, múltiplas fontes e recuperação após falha. A demonstração automática é <b>python3 executar.py</b>: cria a rede, provoca falhas, verifica integridade e encerra todos os processos, sem abrir terminais adicionais.')
page();title('5. Falhas e recuperação')
x=next(x for x in extra if x['case']=='queda_temporaria')
y=next(x for x in extra if x['case']=='queda_permanente')
p(f"<b>Queda temporária:</b> única semente interrompida por SIGKILL durante downloads incompletos. Leechers preservaram blocos e reconectaram após seu retorno: {x['retries']} tentativas e {x['recovery_seconds']:.3f} s entre queda e conclusão. <b>Queda permanente controlada:</b> duas sementes iniciais; uma foi morta sem retorno, e os três sobreviventes concluíram em {y['recovery_seconds']:.3f} s após a queda. Tamanho e SHA-256 corretos em ambos.")
p('<b>Peer aleatório offline:</b> cinco ensaios, quatro peers em malha e duas sementes iniciais (A/B). O ID foi sorteado entre os quatro peers com sementes 0 a 4. A falha foi aplicada após observar envio real pelo peer escolhido e downloads sobreviventes incompletos. Novos blocos vieram de outras fontes, sem reiniciar o peer morto.')
data=[['Sorteio','Peer morto','Blocos novos','Fontes após queda','Tempo (s)','SHA-256']]
for x in extra:
 if x.get('fault')!='aleatoria':continue
 labels={port:chr(65+i) for i,port in enumerate(x['peer_ports'])}
 sources='; '.join(chr(65+int(i))+': '+ '/'.join(labels[p] for p in ports if p!=x['failed_port']) for i,ports in x['sources_after_failure'].items())
 data.append([str(x['random_seed']),chr(65+x['failed_peer']),str(sum(x['received_after_failure'].values())),sources,f"{x['recovery_seconds']:.3f}",'OK'])
table(data,[42,62,73,145,77,60])
p('Cada linha é um ensaio de falha (n = 1), não uma média de desempenho. Blocos novos soma os recebidos pelos leechers sobreviventes após a queda; fontes excluem o peer morto. Tempo vai do SIGKILL à conclusão dos ativos. Arquivo: 524.325 bytes, blocos de 1 KiB; atrasos artificiais tornam a falha observável. Evidências em resultados/queda_aleatoria_N/controle.json e peer_N.jsonl.')
x=next(x for x in extra if x['case']=='compartilhamento_parcial')
p(f"<b>Outras verificações:</b> {x['early_served']} envios por leechers antes de completar no cenário parcial; semente tardia e malha aprovadas. <b>11/11 unitários</b>: remontagem fora de ordem, último bloco, corrupção, tamanho, arquivo vazio, metadados, hashes, frames fragmentados/truncados/excessivos e conexão após conclusão curta.")
title('6. Conclusão e limites')
p('<b>130 integrações e 11 unitários aprovados.</b> A malha permite fontes alternativas e o executor automatiza início, falha, verificação e encerramento. Sem outra cópia de um bloco perdido, é necessário aguardar sua fonte. Reiniciar o próprio leecher ainda descarta seu parcial. Os testes mantêm os leechers sobreviventes ativos; não demonstram retomada persistente nem tolerância a perda simultânea de todas as cópias.')
p('Referências: enunciado SD_TP2_2_2026.pdf, pp. 1-2; código e evidências no repositório indicado. Ensaios locais com metadado confiável; não há autenticação, descoberta automática ou medição em rede remota.')
def footer(c,d):
 c.setFont('Helvetica',8);c.setFillColor(HexColor('#667780'));c.drawString(48,28,'TP2 | Sistemas Distribuídos | 30/10/2026');c.drawRightString(A4[0]-48,28,str(d.page))
SimpleDocTemplate(str(ROOT/'docs/relatorio.pdf'),title='Transferência de arquivos P2P - Relatório',author='Augusto Coelho Fagundes; ADJAILSON FREIRE DE SÁ FILHO',pagesize=A4,rightMargin=48,leftMargin=48,topMargin=42,bottomMargin=45).build(story,onFirstPage=footer,onLaterPages=footer)
