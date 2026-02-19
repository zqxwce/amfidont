from pathlib import Path
from typing import List, Optional

import typer


CONFIG_DIR = Path("~/.amfidont").expanduser()
PATHS_FILE = CONFIG_DIR / "paths"
CDHASHES_FILE = CONFIG_DIR / "cdhashes"


def read_list_file(path: Path) -> List[str]:
    """
    Read newline-separated values from a file.

    :param path: Path to the list file.
    :return: A list of non-empty trimmed lines.
    """
    if not path.exists():
        path.write_text("")
        return []
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def load_persistent_config(config_dir: Path = CONFIG_DIR) -> dict[str, List[str]]:
    """
    Load persisted path and cdhash allow-lists from disk.

    :param config_dir: Base configuration directory.
    :return: A dictionary containing `paths` and `cdhashes` lists.
    """
    if config_dir.exists() and not config_dir.is_dir():
        raise typer.BadParameter(f"Persistent config path {config_dir} is not a directory")

    config_dir.mkdir(parents=True, exist_ok=True)
    return {
        "paths": read_list_file(PATHS_FILE),
        "cdhashes": read_list_file(CDHASHES_FILE),
    }


def file_mtime_ns(path: Path) -> Optional[int]:
    """
    Return file modification time in nanoseconds.

    :param path: Path to inspect.
    :return: File mtime in nanoseconds, or `None` if the file does not exist.
    """
    if not path.exists():
        return None
    return path.stat().st_mtime_ns


def config_modified_time_state() -> tuple[Optional[int], Optional[int]]:
    """
    Return a snapshot of config file modification times.

    :return: A tuple of `(paths_mtime_ns, cdhashes_mtime_ns)`.
    """
    return (file_mtime_ns(PATHS_FILE), file_mtime_ns(CDHASHES_FILE))


def write_list_file(path: Path, values: List[str]) -> None:
    """
    Write newline-separated values to a list file.

    :param path: Output file path.
    :param values: Values to write.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if values:
        path.write_text("\n".join(values) + "\n")
    else:
        path.write_text("")


def add_config_entry(path: Path, value: str) -> bool:
    """
    Add a value to a config list file if not already present.

    :param path: Path to the config list file.
    :param value: Entry value to add.
    :return: `True` if added, `False` if already present.
    """
    values = read_list_file(path)
    if value in values:
        return False
    values.append(value)
    write_list_file(path, values)
    return True


def remove_config_entry(path: Path, value: str) -> bool:
    """
    Remove a value from a config list file.

    :param path: Path to the config list file.
    :param value: Entry value to remove.
    :return: `True` if removed, `False` if not found.
    """
    values = read_list_file(path)
    if value not in values:
        return False
    write_list_file(path, [entry for entry in values if entry != value])
    return True
