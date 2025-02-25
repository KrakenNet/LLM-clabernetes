import os
import shutil
import subprocess


TOOLKIT_DIR = "/usr/local/bin"
SCRIPTS = {
    "kkk.sh": "kkk",
    "kube_up.py": "kube_up.py",
    "kube_down.py": "kube_down.py"
}


def install_koolkit():
    """Installs the k8s troubleshooting script and required Python scripts system-wide."""
    
    print("\n=== Installing Kubernetes KubeKit ===\n")

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

    # Refresh shell to recognize the new command
    try:
        subprocess.run(["hash", "-r"], check=True)
        print("\n[SUCCESS] Kubernetes KubeKit installed! Run 'kkk' to use it.")
    except Exception as e:
        print(f"[ERROR] Failed to refresh shell: {e}")



def main():
    """Main function that handles installation and setup."""
    print("\n=== Installing Kubernetes KubeKit ===\n")
    install_koolkit()

if __name__ == "__main__":
    main()
