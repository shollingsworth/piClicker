#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'
interwebs_timeout=30
debug="${1:-"0"}"

intro=$(cat <<EOF
Generate this outside of the pi, now we\'re going to feed it some information!
EOF
)
doc=$(mktemp)
trap "rm -f ${doc}" EXIT

err() {
    text="${1?"argv[1]: text"}"
    echo "====================================="
    echo "Error: ${text}"
    exit 1
}

checkreqs() {
    which jq >/dev/null || err "Error jq is not installed, (apt install jq, yum install jq, etc...)"
    which wpa_passphrase >/dev/null || err "Error wpa_passphrase is not installed, (apt install jq, yum install jq, etc...)"
}


getjson() {
    key="${1?"argv[1]: key value"}"
    val=$(cat ${doc} | jq -r ".${key}") || err "Error parsing json file, try again"
    echo "${val}"
}

mkdoc() {
    echo "${intro}"
    echo -ne "Press enter when ready: "
    read
    cat <<'EOF' > ${doc}
{
    "ssid":"",
    "psk":""
}
EOF
}

parsedoc() {
    vim ${doc}
    ssid=$(getjson ssid)
    psk=$(getjson psk)
    ssh_keyfile=$(getjson psk)
}

checkreqs

if [ "${debug}" == "0" ]; then
    mkdoc
    parsedoc
else
    #TESTING
    psk="${WCTF_PW?"Error export WCTF_PW not set"}"
    ssid="${WCTF_SSID?"Error export WCTF_SSID not set"}"
fi

dts=$(date +%s)
netblock=$(wpa_passphrase "${ssid}" "${psk}" | grep -v '#psk') || err "Error generating passphrase! (test with wpa_passphrase <ssid> <psk>)"
wpa_file="/etc/wpa_supplicant/wpa_supplicant.conf"
ifile="/etc/network/interfaces"

b64=$(cat <<EOF | gzip | base64 -w0  
#########################################################
#START DESTINATION RUN
#########################################################

test "root" == "\$(whoami)" || { echo "Error, need to be root to run"; exit 1; }

#////////////////////////////////////////////
echo "Modifying WPA / bringing up network"
cp -v ${wpa_file} ${wpa_file}.${dts}
cat <<ZOF > ${wpa_file}
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
${netblock}
ZOF

echo "Modifying interfaces file"
cp -v ${ifile} ${ifile}.${dts}
cat <<ZOF > ${ifile}
auto lo
iface lo inet loopback
iface eth0 inet manual

#connection interface
allow-hotplug wlan0
iface wlan0 inet manual
    wpa-conf ${wpa_file}

#scanning interface
allow-hotplug wlan1
#iface wlan1 inet manual
#    wpa-conf ${wpa_file}
ZOF

echo "Bringing up wlan0"
ifdown wlan0
ifup wlan0
sleep 10
#////////////////////////////////////////////

#////////////////////////////////////////////
echo "checking interweb connectivity"
interwebs=0
timeout ${interwebs_timeout} ping -c 1 google.com && interwebs=1
echo interwebs = \${interwebs}
if [ \${interwebs} -eq 1  ]; then
    echo "You have interwebs!"
else
    echo "no internets for you... I guess I'm done for now"
    echo "There is more after this, but you'd have to have internets to see it"
    echo "Sorry."
    exit 1
fi

#////////////////////////////////////////////
echo "Rebooting host"
sleep 5
reboot

#////////////////////////////////////////////
#########################################################
#END DESTINATION RUN
#########################################################
EOF
)

echo "Paste/Run the following line in the pi console"
echo "echo ${b64} | base64 -d | gunzip | bash -" 
