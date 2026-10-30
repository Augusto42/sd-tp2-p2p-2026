"""Gera o relatório com ReportLab."""
from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.pagesizes import A4
ROOT=Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'resultados/resumo.json').read_text())
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
p('Os blocos ficam em um arquivo parcial em disco, gravados por offset, evitando carregar todo o arquivo em memória. O conjunto have registra os blocos verificados; busy reserva pedidos em voo e evita que duas tarefas solicitem o mesmo bloco ao mesmo tempo.')
p('Após cada bloco passar na checagem de tamanho e SHA-256, ele fica disponível para upload. Ao concluir, verifica-se o SHA-256 completo e renomeia-se o parcial para arquivo_final.bin. O peer continua servindo até receber SIGINT ou SIGTERM.')
page();title('2. Protocolo e implementação')
p('TCP fornece um fluxo de bytes, não mensagens. Por isso cada frame usa prefixo de comprimento de 4 bytes big-endian e corpo de até 8 MiB. readexactly trata frames divididos em múltiplas leituras. Conexões persistentes evitam reconectar a cada bloco.')
table([['Mensagem','Conteúdo / função'],['have (JSON)','Pedir lista dos índices disponíveis'],['get (JSON)','Pedir índice de bloco e identificar arquivo pelo hash'],['J + JSON','Responder inventário de blocos'],['B + bytes','Entregar bloco binário sem base64'],['E + texto','Indicar arquivo incorreto ou bloco indisponível']],[120,360])
p('Um pedido fica em voo por conexão, dispensando identificador de correlação. Cada vizinho possui sua própria tarefa de download. O servidor mantém uma tarefa por conexão recebida. Gravação/atualização do conjunto e leitura do bloco não contêm await; assim, outras tarefas não alteram o ponteiro compartilhado entre seek e read/write.')
p('Conexão tem timeout de 2 s; resposta, 5 s; servidor ocioso, 15 s. Falhas liberam reservas e tentam novamente após 100 ms; falta de blocos novos gera nova consulta após 20 ms. Estes valores privilegiam uma demonstração em rede local. Não há limite global de espera.')
p('Hashes por bloco rejeitam dados corrompidos antes de publicá-los. O hash final confirma remontagem. O nome do metadado é informativo: a saída usa nome local fixo, evitando usar dados remotos como caminho de escrita.')
title('3. Procedimento experimental')
p('Executaram-se 24 combinações: 2/4 peers x 1.024/4.096 bytes x 10/20 KiB, 1/5/10/20 MiB. KB e MB do enunciado foram interpretados como unidades binárias. Cada caso usa conteúdo aleatório, processos independentes e sockets TCP reais em loopback.')
p('Cada transferência verifica tamanho, SHA-256 e origem dos blocos nos logs. Os testes preservam metadados, eventos JSONL, verificações e tabelas CSV/JSON; os binários temporários são descartados. A repetição gera novos dados. Cada configuração teve uma execução; não há intervalos de confiança.')
page();title('4. Resultados da matriz completa')
data=[['Arquivo','2 peers / 1 KiB','2 peers / 4 KiB','4 peers / 1 KiB','4 peers / 4 KiB']]
for size,label in [(10240,'10 KiB'),(20480,'20 KiB'),(1048576,'1 MiB'),(5242880,'5 MiB'),(10485760,'10 MiB'),(20971520,'20 MiB')]:
 vals=[]
 for n,b in [(2,1024),(2,4096),(4,1024),(4,4096)]:
  x=next(x for x in r[:24] if x['size_bytes']==size and x['peers']==n and x['block_bytes']==b)
  vals.append(f"{x['seconds']:.4f} s")
 data.append([label,*vals])
table(data,[65,105,105,105,105])
p('<b>Integridade: 24/24 combinações aprovadas.</b> Todos os arquivos finais tiveram tamanho e SHA-256 iguais ao original. Os logs confirmam que cada leecher se conectou a todos os vizinhos configurados. Cada bloco foi recebido uma única vez e sua fonte pertence à lista de vizinhos.')
p('Os valores acima são medições da malha completa. Quatro peers entregam três cópias em paralelo, com possibilidade de redistribuição entre leechers. Os tempos incluem inicialização, cópia da semente, espera pelo contato com todos os vizinhos, polling e logs; não medem apenas transmissão de bytes.')
p('O campo aggregate_mib_s do CSV é tamanho x (peers - 1) / tempo / 2^20: taxa agregada de cópias entregues, não capacidade física de enlace. Rede local em loopback, caches e escalonamento limitam qualquer generalização para LAN/WAN.')
p('Ambiente detalhado em resultados/ambiente.json. Logs por caso em resultados/&lt;caso&gt;/peer_N.jsonl; verificacao.json associa hashes, fontes, tempo e contagem de repasses parciais.')
page();title('5. Casos adicionais e avaliação')
for case,label in [('compartilhamento_parcial','Compartilhamento parcial'),('seeder_tardio','Seeder tardio'),('malha_completa','Malha completa')]:
 x=next(x for x in r if x['case']==case)
 p(f"<b>{label}:</b> integridade aprovada em {x['seconds']:.4f} s; {x['early_served']} envios por leechers antes de completar; {x['retries']} novas tentativas.")
p('O cenário de compartilhamento parcial usa atraso artificial de 1 ms; no seeder tardio, a fonte inicia 700 ms depois.')
p('<b>Queda temporária:</b> quatro peers em malha, uma semente. SIGKILL interrompe a semente com downloads ainda incompletos. Os leechers registram falhas, mantêm os blocos válidos e reconectam após seu retorno. Todos concluem com tamanho e SHA-256 corretos, sem baixar novamente blocos já recebidos.')
p('<b>Queda permanente:</b> quatro peers em malha, duas sementes iniciais. Uma é morta durante a transferência. Os três processos restantes concluem sem seu retorno, recebendo novos blocos de fontes alternativas. A redundância garante disponibilidade dos blocos; não é possível reconstruir blocos que só existiam em um peer definitivamente perdido.')
p('<b>Testes unitários: 11/11 aprovados.</b> Cobrem último bloco parcial e montagem fora de ordem, corrupção, tamanho incorreto, arquivo vazio, metadado inválido, tamanho de bloco inválido, hash final divergente, frame fragmentado, frame truncado limite de frame e conexão a vizinho mesmo após download curto concluir.')
title('6. Limitações e conclusão')
p('A solução atende à simetria, fragmentação, registro local de blocos, redistribuição durante o download e montagem verificada. Usa operações de disco síncronas curtas no event loop; a aplicação não garante durabilidade contra queda de energia. Não implementa autenticação/TLS, rarest-first, descoberta de peers, retomada persistente nem distribuição automática de metadados. Vizinhos são cooperativos e o metadado é confiável.')
p('As 29 integrações e os 11 testes unitários passaram. Melhorias futuras: retomada com bitmap persistente, inventários incrementais, agendamento de blocos e ensaios repetidos em máquinas/redes distintas.')
p('<b>Referências:</b> enunciado SD_TP2_2_2026.pdf, seções 1 a 3, pp. 1-2; código e evidências no repositório acima. Instruções reproduzíveis no README e especificação detalhada em docs/protocolo.md.')
def footer(c,d):
 c.setFont('Helvetica',8);c.setFillColor(HexColor('#667780'));c.drawString(48,28,'TP2 | Sistemas Distribuídos | 30/10/2026');c.drawRightString(A4[0]-48,28,str(d.page))
SimpleDocTemplate(str(ROOT/'docs/relatorio.pdf'),title='Transferência de arquivos P2P - Relatório',author='Augusto Coelho Fagundes; ADJAILSON FREIRE DE SÁ FILHO',pagesize=A4,rightMargin=48,leftMargin=48,topMargin=42,bottomMargin=45).build(story,onFirstPage=footer,onLaterPages=footer)
