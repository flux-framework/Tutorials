#!/bin/bash

cd /home/ubuntu/usernetes

# Clean up state from any previous run. "make down-v" is not reliable here,
# so remove the containers, network, and volumes directly.
docker rm -f $(docker ps -aq --filter "name=usernetes") 2>/dev/null
docker network rm usernetes_default 2>/dev/null
docker volume rm usernetes_node-var usernetes_node-opt usernetes_node-etc 2>/dev/null

# The spawner starts this build in the background at boot; the lock makes us
# wait if it is still going, and otherwise this is an instant cache hit (the
# usernetes checkout is pinned, so the image is deterministic - no need to
# rmi and rebuild from scratch). The compose file pins "image: usernetes_node"
# with no build section, so "make up" below will not build a second time.
flock /tmp/usernetes-build.lock docker build -t usernetes_node .
cd -

make -C /home/ubuntu/usernetes up
sleep 10
make -C /home/ubuntu/usernetes kubeadm-init
sleep 10
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

# This ensures the node is ingress ready
kubectl label node u7s-$(hostname) ingress-ready=true

echo "Cluster is ready. 🤓"
# echo "export KUBECONFIG=/home/ubuntu/usernetes/kubeconfig" 
