# binaryfile

A library for defining the structure of a binary file and then reading or writing it.

```python
import binaryfile

def png(b):
	b.byteorder = 'big'
	b.bytes('misc', 16)
	b.int('width', 4)
	b.int('height', 4)
	b.int('depth', 1)

with open('image.png', 'rb') as fh:
	data = binaryfile.read(fh, png)
print(f"Image is {data.width} pixels wide, {data.height} pixels tall, and {data.depth} bits deep.")
```

## Getting Started

### Requirements

You will need Python 3.6 or later.

### Installing

Windows with Python launcher:

```bat
py -3 -m pip install binaryfile
```

Linux with python3-pip:
```bash
pip3 install binaryfile
```

### How to use

If you want to read or write to a binary file, first you will need to define the file structure. You do this by writing a function that takes a single argument, which is a subclass of binaryfile.fileformat.BinarySectionBase. The file structure is then defined by calling methods on said argument:

```python
import io
import binaryfile

# Define the file structure
def file_spec(binary_section):
	binary_section.bytes('identifier', 4)  # Four bytes
	size = binary_section.uint('size', 2)  # A two-byte unsigned integer
	binary_section.bytes('text', size)  # A variable number of bytes

if __name__ == '__main__':
	# Read the file and print the text field
	with open('myfile.dat', 'rb') as file_handle:
		data = binaryfile.read(file_handle, file_spec)
	print(data.text.decode('utf-8'))

	# Modify the text field
	data.text += ' More Text!'.encode('utf-8')
	data.size = len(data['text'])  # Update the size

	# Errors will throw exceptions and
	# cause the written file to be truncated,
	# so write to a memory buffer first
	modified_buffer = io.BytesIO()
	binaryfile.write(modified_buffer, data, file_spec)

	# Then write back to file
	with open('myfile.dat', 'wb') as file_handle:
		file_handle.write(modified_buffer.getvalue())
		
```

You can break the definition into reusable sections and sub-sections:

```python
def subsection_spec(binary_section):
	binary_section.struct('position', 'fff')  # Three floats, using a format string from Python's built-in struct module.

def section_spec(binary_section):
	binary_section.int('type', 1)  # A one-byte signed integer.
	binary_section.section('subsection1', subsection_spec)  # Three floats, as specified in subsection_spec.
	binary_section.section('subsection2', subsection_spec)  # Section can be reused.

def file_spec(binary_section):
	binary_section.section(f'section1', section_spec)
	binary_section.section(f'section2', section_spec)
	binary_section.section(f'section3', section_spec)

if __name__ == '__main__':
	with open('myfile2.dat', 'rb') as file_handle:
		data = binaryfile.read(file_handle, file_spec)
	print(data.section2.subsection1.position)
```

And you can declare fields to be arrays and use loops:

```python
def file_spec(binary_section):
	count = binary_section.uint('count', 4)
	binary_section.array('positions')  # Declare "positions" to be an array
	for i in range(count):
		binary_section.struct('positions', 'fff')  # Now each time "positions" is used, it's the next element of the array
```

### Configuration
#### Result type
By default, a file is read into a `binaryfile.utils.SimpleDict`, which allows you to access the fields by dot notation (e.g. `foo.bar.baz`). This means you cannot use names that are invalid field names in Python.

To override the result type, pass the desired type to `result_type` in the read call, e.g.:
```python
binaryfile.read(fh, spec, result_type=dict)
```

The desired type must be a dict-like type that implements `__getitem__`, `__setitem__` and `__contains__`.

#### Byte order
The default byte order is big-endian. You can change the endianness either by setting `byteorder` on the `BinarySectionBase` object, or in individual methods that support it.
Valid byteorders are 'big' and 'little', which is also the possible values returned by `sys.byteorder`.

```python
def spec(b):
	b.byteorder = 'little'
	b.int('a', 4)  # Little-endian
	b.int('b', 4, byteorder='big')  # Big-endian
	b.int('c', 4)  # Little-endian again

```

### Running the tests

To run the tests, CD into the "tests" folder and run the scripts there.

### License

This project is licensed under MIT License, see [LICENSE](LICENSE) for details.