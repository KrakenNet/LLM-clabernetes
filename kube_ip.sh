#!/bin/bash

# Allow incoming connections on Kubernetes API Server (change CIDR if needed)
sudo iptables -A INPUT -p tcp --dport 6443 -s 192.168.0.0/16 -j ACCEPT

# Allow all traffic from and to Kubernetes pods (Flannel/Calico)
sudo iptables -A INPUT -s 10.244.0.0/16 -j ACCEPT
sudo iptables -A INPUT -d 10.244.0.0/16 -j ACCEPT
sudo iptables -A FORWARD -s 10.244.0.0/16 -j ACCEPT
sudo iptables -A FORWARD -d 10.244.0.0/16 -j ACCEPT

# Allow node-to-node communication
sudo iptables -A INPUT -s 192.168.0.0/16 -j ACCEPT
sudo iptables -A FORWARD -s 192.168.0.0/16 -j ACCEPT
sudo iptables -A FORWARD -d 192.168.0.0/16 -j ACCEPT

# Ensure Flannel (VXLAN) encapsulated traffic is allowed
sudo iptables -A INPUT -p udp --dport 4789 -j ACCEPT

# Ensure Calico (IP-in-IP) encapsulated traffic is allowed
sudo iptables -A INPUT -p 4 -s 10.244.0.0/16 -j ACCEPT

# Set default policies (only do this once after ensuring necessary rules are set)
sudo iptables -P INPUT ACCEPT
sudo iptables -P FORWARD ACCEPT

# Save the rules to persist after reboot
sudo iptables-save | sudo tee /etc/iptables.rules > /dev/null

echo "✅ Kubernetes iptables rules applied successfully!"
