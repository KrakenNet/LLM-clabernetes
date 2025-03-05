import yaml
import os
import sys
from local import run_command  # Import run_command from local.py

# Load the leaf nodes configuration file dynamically
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "secret", "leaf_nodes.yaml")

def load_leaf_nodes():
    """Loads leaf node IPs from the YAML config file."""
    if not os.path.exists(CONFIG_PATH):
        print(f"[ERROR] Config file not found: {CONFIG_PATH}")
        sys.exit(1)

    with open(CONFIG_PATH, "r") as file:
        try:
            config = yaml.safe_load(file)
            return config.get("nodes", [])
        except yaml.YAMLError as e:
            print(f"[ERROR] Failed to parse YAML file: {e}")
            sys.exit(1)

def get_control_plane_ip():
    """Gets the control plane's primary IP address."""
    return os.popen("hostname -I | awk '{print $1}'").read().strip()

def generate_kubeadm_token():
    """Generates a new kubeadm token and retrieves the CA cert hash."""
    print("\n[INFO] Generating new Kubernetes join token...")
    
    # Generate a new token
    token_cmd = "kubeadm token create --print-join-command"
    token_output = os.popen(token_cmd).read().strip()

    if not token_output:
        print("[ERROR] Failed to generate kubeadm token.")
        sys.exit(1)

    # Extract token, IP, and cert hash
    parts = token_output.split()
    if len(parts) < 5:
        print("[ERROR] Invalid token output format.")
        sys.exit(1)

    # Extract and return values
    join_command = " ".join(parts)
    token = parts[4]
    cert_hash = parts[6]

    print(f"[INFO] Generated join command:\n{join_command}")
    print(f"[INFO] returning token and cert hash: token:{token}, hash:{cert_hash}")
    return token, cert_hash

def check_installed(package, host, user, password):
    """Checks if a package is installed on a remote machine."""
    print(f"\n[INFO] Checking if {package} is installed on {host}...")
    result = run_command(f"dpkg -l | grep -w {package}", f"Checking {package}", host=host, user=user, password=password, exit_on_fail=False)
    return result == 0

def install_dependencies(host, user, password):
    """Installs required dependencies on the remote node."""
    required_packages = ["apt-transport-https", "ca-certificates", "curl", "wget", "jq"]
    for package in required_packages:
        if not check_installed(package, host, user, password):
            run_command(f"sudo apt-get install -y {package}", f"Installing {package}", host=host, user=user, password=password)

def check_and_load_netfilter(host, user, password):
    """Ensures br_netfilter is loaded and persists sysctl settings."""
    print(f"\n[INFO] Checking Netfilter Module on {host}...")

    result = run_command("lsmod | grep -q br_netfilter", "Checking br_netfilter module", host=host, user=user, password=password, exit_on_fail=False)
    
    if result == 0:
        print(f"[INFO] br_netfilter module is already loaded on {host}.")
    else:
        print(f"[WARNING] br_netfilter module is not loaded. Loading it on {host}...")
        run_command("sudo modprobe br_netfilter", "Loading br_netfilter module", host=host, user=user, password=password)

    # Apply sysctl settings
    run_command("echo 'net.bridge.bridge-nf-call-iptables = 1' | sudo tee -a /etc/sysctl.conf", "Setting iptables", host=host, user=user, password=password)
    run_command("echo 'net.bridge.bridge-nf-call-ip6tables = 1' | sudo tee -a /etc/sysctl.conf", "Setting ip6tables", host=host, user=user, password=password)
    run_command("echo 'br_netfilter' | sudo tee /etc/modules-load.d/k8s.conf", "Persisting br_netfilter module", host=host, user=user, password=password)
    run_command("sudo sysctl --system", "Applying sysctl settings", host=host, user=user, password=password)

def install_cri_dockerd(host, user, password):
    """Installs cri-dockerd on a remote machine."""
    print(f"\n[INFO] Installing cri-dockerd on {host}...")

    if check_installed("cri-dockerd", host, user, password):
        print(f"[INFO] cri-dockerd is already installed on {host}. Skipping installation.")
        return

    install_dependencies(host, user, password)

    run_command("sudo apt-get install -y cri-dockerd", "Installing cri-dockerd", host=host, user=user, password=password)
    run_command("sudo systemctl enable cri-docker.service", "Enabling cri-dockerd service", host=host, user=user, password=password)
    run_command("sudo systemctl start cri-docker.service", "Starting cri-dockerd service", host=host, user=user, password=password)

def install_kubernetes(host, user, password):
    """Installs Kubernetes components on a remote machine."""
    kube_packages = ["kubelet", "kubeadm", "kubectl"]

    print(f"[INFO] Installing Kubernetes on {host}...")
    
    run_command("sudo mkdir -p /etc/apt/keyrings", "Creating keyrings directory", host=host, user=user, password=password)
    run_command("curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-archive-keyring.gpg", "Adding Kubernetes GPG key", host=host, user=user, password=password)
    run_command("echo \"deb [signed-by=/etc/apt/keyrings/kubernetes-archive-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /\" | sudo tee /etc/apt/sources.list.d/kubernetes.list", "Adding Kubernetes repository", host=host, user=user, password=password)
    run_command("sudo apt-get update", "Updating package list", host=host, user=user, password=password)

    for package in kube_packages:
        run_command(f"sudo apt-get install -y {package}", f"Installing {package}", host=host, user=user, password=password)

    run_command("sudo apt-mark hold kubelet kubeadm kubectl", "Holding Kubernetes packages to prevent updates", host=host, user=user, password=password)

def join_cluster(host, user, password, control_plane_ip, token, cert_hash):
    """Joins the remote node to the Kubernetes cluster."""
    print(f"[INFO] Joining {host} to Kubernetes cluster...")
    join_cmd = f"sudo kubeadm join {control_plane_ip}:6443 --token {token} --discovery-token-ca-cert-hash sha256:{cert_hash} --cri-socket=unix:///var/run/cri-dockerd.sock"
    run_command(join_cmd, "Joining Kubernetes cluster", host=host, user=user, password=password)

def main():
    """Main function to set up leaf nodes and join them to the cluster."""
    print("\n=== Kubernetes Leaf Node Setup Script ===\n")
    
    nodes = load_leaf_nodes()
    control_plane_ip = get_control_plane_ip()

    # Generate token and cert hash dynamically
    cluster_token, cert_hash = generate_kubeadm_token()

    for node in nodes:
        host = node["ip"]
        user = node["user"]
        password = node["password"]

        print(f"\n[INFO] Setting up node {host}...")

        install_dependencies(host, user, password)
        check_and_load_netfilter(host, user, password)
        install_cri_dockerd(host, user, password)
        install_kubernetes(host, user, password)
        join_cluster(host, user, password, control_plane_ip, cluster_token, cert_hash)

    print("\n[INFO] All leaf nodes have been set up successfully!")

if __name__ == "__main__":
    main()
