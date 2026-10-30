"""24 combinações do enunciado + cenários de concorrência e recuperação."""
import argparse
import csv
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import socket
import subprocess
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from peer import manifest
ROOT=Path(__file__).resolve().parents[1]

def free_ports(n):
    sockets=[]
    for _ in range(n):
        s=socket.socket(); s.bind(('127.0.0.1',0)); sockets.append(s)
    ports=[s.getsockname()[1] for s in sockets]
    for s in sockets:s.close()
    return ports

def run_case(size, block, count, name, recovery=False, delay=0, random_seed=None):
    dest=ROOT/'resultados'/name; dest.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp); source=tmp/'source.bin'; source.write_bytes(random.Random(random_seed).randbytes(size) if random_seed is not None else os.urandom(size))
        m=manifest(source,block); meta=tmp/'meta.json'; meta.write_text(json.dumps(m))
        (dest/'metadados.json').write_text(json.dumps(m))
        ports=free_ports(count); processes=[]; streams=[]
        started=time.monotonic()
        def start(i):
            neighbors=[p for p in ports if p!=ports[i]]
            command=[sys.executable,str(ROOT/'src/peer.py'),'run','--meta',str(meta),'--dir',str(tmp/str(i)),
                     '--port',str(ports[i]),'--log',str(dest/f'peer_{i}.jsonl'),'--serve-delay',str(delay)]
            for p in neighbors: command += ['--neighbor',f'127.0.0.1:{p}']
            if i==0: command += ['--seed',str(source)]
            stream=(dest/f'peer_{i}.stderr').open('w'); streams.append(stream)
            processes.append(subprocess.Popen(command,stdout=stream,stderr=stream))
        try:
            # Leechers iniciam antes do seeder: exercita tentativas de reconexão.
            for i in range(1,count): start(i)
            if recovery: time.sleep(.7)
            start(0)
            while True:
                if any(p.poll() is not None for p in processes): raise RuntimeError('processo terminou prematuramente')
                complete=all((tmp/str(i)/'arquivo_final.bin').exists() for i in range(count))
                connected_all=True
                if complete:
                    for i in range(1,count):
                        rows=[json.loads(line) for line in (dest/f'peer_{i}.jsonl').read_text().splitlines()]
                        connected_all &= {e['source'] for e in rows if e['event']=='connected'} == set(ports)-{ports[i]}
                if complete and connected_all: break
                if time.monotonic()-started>120: raise TimeoutError(name)
                time.sleep(.02)
            elapsed=time.monotonic()-started
            for i in range(count):
                output=tmp/str(i)/'arquivo_final.bin'
                assert output.stat().st_size==size
                assert hashlib.sha256(output.read_bytes()).hexdigest()==m['sha256']
            time.sleep(.03)
        finally:
            for p in processes:p.terminate()
            for p in processes:
                try:p.wait(timeout=5)
                except subprocess.TimeoutExpired:p.kill();p.wait()
            for s in streams:s.close()
        events=[[json.loads(l) for l in (dest/f'peer_{i}.jsonl').read_text().splitlines()] for i in range(count)]
        sources={str(i):sorted({e['source'] for e in events[i] if e['event']=='received'}) for i in range(1,count)}
        for i in range(1,count):
            got=[e for e in events[i] if e['event']=='received']
            assert len(got)==len(m['blocks'])
            expected=set(ports)-{ports[i]}
            assert set(sources[str(i)])<=expected
            assert {e['index'] for e in got} == set(range(len(m['blocks'])))
            connected={e['source'] for e in events[i] if e['event']=='connected'}
            assert connected == expected, f'peer {i} não conectou a todos: {connected} != {expected}'
        early=sum(e['event']=='sent' and not e.get('complete',True) for es in events[1:] for e in es)
        retries=sum(e['event']=='retry' for es in events for e in es)
        if delay and count>2: assert early>0, 'não comprovou compartilhamento antes de completar'
        if recovery: assert retries>0
        row=dict(case=name,size_bytes=size,block_bytes=block,peers=count,topology='mesh',
                 seconds=round(elapsed,4),aggregate_mib_s=round(size*(count-1)/1048576/elapsed,3),
                 integrity='PASS',early_served=early,retries=retries,sources=sources,sha256=m['sha256'])
        (dest/'verificacao.json').write_text(json.dumps(row,indent=2))
        print(json.dumps(row),flush=True)
        return row


def run_failure(mode, demo=False, random_seed=None):
    """SIGKILL durante download: reconexão ou continuidade por outra fonte."""
    victim=random.Random(random_seed).randrange(4) if mode=='aleatoria' else 0
    name='queda_'+mode+(f'_{random_seed}' if mode=='aleatoria' else '')
    dest=ROOT/'resultados'/('demo' if demo else '')/name
    dest.mkdir(parents=True,exist_ok=True)
    for old in dest.glob('peer_*'): old.unlink()
    size,block,count=524325,1024,4
    ports=free_ports(count); processes={}; streams=[]
    started=time.monotonic(); controller=[]
    def announce(event, **data):
        entry=dict(event=event,seconds=round(time.monotonic()-started,4),**data)
        controller.append(entry)
        if demo: print(json.dumps(entry,ensure_ascii=False),flush=True)
    def events(i):
        result=[]
        for file in sorted(dest.glob(f'peer_{i}*.jsonl')):
            for line in file.read_text().splitlines():
                try: result.append(json.loads(line))
                except json.JSONDecodeError: pass # leitura concorrente; linha ainda em escrita
        return result
    def wait(predicate):
        while not predicate():
            if time.monotonic()-started>60: raise TimeoutError(name)
            if any(p.poll() is not None for p in processes.values()):
                raise RuntimeError('peer ativo terminou inesperadamente')
            time.sleep(.01)
    with tempfile.TemporaryDirectory() as folder:
        tmp=Path(folder); source=tmp/'source.bin'; source.write_bytes(os.urandom(size))
        m=manifest(source,block); meta=tmp/'meta.json'; meta.write_text(json.dumps(m))
        (dest/'metadados.json').write_text(json.dumps(m))
        def start(i,restart=False):
            suffix='_reiniciado' if restart else ''
            command=[sys.executable,str(ROOT/'src/peer.py'),'run','--meta',str(meta),'--dir',str(tmp/str(i)),
                '--port',str(ports[i]),'--log',str(dest/f'peer_{i}{suffix}.jsonl'),'--serve-delay','0.01' if demo else '0.003']
            for j in range(count):
                if i!=j: command+=['--neighbor',f'127.0.0.1:{ports[j]}']
            if i==0 or (mode!='temporaria' and i==1): command+=['--seed',str(source)]
            stream=(dest/f'peer_{i}{suffix}.stderr').open('w'); streams.append(stream)
            processes[i]=subprocess.Popen(command,stdout=stream,stderr=stream)
        try:
            for i in range(count): start(i)
            announce('malha_iniciada',ports=ports,seeds=[0,1] if mode!='temporaria' else [0])
            # Espera downloads reais e todas as conexões iniciais antes de provocar a falha.
            leechers=[2,3] if mode!='temporaria' else [1,2,3]
            survivors=[i for i in leechers if i!=victim]
            wait(lambda: all({e['source'] for e in events(i) if e['event']=='connected'}==set(ports)-{ports[i]} for i in leechers)
                and all(sum(e['event']=='received' for e in events(i))>=20 for i in leechers)
                and any(e['event']=='received' and e['source']==ports[victim] for i in survivors for e in events(i)))
            leechers=survivors
            before={i:len(events(i)) for i in leechers}
            counts={i:sum(e['event']=='received' for e in events(i)) for i in leechers}
            assert all(0<n<len(m['blocks']) for n in counts.values()), counts
            failed=processes.pop(victim); failed.kill(); failed.wait(timeout=5)
            announce('peer_offline',peer=victim,port=ports[victim],blocks_received=counts,total_blocks=len(m['blocks']))
            wait(lambda: all(any(e['event']=='retry' and e['source']==ports[victim] for e in events(i)[before[i]:]) for i in leechers))
            time.sleep(2 if demo else .6)
            if mode=='temporaria':
                assert all(not (tmp/str(i)/'arquivo_final.bin').exists() for i in leechers), 'faltam blocos exclusivos do seeder offline'
                start(0,restart=True)
                announce('peer_reiniciado',peer=0)
            active=list(processes)
            wait(lambda: all((tmp/str(i)/'arquivo_final.bin').exists() for i in active))
            for i in active:
                output=tmp/str(i)/'arquivo_final.bin'
                assert output.stat().st_size==size
                assert hashlib.sha256(output.read_bytes()).hexdigest()==m['sha256']
            after={i:events(i)[before[i]:] for i in leechers}
            for i in leechers:
                got=[e for e in events(i) if e['event']=='received']
                assert len(got)==len(m['blocks'])
                assert {e['index'] for e in got}==set(range(len(m['blocks'])))
                assert any(e['event']=='received' for e in after[i])
                if mode!='temporaria':
                    assert any(e['event']=='received' and e['source']!=ports[victim] for e in after[i])
                if mode=='temporaria':
                    assert any(e['event']=='connected' and e['source']==ports[0] for e in after[i])
            announce('integridade_confirmada',peers=active,sha256=m['sha256'],size_bytes=size)
        finally:
            for process in processes.values(): process.terminate()
            for process in processes.values():
                try: process.wait(timeout=5)
                except subprocess.TimeoutExpired: process.kill(); process.wait()
            for stream in streams: stream.close()
    all_events=[events(i) for i in range(count)]
    elapsed=time.monotonic()-started
    row=dict(case=name,size_bytes=size,block_bytes=block,peers=count,topology='mesh',seconds=round(elapsed,4),
        aggregate_mib_s=None,integrity='PASS',early_served=sum(e['event']=='sent' and not e.get('complete',True) for es in all_events for e in es),
        retries=sum(e['event']=='retry' for es in all_events for e in es),
        sources={str(i):sorted({e['source'] for e in all_events[i] if e['event']=='received'}) for i in leechers},
        sha256=m['sha256'],fault=mode,failed_peer=victim,failed_port=ports[victim],peer_ports=ports,random_seed=random_seed,verified_peers=active,blocks_before_failure=counts,
        received_after_failure={str(i):sum(e['event']=='received' for e in after[i]) for i in leechers},
        sources_after_failure={str(i):sorted({e['source'] for e in after[i] if e['event']=='received'}) for i in leechers},
        recovery_seconds=round(next(e['seconds'] for e in controller if e['event']=='integridade_confirmada')-next(e['seconds'] for e in controller if e['event']=='peer_offline'),4),
        recovery='reconexao apos retorno da unica fonte' if mode=='temporaria' else 'conclusao sem retorno do peer; segunda semente disponivel')
    (dest/'controle.json').write_text(json.dumps(controller,indent=2))
    (dest/'verificacao.json').write_text(json.dumps(row,indent=2))
    print(json.dumps(row),flush=True)
    return row

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--quick',action='store_true'); ap.add_argument('--demo',action='store_true',help='Demonstra queda e recuperação em uma malha de quatro peers'); a=ap.parse_args()
    if a.demo:
        run_failure('temporaria', demo=True)
        run_failure('permanente', demo=True)
        return
    results=[]
    sizes=[10240,20480,1048576,5242880,10485760,20971520]
    for size in (sizes[:1] if a.quick else sizes):
        for block in (1024,4096):
            for peers in (2,4):
                results.append(run_case(size,block,peers,f'n{peers}_b{block}_s{size}'))
    results.append(run_case(131123,1024,4,'compartilhamento_parcial',delay=.001))
    results.append(run_case(65539,1024,2,'seeder_tardio',recovery=True))
    results.append(run_case(1048576,4096,4,'malha_completa'))
    results.extend([run_failure('temporaria'),run_failure('permanente')])
    out=ROOT/'resultados'
    (out/'resumo.json').write_text(json.dumps(results,indent=2))
    with (out/'resumo.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for row in results for k in row)));writer.writeheader();writer.writerows(results)
    (out/'ambiente.json').write_text(json.dumps(dict(python=sys.version,platform=platform.platform(),
        cpu_count=os.cpu_count(),date=date.today().isoformat(),network='loopback TCP, processos independentes',
        repetitions=1, units='KB/MB do enunciado interpretados como KiB/MiB'),indent=2))
if __name__=='__main__':main()
