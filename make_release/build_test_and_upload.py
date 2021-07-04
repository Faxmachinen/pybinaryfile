from pathlib import Path
from utils import getRepoRoot, runOrDie
import sys
from shutil import rmtree

def build(repo_root):
	runOrDie([sys.executable, 'setup.py', 'sdist', 'bdist_wheel'], cwd=repo_root)

def test(repo_root):
	testenv = (repo_root / 'testenv').resolve()
	rmtree(testenv, ignore_errors=True)
	runOrDie([sys.executable, '-m', 'venv', testenv], cwd=repo_root)
	testenv_py = testenv / 'Scripts/python'
	runOrDie([testenv_py, 'setup.py', 'develop'], cwd=repo_root)
	for testfile in (repo_root / 'tests').glob('*.py'):
		runOrDie([testenv_py, testfile])

def upload(repo_root):
	upload = input("Upload to [P]yPi, [T]est PyPi or [N]either? ")
	if upload.upper() == 'P':
		runOrDie([sys.executable, '-m', 'twine', 'upload', 'dist/*', '--skip-existing'], cwd=repo_root)
	elif upload.upper() == 'T':
		runOrDie([sys.executable, '-m', 'twine', 'upload', '-r', 'testpypi', 'dist/*', '--skip-existing'], cwd=repo_root)
	else:
		print("Not uploading.")

if __name__ == '__main__':
	repo_root = getRepoRoot()
	build(repo_root)
	test(repo_root)
	upload(repo_root)
	print("Done.")
