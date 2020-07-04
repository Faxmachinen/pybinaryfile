import unittest
import io
import struct

from binaryfile import fileformat

class TestBinarySectionReader(unittest.TestCase):
	def setUp(self):
		self.bytes = b'\xff123'
		self.file = io.BytesIO(self.bytes)
	def test_skip(self):
		def spec(f):
			f.skip(1)
			f.skip(3)
		result = fileformat.read(self.file, spec)
		self.assertEqual(result, { '__skipped': [self.bytes[0:1], self.bytes[1:4]] })
	def test_count(self):
		file = io.BytesIO(b'\x05Q12345Q')
		def spec(f):
			count = f.count('count', 'array', 1)
			f.skip(1)
			f.bytes('array', count)
		result = fileformat.read(file, spec)
		self.assertEqual(result.count, 5)
		self.assertEqual(result.array, b'12345')
	def test_bytes(self):
		def spec(f):
			first = f.bytes('first', 1)
			self.assertEqual(first, self.bytes[:1])
			rest = f.bytes('rest', None)
			self.assertEqual(rest, self.bytes[1:])
		result = fileformat.read(self.file, spec)
		self.assertEqual(result, { 'first': self.bytes[:1], 'rest': self.bytes[1:] })
	def test_uint(self):
		expected_value = int.from_bytes(self.bytes[:4], 'big', signed=False)
		def spec(f):
			value = f.uint('uint', 4)
			self.assertEqual(value, expected_value)
		result = fileformat.read(self.file, spec)
		self.assertEqual(result, { 'uint': expected_value })
	def test_int(self):
		expected_value = int.from_bytes(self.bytes[:4], 'big', signed=True)
		def spec(f):
			value = f.int('int', 4)
			self.assertEqual(value, expected_value)
		result = fileformat.read(self.file, spec)
		self.assertEqual(result, { 'int': expected_value })
	def test_struct(self):
		def spec(f):
			f.struct('struct', '>?3s')
		result = fileformat.read(self.file, spec)
		self.assertEqual(result, { 'struct': struct.unpack('>?3s', self.bytes) })
	def test_section(self):
		self.entered_section = False
		def spec(f):
			def section(f):
				self.entered_section = True
				self.assertIsInstance(f, fileformat.BinarySectionReader)
				f.bytes('first', 1)
			section = f.section('section', section)
			self.assertEqual(section, { 'first': self.bytes[:1] })
		result = fileformat.read(self.file, spec)
		self.assertTrue(self.entered_section)
		self.assertEqual(result, { 'section': { 'first': self.bytes[:1] }})
	def test_empty_array(self):
		def spec(f):
			f.array('empty')
		result = fileformat.read(self.file, spec)
		self.assertTrue('empty' in result)
		self.assertEqual(result.empty, [])
	def test_array(self):
		def spec(f):
			f.array('uints')
			for i in range(len(self.bytes)):
				f.uint('uints', 1)
		result = fileformat.read(self.file, spec)
		self.assertEqual(result, { 'uints': [b for b in self.bytes] })
	def test_bytes_eof(self):
		def spec(f):
			f.bytes('too_long', len(self.bytes) + 1)
		with self.assertRaises(EOFError):
			fileformat.read(self.file, spec)
	def test_uint_eof(self):
		def spec(f):
			f.uint('too_long', len(self.bytes) + 1)
		with self.assertRaises(EOFError):
			fileformat.read(self.file, spec)

class TestBinarySectionWriter(unittest.TestCase):
	def setUp(self):
		self.file = io.BytesIO()
	def test_skip_no_data(self):
		def spec(f):
			f.skip(1)
			f.skip(3)
		data = { }
		fileformat.write(self.file, data, spec)
		self.assertEqual(self.file.getvalue(), b'\x00' * 4)
	def test_skip_with_data(self):
		def spec(f):
			f.skip(1)
			f.skip(3)
		data = { '__skipped': [b'1', b'234'] }
		fileformat.write(self.file, data, spec)
		self.assertEqual(self.file.getvalue(), b'1234')
	def test_bytes(self):
		def spec(f):
			first = f.bytes('first', 1)
			self.assertEqual(first, b'1')
			rest = f.bytes('rest', None)
			self.assertEqual(rest, b'234')
		data = { 'first': b'1', 'rest': b'234' }
		fileformat.write(self.file, data, spec)
		self.assertEqual(self.file.getvalue(), b'1234')
	def test_uint(self):
		def spec(f):
			uint = f.uint('uint', 4)
			self.assertEqual(uint, 65535)
		data = { 'uint': 65535 }
		fileformat.write(self.file, data, spec)
		self.assertEqual(self.file.getvalue(), b'\x00\x00\xff\xff')
	def test_int(self):
		def spec(f):
			int_ = f.int('int', 4)
			self.assertEqual(int_, -65536)
		data = { 'int': -65536 }
		fileformat.write(self.file, data, spec)
		self.assertEqual(self.file.getvalue(), b'\xff\xff\x00\x00')
	def test_struct(self):
		def spec(f):
			struct_ = f.struct('struct', '>?3s')
			self.assertEqual(struct_, (False, b'yes'))
		data = { 'struct': (False, b'yes') }
		fileformat.write(self.file, data, spec)
		self.assertEqual(self.file.getvalue(), b'\x00yes')
	def test_section(self):
		self.entered_section = False
		def spec(f):
			def section(f):
				self.entered_section = True
				self.assertIsInstance(f, fileformat.BinarySectionWriter)
				f.bytes('byte', 1)
			section = f.section('section', section)
			self.assertEqual(section, { 'byte': b'Q' })
		data = { 'section': { 'byte': b'Q' } }
		fileformat.write(self.file, data, spec)
		self.assertTrue(self.entered_section)
		self.assertEqual(self.file.getvalue(), b'Q')
	def test_array(self):
		def spec(f):
			f.array('uints')
			for i in range(4):
				f.uint('uints', 1)
		data = { 'uints': [1, 2, 3, 4] }
		fileformat.write(self.file, data, spec)
		self.assertEqual(self.file.getvalue(), b'\x01\x02\x03\x04')
	def test_skipped_oversized(self):
		def spec(f):
			f.skip(2)
		data = { '__skipped': [b'123'] }
		with self.assertRaises(fileformat.DataFormatError):
			fileformat.write(self.file, data, spec)
			self.fail(f"Should have thrown a DataFormatError for trying to write b'123' into a two-byte skipped field, but wrote {self.file.getvalue()} instead.")
	def test_bytes_oversized(self):
		def spec(f):
			f.bytes('first', 1)
		data = { 'first': b'12' }
		with self.assertRaises(fileformat.DataFormatError):
			fileformat.write(self.file, data, spec)
			self.fail(f"Should have thrown a DataFormatError for trying to write b'12' into a single-byte field, but wrote {self.file.getvalue()} instead.")
	def test_uint_overflow(self):
		def spec(f):
			f.uint('uint', 2)
		data = { 'uint': 65540 }
		with self.assertRaises(fileformat.DataFormatError):
			fileformat.write(self.file, data, spec)
			self.fail(f"Should have thrown a DataFormatError for trying to write uint value 65540 into a two-byte field, but wrote {self.file.getvalue()} instead.")
	def test_struct_oversized_string(self):
		def spec(f):
			f.struct('struct', '>4B')
		data = { 'struct': b'hello' }
		with self.assertRaises(fileformat.DataFormatError):
			fileformat.write(self.file, data, spec)
			self.fail(f"Should have thrown a DataFormatError for trying to write b'hello' into a 4-byte struct, but wrote {self.file.getvalue()} instead.")

if __name__ == '__main__':
	unittest.main()