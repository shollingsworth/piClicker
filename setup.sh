#!/usr/bin/env bash
set -u 
IFS=$'\n\t'

############################################################################
# STATIC VARS
############################################################################
interwebs_timeout=30 #how long we want to wait for internets
#------------------
# Apt packages
#------------------
packages+=("vim")
packages+=("jq")
packages+=("screen")
packages+=("git")
packages+=("python-pip")
packages+=("python-dev")
packages+=("alsa-utils")
packages+=("python-alsaaudio")
#------------------
# pip modules
#------------------
pip_modules+=("wifi")

############################################################################
# Functions
############################################################################
usage() {
    cat <<EOF
usage:
    -------------------------------------------------
    $0 <hostname> [--ssh | --nossh (default) ]
    -------------------------------------------------
        --nossh : do not secure ssh
        --ssh   : Enable securing of SSH, putting public keys in ./sshpubkeyblob.txt in ~/.ssh/authorized_keys
EOF
    exit -1
}

err() {
    echo "!!ERROR: ${1:?"argv[1]: error text"}"
    exit 1
}

insult() {
    echo "Insulting bash script says: ${1?"argv[1]: text"} you nitwit"
}

pbanner() {
    echo '======================================================'
    echo "${1:?"argv[1]: banner text"}"
    echo '======================================================'
    echo
}

checkweb() {
    test "root" == "$(whoami)" || err "Error, need to be root to run"
    pbanner "checking interweb connectivity"
    interwebs=0
    timeout ${interwebs_timeout} ping -c 1 google.com && { interwebs=1; pbanner "interwebs are on! (unless you messed with dns you hacker weirdo)"; }
    if [ ${interwebs} -ne 1  ]; then
        echo "no internets for you... I guess I'm done for now"
        echo "There is more after this, but you'd have to have internets to see it"
        echo "Sorry."
        exit -1
    fi
}

sethostname() {
    pbanner "Setting hostname"
    hostnamectl set-hostname ${hostname}
}

installpackages() {
    pbanner "Installing Necessary apt packages"
    apt install -y ${packages[@]}
    pbanner "Installing Necessary python v2.7 pip packages"
    pip install ${pip_modules[@]}
}

securessh() {
    ssh_auth_hosts="${HOME}/.ssh/authorized_keys"
    sshd_config="/etc/ssh/sshd_config"
    pbanner "Dropping in authorized keys"
    test -f ${ssh_auth_hosts} && cp -v ${ssh_auth_hosts} ${ssh_auth_hosts}.${dts}
    mkdir -pv $(dirname ${ssh_auth_hosts})
    chmod 700 ${ssh_auth_hosts}
    cat ./sshpubkeyblob.txt  > ${ssh_auth_hosts}
    chmod 600 ${ssh_auth_hosts}

    pbanner "Securing SSH"
    cp -v ${sshd_config} ${sshd_config}.${dts}
    cat ./sshd_config >  ${sshd_config}
    echo "Enabling SSH Daemon"
    systemctl enable ssh
    echo "Restarting SSH Daemon"
    /etc/init.d/ssh restart
}

setup_alsa() {
    alsa_config="/usr/share/alsa/alsa.conf"
    test -f ${alsa_config} && cp -v ${alsa_config} ${alsa_config}.${dts}
    cat ./alsa.conf > ${alsa_config}
    #systemctl alsa-utils enable
    #systemctl alsa-utils start
}


############################################################################
# START
############################################################################
dts="$(date +%s)"
hostname="${1?"argv[1]: $(insult "I need a hostname as a first argument")"}"
arg_secure_ssh="${2:-"--nossh"}"
[[ "${arg_secure_ssh}" == '--nossh'  || "${arg_secure_ssh}" == '--ssh' ]] || usage

checkweb
sethostname
installpackages
setup_alsa
test "${arg_secure_ssh}" == '--ssh' && securessh

pbanner "I would suggest rebooting. Or don't, I really don't care"
pbanner "Now I'm done I guess. I'm probably buggy and won't work properly, but we'll see. Just blame my author, that's what I do. Bye."
