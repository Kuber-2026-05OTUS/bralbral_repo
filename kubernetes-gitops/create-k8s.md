# Установка Kubernetes-кластера через kubeadm

Схема кластера:

| Узел | Роль | IP-адрес |
|---|---|---|
| `master` | control plane | `192.168.122.101` |
| `worker1` | worker | `192.168.122.102` |
| `worker2` | worker | `192.168.122.103` |

Используем Kubernetes 1.36, containerd и Flannel. Сеть узлов —
`192.168.122.0/24`, сеть Pod — `10.244.0.0/16`.

## 1. Подключение к виртуальным машинам

```bash
ssh ubuntu@192.168.122.101  # master
ssh ubuntu@192.168.122.102  # worker1
ssh ubuntu@192.168.122.103  # worker2
```

Если имя пользователя отличается, можно подключиться через uvtool:

```bash
uvt-kvm ssh master
uvt-kvm ssh worker1
uvt-kvm ssh worker2
```

## 2. Подготовка всех узлов

Следующие команды нужно выполнить на `master`, `worker1` и `worker2`.

Отключить swap:

```bash
sudo swapoff -a
sudo sed -i '/[[:space:]]swap[[:space:]]/s/^/#/' /etc/fstab
```

Загрузить модули ядра:

```bash
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter
```

Настроить сетевые параметры ядра:

```bash
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
EOF

sudo sysctl --system
```

Проверить forwarding:

```bash
sysctl net.ipv4.ip_forward
```

Ожидаемое значение — `1`.

## 3. Установка containerd на всех узлах

```bash
sudo apt-get update
sudo apt-get install -y containerd

sudo mkdir -p /etc/containerd
containerd config default |
  sudo tee /etc/containerd/config.toml >/dev/null

sudo sed -i \
  's/SystemdCgroup = false/SystemdCgroup = true/' \
  /etc/containerd/config.toml

sudo systemctl restart containerd
sudo systemctl enable containerd
```

Проверить состояние containerd:

```bash
systemctl is-active containerd
```

Команда должна вернуть `active`.

## 4. Установка Kubernetes на всех узлах

```bash
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gpg

sudo mkdir -p -m 755 /etc/apt/keyrings

curl -fsSL \
  https://pkgs.k8s.io/core:/stable:/v1.36/deb/Release.key |
  sudo gpg --dearmor \
    -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

echo \
  'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.36/deb/ /' |
  sudo tee /etc/apt/sources.list.d/kubernetes.list

sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
sudo systemctl enable kubelet
```

Проверить версии:

```bash
kubeadm version
kubelet --version
kubectl version --client
```

До инициализации кластера kubelet может постоянно перезапускаться. Это
нормальное поведение: kubelet ожидает конфигурацию от kubeadm.

## 5. Инициализация control plane

Следующие команды выполняются только на `master`.

```bash
sudo kubeadm init \
  --apiserver-advertise-address=192.168.122.101 \
  --control-plane-endpoint=192.168.122.101:6443 \
  --pod-network-cidr=10.244.0.0/16
```

После завершения сохранить выведенную команду `kubeadm join`. Она понадобится
для подключения worker-узлов.

Настроить kubectl для текущего пользователя:

```bash
mkdir -p "$HOME/.kube"
sudo cp /etc/kubernetes/admin.conf "$HOME/.kube/config"
sudo chown "$(id -u):$(id -g)" "$HOME/.kube/config"
```

Проверить control plane:

```bash
kubectl get nodes
```

До установки сетевого плагина узел будет иметь состояние `NotReady`.

## 6. Установка Flannel

Выполнить на `master`:

```bash
kubectl apply -f \
  https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
```

Следить за запуском системных Pod:

```bash
kubectl get pods -A -w
```

Для выхода из режима наблюдения нажать `Ctrl+C`. CoreDNS и Flannel должны
перейти в состояние `Running`.

## 7. Подключение worker-узлов

После `kubeadm init` будет выведена команда примерно такого вида:

```bash
sudo kubeadm join 192.168.122.101:6443 \
  --token TOKEN \
  --discovery-token-ca-cert-hash sha256:HASH
```

Выполнить полученную команду сначала на `worker1`, затем на `worker2`.

Если команда была потеряна или срок действия токена закончился, создать новую
на `master`:

```bash
kubeadm token create --print-join-command
```

## 8. Проверка кластера

Выполнить на `master`:

```bash
kubectl get nodes -o wide
kubectl get pods -A
```

Все три узла должны перейти в состояние `Ready`:

```text
NAME      STATUS   ROLES           AGE   VERSION
master    Ready    control-plane   ...   ...
worker1   Ready    <none>          ...   ...
worker2   Ready    <none>          ...   ...
```

Дополнительная проверка состояния компонентов:

```bash
kubectl cluster-info
kubectl get pods -n kube-system -o wide
```