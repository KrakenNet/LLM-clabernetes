import os
import shutil
import subprocess




import os
import shutil
import subprocess

def install_koolkit():
    """Installs the k8s troubleshooting script as a system-wide command."""
    script_name = "kkk.sh"
    target_path = "/usr/local/bin/kkk"

    # Check if the script is already installed
    if os.path.exists(target_path) and os.access(target_path, os.X_OK):
        print("[INFO] Kubernetes KubeKit is already installed. Run 'kkk' to use it.")
        return

    # Check if the script exists in the current directory
    if not os.path.exists(script_name):
        print(f"[ERROR] {script_name} not found in the current directory! Please ensure it exists.")
        return
    
    try:
        print("[INFO] Installing Kubernetes KubeKit...")

        # Copy script to /usr/local/bin
        shutil.copy(script_name, target_path)
        print("[INFO] Copied script to /usr/local/bin.")

        # Set execute permissions
        os.chmod(target_path, 0o755)
        print("[INFO] Set execute permissions.")

        # Refresh shell to recognize the new command
        subprocess.run(["hash", "-r"], check=True)
        print("[SUCCESS] 'Kubernetes KubKit' is now installed! Run 'kkk' from anywhere.")

    except Exception as e:
        print(f"[ERROR] Installation failed: {e}")



def main():
    """Main function that handles installation and setup."""
    print("\n=== Installing Kubernetes KubeKit ===\n")
    install_koolkit()

if __name__ == "__main__":
    main()
