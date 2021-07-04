import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("version", "r") as fh:
    version = fh.readline()

setuptools.setup(
    name="binaryfile",
    version=version,
    author="Faxmachinen",
    author_email="binaryfile@faxmachinen.com",
    description="A library for defining the structure of a binary file and then reading or writing it.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=f"https://github.com/Faxmachinen/pybinaryfile/tree/{version}",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
