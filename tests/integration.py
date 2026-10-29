"""24 combinações do enunciado + cenários de concorrência e recuperação."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
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

def run_case(size, block, count, name, topology='chain', recovery=False, delay=0):
    dest=ROOT/'resultados'/name; dest.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp); source=tmp/'source.bin'; source.write_bytes(os.urandom(size))
        m=manifest(source,block); meta=tmp/'meta.json'; meta.write_text(json.dumps(m))
        (dest/'metadados.json').write_text(json.dumps(m))
        ports=free_ports(count); processes=[]; streams=[]
        started=time.monotonic()
        def start(i):
            neighbors=([ports[i-1]] if i else [ports[1]]) if topology=='chain' else [p for p in ports if p!=ports[i]]
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
                if all((tmp/str(i)/'arquivo_final.bin').exists() for i in range(count)): break
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
            expected={ports[i-1]} if topology=='chain' else set(ports)-{ports[i]}
            assert set(sources[str(i)])<=expected
        early=sum(e['event']=='sent' and not e.get('complete',True) for es in events[1:] for e in es)
        retries=sum(e['event']=='retry' for es in events for e in es)
        if delay and count>2: assert early>0, 'não comprovou compartilhamento antes de completar'
        if recovery: assert retries>0
        row=dict(case=name,size_bytes=size,block_bytes=block,peers=count,topology=topology,
                 seconds=round(elapsed,4),aggregate_mib_s=round(size*(count-1)/1048576/elapsed,3),
                 integrity='PASS',early_served=early,retries=retries,sources=sources,sha256=m['sha256'])
        (dest/'verificacao.json').write_text(json.dumps(row,indent=2))
        print(json.dumps(row),flush=True)
        return row

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--quick',action='store_true'); a=ap.parse_args()
    results=[]
    sizes=[10240,20480,1048576,5242880,10485760,20971520]
    for size in (sizes[:1] if a.quick else sizes):
        for block in (1024,4096):
            for peers in (2,4):
                results.append(run_case(size,block,peers,f'n{peers}_b{block}_s{size}'))
    results.append(run_case(131123,1024,4,'compartilhamento_parcial',delay=.001))
    results.append(run_case(65539,1024,2,'seeder_tardio',recovery=True))
    results.append(run_case(1048576,4096,4,'malha_completa',topology='mesh'))
    out=ROOT/'resultados'
    (out/'resumo.json').write_text(json.dumps(results,indent=2))
    with (out/'resumo.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(results[0]));writer.writeheader();writer.writerows(results)
    (out/'ambiente.json').write_text(json.dumps(dict(python=sys.version,platform=platform.platform(),
        cpu_count=os.cpu_count(),date='2026-10-29',network='loopback TCP, processos independentes',
        repetitions=1, units='KB/MB do enunciado interpretados como KiB/MiB'),indent=2))
if __name__=='__main__':main()
