# Molecule Testing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add molecule-based testing infrastructure to test amun Ansible roles using Docker containers.

**Architecture:** Create a root molecule script that manages virtual environments and runs molecule tests. Each testable role (permissions, dotfiles, utils) gets a molecule/default/ directory with configuration and test files. Tests run in Docker containers using Debian 12 with systemd support.

**Tech Stack:** Python 3, molecule, ansible, Docker, molecule-plugins[docker]

---

## Task 1: Create Root Molecule Script

**Files:**
- Create: `molecule`

**Step 1: Create the molecule executable script**

Create `molecule` file with complete implementation:

```bash
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR=$(mktemp -d)
TESTABLE_ROLES=("permissions" "dotfiles" "utils")

trap 'rm -rf "$VENV_DIR"' EXIT SIGINT SIGTERM

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel > /dev/null 2>&1
"$VENV_DIR/bin/pip" install ansible molecule 'molecule-plugins[docker]' > /dev/null 2>&1

export PATH="$VENV_DIR/bin:$PATH"

if [ $# -gt 0 ] && [[ " ${TESTABLE_ROLES[@]} " =~ " $1 " ]]; then
    ROLE="$1"
    shift
    cd "$SCRIPT_DIR/roles/$ROLE"
    molecule "${@:-test}"
elif [ $# -eq 0 ]; then
    for role in "${TESTABLE_ROLES[@]}"; do
        echo "========================================"
        echo "Testing role: $role"
        echo "========================================"
        cd "$SCRIPT_DIR/roles/$role"
        molecule test
    done
else
    echo "Usage: $0 [role] [molecule-command]"
    echo ""
    echo "Available roles: ${TESTABLE_ROLES[*]}"
    echo ""
    echo "Examples:"
    echo "  $0                    # Test all roles"
    echo "  $0 permissions        # Test permissions role"
    echo "  $0 permissions verify # Run verify step only"
    exit 1
fi
```

**Step 2: Make script executable**

Run: `chmod +x molecule`

**Step 3: Verify script structure**

Run: `head -20 molecule`
Expected: See shebang, set -e, and variable declarations

**Step 4: Commit**

```bash
git add molecule
git commit -m "Add molecule test runner script"
```

---

## Task 2: Add Molecule Testing for Permissions Role

**Files:**
- Create: `roles/permissions/molecule/default/molecule.yml`
- Create: `roles/permissions/molecule/default/converge.yml`
- Create: `roles/permissions/molecule/default/prepare.yml`
- Create: `roles/permissions/molecule/default/verify.yml`

**Step 1: Create molecule directory structure**

Run: `mkdir -p roles/permissions/molecule/default`

**Step 2: Create molecule.yml**

Create `roles/permissions/molecule/default/molecule.yml`:

```yaml
---
driver:
  name: docker
platforms:
  - name: permissions-test
    image: geerlingguy/docker-debian12-ansible:latest
    privileged: true
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:rw
    cgroupns_mode: host
    command: /usr/lib/systemd/systemd
    pre_build_image: true
provisioner:
  name: ansible
  config_options:
    defaults:
      roles_path: ${MOLECULE_PROJECT_DIRECTORY}/..
verifier:
  name: ansible
scenario:
  test_sequence:
    - destroy
    - syntax
    - create
    - prepare
    - converge
    - idempotence
    - verify
    - destroy
```

**Step 3: Create converge.yml**

Create `roles/permissions/molecule/default/converge.yml`:

```yaml
---
- name: Converge
  hosts: all
  roles:
    - role: permissions
```

**Step 4: Create prepare.yml**

Create `roles/permissions/molecule/default/prepare.yml`:

```yaml
---
- name: Prepare
  hosts: all
  tasks:
    - name: Update apt cache
      ansible.builtin.apt:
        update_cache: true
        cache_valid_time: 3600
      become: true

    - name: Install sudo
      ansible.builtin.apt:
        name: sudo
        state: present
      become: true
```

**Step 5: Read the permissions role tasks to understand what to verify**

Run: `cat roles/permissions/tasks/main.yml`
Expected: See what the role does (visudo configuration)

**Step 6: Create verify.yml**

Create `roles/permissions/molecule/default/verify.yml`:

```yaml
---
- name: Verify
  hosts: all
  tasks:
    - name: Check /etc/sudoers.d directory exists
      ansible.builtin.stat:
        path: /etc/sudoers.d
      register: sudoers_d
      failed_when: not sudoers_d.stat.exists or not sudoers_d.stat.isdir

    - name: Verify visudo configuration was applied
      ansible.builtin.shell: ls -la /etc/sudoers.d/
      register: sudoers_files
      changed_when: false
      failed_when: sudoers_files.rc != 0
```

**Step 7: Commit permissions molecule tests**

```bash
git add roles/permissions/molecule/
git commit -m "Add molecule tests for permissions role"
```

---

## Task 3: Add Molecule Testing for Dotfiles Role

**Files:**
- Create: `roles/dotfiles/molecule/default/molecule.yml`
- Create: `roles/dotfiles/molecule/default/converge.yml`
- Create: `roles/dotfiles/molecule/default/prepare.yml`
- Create: `roles/dotfiles/molecule/default/verify.yml`

**Step 1: Create molecule directory structure**

Run: `mkdir -p roles/dotfiles/molecule/default`

**Step 2: Create molecule.yml**

Create `roles/dotfiles/molecule/default/molecule.yml`:

```yaml
---
driver:
  name: docker
platforms:
  - name: dotfiles-test
    image: geerlingguy/docker-debian12-ansible:latest
    privileged: true
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:rw
    cgroupns_mode: host
    command: /usr/lib/systemd/systemd
    pre_build_image: true
provisioner:
  name: ansible
  config_options:
    defaults:
      roles_path: ${MOLECULE_PROJECT_DIRECTORY}/..
verifier:
  name: ansible
scenario:
  test_sequence:
    - destroy
    - syntax
    - create
    - prepare
    - converge
    - idempotence
    - verify
    - destroy
```

**Step 3: Create converge.yml**

Create `roles/dotfiles/molecule/default/converge.yml`:

```yaml
---
- name: Converge
  hosts: all
  roles:
    - role: dotfiles
```

**Step 4: Create prepare.yml**

Create `roles/dotfiles/molecule/default/prepare.yml`:

```yaml
---
- name: Prepare
  hosts: all
  tasks:
    - name: Update apt cache
      ansible.builtin.apt:
        update_cache: true
        cache_valid_time: 3600
      become: true

    - name: Install git
      ansible.builtin.apt:
        name: git
        state: present
      become: true

    - name: Ensure HOME directory exists
      ansible.builtin.file:
        path: "{{ ansible_env.HOME }}"
        state: directory
        mode: "0755"
```

**Step 5: Read the dotfiles role tasks to understand what to verify**

Run: `cat roles/dotfiles/tasks/main.yml`
Expected: See git cloning of dotfiles and gear repos

**Step 6: Create verify.yml**

Create `roles/dotfiles/molecule/default/verify.yml`:

```yaml
---
- name: Verify
  hosts: all
  tasks:
    - name: Check .dotfiles directory exists
      ansible.builtin.stat:
        path: "{{ ansible_env.HOME }}/.dotfiles"
      register: dotfiles_dir
      failed_when: not dotfiles_dir.stat.exists or not dotfiles_dir.stat.isdir

    - name: Verify dotfiles is a git repository
      ansible.builtin.stat:
        path: "{{ ansible_env.HOME }}/.dotfiles/.git"
      register: dotfiles_git
      failed_when: not dotfiles_git.stat.exists or not dotfiles_git.stat.isdir

    - name: Check gear directory exists
      ansible.builtin.stat:
        path: "{{ ansible_env.HOME }}/.gear"
      register: gear_dir
      failed_when: not gear_dir.stat.exists or not gear_dir.stat.isdir
```

**Step 7: Commit dotfiles molecule tests**

```bash
git add roles/dotfiles/molecule/
git commit -m "Add molecule tests for dotfiles role"
```

---

## Task 4: Add Molecule Testing for Utils Role

**Files:**
- Create: `roles/utils/molecule/default/molecule.yml`
- Create: `roles/utils/molecule/default/converge.yml`
- Create: `roles/utils/molecule/default/prepare.yml`
- Create: `roles/utils/molecule/default/verify.yml`

**Step 1: Create molecule directory structure**

Run: `mkdir -p roles/utils/molecule/default`

**Step 2: Create molecule.yml**

Create `roles/utils/molecule/default/molecule.yml`:

```yaml
---
driver:
  name: docker
platforms:
  - name: utils-test
    image: geerlingguy/docker-debian12-ansible:latest
    privileged: true
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:rw
    cgroupns_mode: host
    command: /usr/lib/systemd/systemd
    pre_build_image: true
provisioner:
  name: ansible
  config_options:
    defaults:
      roles_path: ${MOLECULE_PROJECT_DIRECTORY}/..
verifier:
  name: ansible
scenario:
  test_sequence:
    - destroy
    - syntax
    - create
    - prepare
    - converge
    - idempotence
    - verify
    - destroy
```

**Step 3: Create converge.yml**

Create `roles/utils/molecule/default/converge.yml`:

```yaml
---
- name: Converge
  hosts: all
  roles:
    - role: utils
```

**Step 4: Create prepare.yml**

Create `roles/utils/molecule/default/prepare.yml`:

```yaml
---
- name: Prepare
  hosts: all
  tasks:
    - name: Ensure apt is available
      ansible.builtin.wait_for:
        path: /usr/bin/apt
        state: present
        timeout: 10
```

**Step 5: Read the utils role tasks to understand what to verify**

Run: `cat roles/utils/tasks/main.yml`
Expected: See apt update and upgrade tasks

**Step 6: Create verify.yml**

Create `roles/utils/molecule/default/verify.yml`:

```yaml
---
- name: Verify
  hosts: all
  tasks:
    - name: Check apt cache is recent
      ansible.builtin.stat:
        path: /var/cache/apt/pkgcache.bin
      register: apt_cache
      failed_when: not apt_cache.stat.exists

    - name: Verify apt is functional
      ansible.builtin.command: apt-get --version
      register: apt_version
      changed_when: false
      failed_when: apt_version.rc != 0

    - name: Check system is in clean state
      ansible.builtin.command: dpkg --audit
      register: dpkg_audit
      changed_when: false
      failed_when: dpkg_audit.rc != 0
```

**Step 7: Commit utils molecule tests**

```bash
git add roles/utils/molecule/
git commit -m "Add molecule tests for utils role"
```

---

## Task 5: Verify Molecule Tests Work

**Step 1: Check Docker is running**

Run: `docker ps`
Expected: Docker daemon running, command succeeds

**Step 2: Test permissions role individually**

Run: `./molecule permissions`
Expected: Full test sequence runs (destroy, syntax, create, prepare, converge, idempotence, verify, destroy), all steps PASS

**Step 3: Test dotfiles role individually**

Run: `./molecule dotfiles`
Expected: Full test sequence runs, all steps PASS

**Step 4: Test utils role individually**

Run: `./molecule utils`
Expected: Full test sequence runs, all steps PASS

**Step 5: Run all tests together**

Run: `./molecule`
Expected: All three roles tested in sequence, all PASS

**Step 6: Test molecule command passthrough**

Run: `./molecule permissions verify`
Expected: Only verify step runs for permissions role, PASS

**Step 7: Update README with molecule testing instructions**

Add to `README.md` in the Development section, after the VM testing section:

```markdown
### Molecule Testing

For faster iteration on individual roles, you can use molecule to test roles in Docker containers:

```bash
./molecule                    # Test all roles
./molecule permissions        # Test specific role
./molecule permissions verify # Run specific test step
```

Prerequisites:
- Docker installed and running
- Python 3 available

Molecule tests are available for: permissions, dotfiles, utils
```

**Step 8: Commit README update**

```bash
git add README.md
git commit -m "Document molecule testing in README"
```

**Step 9: Verify script shows help for invalid role**

Run: `./molecule invalid-role`
Expected: Error message showing available roles and usage examples

---

## Testing Strategy

Each molecule test follows this sequence:
1. **destroy** - Clean up any existing containers
2. **syntax** - Validate Ansible syntax
3. **create** - Create Docker container
4. **prepare** - Install prerequisites
5. **converge** - Apply the role
6. **idempotence** - Apply again, verify no changes
7. **verify** - Run verification tests
8. **destroy** - Clean up

Tests verify basic functionality:
- **permissions**: sudoers.d directory and configuration exist
- **dotfiles**: git repos cloned to correct locations
- **utils**: apt cache updated and system in clean state

---

## Troubleshooting

**If molecule command fails:**
- Ensure Docker is running: `docker ps`
- Check Python 3 is available: `python3 --version`
- Manually test venv creation: `python3 -m venv /tmp/test-venv`

**If idempotence fails:**
- Check role tasks use proper ansible state management
- Verify tasks have `changed_when` set appropriately
- Review task output to see what's changing

**If Docker pull fails:**
- Check internet connectivity
- Verify Docker Hub is accessible
- Try pulling image manually: `docker pull geerlingguy/docker-debian12-ansible:latest`

**If verify fails:**
- Check the role actually ran: `./molecule <role> converge`
- Shell into container: `docker exec -it <role>-test bash`
- Manually verify expected files/state exist
