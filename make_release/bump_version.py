import sys
from pathlib import Path
import subprocess
import re
from utils import getRepoRoot, runOrDie

REPO_ROOT = '..'
VERSION_FILE = 'version'
COMMIT_MESSAGE = 'Bumped version'
VERSION_RE = re.compile(r'(\d+)\.(\d+)\.(\d+)')

def getTags(repo):
	git_tag = runOrDie(['git', '-C', repo, 'tag', '-l'], capture_output=True)
	return git_tag.splitlines()

def commit(repo, file):
	runOrDie(['git', '-C', repo, 'reset', '--', '.'])
	runOrDie(['git', '-C', repo, 'add', str(file)])
	runOrDie(['git', '-C', repo, 'commit', '-m', COMMIT_MESSAGE])

def tagHead(repo, tag):
	runOrDie(['git', '-C', repo, 'tag', tag])

def versions(tags):
	for tag in tags:
		match = VERSION_RE.fullmatch(tag)
		if match:
			yield match.groups()

def askForNewVersion():
	while True:
		new_ver = input("New version: ")
		if VERSION_RE.fullmatch(new_ver):
			return new_ver
		else:
			"Not a version!"

def writeVersion(ver):
	with open(repo_root / VERSION_FILE, 'w') as fh:
		fh.write(ver)

if __name__ == '__main__':
	repo_root = getRepoRoot()
	tags = getTags(repo_root)
	vers = versions(tags)
	if vers:
		latest = '.'.join(max(vers))
		print(f'Previous version: {latest}')
	new_version = askForNewVersion()

	writeVersion(new_version)
	commit(repo_root, VERSION_FILE)
	tagHead(repo_root, new_version)
	print("Version bump completed.")
