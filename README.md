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

Before running tests, ensure you have the following tools installed:

- [`tart`](https://github.com/cirruslabs/tart) — lightweight macOS virtualization tool  
- [`sshpass`](https://linux.die.net/man/1/sshpass) — non-interactive SSH password provider  

On macOS:

```bash
brew install cirruslabs/cli/tart cirruslabs/cli/sshpass
```

### Running tests

Running Tests

Once dependencies are in place, run the integrated test suite:

```bash
./test
```
This will execute end-to-end provisioning and validation flows to ensure amun works correctly.

### Cloud testing (`--cloud`, `--kvm`)

Local tart/QEMU VMs run under macOS hvf, which cannot nest virtualization —
plugins that need a real `/dev/kvm` (e.g. `amun-qemu`) can't be validated
locally. The cloud path provisions a **billable** AWS devbox via the
[`clouddevbox`](https://github.com/GonzaloAlvarez/cn-cli-devbox) CLI instead:

```bash
./test debian --cloud --profile <aws-profile> -p <plugin>        # Debian 13 amd64 box
./test debian --cloud --kvm --profile <aws-profile> -p <plugin>  # + nested virt (m7i.large, /dev/kvm)
DEBUG=1 ./test debian --cloud --kvm --profile <p> -p <plugin>    # shell on the box before teardown
```

- Cost: m7i.large ≈ $0.10/h (m7g.large ≈ $0.082/h without `--kvm`); a typical
  run is 15–25 min. The box is **destroyed automatically on exit** (EXIT trap,
  also on failure/interrupt).
- The profile falls back to `CLOUDDEVBOX_PROFILE`, then `AWS_PROFILE`.
- Prerequisites: `clouddevbox` on PATH (gear `com/clouddevbox`) and its tailnet
  route (cn-socksnode proxy on `127.0.0.1:1055`).
- Unlike the tart/QEMU paths, **amun core is NOT re-run**: the box's user-data
  bootstraps core from GitHub `main` at boot, and the harness ships only the
  local working-tree plugin(s) on top. With `--kvm` the harness additionally
  asserts `/dev/kvm` exists after the plugins converge.

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

When DEBUG=1 is active, the process will pause and drop you into a command prompt inside the provisioned environment.
This allows you to manually verify configuration, inspect variables, and test system state before the run continues.

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
