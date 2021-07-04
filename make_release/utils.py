from pathlib import Path
import subprocess

REPO_ROOT = '..'

def getRepoRoot():
	script_dir = Path(__file__) / '..'
	return (script_dir / REPO_ROOT).resolve()

def runOrDie(args, **subprocess_args):
	defaults = {'text': True}
	merged_args = defaults | subprocess_args
	try:
		result = subprocess.run(args, **merged_args)
	except FileNotFoundError as ex:
		raise Exception(f"'{args[0]}' is not on path ({str(ex)})")
	if result.returncode:
		message = f"Error running subprocess with the following arguments:\n{args}"
		if merged_args.get('capture_output'):
			message += f"The output was:\n{result.stdout}\n{result.stderr}"
		raise Exception(message)
	return result.stdout

