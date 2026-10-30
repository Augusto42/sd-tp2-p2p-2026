"""Peer P2P assíncrono: biblioteca padrão Python 3.10+."""
import argparse
import asyncio
import hashlib
import json
import math
from pathlib import Path
import signal
import struct
import time

MAX_FRAME = 8 * 1024 * 1024

def sha(data):
    return hashlib.sha256(data).hexdigest()

def manifest(path, block_size):
    if not 1 <= block_size <= 65536:
        raise ValueError('block_size deve estar entre 1 e 65536')
    hashes, whole, size = [], hashlib.sha256(), 0
    with Path(path).open('rb') as f:
        while chunk := f.read(block_size):
            hashes.append(sha(chunk)); whole.update(chunk); size += len(chunk)
    return dict(version=1, name=Path(path).name, size=size, block_size=block_size,
                sha256=whole.hexdigest(), blocks=hashes)

def validate_meta(m):
    if m['version'] != 1 or type(m['size']) is not int or m['size'] < 0:
        raise ValueError('metadado inválido')
    if type(m['block_size']) is not int or not 1 <= m['block_size'] <= 65536:
        raise ValueError('bloco inválido')
    if len(m['blocks']) != math.ceil(m['size'] / m['block_size']):
        raise ValueError('quantidade de blocos inválida')
    for h in [m['sha256'], *m['blocks']]:
        if len(h) != 64 or any(c not in '0123456789abcdef' for c in h):
            raise ValueError('hash inválido')

async def send(writer, data):
    if len(data) > MAX_FRAME:
        raise ValueError('frame excessivo')
    writer.write(struct.pack('!I', len(data)) + data)
    await writer.drain()

async def receive(reader):
    n = struct.unpack('!I', await reader.readexactly(4))[0]
    if n > MAX_FRAME:
        raise ValueError('frame excessivo')
    return await reader.readexactly(n)

class Peer:
    def __init__(self, meta, folder, host, port, neighbors, log, seed=None, delay=0):
        validate_meta(meta)
        self.m = meta; self.folder = Path(folder); self.folder.mkdir(parents=True, exist_ok=True)
        self.host, self.port, self.neighbors = host, port, neighbors
        self.logfile = Path(log).open('w', encoding='utf8')
        self.have, self.busy = set(), set()
        self.delay = delay
        self.final = self.folder / 'arquivo_final.bin'
        self.part = self.folder / 'arquivo.part'
        self.file = self.part.open('w+b'); self.file.truncate(meta['size'])
        self.started = time.monotonic(); self.done = False
        self.seed = Path(seed) if seed else None
        if self.seed:
            with self.seed.open('rb') as source:
                for i in range(len(meta['blocks'])):
                    self.put(i, source.read(meta['block_size']))
                if source.read(1):
                    raise ValueError('semente maior que metadado')
            self.finish()

    def event(self, event, **kw):
        self.logfile.write(json.dumps(dict(event=event, peer=self.port,
            elapsed=round(time.monotonic()-self.started, 6), **kw))+'\n')
        self.logfile.flush()

    def expected(self, i):
        return min(self.m['block_size'], self.m['size']-i*self.m['block_size'])

    def put(self, i, data):
        if len(data) != self.expected(i) or sha(data) != self.m['blocks'][i]:
            raise ValueError('integridade de bloco inválida')
        self.file.seek(i*self.m['block_size']); self.file.write(data); self.file.flush()
        self.have.add(i)

    def finish(self):
        if self.done or len(self.have) != len(self.m['blocks']):
            return
        self.file.flush(); self.file.seek(0)
        digest = hashlib.file_digest(self.file, 'sha256').hexdigest() if hasattr(hashlib, 'file_digest') else self.hash_file()
        if digest != self.m['sha256']:
            raise ValueError('integridade final inválida')
        self.part.replace(self.final)
        self.done = True
        self.event('complete', sha256=digest, size=self.m['size'], blocks=len(self.have))

    def hash_file(self):
        h = hashlib.sha256()
        while data := self.file.read(65536): h.update(data)
        return h.hexdigest()

    async def serve(self, reader, writer):
        try:
            while True:
                q = json.loads(await asyncio.wait_for(receive(reader), 15))
                if q.get('file') != self.m['sha256']:
                    await send(writer, b'Ewrong_file'); continue
                if q.get('op') == 'have':
                    await send(writer, b'J'+json.dumps(sorted(self.have)).encode())
                elif q.get('op') == 'get' and type(q.get('index')) is int and q['index'] in self.have:
                    i = q['index']; self.file.seek(i*self.m['block_size'])
                    data = self.file.read(self.expected(i))
                    if self.delay: await asyncio.sleep(self.delay)
                    await send(writer, b'B'+data)
                    self.event('sent', index=i, target=str(writer.get_extra_info('peername')), complete=self.done)
                else:
                    await send(writer, b'Enot_available')
        except (asyncio.IncompleteReadError, ConnectionError, ValueError, asyncio.TimeoutError, KeyError, TypeError):
            pass
        finally:
            writer.close()
            try: await writer.wait_closed()
            except ConnectionError: pass

    async def fetch(self, host, port):
        if self.seed or not self.m["blocks"]:
            return
        connected_once = False
        # Mesmo downloads curtos devem estabelecer contato com todos os vizinhos.
        while not self.done or not connected_once:
            writer = None
            try:
                reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), 2)
                connected_once = True
                self.event('connected', source=port)
                while not self.done:
                    await send(writer, json.dumps(dict(op='have', file=self.m['sha256'])).encode())
                    reply = await asyncio.wait_for(receive(reader), 5)
                    if reply[:1] != b'J': raise ValueError('resposta HAVE inválida')
                    available = json.loads(reply[1:])
                    if not isinstance(available, list) or any(type(i) is not int or not 0 <= i < len(self.m['blocks']) for i in available):
                        raise ValueError('inventário inválido')
                    # Prioridades circulares diferentes evitam downloads idênticos em todos os peers.
                    candidates = sorted((i for i in available if i not in self.have and i not in self.busy),
                                        key=lambda i: (i - self.port) % len(self.m['blocks']))
                    for i in candidates:
                        if i in self.have or i in self.busy: continue
                        self.busy.add(i)
                        try:
                            await send(writer, json.dumps(dict(op='get', index=i, file=self.m['sha256'])).encode())
                            reply = await asyncio.wait_for(receive(reader), 5)
                            if reply[:1] != b'B': raise ValueError('bloco indisponível')
                            self.put(i, reply[1:])
                            self.event('received', index=i, source=port, have=len(self.have))
                            self.finish()
                        finally: self.busy.discard(i)
                    if not candidates: await asyncio.sleep(.02)
            except (OSError, ValueError, asyncio.TimeoutError, asyncio.IncompleteReadError, TypeError):
                self.event('retry', source=port)
                await asyncio.sleep(.1)
            finally:
                if writer:
                    writer.close()
                    try: await writer.wait_closed()
                    except ConnectionError: pass

    async def run(self):
        server = await asyncio.start_server(self.serve, self.host, self.port)
        self.event('listening', neighbors=self.neighbors)
        self.finish()
        tasks = [asyncio.create_task(self.fetch(h,p)) for h,p in self.neighbors]
        stop = asyncio.Event()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM): loop.add_signal_handler(sig, stop.set)
        try:
            async with server: await stop.wait()
        finally:
            for t in tasks: t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            self.file.close(); self.logfile.close()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    m = sub.add_parser('manifest'); m.add_argument('file'); m.add_argument('output'); m.add_argument('--block-size', type=int, default=1024)
    r = sub.add_parser('run'); r.add_argument('--meta', required=True); r.add_argument('--dir', required=True)
    r.add_argument('--host', default='127.0.0.1'); r.add_argument('--port', type=int, required=True)
    r.add_argument('--neighbor', action='append', default=[]); r.add_argument('--seed'); r.add_argument('--log', required=True)
    r.add_argument('--serve-delay', type=float, default=0, help='Atraso artificial por bloco, somente para testes')
    a = parser.parse_args()
    if a.command == 'manifest':
        Path(a.output).write_text(json.dumps(manifest(a.file, a.block_size)), encoding='utf8')
    else:
        neighbors = [(s.rsplit(':',1)[0], int(s.rsplit(':',1)[1])) for s in a.neighbor]
        asyncio.run(Peer(json.loads(Path(a.meta).read_text()), a.dir, a.host, a.port, neighbors, a.log, a.seed, a.serve_delay).run())

if __name__ == '__main__': main()
