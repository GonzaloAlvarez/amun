# Amun - The Hidden One

**amun** is a lightweight provisioning and configuration management framework that combines the best of **Ansible** and **Python**.  
It enables teams to declaratively define infrastructure and environments while retaining the power of scripting when needed.

---

## Table of Contents

- [Usage](#usage)
- [Features](#features)
- [Development](#development)
- [License](#license)

---

## Usage

You can install **amun** into your environment with a single command.
This will automatically fetch and execute the amun script to prepare your workspace:

```bash
bash <(curl -fsSL https://go.gn.al/amun)
```
or, if you are a bare debian install without curl, you can use:

```bash    
bash <(wget -qO- https://go.gn.al/amun)
```

> `https://go.gn.al/amun` is a Cloudflare redirect to
> `https://raw.githubusercontent.com/gonzaloalvarez/amun/main/amun` (the raw URL
> still works directly if you prefer).

### Termux (Android)

Termux is its own platform with its own bootstrap (`amun-termux`) that runs
the same `main.yml` and roles — no root, no sudo, packages via `pkg`, sshd on
port 8022 with key-only auth. On a new device:

```bash
bash <(curl -fsSL https://go.gn.al/amun-termux)
```

Plugins follow the usual convention (`... | bash -s -- <plugin>`), and after
the first run the installed `~/bin/amun` command re-runs the Termux bootstrap.
Skipped on Termux: `permissions` (no sudoers), `pki` (no OS trust store yet),
`config`, and `ufw`. Detection is by the `TERMUX_VERSION` environment variable
only — the standard `amun` script refuses to run when it is set and points
here instead. Note: an `amun-termux` file exists at this repo's root, while
`amun <plugin>` resolves plugin repos named `amun-<plugin>` — `amun termux` on
a non-Android box is therefore a name collision that 404s; use the URL above.

On Android 12+ the phantom process killer will eventually kill a background
sshd: acquire the Termux wake lock (notification → "Acquire wakelock"), and/or
relax the limit over adb:

```bash
adb shell device_config put activity_manager max_phantom_processes 2147483647
```

Testing (requires Docker; uses `termux/termux-docker:aarch64`):

```bash
./test termux-bootstrap   # fast: bootstrap + packages, no dotfiles/sshd
./test termux             # complete provisioning, idempotence, sshd, dotfiles
```

Knobs: `TERMUX_DOCKER_IMAGE` (alternate image/tag), `TERMUX_DOCKER_UNCONFINED=0`
(re-enable the default seccomp profile), `AMUN_KEEP_PROVISIONING=1` (keep
`~/.provisioning` for debugging).

## Features

- ⚙️ **Hybrid provisioning:** combines **Ansible** and **Python** for flexible, scriptable infrastructure management  
- 🧩 **Modular architecture:** role-based structure for clean separation of responsibilities  
- 🚀 **One-line install:** quick setup with a single `curl | bash` command
- 🔁 **Idempotent operations:** safe to re-run without corrupting your setup  
- 🧰 **Extensible tooling:** easily integrate custom Python or shell utilities  
- 🧮 **Reproducible environments:** ensures consistent system states across machines  
- 🧑‍💻 **Developer-friendly testing:** built-in testing and debugging modes for validation and exploration

## Core roles

| Role | Purpose |
|------|---------|
| `permissions` | Add the current user to `/etc/sudoers` with `NOPASSWD`. |
| `homebrew` | Install Homebrew on macOS. |
| `utils` | Install the curated package set (apt / brew / pacman) and ensure `nvim` meets a minimum version. |
| `pki` | Fetch the homelab step-ca root CA from `http://pki.lan/cert/ca.crt` and install it into the OS trust store (Debian/Ubuntu/Arch trust dirs, macOS System keychain). Silently skips when the PKI host is unreachable, so the playbook stays green off-LAN. |
| `dotfiles` | Clone and install `dotfiles` and `gear`. |
| `config` | Apply OS-level UI/locale/keyboard configuration. |
| `ufw` | Install and enable UFW with a default-deny policy on Linux. |
| `remoteaccess` | Install OpenSSH, harden sshd, and trust the master SSH public key. |

## Development

Developers can easily build, test, and validate **amun** locally.

### Prerequisites

VM lifecycle is delegated to [`kora`](https://github.com/GonzaloAlvarez/kora)
(gear: `~/.gear/com/kora/setup-darwin`), which in turn needs:

- [`tart`](https://github.com/cirruslabs/tart) + [`sshpass`](https://linux.die.net/man/1/sshpass)
  for sequoia/debian/ubuntu guests on Apple Silicon
- `qemu` (Homebrew) for the arch guest

```bash
brew install cirruslabs/cli/tart cirruslabs/cli/sshpass qemu
```

An uninstalled kora working tree also works: `KORA_BIN=~/dev/kora/kora ./test …`

### Running tests

```bash
./test              # all platforms: sequoia, debian, ubuntu, arch
./test debian       # one platform
./test debian -p docker   # converge core, then the amun-docker plugin
```

Each platform run creates a fresh VM in an isolated `KORA_HOME` (unique VM
names, no interference with a dev VM you may have), stages the working trees
into the guest with `kora copy`, runs `AMUN_REPO=… ./amun`, and removes the
VM. The staged tree is always what's tested — never a live host mount.

### Cloud testing (`--cloud`)

Local tart/QEMU VMs run under macOS hvf, which cannot nest virtualization —
plugins that need a real `/dev/kvm` (e.g. `amun-qemu`) can't be validated
locally. `--cloud` runs the same payload in a fresh QEMU/KVM guest on the
**persistent** `kvm` devbox (created on first use via
[`clouddevbox`](https://github.com/GonzaloAlvarez/cn-cli-devbox)):

```bash
./test --cloud --profile <aws-profile> -p <plugin>          # debian guest (default)
./test arch --cloud --profile <aws-profile> -p <plugin>     # ubuntu/arch guests too
DEBUG=1 ./test --cloud --profile <p> -p <plugin>            # shell in the guest before teardown
```

- Cost: the `kvm` box is m7i.large ≈ $0.10/h while running (~$4/mo stopped),
  with autostop re-asserted to 12h per boot. The harness **prompts before a
  billable run** (`--yes` skips). The guest VM is removed after the run; the
  box persists — no per-run CDK deploy, so subsequent runs start in ~1 min.
- Without `--profile`, kora delegates selection to `clouddevbox profile`
  (interactive bullet picker on a tty).
- Prerequisites: `clouddevbox` on PATH (gear `com/clouddevbox`) and its
  tailnet route (cn-socksnode proxy on `127.0.0.1:1055`).
- Unlike the pre-kora harness, **amun core IS re-run** — the guest is a fresh
  VM, not the devbox itself. Destroy the box when done experimenting:
  `clouddevbox destroy kvm --profile <p>`.

### Molecule Testing

For faster iteration on individual roles, you can use molecule to test roles in Docker containers:

Prerequisites:
- Docker installed and running
- Python 3 available

The `./molecule` script will automatically install molecule and its dependencies in a temporary virtual environment.

```bash
./molecule                    # Test all roles
./molecule permissions        # Test specific role
./molecule permissions verify # Run specific test step
```

Molecule tests are available for: permissions, dotfiles, utils, remoteaccess, ufw, pki

### Debugging

To step into the environment during testing and inspect the system interactively,
set the DEBUG flag before running tests:

```bash
DEBUG=1 ./test
```

When DEBUG=1 is active, the process will pause and drop you into a command prompt inside the provisioned environment (kora ssh).
This allows you to manually verify configuration, inspect variables, and test system state before the run continues.

To watch the VM display (mandatory for desktop/X11 plugins, per homelab
CLAUDE.md §14.1): the harness prints its per-run `KORA_HOME` in the logs —
run `KORA_HOME=<that path> kora vnc` in a second terminal, or use DEBUG=1 to
hold the VM open.

## License

GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007

Copyright (c) 2025 Gonzalo Alvarez

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see https://www.gnu.org/licenses/.
