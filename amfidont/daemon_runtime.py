import subprocess
import sys
from typing import List, Optional


def start_daemon(
    paths: Optional[List[str]] = None,
    cdhashes: Optional[List[str]] = None,
    verbose: bool = False,
    allow_all: bool = False,
) -> None:
    """
    Start amfidont in a detached background process.

    :param paths: Optional path prefixes to pass to the child process.
    :param cdhashes: Optional cdhashes to pass to the child process.
    :param verbose: Enables verbose startup logging and forwards `--verbose` to child.
    :param allow_all: Forwards unconditional validation bypass mode to child.
    """
    child_args = [sys.executable, "-m", "amfidont"]
    if verbose:
        child_args.append("--verbose")
    if allow_all:
        child_args.append("--allow-all")
    for path in paths or []:
        child_args.extend(["--path", path])
    for cdhash in cdhashes or []:
        child_args.extend(["--cdhash", cdhash])

    process = subprocess.Popen(
        child_args,
        start_new_session=True,
    )

    print(f"Starting daemon with command: {' '.join(child_args)}")
    print(f"amfidont daemon started (pid: {process.pid})")
