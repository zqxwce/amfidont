from typing import Annotated, List, Optional

import typer
from typer_injector import InjectingTyper

from amfidont.bypass_runtime import run_bypass
from amfidont.config_store import (
    CDHASHES_FILE,
    PATHS_FILE,
    add_config_entry,
    load_persistent_config,
    remove_config_entry,
)
from amfidont.daemon_runtime import start_daemon

cli = InjectingTyper(help="A simple utility for bypassing amfid signature verification")


@cli.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    paths: Annotated[
        Optional[List[str]],
        typer.Option(
            '-p',
            '--path',
            help='path of executable to allow (can be specified multiple times, merged with ~/.amfidont/paths)'
        )] = None,
    cdhashes: Annotated[
        Optional[List[str]],
        typer.Option(
            '-c',
            '--cdhash',
            help='cdhash of executable to allow (can be specified multiple times, merged with ~/.amfidont/cdhashes)'
        )] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            '-v',
            '--verbose',
            help='enable verbose output'
        )] = False,
    allow_all: Annotated[
        bool,
        typer.Option(
            '--allow-all',
            help='allow all validations to pass'
        )] = False,
) -> None:
    """
    Run bypass mode by default when no subcommand is selected.

    :param ctx: Typer context used to detect invoked subcommand.
    :param paths: Optional executable path prefixes to allow.
    :param cdhashes: Optional cdhashes to allow.
    :param verbose: Enables verbose runtime output.
    :param allow_all: Enables unconditional validation bypass for all binaries.
    """
    if ctx.invoked_subcommand is None:
        run_bypass(paths=paths, cdhashes=cdhashes, verbose=verbose, allow_all=allow_all)


@cli.command()
def daemon(
    paths: Annotated[
        Optional[List[str]],
        typer.Option(
            '-p',
            '--path',
            help='path of executable to allow (can be specified multiple times, merged with ~/.amfidont/paths)'
        )] = None,
    cdhashes: Annotated[
        Optional[List[str]],
        typer.Option(
            '-c',
            '--cdhash',
            help='cdhash of executable to allow (can be specified multiple times, merged with ~/.amfidont/cdhashes)'
        )] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            '-v',
            '--verbose',
            help='enable verbose output'
        )] = False,
    allow_all: Annotated[
        bool,
        typer.Option(
            '--allow-all',
            help='allow all validations to pass'
        )] = False,
) -> None:
    """
    Start amfidont in daemon mode.

    :param paths: Optional executable path prefixes to allow.
    :param cdhashes: Optional cdhashes to allow.
    :param verbose: Enables verbose runtime output.
    :param allow_all: Enables unconditional validation bypass for all binaries.
    """
    start_daemon(paths=paths, cdhashes=cdhashes, verbose=verbose, allow_all=allow_all)


@cli.command("add-path")
def add_path(
    path: Annotated[str, typer.Argument(help="path to add to ~/.amfidont/paths")]
) -> None:
    """
    Add an allowed path prefix to persistent configuration.

    :param path: Path prefix to add.
    """
    load_persistent_config()
    if add_config_entry(PATHS_FILE, path):
        print(f"added path: {path}")
    else:
        print(f"path already present: {path}")


@cli.command("remove-path")
def remove_path(
    path: Annotated[str, typer.Argument(help="path to remove from ~/.amfidont/paths")]
) -> None:
    """
    Remove an allowed path prefix from persistent configuration.

    :param path: Path prefix to remove.
    """
    load_persistent_config()
    if remove_config_entry(PATHS_FILE, path):
        print(f"removed path: {path}")
    else:
        print(f"path not found: {path}")


@cli.command("add-cdhash")
def add_cdhash(
    cdhash: Annotated[str, typer.Argument(help="cdhash to add to ~/.amfidont/cdhashes")]
) -> None:
    """
    Add an allowed cdhash to persistent configuration.

    :param cdhash: Cdhash value to add.
    """
    load_persistent_config()
    if add_config_entry(CDHASHES_FILE, cdhash):
        print(f"added cdhash: {cdhash}")
    else:
        print(f"cdhash already present: {cdhash}")


@cli.command("remove-cdhash")
def remove_cdhash(
    cdhash: Annotated[str, typer.Argument(help="cdhash to remove from ~/.amfidont/cdhashes")]
) -> None:
    """
    Remove an allowed cdhash from persistent configuration.

    :param cdhash: Cdhash value to remove.
    """
    load_persistent_config()
    if remove_config_entry(CDHASHES_FILE, cdhash):
        print(f"removed cdhash: {cdhash}")
    else:
        print(f"cdhash not found: {cdhash}")


if __name__ == '__main__':
    cli()
