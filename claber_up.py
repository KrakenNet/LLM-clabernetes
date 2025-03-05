import os
import subprocess
import sys
from local import run_command

namespace = ''

def check_helm():
    """Checks if Helm is installed, and installs it if not found."""
    try:
        subprocess.run(["helm", "version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("[INFO] Helm is already installed.")
    except subprocess.CalledProcessError:
        print("[WARNING] Helm is not installed. Installing now...")
        install_helm()

def install_helm():
    """Installs Helm based on the operating system."""
    try:
        if sys.platform.startswith("linux"):
            run_command("curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash", 
                        "Installing Helm on Linux")
        elif sys.platform.startswith("darwin"):
            run_command("brew install helm", "Installing Helm on macOS using Homebrew")
        elif sys.platform.startswith("win"):
            run_command("choco install kubernetes-helm", "Installing Helm on Windows using Chocolatey")
        else:
            print("[ERROR] Unsupported OS for automatic Helm installation. Install Helm manually.")
            sys.exit(1)
        
        print("[SUCCESS] Helm installed successfully.")
    except Exception as e:
        print(f"[ERROR] Helm installation failed: {e}")
        sys.exit(1)

def install_clabernetes():
    """Installs Clabernetes into the Kubernetes cluster."""
    run_command("helm upgrade --install --create-namespace --namespace c9s clabernetes oci://ghcr.io/srl-labs/clabernetes/clabernetes", 
                "Installing Clabernetes via Helm")

def install_un_s_images():
    """Set up the UnS images in the Kubernetes cluster."""
    run_command("python3 setup_images.py", "Running setup_images.py to install local images")

def install_clabverter():
    """Sets up Clabverter for converting topologies."""
    run_command("alias clabverter='sudo docker run --user $(id -u) -v $(pwd):/clabernetes/work --rm ghcr.io/srl-labs/clabernetes/clabverter'", 
                "Setting up Clabverter alias")

def convert_deploy(topology_file):
    run_command("./deploy_clab.sh", "Converting and Deploying the Lab")

def verify_deployment():
    """Verifies that Clabernetes and the lab are running."""
    run_command("kubectl get pods -n c9s", "Checking Clabernetes pods")
    run_command("kubectl get svc -n c9s", "Checking Clabernetes services")

def main():
    """Main function to deploy Clabernetes and a custom lab."""
    print("\n=== Clabernetes Setup Script ===\n")
    check_helm()  # Ensure Helm is installed before proceeding
    install_clabernetes()
    install_clabverter()
    
    topology_file = "ground.clab.yml"
    convert_deploy(topology_file)
    verify_deployment()
    
    print("\n[INFO] Clabernetes setup complete!")
    print("[INFO] Run 'kubectl get pods -n c9s' to verify deployment.")

if __name__ == "__main__":
    main()
