import unittest
import zlib
from pathlib import Path

import sys
sys.path.append('..')
from binaryfile import fileformat
from binaryfile.utils import SimpleDict

def png_root(f):
	header = f.bytes('header', 8)
	for chunk in f.repeat('chunks', png_chunk):
		if chunk.type == b'IEND':
			break

def png_chunk(f):
	length = f.uint('size', 4)
	type_ = f.bytes('type', 4)
	if type_ == b'IHDR':
		data = f.section('data', png_ihdr)
	else:
		data = f.bytes('data', length)
	f.uint('crc', 4)

def png_ihdr(f):
	f.uint('width', 4)
	f.uint('height', 4)
	f.uint('bit_depth', 1)
	f.uint('color_type', 1)
	f.uint('compression_method', 1)
	f.uint('filter_method', 1)
	f.uint('interlace_method', 1)

def read_data(fname):
	with open(fname, 'rb') as fh:
		return fileformat.read(fh, png_root, result_type=SimpleDict)
def write_data(file, data):
	Path(file).parent.mkdir(parents=True, exist_ok=True)
	with open(file, 'wb') as fh:
		fileformat.write(fh, data, png_root)
def slurp_bytes(file):
	with open(file, 'rb') as fh:
		return fh.read()
def set_palette(data, index, rgb):
	types = [chunk.type for chunk in data.chunks]
	palette = data.chunks[types.index(b'PLTE')]
	palette.data = bytearray(palette.data)
	palette.data[index * 3 : index * 3 + 3] = rgb
	palette.crc = zlib.crc32(palette.type + palette.data)

class TestPng(unittest.TestCase):
	def testReadPng(self):
		data = read_data('files/green.png')
		self.assertEqual(data.header, b'\x89PNG\r\n\x1a\n')
		ihdr_chunk = data.chunks[0]
		self.assertEqual(ihdr_chunk.type, b'IHDR')
		self.assertEqual(ihdr_chunk.data.width, 3)
		self.assertEqual(ihdr_chunk.data.height, 3)
		self.assertEqual(ihdr_chunk.data.color_type, 3)  # Indexed
		iend_chunk = data.chunks[-1]
		self.assertEqual(iend_chunk.type, b'IEND')
	def testWriteUnmodifiedPng(self):
		data = read_data('files/green.png')
		write_data('out/green_unmodified.png', data)
		self.assertEqual(slurp_bytes('files/green.png'), slurp_bytes('out/green_unmodified.png'))
	def testWriteModifiedPng(self):
		data = read_data('files/green.png')
		set_palette(data, 4, (255, 0, 255))
		write_data('out/green_modified.png', data)
		self.assertNotEqual(slurp_bytes('files/green.png'), slurp_bytes('out/green_modified.png'))

if __name__ == '__main__':
	unittest.main()