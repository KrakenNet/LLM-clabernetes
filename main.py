import os
import shutil
import subprocess
import sys

TOOLKIT_DIR = "/usr/local/bin"
SCRIPTS = {
    "kkk.sh": "kkk",
    "kube_up.py": "kube_up.py",
    "kube_down.py": "kube_down.py",
    "claber_up.py": "claber_up.py"
}

def check_permissions():
    """Checks if the script has permission to write to /usr/local/bin."""
    if not os.access(TOOLKIT_DIR, os.W_OK):
        print(f"\n[ERROR] Permission denied: Cannot write to {TOOLKIT_DIR}")
        print("[INFO] Try running this script with 'sudo'.")
        sys.exit(1)

def refresh_shell():
    """Refreshes the shell to recognize the new command."""
    shell = os.environ.get("SHELL", "")
    try:
        if "bash" in shell:
            subprocess.run(["bash", "-c", "source ~/.bashrc"], check=True)
        elif "zsh" in shell:
            subprocess.run(["zsh", "-c", "source ~/.zshrc"], check=True)
        else:
            print("[WARNING] Unknown shell. Please restart your terminal for changes to take effect.")
    except subprocess.CalledProcessError:
        print("[WARNING] Failed to refresh shell. Restart your terminal for changes to take effect.")

def install_koolkit():
    """Installs the k8s troubleshooting script and required Python scripts system-wide."""
    print("\n=== Installing Kubernetes KubeKit ===\n")

    # Check for necessary permissions
    check_permissions()

    for src_name, dest_name in SCRIPTS.items():
        src_path = os.path.join(os.getcwd(), src_name)
        dest_path = os.path.join(TOOLKIT_DIR, dest_name)

        # Check if the script already exists
        if os.path.exists(dest_path):
            print(f"[INFO] {dest_name} already exists in {TOOLKIT_DIR}. Skipping...")
        else:
            if os.path.exists(src_path):
                try:
                    print(f"[INFO] Copying {src_name} to {TOOLKIT_DIR}...")
                    shutil.copy(src_path, dest_path)

                    # Set execute permissions if it's `kkk`
                    if dest_name == "kkk":
                        os.chmod(dest_path, 0o755)
                        print("[INFO] Set execute permissions for 'kkk'.")

                except Exception as e:
                    print(f"[ERROR] Failed to copy {src_name}: {e}")
            else:
                print(f"[WARNING] {src_name} not found in the current directory!")

    # Refresh shell
    refresh_shell()
    print("\n[SUCCESS] Kubernetes KubeKit installed! Run 'kkk' to use it.")

    # Refresh shell to recognize the new command
    try:
        subprocess.run(["hash", "-r"], check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("[WARNING] Shell refresh skipped. Restart terminal if needed.")

def run_kube_up():
    """Runs kube_up.py and if successful, runs claber_up.py."""
    kube_up_path = os.path.join(TOOLKIT_DIR, "kube_up.py")
    claber_up_path = os.path.join(TOOLKIT_DIR, "claber_up.py")

    if not os.path.exists(kube_up_path):
        print(f"[ERROR] {kube_up_path} not found! Cannot start Kubernetes.")
        return

    print("\n[INFO] Running kube_up.py...\n")
    kube_up_process = subprocess.run(["python3", kube_up_path], capture_output=True, text=True)

    if kube_up_process.returncode == 0:
        print("\n[SUCCESS] kube_up.py completed successfully!")
        
        if os.path.exists(claber_up_path):
            print("\n[INFO] Running claber_up.py...\n")
            claber_up_process = subprocess.run(["python3", claber_up_path], capture_output=True, text=True)

            if claber_up_process.returncode == 0:
                print("\n[SUCCESS] claber_up.py completed successfully!")
            else:
                print(f"\n[ERROR] claber_up.py failed with error:\n{claber_up_process.stderr}")
        else:
            print(f"\n[WARNING] {claber_up_path} not found. Skipping claber_up.py.")
    else:
        print(f"\n[ERROR] kube_up.py failed with error:\n{kube_up_process.stderr}")

def main():
    """Main function that handles installation and setup."""
    print("\n=== Installing Kubernetes KubeKit ===\n")
    install_koolkit()
    print("\n=== Installing Kubernetes and Calbernetes ===\n")
    run_kube_up()

if __name__ == "__main__":
    main()
