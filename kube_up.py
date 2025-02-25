import os
import subprocess
import sys
from local import run_command

cluster_n = 'cluster-1'

def check_installed(package):
    """Checks if a package is installed and returns True if found."""
    print(f"\n[INFO] Checking if {package} is installed...")
    result = subprocess.run(f"dpkg -l | grep -w {package}", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[SKIP] {package} is already installed.")
        return True
    print(f"[INSTALL] {package} is not installed.")

    return False

def setup_ips():
    print("[INFO] setting up ip's for kubernetes")
    run_command("chmod +x kube_ip.sh && ./kube_ip.sh", "Setting up Kube-VIP IP configuration")

#not instantiated yet
def ensure_hostname_in_hosts():
    """Ensures the current hostname is present in /etc/hosts."""
    hostname = cluster_n

    try:
        # Read the contents of /etc/hosts
        with open("/etc/hosts", "r") as f:
            lines = f.readlines()

        # Check if the hostname already exists in /etc/hosts
        for line in lines:
            if hostname in line:
                print(f"[INFO] Hostname '{hostname}' is already present in /etc/hosts.")
                return

        # Get the machine's primary IP address
        ip_address = subprocess.getoutput("hostname -I | awk '{print $1}'").strip()

        if not ip_address:
            print("[ERROR] Could not determine the system's IP address.")
            return

        # Append the new hostname entry
        new_entry = f"{ip_address} {hostname}\n"
        with open("/etc/hosts", "a") as f:
            f.write(new_entry)

        print(f"[SUCCESS] Added '{hostname}' to /etc/hosts with IP: {ip_address}")

    except Exception as e:
        print(f"[ERROR] Failed to modify /etc/hosts: {e}")


def wait_for_flannel():
    """Waits for Flannel DaemonSet to appear and become ready."""
    print("[INFO] Waiting for Flannel to be created...")
    retries = 30  # 30 attempts (30s total)
    while retries > 0:
        result = subprocess.run("kubectl get daemonset -n kube-flannel", shell=True, capture_output=True, text=True)
        if "kube-flannel-ds" in result.stdout:
            print("[INFO] Flannel DaemonSet found! Waiting for readiness...")
            run_command("kubectl rollout status daemonset -n kube-flannel kube-flannel-ds --timeout=120s", "Waiting for Flannel rollout")
            return
        time.sleep(2)  # Wait before retrying
        retries -= 1
    print("[ERROR] Flannel DaemonSet did not appear in time!")



def install_dependencies():
    """Installs system dependencies required for Kubernetes."""
    required_packages = ["apt-transport-https", "ca-certificates", "curl", "wget", "jq"]
    for package in required_packages:
        if not check_installed(package):
            run_command(f"sudo apt-get install -y {package}", f"Installing {package}")
            
def check_flannel_routes():
    """Ensures Flannel has correct routing."""
    print("[INFO] Checking Flannel routes...")
    run_command("ip r | grep 10.96", "Validating Kubernetes internal routes")
    run_command("ip a show flannel.1", "Validating Flannel network interface")


def install_flannel():
    """Installs Flannel as the CNI plugin for Kubernetes networking."""
    run_command("kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml", "Deploying Flannel network plugin")

    print("[INFO] Waiting for Flannel to be ready...")
    wait_for_flannel()





def install_calico():
    """Installs Calico as the CNI plugin for Kubernetes networking."""
    print("\n[INFO] Installing Calico for Kubernetes networking...")

    # Apply the official Calico manifest
    apply_command = "kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml"
    try:
        subprocess.run(apply_command, shell=True, check=True)
        print("[SUCCESS] Calico has been installed.")

        # Verify installation
        print("[INFO] Waiting for Calico pods to be ready...")
        subprocess.run("kubectl wait --for=condition=Available -n kube-system daemonset/calico-node --timeout=120s", shell=True, check=True)
        print("[SUCCESS] Calico pods are ready.")
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to install Calico: {e}")




def install_docker():
    """Installs and configures Docker for Kubernetes."""
    if check_installed("docker.io"):
        print("[INFO] Docker is already installed. Skipping installation.")
        return
    run_command("sudo apt-get install -y docker.io || sudo apt-get -f install", "Installing Docker")
    run_command("sudo systemctl enable docker", "Enabling Docker service")
    run_command("sudo systemctl restart docker", "Restarting Docker service")

def install_cri_dockerd():
    """Installs cri-dockerd to allow Kubernetes to use Docker as the runtime."""
    if os.path.exists("/usr/local/bin/cri-dockerd"):
        print("[SKIP] cri-dockerd is already installed.")
        return

    if not check_installed("golang"):
        run_command("sudo apt-get install -y golang", "Installing Go")

    run_command("git clone https://github.com/Mirantis/cri-dockerd.git", "Cloning cri-dockerd repository")
    os.chdir("cri-dockerd")
    run_command("mkdir bin", "Creating bin directory for cri-dockerd")
    run_command("go build -o bin/cri-dockerd", "Building cri-dockerd binary")
    run_command("sudo mv bin/cri-dockerd /usr/local/bin/", "Moving cri-dockerd binary to /usr/local/bin")
    os.chdir("..")

    run_command("sudo cp -a cri-dockerd/packaging/systemd/* /etc/systemd/system/", "Copying systemd service files")
    run_command("sudo sed -i -e 's,/usr/bin/cri-dockerd,/usr/local/bin/cri-dockerd,' /etc/systemd/system/cri-docker.service", "Updating service file paths")
    run_command("sudo systemctl daemon-reload", "Reloading systemd daemon")
    run_command("sudo systemctl enable cri-docker.service", "Enabling cri-dockerd service")
    run_command("sudo systemctl enable --now cri-dockerd.socket", "Starting and enabling cri-dockerd socket")

def install_kubernetes():
    """Installs Kubernetes components (kubelet, kubeadm, kubectl)."""
    kube_packages = ["kubelet", "kubeadm", "kubectl"]
    if all(check_installed(pkg) for pkg in kube_packages):
        return
    run_command("sudo mkdir -p /etc/apt/keyrings", "Creating keyrings directory")
    run_command("curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-archive-keyring.gpg", "Adding Kubernetes GPG key")
    run_command("echo \"deb [signed-by=/etc/apt/keyrings/kubernetes-archive-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /\" | sudo tee /etc/apt/sources.list.d/kubernetes.list", "Adding Kubernetes repository")
    run_command("sudo apt-get update", "Updating package list")
    for package in kube_packages:
        if not check_installed(package):
            run_command(f"sudo apt-get install -y {package}", f"Installing {package}")
    run_command("sudo apt-mark hold kubelet kubeadm kubectl", "Holding Kubernetes packages to prevent updates")
    print("[INFO] Applying kube-proxy configuration")
    run_command("kubectl apply -f https://raw.githubusercontent.com/kubernetes/kubernetes/master/cluster/addons/kube-proxy/kube-proxy.yaml", "Applying kube-proxy settings")

def initialize_cluster():
    """Initializes the Kubernetes cluster using kubeadm with Docker as CRI."""
    if os.path.exists("/etc/kubernetes/admin.conf"):
        print("[SKIP] Kubernetes cluster already initialized.")
        return
    run_command(f"sudo kubeadm init --pod-network-cidr=10.244.0.0/16 --cri-socket unix:///run/cri-dockerd.sock", "Initializing Kubernetes cluster")
    run_command("mkdir -p $HOME/.kube", "Creating kubeconfig directory")
    run_command("sudo cp -f /etc/kubernetes/admin.conf $HOME/.kube/config", "Copying kubeconfig file")
    run_command("sudo chown $(id -u):$(id -g) $HOME/.kube/config", "Setting kubeconfig ownership")
    install_flannel()
    # install_calico()
    print ('[INFO] Clearing the Taint')
    run_command("kubectl taint nodes --all node-role.kubernetes.io/control-plane-", "Removing control-plane taint")


def setup_kube_vip_loadbalancer():
    """Deploys Kube-VIP LoadBalancer after cluster setup."""
    run_command("kubectl apply -f https://kube-vip.io/manifests/rbac.yaml", "Applying Kube-VIP RBAC")
    run_command("kubectl apply -f https://raw.githubusercontent.com/kube-vip/kube-vip-cloud-provider/main/manifest/kube-vip-cloud-controller.yaml", "Applying Kube-VIP Cloud Controller")
    run_command("kubectl create configmap --namespace kube-system kubevip --from-literal range-global=172.18.1.10-172.18.1.250", "Creating Kube-VIP ConfigMap")
    # run_command("KVVERSION=$(curl -sL https://api.github.com/repos/kube-vip/kube-vip/releases | jq -r '.[0].name')", "Fetching latest Kube-VIP version")
    # run_command("alias kube-vip='docker run --network host --rm ghcr.io/kube-vip/kube-vip:$KVVERSION'", "Setting up kube-vip alias")
    run_command("./kube_vip_dae.sh", "Deploying Kube-VIP Daemonset")


def main():
    """Main function to set up Kubernetes."""
    print("\n=== Kubernetes Cluster Setup Script ===\n")
    install_dependencies()
    install_docker()
    install_cri_dockerd()
    install_kubernetes()
    initialize_cluster()
    # install_flannel()
    setup_kube_vip_loadbalancer()
    print("\n[INFO] Kubernetes cluster setup complete!")
    print("[INFO] Run 'kubectl get nodes' to verify cluster status.")

if __name__ == "__main__":
    main()
