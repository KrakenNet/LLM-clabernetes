#!/bin/bash

# Function to check if a rule exists before adding it
add_rule_if_not_exists() {
    local rule="$1"
    if sudo iptables-save | grep --quiet -- "$rule"; then
        echo "✅ Rule already exists: $rule"
    else
        echo "➕ Adding rule: $rule"
        sudo iptables $rule
    fi
}

echo "🚀 Applying Kubernetes iptables rules..."

# Allow incoming connections on Kubernetes API Server (change CIDR if needed)
add_rule_if_not_exists "-A INPUT -p tcp --dport 6443 -s 192.168.0.0/16 -j ACCEPT"

# Allow all traffic from and to Kubernetes pods (Flannel/Calico)
add_rule_if_not_exists "-A INPUT -s 10.244.0.0/16 -j ACCEPT"
add_rule_if_not_exists "-A INPUT -d 10.244.0.0/16 -j ACCEPT"
add_rule_if_not_exists "-A FORWARD -s 10.244.0.0/16 -j ACCEPT"
add_rule_if_not_exists "-A FORWARD -d 10.244.0.0/16 -j ACCEPT"

# Allow node-to-node communication
add_rule_if_not_exists "-A INPUT -s 192.168.0.0/16 -j ACCEPT"
add_rule_if_not_exists "-A FORWARD -s 192.168.0.0/16 -j ACCEPT"
add_rule_if_not_exists "-A FORWARD -d 192.168.0.0/16 -j ACCEPT"

# Ensure Flannel (VXLAN) encapsulated traffic is allowed
add_rule_if_not_exists "-A INPUT -p udp --dport 4789 -j ACCEPT"

# Ensure Calico (IP-in-IP) encapsulated traffic is allowed
add_rule_if_not_exists "-A INPUT -p 4 -s 10.244.0.0/16 -j ACCEPT"

# Set default policies (only do this once after ensuring necessary rules are set)
add_rule_if_not_exists "-P INPUT ACCEPT"
add_rule_if_not_exists "-P FORWARD ACCEPT"

# Save the rules to persist after reboot
sudo iptables-save | sudo tee /etc/iptables.rules > /dev/null

echo "✅ Kubernetes iptables rules applied successfully!"
