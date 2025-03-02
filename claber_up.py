import os
import subprocess
import sys
from local import run_command


namespace = ''

# def run_piped_command(cmd1, cmd2, description="Executing piped command", exit_on_fail=True):
#     """Runs two shell commands, piping the output of the first into the second."""
#     print(f"\n[INFO] {description}...")
#     try:
#         # Start the first process (clabverter)
#         process1 = subprocess.Popen(cmd1.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

#         # Start the second process (kubectl apply) and pipe the output from process1
#         process2 = subprocess.Popen(cmd2.split(), stdin=process1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
#         # Close process1 stdout so process2 knows input is finished
#         process1.stdout.close()
        
#         # Capture output
#         stdout, stderr = process2.communicate()

#         print(stdout, end="")
#         if stderr:
#             print(stderr, end="")

#         if process2.returncode != 0:
#             raise subprocess.CalledProcessError(process2.returncode, cmd2)

#         print(f"[SUCCESS] {description}")
#     except subprocess.CalledProcessError as e:
#         print(f"[ERROR] {description} failed.")
#         print(f"Error Output:\n{e}")
#         if exit_on_fail:
#             sys.exit(1)




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

# def convert_topology(topology_file):
#     """Converts an existing Containerlab topology to Clabernetes-compatible format."""
#     run_command(f"clabverter -t {topology_file}", "Converting topology with Clabverter")

def convert_deploy(topology_file):
    run_command("./deploy_clab.sh", "Converting and Deploying the Lab")


# def deploy_custom_lab(manifest_file):
#     """Deploys the custom lab into the Kubernetes cluster."""
#     run_command(f"kubectl apply -f {manifest_file}", "Deploying custom lab")

def verify_deployment():
    """Verifies that Clabernetes and the lab are running."""
    run_command("kubectl get pods -n c9s", "Checking Clabernetes pods")
    run_command("kubectl get svc -n c9s", "Checking Clabernetes services")

def main():
    """Main function to deploy Clabernetes and a custom lab."""
    print("\n=== Clabernetes Setup Script ===\n")
    install_clabernetes()
    install_clabverter()
    topology_file = "ground.clab.yml"
    manifest_file = "generated-manifest.yml"
    # convert_topology(topology_file)
    # deploy_custom_lab(manifest_file)
    convert_deploy(topology_file)
    verify_deployment()
    print("\n[INFO] Clabernetes setup complete!")
    print("[INFO] Run 'kubectl get pods -n c9s' to verify deployment.")

if __name__ == "__main__":
    main()
