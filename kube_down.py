import os
import subprocess
import sys
from local import run_command


def kubeadm_reset():
    """Resets the Kubernetes cluster."""
    print("Resetting kubeadm...")
    run_command("sudo kubeadm reset --cri-socket unix:///var/run/cri-dockerd.sock -f", "Resetting kubeadm")

def reset_kubeconfig():
    """Removes Kubernetes configuration files."""
    print("Resetting kubeconfig...")
    run_command("rm -rf $HOME/.kube", "Removing kubeconfig directory")

def remove_kubernetes_files():
    """Deletes all leftover Kubernetes files and directories."""
    print("Removing Kubernetes files...")
    run_command("sudo rm -rf /etc/kubernetes /var/lib/kubelet /var/lib/etcd", "Removing Kubernetes system files")
    run_command("sudo rm -rf /etc/cni/net.d", "Removing CNI configuration")

def clean_kubernetes_iptables():
    """Remove only Kubernetes-related iptables rules without affecting the system firewall."""
    print("[INFO] Cleaning Kubernetes-related iptables rules...")

    # Delete kube-proxy and Kubernetes NAT rules
    run_command("sudo iptables -t nat -D PREROUTING -d 10.96.0.0/12 -j KUBE-SERVICES", "Removing Kube-Proxy PREROUTING")
    run_command("sudo iptables -t nat -D OUTPUT -d 10.96.0.0/12 -j KUBE-SERVICES", "Removing Kube-Proxy OUTPUT")
    
    # Delete Flannel forwarding rules (if exist)
    run_command("sudo iptables -D FORWARD -s 10.244.0.0/16 -j ACCEPT", "Removing Flannel Forwarding (src)")
    run_command("sudo iptables -D FORWARD -d 10.244.0.0/16 -j ACCEPT", "Removing Flannel Forwarding (dst)")

    # Delete kube-service and kube-masq rules
    run_command("sudo iptables -t nat -F KUBE-SERVICES", "Flushing KUBE-SERVICES")
    run_command("sudo iptables -t nat -X KUBE-SERVICES", "Deleting KUBE-SERVICES chain")
    run_command("sudo iptables -t nat -F KUBE-MARK-MASQ", "Flushing KUBE-MARK-MASQ")
    run_command("sudo iptables -t nat -X KUBE-MARK-MASQ", "Deleting KUBE-MARK-MASQ chain")

    # Remove any Kubernetes IP masquerade rules
    run_command("sudo iptables -t nat -D POSTROUTING -s 10.244.0.0/16 ! -d 10.244.0.0/16 -j MASQUERADE", "Removing Flannel NAT masquerade")
    
    print("[INFO] Kubernetes iptables rules cleaned up.")

def clean_kubernetes_routes():
    """Remove only Kubernetes-related routes to prevent conflicts on restart."""
    print("[INFO] Cleaning up Kubernetes-specific routes...")

    # Remove Kubernetes service and pod network routes
    run_command("sudo ip route del 10.96.0.0/12", "Removing Kubernetes service CIDR route")
    run_command("sudo ip route del 10.244.0.0/16", "Removing Flannel pod network route")

    print("[INFO] Kubernetes routes cleaned up.")


def main():
    """Main function to reset Kubernetes and clean up system."""
    print("\n=== Kubernetes Reset Script ===\n")
    kubeadm_reset()
    reset_kubeconfig()
    remove_kubernetes_files()
    clean_kubernetes_iptables()
    clean_kubernetes_routes()
    print("\n[INFO] Kubernetes cluster has been completely reset.")
    print("[INFO] You can now run your Kubernetes setup script to start fresh.")

if __name__ == "__main__":
    main()