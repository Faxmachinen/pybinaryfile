# binaryfile

A library for defining the structure of a binary file and then reading or writing it.

```python
import binaryfile

def png(b):
	b.byteorder = 'big'
	b.skip(16)
	b.uint('width', 4)
	b.uint('height', 4)
	b.uint('depth', 1)

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
import binaryfile
import io

# Define the file structure
def file_spec(f):
	count = f.count('size', 'text', 2)  # A two-byte unsigned integer
	f.bytes('text', size)  # A variable number of bytes

if __name__ == '__main__':
	# Read the file and print the text field
	with open('myfile.dat', 'rb') as file_handle:
		data = binaryfile.read(file_handle, file_spec)
	print(data.text.decode('utf-8'))

	# Modify the text field
	data.text += ' More Text!'.encode('utf-8')

	# Errors will throw exceptions and
	# cause the written file to be truncated,
	# so write to a memory buffer first
	modified_buffer = io.BytesIO()
	binaryfile.write(modified_buffer, data, file_spec)

	# Then write back to file
	with open('myfile.dat', 'wb') as file_handle:
		file_handle.write(modified_buffer.getvalue())
		
```

You can break the definition into reusable sections:

```python
def subsection_spec(f):
	f.struct('position', 'fff')  # Three floats, using a format string from Python's built-in struct module

def section_spec(f):
	f.int('type', 1)  # A one-byte signed integer
	f.section('subsection1', subsection_spec)  # Three floats, as specified in subsection_spec
	f.section('subsection2', subsection_spec)

def file_spec(f):
	f.section(f'section1', section_spec)
	f.section(f'section2', section_spec)
	f.section(f'section3', section_spec)

if __name__ == '__main__':
	with open('myfile2.dat', 'rb') as file_handle:
		data = binaryfile.read(file_handle, file_spec)
	print(data.section2.subsection1.position)
```

And you can declare fields to be arrays and use loops:

```python
def file_spec(f):
	f.array('positions')  # Declare "positions" to be an array
	count = f.count('count', 'positions', 4)
	for i in range(count):
		f.struct('positions', 'fff')  # Each time "positions" is used, it's the next element of the array
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

### Automated tests
#### Setting up the environment
1. Create and activate a [Python virtual environment](https://docs.python.org/3/library/venv.html).
2. From the project root, run `./setup.py develop` to install a binaryfile package linked to the project source into the venv.

#### Running the tests
Make sure that the venv is active, then run the Python files in the `tests` folder.

### License
This project is licensed under MIT License, see [LICENSE](LICENSE) for details.
