# binaryfile

A library for defining the structure of a binary file and then reading or writing it. Should work with Python 3.6 or later.

## Getting Started

### Requirements

You will need Python 3.6 or later.

### Installing

This Python package does not yet have an installer, so just copy the "binaryfile" folder into your project.

### How to use

If you want to read or write to a binary file, first you will need to define the file structure. You do this by writing a function that takes a single argument, which is a subclass of binaryfile.fileformat.BinarySectionBase. The file structure is then defined by calling methods on said argument:

```python
import io
import binaryfile

# Define the file structure
def file_spec(binary_section):
	binary_section.bytes('identifier', 4)  # Four bytes identifying the file.
	size = binary_section.uint('size', 2)  # A two-byte unsigned integer denoting the size of the file. Note that we store the result in a variable.
	binary_section.bytes('text', size)  # Read a variable number of bytes based on the size we stored.

if __name__ == '__main__':
	# Read the file and print the text field
	with open('myfile.dat', 'rb') as file_handle:
		data = binaryfile.read(file_handle, file_spec)
	print(data['text'].decode('utf-8'))

	# Modify the text field
	data['text'] += ' More Text!'.encode('utf-8')
	data['size'] = len(data['text'])  # Update the size

	# Write modified data to buffer first, in case there are any errors
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
	# You can use a custom dictionary-like result class for convenience
	# SimpleDict allows us to access entries by attribute notation
	with open('myfile2.dat', 'rb') as file_handle:
		data = binaryfile.read(file_handle, file_spec, result_type=binaryfile.utils.SimpleDict)
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

### Running the tests

To run the tests, CD into the "tests" folder and run the scripts there.

### License

This project is licensed under MIT License, see [LICENSE](LICENSE) for details.