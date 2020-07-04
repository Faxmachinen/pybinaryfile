from abc import ABC, abstractmethod
from os import SEEK_CUR
import struct

from .utils import SimpleDict

def read(handle, definition, result_type=SimpleDict):
	"""
	Read from a binary file handle and iterpret it using the file definition.
	
	Arguments:
	handle -- The file-like object to read from. Must be binary.
	definition -- The function defining the file structure. Must take one argument of type BinarySectionBase.
	result_type -- Override the type of the return value with this dict-like type. Must implement __getitem__, __setitem__ and __contains__.

	Returns a dict of names from the definition mapped to values from the file handle. Subsections become sub-dicts.
	"""
	reader = BinarySectionReader(handle, result_type)
	definition(reader)
	return reader.result

def write(handle, data, definition):
	"""
	Write data to a binary file handle, interpreted using the file definition.
	
	Arguments:
	handle -- The file-like object to write to. Must be binary.
	data -- A dict of data to write to the handle. Must map all named fields in the definition to values. The output from read() should work.
	definition -- The function defining the file structure. Must take one argument of type BinarySectionBase.
	"""
	writer = BinarySectionWriter(handle, data)
	definition(writer)

class DefinitionError(Exception):
	"""Throw when the definition contains errors."""
	pass

class DataFormatError(Exception):
	"""Thrown when the data does not match the file format."""
	pass

class BinarySectionBase(ABC):
	"""
	The base class for classes that interpret file specifications. Passed as the only argument to file specification functions.

	Arguments:
	handle -- The binary file handle to operate on.
	byteorder -- The default byte-order. May be 'big' or 'little'. Defaults to 'big'.
	name -- The name of this section. Set to the field name by parent sections when creating sub-section fields. Defaults to '(root)'.
	parent -- The parent section itself. Set by parent sections.
	"""
	def __init__(self, handle):
		self.handle = handle
		self.byteorder = 'big'
		self.name = '(root)'
		self.parent = None
	@abstractmethod
	def skip(self, size):
		"""
		Skip size number of bytes that you don't really care about.
		After reading, the skipped fields are sill available in the result as an array named '__skipped', and will be written back when writing.
		"""
	@abstractmethod
	def section(self, name, definition):
		"""
		Declare a section using the given definition.
		
		name -- The name of the field containing the section.
		definition -- A function that takes a BinarySectionBase and defines the section.
		
		Returns the section as a dict-like object.
		"""
		...
	@abstractmethod
	def array(self, *names):
		"""
		Set the named fields to [] and mark them as arrays.
		Repeated use of a marked field will append to its array instead of raising an error.
		"""
		...
	@abstractmethod
	def count(self, name, target_name, size, byteorder=None):
		"""
		Like uint, but is automatically updated with the len() of target_name.

		name  -- The name of the count field.
		target_name -- The name of a bytes or array field whose count this represents.
		size -- The number of bytes the count field occupies.
		byteorder -- The byte order of the count field. May be 'big' or 'little'. If not specified, the byteorder property is used instead.
		"""
		...
	@abstractmethod
	def bytes(self, name, size):
		"""
		Declare size number of bytes.
		name -- The name of the field containing the bytes.
		size -- The number of bytes the field occupies.
		
		Returns the bytes.
		"""
		...
	@abstractmethod
	def int(self, name, size, byteorder=None):
		"""
		Declare a signed integer taking up size number of bytes.
		
		name -- The name of the field containing the integer.
		size -- The number of bytes the integer occupies.
		byteorder -- The byte-order of this integer. May be 'big' or 'little'. If not specified, the byteorder property is used instead.
		
		Returns the integer.
		"""
		...
	@abstractmethod
	def uint(self, name, size, byteorder=None):
		"""
		Declare an unsigned integer taking up size number of bytes.
		
		name -- The name of the field containing the integer.
		size -- The number of bytes the integer occupies.
		byteorder -- The byte-order of this integer. May be 'big' or 'little'. If not specified, the byteorder property is used instead.
		
		Returns the integer.
		"""
		...
	@abstractmethod
	def struct(self, name, formatstr):
		"""
		Declare a struct defined by formatstr.
		name -- The name of the field containing the integer.
		formatstr -- A string defining the struct format, as specified in Python's built-in struct module.
		
		Returns the struct as a tuple.
		"""
		...
	def qualified_name(self):
		"""Get the name of parent sections and this section as a list."""
		if self.parent:
			return self.parent.qualified_name() + [self.name]
		return [self.name]
	def get_qualified_field_name(self, name):
		"""Get the qualified name of the named field, including the name of this section and its parents, as a dotted string. Useful for error messages."""
		return '.'.join(self.qualified_name() + [name])

class BinarySectionReader(BinarySectionBase):
	def __init__(self, handle, result_type=dict):
		super().__init__(handle)
		self.result = result_type()
		self.arrays = set()
	def skip(self, size):
		if not '__skipped' in self.result:
			self.result['__skipped'] = []
		skipped = self.result['__skipped']
		name = f'__skipped[{len(skipped)}]'
		skipped.append(self._read_bytes(name, size))
	def section(self, name, definition):
		section = self._section(name, definition)
		self._add_result(name, section.result)
		return section.result
	def array(self, name):
		self.result[name] = []
		self.arrays.add(name)
	def count(self, name, array_name, size, byteorder=None):
		return self.uint(name, size, byteorder)
	def bytes(self, name, size):
		result = self._read_bytes(name, size)
		self._add_result(name, result)
		return result
	def int(self, name, size, byteorder=None):
		return self._int(name, size, byteorder, signed=True)
	def uint(self, name, size, byteorder=None):
		return self._int(name, size, byteorder, signed=False)
	def struct(self, name, formatstr):
		size = struct.calcsize(formatstr)
		bytes_ = self._read_bytes(name, size)
		result = struct.unpack(formatstr, bytes_)
		self._add_result(name, result)
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
			raise EOFError(f'While reading {self.get_qualified_field_name(name)}')
		return bytes_
	def _int(self, name, size, byteorder, signed):
		if byteorder is None:
			byteorder = self.byteorder
		bytes_ = self._read_bytes(name, size)
		result = int.from_bytes(bytes_, byteorder=byteorder, signed=signed)
		self._add_result(name, result)
		return result
	def _add_result(self, name, result):
		if name in self.result:
			if name in self.arrays:
				self.result[name].append(result)
			else:
				raise DefinitionError(f'Used "{name}" multiple times in the same section without declaring it an array.')
		else:
			self.result[name] = result

class BinarySectionWriter(BinarySectionBase):
	def __init__(self, handle, data):
		super().__init__(handle)
		self.data = data
		self.indices = {}
	def skip(self, size):
		if not '__skipped' in self.data:
			self.handle.write(b'\x00' * size)
			return
		if not '__skipped' in self.indices:
			self.array('__skipped')
		bytes_ = self._get_data('__skipped')
		self._write_bytes('__skipped', size, bytes_)
		return bytes_
	def section(self, name, definition):
		data = self._get_data(name)
		self._section(name, data, definition)
		return data
	def array(self, name):
		self.indices[name] = 0
	def count(self, name, array_name, size, byteorder=None):
		self.data[name] = len(self.data[array_name])
		return self.uint(self, name, size, byteorder)
	def bytes(self, name, size):
		bytes_ = self._get_data(name)
		self._write_bytes(name, size, bytes_)
		return bytes_
	def int(self, name, size, byteorder=None):
		return self._int(name, size, byteorder, signed=True)
	def uint(self, name, size, byteorder=None):
		return self._int(name, size, byteorder, signed=False)
	def struct(self, name, formatstr):
		data = self._get_data(name)
		try:
			bytes_ = struct.pack(formatstr, *data)
		except struct.error as e:
			raise DataFormatError(f'While writing struct {self.get_qualified_field_name(name)}: {str(e)}')
		self.handle.write(bytes_)
		return self.data[name]
	def _section(self, name, data, definition):
		section = type(self)(self.handle, data)
		section.parent = self
		section.name = name
		definition(section)
		return section.data
	def _int(self, name, size, byteorder, signed):
		value = int(self._get_data(name))
		if size is None or size == -1:
			size = (value.bit_length() + 7) // 8
		if byteorder is None:
			byteorder = self.byteorder
		try:
			bytes_ = value.to_bytes(size, byteorder=byteorder, signed=signed)
		except OverflowError as e:
			raise DataFormatError(f'While writing (u)int {self.get_qualified_field_name(name)}: {str(e)}')
		self.handle.write(bytes_)
		return value
	def _get_data(self, name):
		if name in self.indices:
			if self.indices[name] >= len(self.data[name]):
				raise DataFormatError(f'Data array "{name}" has {len(self.data[name])} items, but more are required.')
			result = self.data[name][self.indices[name]]
			self.indices[name] += 1
		else:
			result = self.data[name]
		return result
	def _write_bytes(self, name, size, bytes_):
		if not (size is None or size == -1):
			if len(bytes_) != size:
				raise DataFormatError(f'While writing bytes {self.get_qualified_field_name(name)}: Expected {repr(bytes_)} to be {size} bytes long.')
		self.handle.write(bytes_)
