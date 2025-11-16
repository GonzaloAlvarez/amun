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

You can bootstrap **amun** into your environment with a single command.  
This will automatically fetch and execute the bootstrap script to prepare your workspace:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/gonzaloalvarez/amun/main/bootstrap)
```
or, if you are a bare debian install without curl, you can use:

```bash    
bash <(wget -qO- https://raw.githubusercontent.com/gonzaloalvarez/amun/main/bootstrap)
```

## Features

- ⚙️ **Hybrid provisioning:** combines **Ansible** and **Python** for flexible, scriptable infrastructure management  
- 🧩 **Modular architecture:** role-based structure for clean separation of responsibilities  
- 🚀 **One-line bootstrap:** quick setup with a single `curl | bash` command  
- 🔁 **Idempotent operations:** safe to re-run without corrupting your setup  
- 🧰 **Extensible tooling:** easily integrate custom Python or shell utilities  
- 🧮 **Reproducible environments:** ensures consistent system states across machines  
- 🧑‍💻 **Developer-friendly testing:** built-in testing and debugging modes for validation and exploration

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
./tests
```
This will execute end-to-end provisioning and validation flows to ensure amun works correctly.

### Debugging

To step into the environment during testing and inspect the system interactively,
set the DEBUG flag before running tests:

```bash
DEBUG=1 ./tests
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
