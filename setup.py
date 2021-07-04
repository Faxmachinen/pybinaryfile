import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="binaryfile",
    version="1.2.0",
    author="Faxmachinen",
    author_email="binaryfile@faxmachinen.com",
    description="A library for defining the structure of a binary file and then reading or writing it.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Faxmachinen/pybinaryfile/tree/1.2.0",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
