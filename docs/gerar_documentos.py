"""Gera relatório (4 páginas) e rascunho visual (8 slides) com ReportLab."""
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
p('<b>Sistemas Distribuídos - TP2 | CEFET-MG | 2026/2</b><br/>Professora: Michelle Hanne.<br/><b>Integrantes: Augusto Coelho Fagundes e ADJAILSON FREIRE DE SÁ FILHO.</b><br/>Implementação, testes e redação preparados com Codex, assistente de IA da OpenAI, a pedido de Augusto. Data: 29/10/2026.')
p(f'<b>Código-fonte:</b> <link href="{repo}" color="blue">{repo}</link><br/>Repositório público, acessível pelo link. O ZIP contém uma cópia independente do código e das evidências.')
title('1. Arquitetura e decisões')
p('Cada peer é um processo Python com um servidor TCP e tarefas clientes no mesmo event loop asyncio. Ele atende solicitações enquanto baixa de seus vizinhos. A biblioteca padrão reduz dependências e permite concentrar o trabalho em protocolo, concorrência e integridade.')
p('Os vizinhos são estáticos, configurados por IP e porta. Não foi usado tracker, pois é opcional. A matriz de testes usa A -> B -> C -> D para forçar o repasse por peers intermediários. Um teste adicional utiliza malha completa.')
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
p('Executaram-se 24 combinações: 2/4 peers x 1.024/4.096 bytes x 10/20 KiB, 1/5/10/20 MiB. KB e MB do enunciado foram interpretados como unidades binárias. Cada caso usa conteúdo aleatório, processos independentes e sockets TCP reais em loopback; nenhum resultado é simulado.')
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
p('<b>Integridade: 24/24 combinações aprovadas.</b> Todos os arquivos finais tiveram tamanho e SHA-256 iguais ao original. Os logs dos casos em cadeia confirmam que B recebeu de A, C de B e D de C.')
p('Em 20 MiB, dois peers levaram 2,5323 s com blocos de 1 KiB e 0,9107 s com 4 KiB; quatro peers levaram 4,6279 s e 3,4303 s, respectivamente. Nessa execução, blocos maiores reduziram a quantidade de requisições e eventos de log, e apresentaram menor tempo.')
p('Quatro peers na cadeia precisam entregar três cópias e atravessar peers intermediários; não é uma comparação de aceleração de um único download. Os tempos incluem inicialização, cópia da semente, polling e logs, e não apenas transmissão de bytes. Arquivos pequenos são especialmente influenciados por esses custos.')
p('O campo aggregate_mib_s do CSV é tamanho x (peers - 1) / tempo / 2^20: taxa agregada de cópias entregues, não capacidade física de enlace. Rede local em loopback, caches e escalonamento limitam qualquer generalização para LAN/WAN.')
p('Ambiente detalhado em resultados/ambiente.json. Logs por caso em resultados/&lt;caso&gt;/peer_N.jsonl; verificacao.json associa hashes, fontes, tempo e contagem de repasses parciais.')
page();title('5. Casos adicionais e avaliação')
p('<b>Compartilhamento parcial:</b> quatro processos, 131.123 bytes, blocos de 1 KiB e atraso artificial de 1 ms por resposta. Conclusão em 1,4118 s; 216 envios ocorreram por leechers antes da conclusão de seus downloads. O atraso facilita observar a concorrência e não integra a matriz de desempenho.')
p('<b>Seeder tardio:</b> o seeder inicia 700 ms depois do leecher. Houve sete tentativas de reconexão e conclusão correta em 1,0287 s. O caso demonstra recuperação de indisponibilidade inicial; não simula reinício no meio da transferência.')
p('<b>Malha completa:</b> quatro peers, 1 MiB e blocos de 4 KiB. Conclusão correta em 1,1444 s; foram observadas múltiplas fontes em dois leechers e 30 envios antes da conclusão. A seleção depende do escalonamento, sem justiça garantida entre vizinhos.')
p('<b>Testes unitários: 10/10 aprovados.</b> Cobrem último bloco parcial e montagem fora de ordem, corrupção, tamanho incorreto, arquivo vazio, metadado inválido, tamanho de bloco inválido, hash final divergente, frame fragmentado, frame truncado e limite de frame.')
title('6. Limitações e conclusão')
p('A solução atende à simetria, fragmentação, registro local de blocos, redistribuição durante o download e montagem verificada. Usa operações de disco síncronas curtas no event loop; a aplicação não garante durabilidade contra queda de energia. Não implementa autenticação/TLS, rarest-first, descoberta de peers, retomada persistente nem distribuição automática de metadados. Vizinhos são cooperativos e o metadado é confiável.')
p('As 27 integrações e os 10 testes unitários passaram. Isso comprova os cenários executados, sem demonstrar comportamento em toda falha possível. Melhorias futuras: retomada com bitmap persistente, inventários incrementais, agendamento de blocos e ensaios repetidos em máquinas/redes distintas.')
p('<b>Referências:</b> enunciado SD_TP2_2_2026.pdf, seções 1 a 3, pp. 1-2; código e evidências no repositório acima. Instruções reproduzíveis no README e especificação detalhada em docs/protocolo.md.')
def footer(c,d):
 c.setFont('Helvetica',8);c.setFillColor(HexColor('#667780'));c.drawString(48,28,'TP2 | Sistemas Distribuídos | 29/10/2026');c.drawRightString(A4[0]-48,28,str(d.page))
SimpleDocTemplate(str(ROOT/'docs/relatorio.pdf'),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=42,bottomMargin=45).build(story,onFirstPage=footer,onLaterPages=footer)
slides=[
 ('Um peer baixa e compartilha', ['Transferência de arquivos P2P - TP2 / CEFET-MG','Python + asyncio + TCP','Augusto Coelho Fagundes<br/>ADJAILSON FREIRE DE SÁ FILHO'], 'Abrir explicando que a função de cliente e servidor existe no mesmo processo. Material preparado com Codex, assistente de IA da OpenAI.'),
 ('A cadeia comprova o repasse', ['A (semente)  >  B  >  C  >  D','B e C servem blocos antes de completar o arquivo.','Vizinhos estáticos; um processo por peer.'], 'Mostrar o desenho. D não conhece A; portanto a chegada dos dados exige redistribuição pelos intermediários.'),
 ('Do arquivo aos blocos verificados', ['Metadado: tamanho + hashes por bloco + SHA-256 final','Receber > verificar > gravar > anunciar no inventário','Ao completar: verificar o todo e publicar arquivo_final.bin'], 'Explicar bloco final menor, arquivo parcial em disco e dois conjuntos have/busy. Hash identifica corrupção; não autentica o remetente.'),
 ('TCP precisa de enquadramento', ['4 bytes de comprimento + corpo da mensagem','have / get: JSON | inventário: J | bloco: B | erro: E','Conexões persistentes, deadlines e novas tentativas'], 'TCP não preserva fronteiras de mensagens. readexactly reconstrói frames. Uma tarefa por vizinho permite receber e enviar simultaneamente.'),
 ('A matriz cobriu 24 combinações', ['2 e 4 processos; blocos de 1 e 4 KiB','10/20 KiB e 1/5/10/20 MiB','24/24: SHA-256, tamanho e fontes corretos'], 'Todos os testes usaram processos reais e loopback. Explicar unidades binárias. Cada caso foi executado uma vez; dados aleatórios são regenerados.'),
 ('Blocos maiores reduziram o tempo em 20 MiB', ['2 peers: 2,5323 s (1 KiB) > 0,9107 s (4 KiB)','4 peers: 4,6279 s (1 KiB) > 3,4303 s (4 KiB)','Medição inclui inicialização e logs; não representa WAN.'], 'Mais peers na cadeia também significam mais cópias entregues. Não concluir que quatro peers aceleram ou pioram universalmente P2P.'),
 ('As evidências vão além do arquivo final', ['216 envios durante download no caso com atraso','Seeder tardio: 7 tentativas, recuperação correta','Malha: múltiplas fontes | 10 testes unitários aprovados'], 'Abrir verificacao.json e um log received/sent. Mostrar complete=false. O teste de recuperação é de indisponibilidade inicial.'),
 ('Demonstração e próximos passos', ['Gerar metadado; iniciar A e B; comparar SHA-256','Limites: sem retomada persistente, TLS ou tracker','Código, testes, logs e relatório acompanham a entrega.'], 'Executar os comandos do README. Concluir explicando as escolhas e limites. Repositório público: Augusto42/sd-tp2-p2p-2026.')]
c=canvas.Canvas(str(ROOT/'docs/rascunho_apresentacao.pdf'),pagesize=(960,540))
for i,(t,lines,note) in enumerate(slides,1):
 c.setFillColor(HexColor('#f5f8f8'));c.rect(0,0,960,540,fill=1,stroke=0)
 c.setFillColor(HexColor('#147d87'));c.rect(48,458,65,6,fill=1,stroke=0)
 st=ParagraphStyle('s',fontName='Helvetica-Bold',fontSize=29,leading=35,textColor=HexColor('#133749'))
 para=Paragraph(t,st);w,h=para.wrap(860,100);para.drawOn(c,48,425-h)
 y=290
 for line in lines:
  para=Paragraph(line,ParagraphStyle('l',fontName='Helvetica',fontSize=23,leading=30,textColor=HexColor('#263f48')))
  w,h=para.wrap(850,100);para.drawOn(c,48,y-h);y-=h+28
 c.setFillColor(HexColor('#607780'));c.setFont('Helvetica',10);c.drawString(48,30,'RASCUNHO | TP2 - Sistemas Distribuídos | Codex / OpenAI');c.drawRightString(912,30,f'{i}/8');c.showPage()
c.save()
with (ROOT/'docs/roteiro_apresentacao.md').open('w') as f:
 f.write('# Roteiro de apresentação (8 a 10 minutos)\n\n')
 for i,(t,lines,note) in enumerate(slides,1):
  f.write(f'## Slide {i}: {t}\n\n'+ '\n'.join('- '+l for l in lines)+'\n\n**Fala sugerida:** '+note+'\n\n')
 f.write('## Perguntas prováveis\n\n- Por que TCP? Confiabilidade de transporte, com protocolo de frames próprio.\n- Como comprovar P2P? Cadeia força repasse e logs registram envio antes de completar.\n- O que ocorre se um peer cair? Reconexão e nova busca, se existir fonte; reinício do leecher não retoma estado.\n- SHA-256 garante segurança? Detecta divergência frente a metadado confiável; não autentica a origem.\n- Qual a limitação dos tempos? Uma execução por caso em loopback, incluindo custos de inicialização e logs.\n')
print('PDFs e roteiro gerados')
