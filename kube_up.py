import os
import subprocess
import sys
from local import run_command
import time

# cluster_n = 'cluster-1'

def check_installed(package):
    """Checks if a package is installed and returns True if found."""
    print(f"\n[INFO] Checking if {package} is installed...")
    result = subprocess.run(f"dpkg -l | grep -w {package}", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[SKIP] {package} is already installed.")
        return True
    print(f"[INSTALL] {package} is not installed.")

    return False

def check_and_kill_ports():
    """Checks if required Kubernetes ports are available and kills any processes using them."""
    required_ports = [6443, 2379, 2380, 10250, 10259, 10257]
    max_retries = 3
    
    for port in required_ports:
        for attempt in range(1, max_retries + 1):
            result = subprocess.run(f"sudo lsof -i :{port}", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[WARNING] Port {port} is in use. Attempting to free it (Attempt {attempt}/{max_retries})...")
                lines = result.stdout.split('\n')
                for line in lines[1:]:  # Skip header
                    parts = line.split()
                    if len(parts) > 1:
                        pid = parts[1]
                        run_command(f"sudo kill -9 {pid}", f"Killing process {pid} using port {port}")
                time.sleep(2)  # Wait before rechecking
            else:
                print(f"[INFO] Port {port} is available.")
                break
        else:
            print(f"[ERROR] Port {port} is still in use after {max_retries} attempts. Manual intervention required.")

def setup_ips():
    print("[INFO] setting up ip's for kubernetes")
    run_command("chmod +x kube_ip.sh && ./kube_ip.sh", "Setting up Kube-VIP IP configuration")

def check_and_load_netfilter():
    """Ensures br_netfilter is loaded and persists sysctl settings without duplication."""
    
    print("\n=== Checking Netfilter Module ===")

    # Check if br_netfilter is loaded
    result = subprocess.run("lsmod | grep -q br_netfilter", shell=True)
    
    if result.returncode == 0:
        print("[INFO] br_netfilter module is already loaded.")
    else:
        print("[WARNING] br_netfilter module is not loaded. Loading it now...")
        run_command("sudo modprobe br_netfilter", "Loading br_netfilter module")

        # Verify that the module was loaded
        result = subprocess.run("lsmod | grep -q br_netfilter", shell=True)
        if result.returncode == 0:
            print("[SUCCESS] br_netfilter module successfully loaded.")
        else:
            print("[ERROR] Failed to load br_netfilter module.")
            return
    
    print("\n=== Ensuring Persistent Netfilter Settings ===")

    # Remove any existing net.bridge entries to avoid duplicates
    run_command("sudo sed -i '/^net.bridge.bridge-nf-call-iptables/d' /etc/sysctl.conf", "Removing duplicate net.bridge.bridge-nf-call-iptables")
    run_command("sudo sed -i '/^net.bridge.bridge-nf-call-ip6tables/d' /etc/sysctl.conf", "Removing duplicate net.bridge.bridge-nf-call-ip6tables")

    # Check if the settings already exist before adding them
    check_iptables = subprocess.run("grep -q '^net.bridge.bridge-nf-call-iptables = 1' /etc/sysctl.conf", shell=True)
    check_ip6tables = subprocess.run("grep -q '^net.bridge.bridge-nf-call-ip6tables = 1' /etc/sysctl.conf", shell=True)

    if check_iptables.returncode != 0:
        run_command("echo 'net.bridge.bridge-nf-call-iptables = 1' | sudo tee -a /etc/sysctl.conf > /dev/null", "Adding net.bridge.bridge-nf-call-iptables")

    if check_ip6tables.returncode != 0:
        run_command("echo 'net.bridge.bridge-nf-call-ip6tables = 1' | sudo tee -a /etc/sysctl.conf > /dev/null", "Adding net.bridge.bridge-nf-call-ip6tables")

    # Ensure module is loaded on boot
    run_command("echo 'br_netfilter' | sudo tee /etc/modules-load.d/k8s.conf > /dev/null", "Persisting br_netfilter module")

    # Apply sysctl changes
    run_command("sudo sysctl --system", "Applying sysctl settings")




#not instantiated yet
# def ensure_hostname_in_hosts():
#     """Ensures the current hostname is present in /etc/hosts."""
#     hostname = cluster_n

#     try:
#         # Read the contents of /etc/hosts
#         with open("/etc/hosts", "r") as f:
#             lines = f.readlines()

#         # Check if the hostname already exists in /etc/hosts
#         for line in lines:
#             if hostname in line:
#                 print(f"[INFO] Hostname '{hostname}' is already present in /etc/hosts.")
#                 return

#         # Get the machine's primary IP address
#         ip_address = subprocess.getoutput("hostname -I | awk '{print $1}'").strip()

#         if not ip_address:
#             print("[ERROR] Could not determine the system's IP address.")
#             return

#         # Append the new hostname entry
#         new_entry = f"{ip_address} {hostname}\n"
#         with open("/etc/hosts", "a") as f:
#             f.write(new_entry)

#         print(f"[SUCCESS] Added '{hostname}' to /etc/hosts with IP: {ip_address}")

#     except Exception as e:
#         print(f"[ERROR] Failed to modify /etc/hosts: {e}")


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



def is_swap_disabled():
    """Checks if swap is disabled and forces it off if still enabled, retrying up to 3 times."""
    print("\n[INFO] Verifying that swap is disabled...")

    # Run the command using subprocess and capture the output
    result = subprocess.run("swapon --show", shell=True, capture_output=True, text=True)

    if result.stdout.strip():  # If there's output, swap is still enabled
        print("[ERROR] Swap is still enabled! Attempting to disable it...")

        for attempt in range(1, 4):  # Try up to 3 times
            print(f"[INFO] Attempt {attempt} to disable swap...")
            
            # Disable swap temporarily
            subprocess.run("sudo swapoff -a", shell=True, check=False)
            
            # Permanently disable swap in /etc/fstab
            subprocess.run("sudo sed -i '/swap/d' /etc/fstab", shell=True, check=False)

            # Wait 2 seconds before rechecking
            time.sleep(2)

            # Verify if swap is disabled
            result = subprocess.run("swapon --show", shell=True, capture_output=True, text=True)
            if not result.stdout.strip():  # If no output, swap is disabled
                print(f"[SUCCESS] Swap successfully disabled on attempt {attempt}.")
                return

        # If all attempts fail, exit with an error
        print("[FATAL ERROR] Swap could not be disabled after 3 attempts. Please disable it manually and rerun the script.")
        sys.exit(1)
    else:
        print("[SUCCESS] Swap is already disabled.")



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
    run_command("sudo systemctl enable --now cri-docker.socket", "Starting and enabling cri-dockerd socket")

def install_kubernetes():
    """Installs Kubernetes components (kubelet, kubeadm, kubectl)."""
    is_swap_disabled()
    kube_packages = ["kubelet", "kubeadm", "kubectl"]
    if all(check_installed(pkg) for pkg in kube_packages):
        return
    print("[INFO] installing kubernetes")
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
    
    # IF YOUR REQUIRE ISNTALLING PODS ON THE MASTER NODE, PLEASE UNCOMMENT THE FOLLOWING LINES
    #print ('[INFO] Clearing the Taint')
    #run_command("kubectl taint nodes --all node-role.kubernetes.io/control-plane-", "Removing control-plane taint")


def setup_kube_vip_loadbalancer():
    """Deploys Kube-VIP LoadBalancer after cluster setup."""
    run_command("kubectl apply -f https://kube-vip.io/manifests/rbac.yaml", "Applying Kube-VIP RBAC")
    run_command("kubectl apply -f https://raw.githubusercontent.com/kube-vip/kube-vip-cloud-provider/main/manifest/kube-vip-cloud-controller.yaml", "Applying Kube-VIP Cloud Controller")
    run_command("kubectl create configmap --namespace kube-system kubevip --from-literal range-global=172.18.1.10-172.18.1.250", "Creating Kube-VIP ConfigMap")

    # Try running kube-vip script without sudo first
    try:
        run_command("./kube_vip_dae.sh", "Deploying Kube-VIP Daemonset")
    except subprocess.CalledProcessError as e:
        if "permission denied" in str(e).lower() or "operation not permitted" in str(e).lower():
            print("[WARNING] Permission error detected, retrying with sudo...")
            run_command("sudo ./kube_vip_dae.sh", "Deploying Kube-VIP Daemonset (sudo)")
        else:
            raise  # If the error is not permission-related, re-raise it



def main():
    """Main function to set up Kubernetes."""
    print("\n=== Kubernetes Cluster Setup Script ===\n")
    install_dependencies()
    setup_ips()
    check_and_load_netfilter()
    check_and_kill_ports()
    install_docker()
    install_cri_dockerd()
    install_kubernetes()
    initialize_cluster()
    setup_kube_vip_loadbalancer()
    print("\n[INFO] Kubernetes cluster setup complete!")
    print("[INFO] Run 'kubectl get nodes' to verify cluster status.")

if __name__ == "__main__":
    main()
