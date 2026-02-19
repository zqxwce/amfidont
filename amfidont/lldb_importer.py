import subprocess
import sys
from types import ModuleType


def get_lldb_python_path() -> str:
    """
    Query LLDB for its bundled Python module path.

    :return: Filesystem path that contains the `lldb` Python module.
    """
    result = subprocess.run(["lldb", "-P"], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def import_lldb() -> ModuleType:
    """
    Import the `lldb` Python module after extending `sys.path` if needed.

    :return: The imported `lldb` module.
    """
    lldb_python_path = get_lldb_python_path()
    if lldb_python_path not in sys.path:
        sys.path.append(lldb_python_path)
    import lldb

    return lldb


lldb = import_lldb()
