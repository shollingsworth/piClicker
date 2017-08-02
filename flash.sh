#!/usr/bin/env bash
set -u
IFS=$'\n\t'

img_path="${1?"argv[1]: pi image *.img file path"}"

yesno() {
    msg="${1?"yea... this function needs an argument"}"
    echo -ne "${msg}: (y/n): "
    read yn
    yn=$(echo "${yn}" | tr 'A-Z' 'a-z')
    case "${yn}" in
        "y")
            return 0
            ;;
        "n")
            return 1
            ;;
        *)
            yesno "${msg}"
            ;;
    esac
}

getRawDevice() {
    raw_device=$(find /dev -name 'mmc*blk0' 2>/dev/null)
    test $(echo "${raw_device}" | wc -l) -gt 1 && {
        echo "Error, more than one device detected: ${raw_device}"
        exit -1
    }
    fdisk -l ${raw_device} >&2
    echo "${raw_device}"
}

test "$(whoami)" != "root" && {
    echo "Error, you need to be running as root!"
    exit -1
}

dev=$(getRawDevice)
if yesno "Using: ${dev} with image: ${img_path}, Does this look correct?"; then
    ddrescue -f "${img_path}" "${dev}" &
else
    echo "Aborting!"
fi

cat <<EOF
After flash is complete:
Eject, and re-insert media to edit anything before inserting into pi
-----------------------
To add console login:
edit on card: /boot/config.txt
At the bottom, last line, add

enable_uart=1
-----------------------
EOF
