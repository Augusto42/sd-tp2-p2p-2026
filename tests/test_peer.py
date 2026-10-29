import asyncio
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from peer import Peer, manifest, validate_meta, receive, MAX_FRAME

class Blocks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()
    def make(self, data):
        f = self.root/'input'; f.write_bytes(data)
        m = manifest(f, 1024)
        p = Peer(m, self.root/'out', '127.0.0.1', 0, [], self.root/'log')
        self.addCleanup(p.logfile.close); self.addCleanup(p.file.close)
        return p, m
    def test_out_of_order_and_partial_last(self):
        data = bytes(range(251))*11; p,m = self.make(data)
        for i in reversed(range(len(m['blocks']))): p.put(i,data[i*1024:(i+1)*1024])
        p.finish(); self.assertEqual(p.final.read_bytes(), data)
    def test_corruption_rejected(self):
        p,_ = self.make(b'x'*1024)
        with self.assertRaises(ValueError): p.put(0,b'y'*1024)
        self.assertEqual(p.have, set())
    def test_truncated_block_rejected(self):
        p,_ = self.make(b'x'*1024)
        with self.assertRaises(ValueError): p.put(0,b'x')
    def test_empty_file(self):
        p,_ = self.make(b''); p.finish(); self.assertEqual(p.final.read_bytes(),b'')
    def test_invalid_meta(self):
        _,m = self.make(b'x'); m['size']=5000
        with self.assertRaises(ValueError): validate_meta(m)
    def test_invalid_block_size(self):
        with self.assertRaises(ValueError): manifest(self.root/'missing',0)
    def test_whole_hash_checked(self):
        p,_ = self.make(b'x'); p.put(0,b'x'); p.m['sha256']='0'*64
        with self.assertRaises(ValueError): p.finish()

class Frames(unittest.IsolatedAsyncioTestCase):
    async def test_fragmented_frame(self):
        r = asyncio.StreamReader()
        async def feed():
            for b in struct.pack('!I',3)+b'abc':
                r.feed_data(bytes([b])); await asyncio.sleep(0)
        t=asyncio.create_task(feed()); self.assertEqual(await receive(r), b'abc'); await t
    async def test_truncated_frame(self):
        r=asyncio.StreamReader(); r.feed_data(struct.pack('!I',3)+b'a'); r.feed_eof()
        with self.assertRaises(asyncio.IncompleteReadError): await receive(r)
    async def test_oversized_frame(self):
        r=asyncio.StreamReader(); r.feed_data(struct.pack('!I',MAX_FRAME+1))
        with self.assertRaises(ValueError): await receive(r)
if __name__ == '__main__': unittest.main(verbosity=2)
