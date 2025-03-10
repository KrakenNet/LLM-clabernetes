#!/bin/bash
set -e  # Exit immediately if a command fails

TOOLKIT_DIR="/usr/local/bin"
PYTHON_BIN=$(which python3)



# Dynamically find the repo root directory
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "")

# Validate that we're in a Git repository
if [ -z "$REPO_ROOT" ]; then
    echo "[ERROR] Could not determine repository root. Ensure this script is inside a Git repo."
    exit 1
fi

KUBE_UP_SCRIPT="$REPO_ROOT/kube_up.py"
KUBE_DOWN_SCRIPT="$REPO_ROOT/kube_down.py"
CLABER_UP_SCRIPT="$REPO_ROOT/claber_up.py"
MAIN_PROJ_SCRIPT="$REPO_ROOT/main.py"
LEAF_SCRIPT="REPO_ROOT/join_leaf_nodes.py"


# Function to run commands with descriptions
run_command() {
    echo -e "\n[INFO] $2..."
    eval "$1"
}

# Function to check Kubernetes networking issues
check_networking() {
    echo -e "\n=== Checking Kubernetes Networking ==="
    run_command "kubectl get pods -n kube-system" "Listing all system pods"
    run_command "kubectl get endpoints -n default kubernetes" "Checking Kubernetes API server endpoints"
    run_command "kubectl get svc -n kube-system | grep kube-dns" "Checking CoreDNS service"
    run_command "kubectl get cm -n kube-system kube-proxy -o yaml" "Checking Kube-Proxy config"
}

# Function to check kube-proxy and iptables
check_kubeproxy() {
    echo -e "\n=== Checking Kube-Proxy ==="
    run_command "kubectl logs -n kube-system -l k8s-app=kube-proxy --tail=50" "Checking kube-proxy logs"
    run_command "sudo iptables -t nat -L -n -v | grep -E 'KUBE|10\.96|10\.244'" "Checking iptables rules"
}

# Function to reset Kubernetes networking rules
reset_iptables() {
    echo -e "\n=== Resetting Kubernetes iptables Rules ==="
    run_command "sudo iptables -t nat -F KUBE-SERVICES" "Flushing KUBE-SERVICES"
    run_command "sudo iptables -t nat -F KUBE-POSTROUTING" "Flushing KUBE-POSTROUTING"
    run_command "sudo iptables -t nat -X KUBE-SERVICES" "Deleting KUBE-SERVICES chain"
    run_command "sudo iptables -t nat -X KUBE-POSTROUTING" "Deleting KUBE-POSTROUTING chain"
}

# Function to restart kube-proxy
restart_kubeproxy() {
    echo -e "\n=== Restarting Kube-Proxy ==="
    run_command "kubectl -n kube-system delete pod -l k8s-app=kube-proxy" "Restarting kube-proxy"
}

# Function to check CoreDNS
check_coredns() {
    echo -e "\n=== Checking CoreDNS ==="
    run_command "kubectl logs -n kube-system -l k8s-app=kube-dns --tail=50" "Checking CoreDNS logs"
    run_command "kubectl get pods -n kube-system -l k8s-app=kube-dns" "Checking CoreDNS pod status"
    run_command "kubectl exec -n kube-system -it $(kubectl get pod -n kube-system -l k8s-app=kube-dns -o jsonpath='{.items[0].metadata.name}') -- nslookup kubernetes.default.svc.cluster.local || true" "Testing DNS resolution"
}

# Function to check Flannel
check_flannel() {
    echo -e "\n=== Checking Flannel ==="
    run_command "kubectl logs -n kube-flannel -l app=flannel --tail=50" "Checking Flannel logs"
    run_command "ip a show flannel.1" "Checking Flannel network interface"
    run_command "ip r | grep 10.96" "Checking Kubernetes internal routes"
}

# Function to reset everything
full_reset() {
    echo -e "\n=== Full Kubernetes Reset ==="
    reset_iptables
    restart_kubeproxy
}

# Function to bring Kubernetes up
kube_up() {
    echo -e "\n=== Bringing Kubernetes Up ==="
    if [ -f "$KUBE_UP_SCRIPT" ]; then
        $PYTHON_BIN "$KUBE_UP_SCRIPT"
    else
        echo "[ERROR] kube_up.py not found at $KUBE_UP_SCRIPT"
        exit 1
    fi
}

# Function to bring Kubernetes down
kube_down() {
    echo -e "\n=== Bringing Kubernetes Down ==="
    if [ -f "$KUBE_DOWN_SCRIPT" ]; then
        $PYTHON_BIN "$KUBE_DOWN_SCRIPT"
    else
        echo "[ERROR] kube_down.py not found at $KUBE_DOWN_SCRIPT"
        exit 1
    fi
}

claber_up(){
        echo -e "\n=== Bringing Clabernetes Up ==="
    if [ -f "$CLABER_UP_SCRIPT" ]; then
        $PYTHON_BIN "$CLABER_UP_SCRIPT"
    else
        echo "[ERROR] claber_up.py not found at $CLABER_UP_SCRIPT"
        exit 1
    fi
}

main_proj(){
        echo -e "\n=== Bringing Clabernetes Up ==="
    if [ -f "$MAIN_PROJ_SCRIPT" ]; then
        $PYTHON_BIN "$MAIN_PROJ_SCRIPT"
    else
        echo "[ERROR] main.py not found at $MAIN_PROJ_SCRIPT"
        exit 1
    fi
}

leaf_nodes(){
        echo -e "\n=== Bringing Leaf Nodes Up ==="
    if [ -f "LEAF_SCRIPT" ]; then
        $PYTHON_BIN "$LEAF_SCRIPT"
    else
        echo "[ERROR] joing_leaf_nodes.py not found at $LEAF_SCRIPT"
        exit 1
    fi
}

# Function to open a debug pod
open_debug_pod() {
    echo -e "\n=== Opening Debug Pod ==="
    run_command "kubectl run debug-pod --rm -it --image=ubuntu -- bash -c 'apt update && apt install -y iputils-ping net-tools dnsutils curl wget iproute2 tcpdump nmap traceroute && bash'" \
    "Starting debug pod with Ubuntu and installing networking tools"
}


proxy_up() {
    echo -e "\n=== Starting kubectl proxy ==="
    nohup kubectl proxy --port=8001 --address=0.0.0.0 --disable-filter=true > kubectl-proxy.log 2>&1 &
    echo "[SUCCESS] kubectl proxy started in the background. Logs: kubectl-proxy.log"
}

# Function to stop kubectl proxy
proxy_down() {
    echo -e "\n=== Stopping kubectl proxy ==="
    pkill -f "kubectl proxy"
    echo "[SUCCESS] kubectl proxy stopped."
}

# Function to show help
show_help() {
    echo -e "\nUsage: $0 [option]"
    echo -e "Options:"
    echo -e "  up          Start Kubernetes (Runs kube_up.py)"
    echo -e "  down        Stop Kubernetes (Runs kube_down.py)"
    echo -e "  main        Run Main Project (Runs main.py)"
    echo -e "  clab        Bring Clabernetes up (Runs claber_up.py)"
    echo -e "  leaf        Bring Leaf Nodes up (Runs join_leaf_nodes.py)"
    echo -e "  net         Check Kubernetes networking"
    echo -e "  proxy       Check kube-proxy"
    echo -e "  iptables    Reset Kubernetes iptables rules"
    echo -e "  restart     Restart kube-proxy"
    echo -e "  dns         Check CoreDNS"
    echo -e "  flannel     Check Flannel networking"
    echo -e "  pu          Start kubectl proxy in the background"
    echo -e "  pd          Stop kubectl proxy"
    echo -e "  reset       Perform a full Kubernetes reset"
    echo -e "  debug       Open a debug pod"
    echo -e "  help        Show this help message"
}

# Handle command-line arguments
case "$1" in
    up) kube_up ;;
    down) kube_down ;;
    main) main_proj ;;
    clab) claber_up ;;
    leaf) join_leaf_nodes ;;
    net) check_networking ;;
    proxy) check_kubeproxy ;;
    iptables) reset_iptables ;;
    restart) restart_kubeproxy ;;
    dns) check_coredns ;;
    flannel) check_flannel ;;
    pu) proxy_up ;;
    pd) proxy_down ;;
    reset) full_reset ;;
    debug) open_debug_pod ;;
    help) show_help ;;
    *) echo "[ERROR] Invalid option. Use 'help' for usage."; exit 1 ;;
esac
