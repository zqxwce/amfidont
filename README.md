# amfidont

## Description

A macOS utility that attaches to `amfid` with LLDB and bypasses app signature validation for explicitly allowed binaries.
Allowed targets are matched by executable path prefix and/or cdhash.

## Requirements

- SIP configuration that allows debugging system processes by either:
  - fully disable SIP
  - disable only debugging restrictions (`csrutil enable --without debug`)

## Installation

```shell
xcrun python3 -m pip install -U amfidont
```

## Usage

```none
Usage: amfidont [OPTIONS] COMMAND [ARGS]...

A simple utility for bypassing amfid signature verification

Options:
  --path, -p TEXT      path of executable to allow (can be specified multiple times, merged with ~/.amfidont/paths)
  --cdhash, -c TEXT    cdhash of executable to allow (can be specified multiple times, merged with ~/.amfidont/cdhashes)
  --verbose, -v        enable verbose output
  --allow-all          allow all validations to pass
  --install-completion Install completion for the current shell.
  --show-completion    Show completion for the current shell, to copy it or customize the installation.
  --help               Show this message and exit.

Commands:
  daemon        Start amfidont in daemon mode.
  add-path      Add an allowed path prefix to persistent configuration.
  remove-path   Remove an allowed path prefix from persistent configuration.
  add-cdhash    Add an allowed cdhash to persistent configuration.
  remove-cdhash Remove an allowed cdhash from persistent configuration.
```

## Example

1. Add a persistent allowed path:

    ```shell
    sudo amfidont add-path /Users/user/dev/myapp/build/Release/MyApp.app/
    ```

2. Start bypass mode (foreground):

    ```shell
    sudo amfidont --verbose
    ```

3. (Optional) Start as daemon instead:

    ```shell
    sudo amfidont daemon --verbose
    ```

4. Stop foreground mode with `Ctrl-C` (this detaches `amfidont` and leaves `amfid` running).

## Inner implementation details

- `amfidont` attaches to `/usr/libexec/amfid` using LLDB.
- It sets a breakpoint on:

```none
-[AMFIPathValidator_macos validateWithError:]
```

- On each breakpoint hit, it inspects validator fields:
  - code path (`codePath`)
  - cdhash (`cdhashAsData`)
  - validation state (`isValid`)
- If the validator is invalid but the path/cdhash matches configured allow-rules,
  the return register is patched to success and execution continues.
- Persistent configuration is stored in:
  - `~/.amfidont/paths`
  - `~/.amfidont/cdhashes`
