from pprint import pprint
import threading
from typing import Dict, List, Optional, Set, Tuple, Union

from amfidont.config_store import config_modified_time_state, load_persistent_config
from amfidont.lldb_importer import lldb


AMFID_PATH = "/usr/libexec/amfid"
REGS_BY_ARCH = {
    "arm64": ("x0", "x0"),
    "x86_64": ("rax", "rdi"),
}


def registers_for_target(target: lldb.SBTarget) -> Tuple[str, str]:
    """
    Return register names for the target architecture.

    :param target: LLDB target being inspected.
    :return: A tuple of `(return_register, self_register)`.
    """
    triple = target.GetTriple().lower()
    for arch, registers in REGS_BY_ARCH.items():
        if arch in triple:
            return registers
    raise RuntimeError(f"Unsupported architecture triple: {triple}")


def validate_hook(
    target: lldb.SBTarget,
    thread: lldb.SBThread,
    paths: Set[str],
    cdhashes: Set[str],
    verbose: bool = False,
    allow_all: bool = False,
) -> None:
    """
    Patch validation result when the validator matches configured allow-rules.

    :param target: LLDB target attached to `amfid`.
    :param thread: The stopped thread at the validation breakpoint.
    :param paths: Allowed executable path prefixes.
    :param cdhashes: Allowed cdhash values.
    :param verbose: Enables additional runtime logging.
    :param allow_all: Forces all validations to pass regardless of path/cdhash.
    """
    ret_reg, self_reg = registers_for_target(target)

    frame = thread.frames[0]
    validator = frame.reg[self_reg].value

    thread.StepOutOfFrame(frame)

    ret = thread.frames[0].reg[ret_reg]
    result = dump_validator(target, validator)

    if allow_all:
        if verbose:
            print(f"Allowed due to --allow-all: {result['path']}")
        ret.SetValueFromCString("1")
        return

    if not result["is_valid"]:
        if result["cdhash"] in cdhashes:
            if verbose:
                print(f"Allowed due to cdhash {result['cdhash']}")
            ret.SetValueFromCString("1")
            return

        for path in paths:
            if result["path"].startswith(path):
                if verbose:
                    print(f"Allowed due to path {result['path']}")
                ret.SetValueFromCString("1")
                return

        if verbose:
            print("Invalid path not patched:")
            pprint(result)


def dump_validator(target: lldb.SBTarget, validator: str) -> Dict[str, Union[str, bool]]:
    """
    Read path/cdhash/validity fields from an `AMFIPathValidator` object.

    :param target: LLDB target attached to `amfid`.
    :param validator: Objective-C object pointer for `AMFIPathValidator`.
    :return: A dictionary with keys `path`, `cdhash`, and `is_valid`.
    """
    is_valid = bool(
        target.EvaluateExpression(f"(BOOL)[(id){validator} isValid]").unsigned
    )

    path = target.EvaluateExpression(
        f"(NSURL*)[(id){validator} codePath]"
    ).GetObjectDescription()
    if not path.startswith("file://"):
        raise ValueError(f"Only file:// code paths are supported (got {path})")
    path = path[len("file://"):]

    cdhash = target.EvaluateExpression(
        f"(NSData*)[(id){validator} cdhashAsData]"
    )
    cdhash = cdhash.GetObjectDescription()[1:-1].replace(" ", "")

    return {
        "path": path,
        "cdhash": cdhash,
        "is_valid": is_valid,
    }


def get_stopped_thread(process: lldb.SBProcess, reason: int) -> Optional[lldb.SBThread]:
    """
    Return the first thread stopped for the specified LLDB stop reason.

    :param process: Active LLDB process object.
    :param reason: LLDB stop reason constant (for example, breakpoint).
    :return: The matching thread if found, otherwise `None`.
    """
    for thread in process:
        if thread.GetStopReason() == reason:
            return thread
    return None


def print_verbose_list(header: str, values: Set[str]) -> None:
    """
    Print a sorted verbose list with a stable empty-state output.

    :param header: Human-readable list title.
    :param values: Items to print.
    """
    print(f"  {header}:")
    if values:
        for value in sorted(values):
            print(f"    - {value}")
    else:
        print("    - (none)")


def bypass_loop(
    process: lldb.SBProcess,
    target: lldb.SBTarget,
    paths: Optional[List[str]] = None,
    cdhashes: Optional[List[str]] = None,
    verbose: bool = False,
    allow_all: bool = False,
) -> None:
    """
    Main runtime loop that continues `amfid`, reloads config changes, and patches
    matching validation results at the breakpoint.

    :param process: Attached LLDB process for `amfid`.
    :param target: LLDB target associated with `process`.
    :param paths: Optional allowlisted executable path prefixes.
    :param cdhashes: Optional allowlisted cdhash values.
    :param verbose: Enables verbose runtime logging.
    :param allow_all: Forces all validations to pass regardless of config.
    """
    cli_paths = set(paths or [])
    cli_cdhashes = set(cdhashes or [])
    config = load_persistent_config()
    modified_time_state = config_modified_time_state()
    allowed_paths = set(config["paths"]) | cli_paths
    allowed_cdhashes = set(config["cdhashes"]) | cli_cdhashes

    if verbose:
        print("Running configuration:")
        print(f"  Allow all: {allow_all}")
        print_verbose_list("Paths", allowed_paths)
        print_verbose_list("CDHashes", allowed_cdhashes)

    while True:
        process.Continue()
        print('got to after continue')
        if process.state not in [
            lldb.eStateRunning,
            lldb.eStateStopped,
            lldb.eStateSuspended,
        ]:
            raise RuntimeError(
                f"Unexpected process state {process.state}"
            )

        current_modified_time_state = config_modified_time_state()
        if current_modified_time_state != modified_time_state:
            config = load_persistent_config()
            allowed_paths = set(config["paths"]) | cli_paths
            allowed_cdhashes = set(config["cdhashes"]) | cli_cdhashes
            modified_time_state = config_modified_time_state()
            if verbose:
                print("Reloaded configuration from ~/.amfidont")

        thread = get_stopped_thread(process, lldb.eStopReasonBreakpoint)
        if thread:
            validate_hook(
                target,
                thread,
                allowed_paths,
                allowed_cdhashes,
                verbose=verbose,
                allow_all=allow_all,
            )


def run_bypass(
    paths: Optional[List[str]] = None,
    cdhashes: Optional[List[str]] = None,
    verbose: bool = False,
    allow_all: bool = False,
) -> None:
    """
    Run the foreground bypass loop against `amfid`.

    :param paths: Optional path prefixes supplied by CLI.
    :param cdhashes: Optional cdhashes supplied by CLI.
    :param verbose: Enables informative runtime logging.
    :param allow_all: Forces all validations to pass regardless of path/cdhash.
    """
    debugger = lldb.SBDebugger.Create()
    debugger.SetAsync(False)
    target = debugger.CreateTarget("")
    process = target.AttachToProcessWithName(
        debugger.GetListener(), AMFID_PATH, False, lldb.SBError()
    )

    if not process:
        print("Failed to attach to process, should probably run as root")
        return

    if verbose:
        print(f"Attached to {AMFID_PATH}")

    target.BreakpointCreateByName("-[AMFIPathValidator_macos validateWithError:]")
    if verbose:
        print("Installed validateWithError breakpoint")

    try:
        thread = threading.Thread(
            target=bypass_loop,
            args=(process, target, paths, cdhashes, verbose, allow_all),
        )
        thread.daemon = True
        thread.start()
        thread.join()
    except KeyboardInterrupt:
        if verbose:
            print("Stopping amfidont (detaching from amfid)...")
