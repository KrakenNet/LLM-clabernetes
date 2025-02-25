import os
import shutil
import subprocess

def install_koolkit():
    """Installs the k8s troubleshooting script as a system-wide command."""
    script_name = "kkk.sh"
    target_path = "/usr/local/bin/kkk"

    # Check if the script exists in the current directory
    if not os.path.exists(script_name):
        print(f"[ERROR] {script_name} not found in the current directory!")
        return
    
    try:
        print("[INFO] Copying script to /usr/local/bin...")
        shutil.copy(script_name, target_path)

        print("[INFO] Setting execute permissions...")
        os.chmod(target_path, 0o755)  # rwxr-xr-x

        print("[INFO] Refreshing shell to recognize the command...")
        subprocess.run(["hash", "-r"], check=True)

        print("[SUCCESS] 'kubernetes KubeKit' is now installed! Run 'kkk' from anywhere.")

    except Exception as e:
        print(f"[ERROR] Installation failed: {e}")

def main():
    """Main function that can be expanded for additional setup steps."""
    print("\n=== Installing Kubernetes Koolkit ===\n")
    install_koolkit()

if __name__ == "__main__":
    main()
