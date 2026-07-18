
# Kubernetes cluster setup

## All nodes

```bash
swapoff -a
sed -i '/ swap / s/^/#/' /etc/fstab

cat <<EOF | tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

modprobe overlay
modprobe br_netfilter

cat <<EOF | tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

sysctl --system

apt update
apt install -y containerd apt-transport-https ca-certificates curl gpg

mkdir -p /etc/containerd
containerd config default > /etc/containerd/config.toml

sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
sed -i 's|sandbox_image = "registry.k8s.io/pause:.*"|sandbox_image = "registry.k8s.io/pause:3.10.2"|' /etc/containerd/config.toml

systemctl restart containerd
systemctl enable containerd

mkdir -p /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.36/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes.gpg

echo "deb [signed-by=/etc/apt/keyrings/kubernetes.gpg] https://pkgs.k8s.io/core:/stable:/v1.36/deb/ /" > /etc/apt/sources.list.d/kubernetes.list

apt update
apt install -y kubelet kubeadm kubectl
apt-mark hold kubelet kubeadm kubectl

cat <<EOF | tee /etc/crictl.yaml
runtime-endpoint: unix:///run/containerd/containerd.sock
image-endpoint: unix:///run/containerd/containerd.sock
timeout: 10
EOF
```

## Master

```bash
kubeadm init --pod-network-cidr=10.244.0.0/16

mkdir -p $HOME/.kube
cp /etc/kubernetes/admin.conf $HOME/.kube/config

kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
```

Create a join command for worker nodes:

```bash
kubeadm token create --print-join-command
```

Example output:

```bash
kubeadm join 192.168.122.201:6443 --token ealsoo.cemkxjseshcmqfri --discovery-token-ca-cert-hash sha256:68c1a11a02e70bd179a9773609ba894ef01017ff84880cb7dbe8d836fee460e1
```

## Worker

Run the generated `kubeadm join` command on each worker:

```bash
kubeadm join 192.168.122.201:6443 --token ealsoo.cemkxjseshcmqfri --discovery-token-ca-cert-hash sha256:68c1a11a02e70bd179a9773609ba894ef01017ff84880cb7dbe8d836fee460e1
```

## Check cluster status

```bash
kubectl get nodes -o wide
kubectl get pods -A
```

## StorageClass

CSI means Container Storage Interface.

```bash
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/master/deploy/local-path-storage.yaml
```

### Check

```bash
kubectl get storageclass
```

### Set as default

```bash
kubectl patch storageclass local-path \
  -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```
