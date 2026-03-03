# Molecule Testing Integration for Amun

**Date:** 2026-03-02
**Status:** Approved

## Overview

Add molecule-based testing to the amun repository to enable automated testing of Ansible roles using Docker containers. This mirrors the testing approach used in amun-docker and provides confidence that roles work correctly.

## Goals

- Enable automated testing of amun roles
- Maintain consistency with amun-docker testing approach
- Test 3 roles: permissions, dotfiles, and utils
- Support testing individual roles or all roles
- Keep tests fast and maintainable

## Non-Goals

- Testing macOS-specific roles (config)
- Testing homebrew role
- Multi-platform testing (Linux distributions beyond Debian)
- Integration with CI/CD systems (can be added later)

## Architecture

### File Structure

```
amun/
├── molecule                          # Executable script (new)
└── roles/
    ├── permissions/
    │   ├── tasks/
    │   └── molecule/                 # New
    │       └── default/
    │           ├── molecule.yml
    │           ├── converge.yml
    │           ├── prepare.yml
    │           └── verify.yml
    ├── dotfiles/
    │   ├── tasks/
    │   └── molecule/                 # New
    │       └── default/
    │           ├── molecule.yml
    │           ├── converge.yml
    │           ├── prepare.yml
    │           └── verify.yml
    └── utils/
        ├── tasks/
        └── molecule/                 # New
            └── default/
                ├── molecule.yml
                ├── converge.yml
                ├── prepare.yml
                └── verify.yml
```

### Molecule Script

The root `molecule` script handles:
- Creating isolated Python virtual environment
- Installing molecule and dependencies (ansible, molecule-plugins[docker])
- Running tests for specified role(s)
- Cleanup via trap on exit or interrupt

**Usage:**
```bash
./molecule                    # Test all roles
./molecule permissions        # Test specific role
./molecule permissions verify # Run specific molecule command
```

**Implementation:**
- Temporary venv created with mktemp
- Dependencies: ansible, molecule, molecule-plugins[docker]
- Trap ensures cleanup on EXIT, SIGINT, SIGTERM
- Default action is "test" (full test sequence)
- Support for any molecule command

### Test Configuration

Each role has a `molecule/default/` directory with 4 files:

**molecule.yml:**
- Driver: docker
- Platform: geerlingguy/docker-debian12-ansible:latest
- Privileged mode with systemd support
- Test sequence: destroy → syntax → create → prepare → converge → idempotence → verify → destroy

**converge.yml:**
- Simple playbook that applies the role

**prepare.yml:**
- Role-specific setup before running the role
- Install prerequisites, create test users, etc.

**verify.yml:**
- Role-specific verification
- Basic assertions to confirm role objectives met

## Role-Specific Test Details

### Permissions Role

**prepare.yml:**
- Ensure sudo is installed
- Create test user for sudo testing

**verify.yml:**
- Verify `/etc/sudoers.d/` directory exists
- Check sudoers configuration applied
- Verify sudo functionality

### Dotfiles Role

**prepare.yml:**
- Install git
- Ensure HOME directory accessible

**verify.yml:**
- Verify `~/.dotfiles` directory exists
- Check git repo cloned successfully
- Verify gear repo exists

### Utils Role

**prepare.yml:**
- Minimal or empty (apt available in Docker image)

**verify.yml:**
- Verify apt cache updated
- Check package manager ran successfully
- Confirm system in clean state

## Testing Approach

- Use Docker-based testing with Debian 12 image
- Basic verification only (file exists, command succeeds)
- Fast, reliable tests with minimal brittleness
- Each test run starts with clean state
- Idempotence checking included in test sequence

## Error Handling

- Script uses `set -e` to fail fast
- Trap ensures venv cleanup on any exit
- Invalid role name produces clear error
- Missing molecule directory fails with message
- Docker availability checked by molecule
- Exit codes propagate from molecule to script

## Requirements

- Docker installed and running
- Python 3 available
- Sufficient permissions to run Docker containers

## Excluded Roles

- **config:** macOS-specific, cannot test in Linux Docker
- **homebrew:** macOS-focused, excluded per requirements

## Future Enhancements

- CI/CD integration (GitHub Actions)
- Multi-distribution testing
- Performance benchmarking
- Coverage reporting
- Parallel test execution
