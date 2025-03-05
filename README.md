# LLM-Clabernetes

## Overview
LLM-Clabernetes is an automated Kubernetes cluster setup and management tool that provides a streamlined way to deploy a master node, manage networking, and join leaf nodes. The toolkit (`kkk`) simplifies interactions with the cluster.

## Getting Started
### Installation
1. **Clone the repository**
   ```sh
   git clone https://github.com/KrakenNet/LLM-clabernetes.git
   cd LLM-clabernetes
   ```

2. **Run `main.py` to install the required components**
   ```sh
   python3 main.py
   ```
   This will install dependencies, configure Kubernetes, and deploy the cluster.

### Toolkit Usage
The toolkit (`kkk`) provides convenient commands for managing the cluster. After running `main.py`, use the following commands:

- **Start the master node:**
  ```sh
  kkk up
  ```
- **Tear down the entire cluster:**
  ```sh
  kkk down
  ```
- **Set up Clabernetes (using a topology file):**
  ```sh
  kkk clab
  ```
- **Set up leaf nodes (from `leaf_nodes.yaml`):**
  ```sh
  kkk leaf
  ```
- **List available commands:**
  ```sh
  kkk --help
  ```

### Leaf Nodes Setup
Leaf nodes are configured using a YAML file.
- The file **`example.yaml`** serves as a template.
- Create `leaf_nodes.yaml` and populate it with the IPs, usernames, and passwords of the leaf nodes.

Example format for `leaf_nodes.yaml`:
```yaml
nodes:
  - ip: 192.168.1.120
    user: ubuntu
    password: mypassword
  - ip: 192.168.1.130
    user: ubuntu
    password: mypassword
  - ip: 192.168.1.140
    user: ubuntu
    password: mypassword
```

### Ports Requirement
Ensure the following ports are available **before** running `main.py`:
- 6443 (Kubernetes API Server)
- 2379-2380 (etcd)
- 10250, 10259, 10257 (Kubernetes components)

The toolkit will attempt to **kill any processes occupying these ports**.

### Running Pods on the Master Node
By default, Kubernetes prevents scheduling pods on the master node. If you need to allow this, **uncomment** the following line in `kube_up.py`:
```python
# run_command("kubectl taint nodes --all node-role.kubernetes.io/control-plane-", "Removing control-plane taint")
```

## Troubleshooting
If you encounter networking issues, use the toolkit commands:
- **Check networking:** `kkk net`
- **Check kube-proxy:** `kkk proxy`
- **Reset iptables:** `kkk iptables`
- **Restart kube-proxy:** `kkk restart`
- **Check CoreDNS:** `kkk dns`
- **Check Flannel:** `kkk flannel`
- **Open a debug pod:** `kkk debug`

## Contributions
Contributions are welcome! Submit a pull request to improve functionality or fix issues.

## License
LLM-Clabernetes is open-source and available under the MIT License.

