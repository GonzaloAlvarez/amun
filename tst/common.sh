#!/bin/bash

TST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_ISO="$TST_DIR/arch-linux-aarch64.iso"
ARCHBOOT_URL="https://release.archboot.com/aarch64/latest/iso/"
REMOTE_ISO="$(curl -so - https://release.archboot.com/aarch64/latest/b2sum.txt | grep  "ARCH-aarch64.iso)" | awk -F'[/)]' '{print $2}')"
DISK_IMG="$TST_DIR/archlinuxarm.qcow2"
DISK_SIZE="30G"
RAM_SIZE="4G"
FW_CODE="$TST_DIR/edk2-aarch64-code.fd"
FW_VARS="$TST_DIR/edk2-aarch64-vars.fd"
SSH_KEY="$TST_DIR/ssh_key.pem"
TEST_KEY="$TST_DIR/test_key"
TEST_KEY_PUB="$TST_DIR/test_key.pub"

uefi_vars() {
    rm -f "$FW_VARS"
    echo "--- Creating blank UEFI variables store file ($FW_VARS) ---"
    dd if=/dev/zero of="$FW_VARS" bs=1m count=64
}

uefi_fw() {
    if [ ! -f "$FW_CODE" ]; then
        echo "--- Searching for QEMU UEFI firmware ---"
        FW_PATH_CODE=$(find /opt/homebrew /usr/local -name "edk2-aarch64-code.fd" 2>/dev/null | head -n 1)

        if [ -z "$FW_PATH_CODE" ]; then
            echo "Could not find QEMU aarch64 UEFI firmware file (edk2-aarch64-code.fd). Make sure QEMU is installed correctly via Homebrew."
            exit 1
        fi

        cp "$FW_PATH_CODE" "$FW_CODE"
        echo "--- QEMU UEFI firmware prepared ---"
    fi
}

ssh_keys() {
    echo "--- Retrieving the SSH Key ---"

    curl -so - https://release.archboot.com/aarch64/latest/Release.txt | sed -n '/-----BEGIN OPENSSH PRIVATE KEY-----/,/-----END OPENSSH PRIVATE KEY-----/p' > "$SSH_KEY"
    chmod 600 "$SSH_KEY"
}

generate_test_key() {
    echo "--- Generating SSH key pair for passwordless auth ---"
    rm -f "$TEST_KEY" "$TEST_KEY_PUB"
    ssh-keygen -t ed25519 -f "$TEST_KEY" -N "" -q
    chmod 600 "$TEST_KEY"
}

dw_iso() {
    if [ ! -f "$LOCAL_ISO" ]; then
        echo "--- Downloading remote image ---"
        curl -o "$LOCAL_ISO" "$ARCHBOOT_URL/$REMOTE_ISO"
    fi
}

new_image() {
    if [ ! -f "$DISK_IMG" ]; then
        echo "--- Creating QCOW2 disk image: $DISK_IMG ---"
        qemu-img create -f qcow2 "$DISK_IMG" "$DISK_SIZE"

        echo "--- Disk image created"
    fi
}

install() {
    echo "--- The VM will boot from the ISO now for installation. ---"

    qemu-system-aarch64 \
        -machine virt,accel=hvf \
        -cpu cortex-a57 -smp 4 -m 4G \
        -device virtio-net-pci,netdev=net0 \
        -netdev user,id=net0,hostfwd=tcp:127.0.0.1:2221-:11838 \
        -device nvme,drive=disk0,serial=d0 \
        -drive id=disk0,if=none,format=qcow2,file="$DISK_IMG",discard=on \
        -drive if=pflash,format=raw,file="$FW_CODE",readonly=on \
        -drive if=pflash,format=raw,file="$FW_VARS" \
        -display none \
        -monitor none \
        -vnc :1 \
        -daemonize \
        -cdrom "$LOCAL_ISO" \
        -boot d

    echo "--- Installation running. Give it a few seconds to boot ---"
    export SSHPASS=Archboot
    until sshpass -e -P assphrase ssh -p 2221 -i "$SSH_KEY" -l root -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=2 127.0.0.1 -o LogLevel=ERROR  exit 0 2>/dev/null; do sleep 1; done
    sleep 2
    sshpass -e -P assphrase ssh -i "$SSH_KEY" -l root -p 2221 -o StrictHostKeychecking=no -o UserKnownHostsFile=/dev/null 127.0.0.1 -o LogLevel=ERROR "/bin/bash -c 'rm -f /etc/profile.d/custom-bash-options.sh'"
    sshpass -e -P assphrase scp -i "$SSH_KEY" -P 2221 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR "$TEST_KEY_PUB" root@127.0.0.1:/tmp/test_key.pub
    sshpass -e -P assphrase scp -i "$SSH_KEY" -P 2221 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR "$TST_DIR/autorun-install.sh" root@127.0.0.1:/tmp/archboot-install.sh
    sshpass -e -P assphrase ssh -i "$SSH_KEY" -l root -p 2221 -o StrictHostKeychecking=no -o UserKnownHostsFile=/dev/null 127.0.0.1 -o LogLevel=ERROR "/bin/bash -c 'chmod +x /tmp/archboot-install.sh'"
    sshpass -e -P assphrase ssh -i "$SSH_KEY" -l root -p 2221 -o StrictHostKeychecking=no -o UserKnownHostsFile=/dev/null 127.0.0.1 -o LogLevel=ERROR "/bin/bash -c 'cd /tmp;./archboot-install.sh'"
    sshpass -e -P assphrase ssh -i "$SSH_KEY" -l root -p 2221 -o StrictHostKeychecking=no -o UserKnownHostsFile=/dev/null 127.0.0.1 -o LogLevel=ERROR "/bin/bash -c 'sleep 2; halt -p'"
}

headless_boot() {
    echo "--- Starting QEMU VM (booting from disk) ---"

    qemu-system-aarch64 \
        -machine virt,accel=hvf \
        -cpu cortex-a57 -smp 4 -m "$RAM_SIZE" \
        -device virtio-net-pci,netdev=net0 \
        -netdev user,id=net0,hostfwd=tcp::2221-:22 \
        -device nvme,drive=disk0,serial=d0 \
        -drive id=disk0,if=none,format=qcow2,file="$DISK_IMG",discard=on \
        -drive if=pflash,format=raw,file="$FW_CODE",readonly=on \
        -drive if=pflash,format=raw,file="$FW_VARS" \
        -display none \
        -monitor none \
        -vnc :1 \
        -daemonize

    echo "--- Waiting for image to boot ---"
    until ssh -p 2221 -i "$TEST_KEY" -l archboot -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=2 127.0.0.1 -o LogLevel=ERROR exit 0 2>/dev/null; do sleep 1; done
}
