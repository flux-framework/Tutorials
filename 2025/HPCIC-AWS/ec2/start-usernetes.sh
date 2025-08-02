#!/bin/bash
make -C /home/ubuntu/usernetes up
make -C /home/ubuntu/usernetes kubeadm-init
make -C /home/ubuntu/usernetes install-flannel
make -C /home/ubuntu/usernetes kubeconfig
export KUBECONFIG=/home/ubuntu/usernetes/kubeconfig

# Untaint the control plane to schedule jobs, etc. on
echo " 🍑  Untainting control plane and labeling node"
control_plane_node=$(kubectl get nodes -l node-role.kubernetes.io/control-plane -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

# Ensure the user interacts with default kubeconfig
sudo cp /home/ubuntu/usernetes/kubeconfig /home/ubuntu/.kube/config

# Taint away!
kubectl taint node "${control_plane_node}" node-role.kubernetes.io/control-plane:NoSchedule- 
kubectl label node "${control_plane_node}" node.kubernetes.io/exclude-from-external-load-balancers-

echo "Cluster is ready. 🤓"
# echo "export KUBECONFIG=/home/ubuntu/usernetes/kubeconfig" 

