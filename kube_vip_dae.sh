#!/bin/bash
set -e

echo "[INFO] Fetching latest Kube-VIP version..."
KVVERSION=$(curl -sL https://api.github.com/repos/kube-vip/kube-vip/releases | jq -r ".[0].name")

echo "[INFO] Detecting primary network interface..."
MAIN_IFACE=$(ip route get 1.1.1.1 | awk '{print $5; exit}')

if [[ -z "$MAIN_IFACE" ]]; then
    echo "[ERROR] Unable to detect main network interface. Exiting."
    exit 1
fi

echo "[INFO] Detected main interface: $MAIN_IFACE"

echo "[INFO] Deploying Kube-VIP Daemonset..."
docker run --network host --rm ghcr.io/kube-vip/kube-vip:$KVVERSION manifest daemonset --services --inCluster --arp --interface $MAIN_IFACE | kubectl apply -f -
