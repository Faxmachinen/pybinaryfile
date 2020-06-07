from abc import ABC, abstractmethod
from os import SEEK_CUR
import struct

def read(handle, definition, result_type=dict):
	reader = BinarySectionReader(handle, result_type)
	definition(reader)
	return reader.result

def write(handle, data, definition):
	writer = BinarySectionWriter(handle, data)
	definition(writer)

class DataFormatError(Exception):
	"""Thrown when the data does not match the file format."""
	pass

class BinarySectionBase(ABC):
	def __init__(self, handle):
		self.handle = handle
		self.byteorder = 'big'
		self.name = '(root)'
		self.parent = None
	@abstractmethod
	def section(self, name, definition):
		...
	@abstractmethod
	def repeat(self, name, definition):
		...
	@abstractmethod
	def bytes(self, name, size):
		...
	@abstractmethod
	def int(self, name, size, byteorder=None):
		...
	@abstractmethod
	def uint(self, name, size, byteorder=None):
		...
	@abstractmethod
	def struct(self, name, formatstr):
		...
	def qualified_name(self):
		if self.parent:
			return self.parent.qualified_name + [self.name]
		return [self.name]
	def _get_qualified_field_name(self, name):
		return '.'.join(self.qualified_name() + [name])

class BinarySectionReader(BinarySectionBase):
	def __init__(self, handle, result_type=dict):
		super().__init__(handle)
		self.result = result_type()
	def eof(self):
		if len(self.handle.read(1)) == 0:
			return True
		self.handle.seek(-1, SEEK_CUR)
		return False
	def section(self, name, definition):
		section = self._section(name, definition)
		self.result[name] = section.result
		return section.result
	def repeat(self, name, definition):
		i = 0
		results = self.result[name] = []
		while not self.eof():
			section = self._section(f'{name}[{i}]', definition)
			results.append(section.result)
			yield section.result
			i += 1
	def bytes(self, name, size):
		result = self._read_bytes(name, size)
		self.result[name] = result
		return result
	def int(self, name, size, byteorder=None):
		return self._int(name, size, byteorder, signed=True)
	def uint(self, name, size, byteorder=None):
		return self._int(name, size, byteorder, signed=False)
	def struct(self, name, formatstr):
		size = struct.calcsize(formatstr)
		bytes_ = self._read_bytes(name, size)
		result = struct.unpack(formatstr, bytes_)
		self.result[name] = result
		return result
	def _section(self, name, definition):
		section = type(self)(self.handle, type(self.result))
		section.parent = self
		section.name = name
		definition(section)
		return section
	def _read_bytes(self, name, size):
		bytes_ = self.handle.read(size)
		if size is None or size == -1:
			return bytes_
		if len(bytes_) < size:
			raise EOFError(f'While reading {self._get_qualified_field_name(name)}')
		return bytes_
	def _int(self, name, size, byteorder, signed):
		if byteorder is None:
			byteorder = self.byteorder
		bytes_ = self._read_bytes(name, size)
		result = int.from_bytes(bytes_, byteorder=byteorder, signed=signed)
		self.result[name] = result
		return result

class BinarySectionWriter(BinarySectionBase):
	def __init__(self, handle, data):
		super().__init__(handle)
		self.data = data
	def section(self, name, definition):
		self._section(name, self.data[name], definition)
		return self.data[name]
	def repeat(self, name, definition):
		i = 0
		for section in self.data[name]:
			self._section(f'{name}[{i}]', section, definition)
			yield section
			i += 1
		return self.data[name]
	def bytes(self, name, size):
		bytes_ = self.data[name]
		if not (size is None or size == -1):
			if len(bytes_) != size:
				raise DataFormatError(f'While writing bytes {self._get_qualified_field_name(name)}: ')
		self.handle.write(bytes_)
		return bytes_
	def int(self, name, size, byteorder=None):
		return self._int(name, size, byteorder, signed=True)
	def uint(self, name, size, byteorder=None):
		return self._int(name, size, byteorder, signed=False)
	def struct(self, name, formatstr):
		try:
			bytes_ = struct.pack(formatstr, *self.data[name])
		except struct.error as e:
			raise DataFormatError(f'While writing struct {self._get_qualified_field_name(name)}: {str(e)}')
		self.handle.write(bytes_)
		return self.data[name]
	def _section(self, name, data, definition):
		section = type(self)(self.handle, data)
		section.parent = self
		section.name = name
		definition(section)
		return section.data
	def _int(self, name, size, byteorder, signed):
		value = int(self.data[name])
		if size is None or size == -1:
			size = (value.bit_length() + 7) // 8
		if byteorder is None:
			byteorder = self.byteorder
		try:
			bytes_ = value.to_bytes(size, byteorder=byteorder, signed=signed)
		except OverflowError as e:
			raise DataFormatError(f'While writing (u)int {self._get_qualified_field_name(name)}: {str(e)}')
		self.handle.write(bytes_)
		return value
