import os
import subprocess
import sys
from local import run_command

def check_installed(package):
    """Checks if a package is installed and returns True if found."""
    print(f"\n[INFO] Checking if {package} is installed...")
    result = subprocess.run(f"dpkg -l | grep -w {package}", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[SKIP] {package} is already installed.")
        return True
    print(f"[INSTALL] {package} is not installed.")
    return False

def install_dependencies():
    """Installs system dependencies required for Kubernetes."""
    required_packages = ["apt-transport-https", "ca-certificates", "curl", "wget", "jq"]
    for package in required_packages:
        if not check_installed(package):
            run_command(f"sudo apt-get install -y {package}", f"Installing {package}")

def install_flannel():
    """Installs Flannel as the CNI plugin for Kubernetes networking."""
    run_command("kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml", "Deploying Flannel network plugin")

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

def initialize_cluster():
    """Initializes the Kubernetes cluster using kubeadm with Docker as CRI."""
    if os.path.exists("/etc/kubernetes/admin.conf"):
        print("[SKIP] Kubernetes cluster already initialized.")
        return
    run_command("sudo kubeadm init --pod-network-cidr=10.244.0.0/16 --cri-socket unix:///run/cri-dockerd.sock --node-name=cluster-1", "Initializing Kubernetes cluster")
    run_command("mkdir -p $HOME/.kube", "Creating kubeconfig directory")
    run_command("sudo cp -f /etc/kubernetes/admin.conf $HOME/.kube/config", "Copying kubeconfig file")
    run_command("sudo chown $(id -u):$(id -g) $HOME/.kube/config", "Setting kubeconfig ownership")
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
    install_flannel()
    setup_kube_vip_loadbalancer()
    print("\n[INFO] Kubernetes cluster setup complete!")
    print("[INFO] Run 'kubectl get nodes' to verify cluster status.")

if __name__ == "__main__":
    main()
