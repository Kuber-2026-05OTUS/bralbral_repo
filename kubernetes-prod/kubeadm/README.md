# Развёртывание и обновление Kubernetes: kubeadm и Kubespray

## Результат

Работа выполнена на локальной машине с Ubuntu 26.04.1 LTS.

На хосте установлено 16 ГБ оперативной памяти. Поэтому для лабораторного стенда
всем виртуальным машинам выделено по 2 ГБ RAM. Это вынужденное ограничение
локального стенда, а не рекомендуемый объём памяти для production-кластера.

На дату выполнения актуальная minor-версия Kubernetes - `1.37`. В соответствии
с заданием кластер первоначально развёрнут на версии на одну ниже - `1.36`, а
затем обновлён до `1.37`.

Фактически установленные версии:

- до обновления - `v1.36.5`;
- после обновления - `v1.37.1`;
- container runtime - `containerd 2.2.1`;
- CNI - Flannel `v0.28.9`;
- гостевая ОС - Ubuntu Server 24.04.5 LTS.

Итоговая конфигурация:

| VM | Роль | vCPU | RAM | Диск | IP |
|---|---|---:|---:|---:|---|
| `master` | control-plane | 2 | 2 ГБ | 20 ГБ | `192.168.122.101` |
| `worker1` | worker | 2 | 2 ГБ | 20 ГБ | `192.168.122.102` |
| `worker2` | worker | 2 | 2 ГБ | 20 ГБ | `192.168.122.103` |
| `worker3` | worker | 2 | 2 ГБ | 20 ГБ | `192.168.122.104` |

## 1. Подготовка хоста

### Версия хостовой ОС

Выполненная команда:

```bash
cat /etc/os-release
```

Полученный вывод:

```text
PRETTY_NAME="Ubuntu 26.04.1 LTS"
NAME="Ubuntu"
VERSION_ID="26.04"
VERSION="26.04.1 LTS (Resolute Raccoon)"
VERSION_CODENAME=resolute
ID=ubuntu
ID_LIKE=debian
UBUNTU_CODENAME=resolute
```

### Установка KVM, libvirt и uvtool

В Ubuntu 26.04 `qemu-kvm` является виртуальным пакетом, поэтому был явно выбран
пакет `qemu-system-x86`.

Выполненные команды:

```bash
sudo apt update
sudo apt install -y \
  qemu-system-x86 \
  libvirt-daemon-system \
  libvirt-clients \
  bridge-utils \
  uvtool \
  uvtool-libvirt

sudo systemctl enable --now libvirtd.service
sudo usermod -aG libvirt,kvm "$USER"
```

После повторного входа в пользовательскую сессию выполнена проверка:

```bash
dpkg-query -W -f='${binary:Package}\t${Status}\t${Version}\n' \
  qemu-system-x86 \
  libvirt-daemon \
  libvirt-daemon-system \
  libvirt-clients \
  uvtool \
  uvtool-libvirt

systemctl is-active libvirtd.service
```

Полученный вывод:

```text
libvirt-clients          install ok installed  12.0.0-1ubuntu5.5
libvirt-daemon           install ok installed  12.0.0-1ubuntu5.5
libvirt-daemon-system    install ok installed  12.0.0-1ubuntu5.5
qemu-system-x86          install ok installed  1:10.2.1+ds-1ubuntu3.2
uvtool                   install ok installed  0~git189-0ubuntu1
uvtool-libvirt           install ok installed  0~git189-0ubuntu1
active
```

### Загрузка образа Ubuntu Server 24.04

Выполненные команды:

```bash
test -f "$HOME/.ssh/id_ed25519.pub" || ssh-keygen -t ed25519
uvt-simplestreams-libvirt sync release=noble arch=amd64
uvt-simplestreams-libvirt query
```

Полученный вывод:

```text
release=noble arch=amd64 label=release (20260926)
```

## 2. Создание виртуальных машин

Каждая VM создана с 2 ГБ RAM:

```bash
for vm in master worker1 worker2 worker3; do
  uvt-kvm create \
    --memory 2048 \
    --cpu 2 \
    --disk 20 \
    --ssh-public-key-file "$HOME/.ssh/id_ed25519.pub" \
    "$vm" release=noble arch=amd64
done
```

Полученный вывод проверки:

```bash
virsh -c qemu:///system list --all
```

```text
 Id   Name      State
-------------------------
 1    master    running
 2    worker1   running
 3    worker2   running
 4    worker3   running
```

Фактическая итоговая конфигурация:

```bash
for vm in master worker1 worker2 worker3; do
  virsh -c qemu:///system dominfo "$vm" |
    awk -v vm="$vm" '/^State:|^CPU\(s\):|^Used memory:/{print vm, $0}'
done
```

```text
master State:          running
master CPU(s):         2
master Used memory:    2097152 KiB
worker1 State:          running
worker1 CPU(s):         2
worker1 Used memory:    2097152 KiB
worker2 State:          running
worker2 CPU(s):         2
worker2 Used memory:    2097152 KiB
worker3 State:          running
worker3 CPU(s):         2
worker3 Used memory:    2097152 KiB
```

## 3. Настройка адресов VM

В сети libvirt были созданы постоянные DHCP-привязки:

```bash
declare -A IPS=(
  [master]=192.168.122.101
  [worker1]=192.168.122.102
  [worker2]=192.168.122.103
  [worker3]=192.168.122.104
)

for vm in master worker1 worker2 worker3; do
  mac="$(
    virsh -c qemu:///system domiflist "$vm" |
      awk '$2 == "network" && $3 == "default" {print $5; exit}'
  )"

  virsh -c qemu:///system net-update default add-last ip-dhcp-host \
    "<host mac='$mac' name='$vm' ip='${IPS[$vm]}'/>" \
    --live --config
done
```

Проверка адресов:

```bash
virsh -c qemu:///system net-dhcp-leases default
```

Полученный вывод:

```text
MAC address         Protocol   IP address           Hostname
52:54:00:e9:ec:63   ipv4       192.168.122.101/24   master
52:54:00:28:8a:49   ipv4       192.168.122.102/24   worker1
52:54:00:06:99:13   ipv4       192.168.122.103/24   worker2
52:54:00:72:11:d1   ipv4       192.168.122.104/24   worker3
```

Проверка SSH:

```bash
for ip in 192.168.122.101 192.168.122.102 \
          192.168.122.103 192.168.122.104; do
  ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new \
    "ubuntu@$ip" 'hostname; ip -4 -br addr show scope global'
done
```

Полученный вывод:

```text
master
enp1s0  UP  192.168.122.101/24
worker1
enp1s0  UP  192.168.122.102/24
worker2
enp1s0  UP  192.168.122.103/24
worker3
enp1s0  UP  192.168.122.104/24
```

## 4. Подготовка всех узлов

Следующий блок выполнен на `master`, `worker1`, `worker2` и `worker3`:

```bash
sudo swapoff -a
sudo sed -ri '/[[:space:]]swap[[:space:]]/s/^#?/#/' /etc/fstab

cat <<'EOF' | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter

cat <<'EOF' | sudo tee /etc/sysctl.d/99-kubernetes-cri.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

sudo sysctl --system
```

Команда проверки на каждом узле:

```bash
swapon --show
sysctl net.bridge.bridge-nf-call-iptables
sysctl net.bridge.bridge-nf-call-ip6tables
sysctl net.ipv4.ip_forward
```

Полученный вывод на каждом узле:

```text
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
```

`swapon --show` не вывел ни одного активного swap-устройства.

## 5. Установка containerd на всех узлах

Выполненные команды:

```bash
sudo apt-get update
sudo apt-get install -y containerd

sudo mkdir -p /etc/containerd
containerd config default |
  sudo tee /etc/containerd/config.toml >/dev/null

sudo sed -i \
  's/SystemdCgroup = false/SystemdCgroup = true/' \
  /etc/containerd/config.toml

sudo systemctl enable --now containerd
sudo systemctl restart containerd
```

Команда проверки:

```bash
systemctl is-active containerd
grep 'SystemdCgroup = true' /etc/containerd/config.toml
containerd --version
```

Полученный вывод:

```text
active
            SystemdCgroup = true
containerd github.com/containerd/containerd/v2 2.2.1
```

## 6. Установка Kubernetes 1.36 на всех узлах

Выполненные команды:

```bash
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gpg
sudo install -m 0755 -d /etc/apt/keyrings

curl -fsSL \
  https://pkgs.k8s.io/core:/stable:/v1.36/deb/Release.key |
  sudo gpg --dearmor --yes \
    -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

echo \
  'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.36/deb/ /' |
  sudo tee /etc/apt/sources.list.d/kubernetes.list

sudo apt-get update

K8S_DEB_VERSION="$(
  apt-cache madison kubeadm |
    awk '$3 ~ /^1\.36\./ && version == "" {version=$3} END {print version}'
)"

sudo apt-get install -y \
  kubelet="$K8S_DEB_VERSION" \
  kubeadm="$K8S_DEB_VERSION" \
  kubectl="$K8S_DEB_VERSION"

sudo apt-mark hold kubelet kubeadm kubectl
sudo systemctl enable kubelet
```

Полученный вывод на узлах:

```text
INSTALLED master 1.36.5-1.1
v1.36.5
Kubernetes v1.36.5
active

INSTALLED worker1 1.36.5-1.1
v1.36.5
Kubernetes v1.36.5
active

INSTALLED worker2 1.36.5-1.1
v1.36.5
Kubernetes v1.36.5
active

INSTALLED worker3 1.36.5-1.1
v1.36.5
Kubernetes v1.36.5
active
```

## 7. Инициализация control-plane

На `master` выполнены команды:

```bash
sudo kubeadm config images pull \
  --kubernetes-version "$(kubeadm version -o short)" \
  --cri-socket=unix:///run/containerd/containerd.sock

sudo kubeadm init \
  --apiserver-advertise-address=192.168.122.101 \
  --control-plane-endpoint=192.168.122.101:6443 \
  --pod-network-cidr=10.244.0.0/16 \
  --cri-socket=unix:///run/containerd/containerd.sock
```

Значимая часть полученного вывода:

```text
[init] Using Kubernetes version: v1.36.5
[control-plane-check] kube-controller-manager is healthy
[control-plane-check] kube-scheduler is healthy
[control-plane-check] kube-apiserver is healthy
[addons] Applied essential addon: CoreDNS
[addons] Applied essential addon: kube-proxy

Your Kubernetes control-plane has initialized successfully!
```

Настройка `kubectl`:

```bash
mkdir -p "$HOME/.kube"
sudo cp /etc/kubernetes/admin.conf "$HOME/.kube/config"
sudo chown "$(id -u):$(id -g)" "$HOME/.kube/config"
```

## 8. Установка Flannel

На `master` выполнена команда:

```bash
kubectl apply -f \
  https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
```

Полученный вывод:

```text
namespace/kube-flannel created
serviceaccount/flannel created
clusterrole.rbac.authorization.k8s.io/flannel created
clusterrolebinding.rbac.authorization.k8s.io/flannel created
configmap/kube-flannel-cfg created
daemonset.apps/kube-flannel-ds created
```

## 9. Подключение worker-узлов

На `master` была создана join-команда:

```bash
kubeadm token create --print-join-command
```

Полученный вывод:

```text
kubeadm join 192.168.122.101:6443 \
  --token xm9ncx.anmuax90f1amng45 \
  --discovery-token-ca-cert-hash sha256:525e777e35f7e8e13bac8b3c2c965ba1b02381b2b871a46f618f08bed9a0cae0
```

На `worker1`, `worker2` и `worker3` выполнена команда:

```bash
sudo kubeadm join 192.168.122.101:6443 \
  --token xm9ncx.anmuax90f1amng45 \
  --discovery-token-ca-cert-hash sha256:525e777e35f7e8e13bac8b3c2c965ba1b02381b2b871a46f618f08bed9a0cae0 \
  --cri-socket=unix:///run/containerd/containerd.sock
```

Полученный вывод на каждом worker:

```text
[preflight] Running pre-flight checks
[kubelet-start] Starting the kubelet
[kubelet-check] The kubelet is healthy
[kubelet-start] Waiting for the kubelet to perform the TLS Bootstrap

This node has joined the cluster:
* Certificate signing request was sent to apiserver and a response was received.
* The Kubelet was informed of the new secure connection details.
```

## 10. Состояние кластера до обновления

Выполненная команда:

```bash
kubectl get nodes -o wide
```

Полученный вывод:

```text
NAME      STATUS   ROLES           AGE     VERSION   INTERNAL-IP       EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION              CONTAINER-RUNTIME
master    Ready    control-plane   5m11s   v1.36.5   192.168.122.101   <none>        Ubuntu 24.04.5 LTS   6.8.0-142-generic (amd64)   containerd://2.2.1
worker1   Ready    <none>          3m56s   v1.36.5   192.168.122.102   <none>        Ubuntu 24.04.5 LTS   6.8.0-142-generic (amd64)   containerd://2.2.1
worker2   Ready    <none>          3m55s   v1.36.5   192.168.122.103   <none>        Ubuntu 24.04.5 LTS   6.8.0-142-generic (amd64)   containerd://2.2.1
worker3   Ready    <none>          3m55s   v1.36.5   192.168.122.104   <none>        Ubuntu 24.04.5 LTS   6.8.0-142-generic (amd64)   containerd://2.2.1
```

Исходный вывод сохранён в
[`01-nodes-before-upgrade.txt`](kubeadm-evidence/01-nodes-before-upgrade.txt).

## 11. Обновление control-plane до Kubernetes 1.37

На `master` выполнены команды:

```bash
sudo apt-mark unhold kubeadm

curl -fsSL \
  https://pkgs.k8s.io/core:/stable:/v1.37/deb/Release.key |
  sudo gpg --dearmor --yes \
    -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

echo \
  'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.37/deb/ /' |
  sudo tee /etc/apt/sources.list.d/kubernetes.list

sudo apt-get update

K8S_DEB_VERSION="$(
  apt-cache madison kubeadm |
    awk '$3 ~ /^1\.37\./ && version == "" {version=$3} END {print version}'
)"

sudo apt-get install -y kubeadm="$K8S_DEB_VERSION"
sudo apt-mark hold kubeadm

kubeadm version -o short
sudo kubeadm upgrade plan
sudo kubeadm upgrade apply --yes "$(kubeadm version -o short)"
```

Полученный вывод плана и обновления:

```text
TARGET_DEB_VERSION=1.37.1-1.1
v1.37.1

[upgrade/versions] Cluster version: 1.36.5
[upgrade/versions] kubeadm version: v1.37.1
[upgrade/versions] Target version: v1.37.1

COMPONENT                 NODE      CURRENT   TARGET
kube-apiserver            master    v1.36.5   v1.37.1
kube-controller-manager   master    v1.36.5   v1.37.1
kube-scheduler            master    v1.36.5   v1.37.1
kube-proxy                          1.36.5    v1.37.1
CoreDNS                             v1.14.2   v1.14.6
etcd                      master    3.6.8-0   3.7.0-0

[upgrade/staticpods] Component "etcd" upgraded successfully!
[upgrade/staticpods] Component "kube-apiserver" upgraded successfully!
[upgrade/staticpods] Component "kube-controller-manager" upgraded successfully!
[upgrade/staticpods] Component "kube-scheduler" upgraded successfully!
[upgrade] SUCCESS! A control plane node of your cluster was upgraded to "v1.37.1".
```

После control-plane обновлены `kubelet` и `kubectl`:

```bash
kubectl drain master \
  --ignore-daemonsets \
  --delete-emptydir-data

sudo apt-mark unhold kubelet kubectl
sudo apt-get install -y \
  kubelet="$K8S_DEB_VERSION" \
  kubectl="$K8S_DEB_VERSION"
sudo apt-mark hold kubelet kubectl

sudo systemctl daemon-reload
sudo systemctl restart kubelet

kubectl uncordon master
kubectl wait --for=condition=Ready node/master --timeout=5m
kubectl get node master -o wide
```

Полученный вывод:

```text
node/master cordoned
node/master drained
kubelet set on hold.
kubectl set on hold.
node/master uncordoned
node/master condition met
NAME     STATUS   ROLES           AGE   VERSION   INTERNAL-IP       EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION              CONTAINER-RUNTIME
master   Ready    control-plane   12m   v1.37.1   192.168.122.101   <none>        Ubuntu 24.04.5 LTS   6.8.0-142-generic (amd64)   containerd://2.2.1
```


## 12. Последовательное обновление worker-узлов

Для каждого worker выполнялся один и тот же порядок: `drain` на master,
обновление на worker, затем `uncordon` и проверка на master. Следующий узел
обновлялся только после перехода предыдущего в `Ready`.

### Команды для каждого worker

На `master`:

```bash
kubectl drain WORKER_NAME \
  --ignore-daemonsets \
  --delete-emptydir-data
```

На соответствующем worker:

```bash
sudo apt-mark unhold kubeadm

curl -fsSL \
  https://pkgs.k8s.io/core:/stable:/v1.37/deb/Release.key |
  sudo gpg --dearmor --yes \
    -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

echo \
  'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.37/deb/ /' |
  sudo tee /etc/apt/sources.list.d/kubernetes.list

sudo apt-get update

K8S_DEB_VERSION="$(
  apt-cache madison kubeadm |
    awk '$3 ~ /^1\.37\./ && version == "" {version=$3} END {print version}'
)"

sudo apt-get install -y kubeadm="$K8S_DEB_VERSION"
sudo apt-mark hold kubeadm
sudo kubeadm upgrade node

sudo apt-mark unhold kubelet kubectl
sudo apt-get install -y \
  kubelet="$K8S_DEB_VERSION" \
  kubectl="$K8S_DEB_VERSION"
sudo apt-mark hold kubelet kubectl

sudo systemctl daemon-reload
sudo systemctl restart kubelet
```

На `master`:

```bash
kubectl uncordon WORKER_NAME
kubectl wait --for=condition=Ready \
  node/WORKER_NAME \
  --timeout=5m
kubectl get node WORKER_NAME -o wide
```

### Полученный вывод для worker1

```text
node/worker1 cordoned
node/worker1 drained
[upgrade/kubelet-config] The kubelet configuration for this node was successfully upgraded!
v1.37.1
Kubernetes v1.37.1
node/worker1 uncordoned
node/worker1 condition met
NAME      STATUS   ROLES    AGE   VERSION   INTERNAL-IP
worker1   Ready    <none>   12m   v1.37.1   192.168.122.102
```


### Полученный вывод для worker2

```text
node/worker2 cordoned
node/worker2 drained
[upgrade/kubelet-config] The kubelet configuration for this node was successfully upgraded!
v1.37.1
Kubernetes v1.37.1
node/worker2 uncordoned
node/worker2 condition met
NAME      STATUS   ROLES    AGE   VERSION   INTERNAL-IP
worker2   Ready    <none>   14m   v1.37.1   192.168.122.103
```


### Полученный вывод для worker3

```text
node/worker3 cordoned
node/worker3 drained
[upgrade/kubelet-config] The kubelet configuration for this node was successfully upgraded!
v1.37.1
Kubernetes v1.37.1
node/worker3 uncordoned
node/worker3 condition met
NAME      STATUS   ROLES    AGE   VERSION   INTERNAL-IP
worker3   Ready    <none>   20m   v1.37.1   192.168.122.104
```


## 13. Состояние кластера после обновления

Выполненная команда:

```bash
kubectl get nodes -o wide
```

Полученный вывод:

```text
NAME      STATUS   ROLES           AGE   VERSION   INTERNAL-IP       EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION              CONTAINER-RUNTIME
master    Ready    control-plane   50m   v1.37.1   192.168.122.101   <none>        Ubuntu 24.04.5 LTS   6.8.0-142-generic (amd64)   containerd://2.2.1
worker1   Ready    <none>          49m   v1.37.1   192.168.122.102   <none>        Ubuntu 24.04.5 LTS   6.8.0-142-generic (amd64)   containerd://2.2.1
worker2   Ready    <none>          49m   v1.37.1   192.168.122.103   <none>        Ubuntu 24.04.5 LTS   6.8.0-142-generic (amd64)   containerd://2.2.1
worker3   Ready    <none>          49m   v1.37.1   192.168.122.104   <none>        Ubuntu 24.04.5 LTS   6.8.0-142-generic (amd64)   containerd://2.2.1
```

Исходный вывод:
[`04-nodes-after-upgrade.txt`](kubeadm-evidence/04-nodes-after-upgrade.txt).

Проверка возврата всех узлов в планирование:

```bash
kubectl get nodes \
  -o custom-columns='NAME:.metadata.name,UNSCHEDULABLE:.spec.unschedulable,VERSION:.status.nodeInfo.kubeletVersion'
```

Полученный вывод:

```text
NAME      UNSCHEDULABLE   VERSION
master    <none>          v1.37.1
worker1   <none>          v1.37.1
worker2   <none>          v1.37.1
worker3   <none>          v1.37.1
```

Проверка версий пакетов и `apt-mark hold` на всех узлах:

```bash
for ip in 192.168.122.101 192.168.122.102 \
          192.168.122.103 192.168.122.104; do
  ssh "ubuntu@$ip" '
    printf "kubeadm="; kubeadm version -o short
    printf "kubelet="; kubelet --version
    printf "holds="
    apt-mark showhold |
      grep -E "^(kubeadm|kubectl|kubelet)$" |
      sort |
      paste -sd, -
  '
done
```

Полученный вывод:

```text
master: kubeadm=v1.37.1
kubelet=Kubernetes v1.37.1
holds=kubeadm,kubectl,kubelet
worker1: kubeadm=v1.37.1
kubelet=Kubernetes v1.37.1
holds=kubeadm,kubectl,kubelet
worker2: kubeadm=v1.37.1
kubelet=Kubernetes v1.37.1
holds=kubeadm,kubectl,kubelet
worker3: kubeadm=v1.37.1
kubelet=Kubernetes v1.37.1
holds=kubeadm,kubectl,kubelet
```

## 14. Приложенные артефакты основной части

- [`01-nodes-before-upgrade.txt`](kubeadm-evidence/01-nodes-before-upgrade.txt) - узлы на `v1.36.5`;
- [`04-nodes-after-upgrade.txt`](kubeadm-evidence/04-nodes-after-upgrade.txt) - узлы на `v1.37.1`.

# Часть 2. Задание со звездочкой: Kubespray

Отдельный отчёт с командами установки: [`kubespray/README.md`](kubespray/README.md).

## 15. Ограничение локального стенда

По условию требовалось развернуть 3 master и 2 worker. Все пять VM были
созданы с 2 vCPU, 2 ГБ RAM и диском 20 ГБ. На локальном хосте доступно только
16 ГБ RAM. При одновременной работе пяти VM потребление памяти достигло 15 ГБ,
свободной памяти оставалось менее 400 МБ, из-за чего процессы завершались по
нехватке памяти.

Поэтому `worker2` был остановлен, а фактический стенд Kubespray развернут в
конфигурации 3 master и 1 worker. Это отклонение от условия зафиксировано явно.

| VM | Роль | vCPU | RAM | IP | Состояние |
|---|---|---:|---:|---|---|
| `master1` | control-plane, etcd | 2 | 2 ГБ | `192.168.122.101` | работает |
| `master2` | control-plane, etcd | 2 | 2 ГБ | `192.168.122.102` | работает |
| `master3` | control-plane, etcd | 2 | 2 ГБ | `192.168.122.103` | работает |
| `worker1` | worker | 2 | 2 ГБ | `192.168.122.104` | работает |
| `worker2` | worker | 2 | 2 ГБ | `192.168.122.105` | остановлена |

## 16. Удаление первого стенда

После сохранения результатов основной части выполнены команды:

```bash
for spec in \
  "<host mac='52:54:00:e9:ec:63' name='master' ip='192.168.122.101'/>" \
  "<host mac='52:54:00:28:8a:49' name='worker1' ip='192.168.122.102'/>" \
  "<host mac='52:54:00:06:99:13' name='worker2' ip='192.168.122.103'/>" \
  "<host mac='52:54:00:72:11:d1' name='worker3' ip='192.168.122.104'/>"; do
  virsh -c qemu:///system net-update default delete ip-dhcp-host \
    "$spec" --live --config
done

uvt-kvm destroy master worker1 worker2 worker3
virsh -c qemu:///system list --all
```

Полученный вывод:

```text
Updated network default persistent config and live state
Updated network default persistent config and live state
Updated network default persistent config and live state
Updated network default persistent config and live state
 Id   Name   State
--------------------
```

## 17. Создание VM для Kubespray

VM создавались так же, как в основной части. В список добавлены два master:

```bash
for vm in master1 master2 master3 worker1 worker2; do
  uvt-kvm create \
    --memory 2048 \
    --cpu 2 \
    --disk 20 \
    --ssh-public-key-file "$HOME/.ssh/id_ed25519.pub" \
    "$vm" release=noble arch=amd64
done
```

Постоянные IP настраивались тем же способом, который показан в разделе 3.

Из-за нехватки памяти второй worker остановлен:

```bash
virsh -c qemu:///system shutdown worker2
virsh -c qemu:///system list --all
```

Полученный вывод:

```text
 Id   Name      State
--------------------------
 10   master1   running
 11   master2   running
 12   master3   running
 13   worker1   running
 -    worker2   shut off
```

## 18. Inventory Kubespray

Фактически использованный файл: [`inventory.ini`](kubespray/inventory.ini).

```ini
[all]
master1 ansible_host=192.168.122.101 ip=192.168.122.101 access_ip=192.168.122.101
master2 ansible_host=192.168.122.102 ip=192.168.122.102 access_ip=192.168.122.102
master3 ansible_host=192.168.122.103 ip=192.168.122.103 access_ip=192.168.122.103
worker1 ansible_host=192.168.122.104 ip=192.168.122.104 access_ip=192.168.122.104

[kube_control_plane]
master1
master2
master3

[etcd]
master1
master2
master3

[kube_node]
worker1

[k8s_cluster:children]
kube_control_plane
kube_node

[k8s_cluster:vars]
kube_version=1.36.4

[calico_rr]

[all:vars]
ansible_user=ubuntu
ansible_become=true
ansible_python_interpreter=/usr/bin/python3
```

Дополнительные переменные: [`homework-vars.yml`](kubespray/homework-vars.yml).
Параметры localhost: [`localhost.yml`](kubespray/localhost.yml).

## 19. Запуск Kubespray

Kubespray использует Ansible. Выполненные команды:

```bash
git clone --branch v2.32.0 --depth 1 \
  https://github.com/kubernetes-sigs/kubespray.git \
  /tmp/kubespray-v2.32.0

python3 -m venv /tmp/kubespray-venv
/tmp/kubespray-venv/bin/pip install uv
/tmp/kubespray-venv/bin/uv python install 3.13 \
  --install-dir /tmp/kubespray-python
/tmp/kubespray-python/cpython-3.13-linux-x86_64-gnu/bin/python3.13 \
  -m venv /tmp/kubespray-venv313
/tmp/kubespray-venv313/bin/pip install \
  -r /tmp/kubespray-v2.32.0/requirements.txt

cp -a /tmp/kubespray-v2.32.0/inventory/sample \
  /tmp/kubespray-v2.32.0/inventory/homework4
cp kubernetes-prod/kubespray/inventory.ini \
  /tmp/kubespray-v2.32.0/inventory/homework4/inventory.ini
cp kubernetes-prod/kubespray/homework-vars.yml \
  /tmp/kubespray-v2.32.0/inventory/homework4/group_vars/k8s_cluster/homework.yml
mkdir -p /tmp/kubespray-v2.32.0/inventory/homework4/host_vars
cp kubernetes-prod/kubespray/localhost.yml \
  /tmp/kubespray-v2.32.0/inventory/homework4/host_vars/localhost.yml

cd /tmp/kubespray-v2.32.0
/tmp/kubespray-venv313/bin/ansible \
  -i inventory/homework4/inventory.ini \
  all -m ping \
  --private-key "$HOME/.ssh/id_ed25519"
```

Полученный вывод проверки доступа:

```text
master1 | SUCCESS => {"changed": false, "ping": "pong"}
master2 | SUCCESS => {"changed": false, "ping": "pong"}
master3 | SUCCESS => {"changed": false, "ping": "pong"}
worker1 | SUCCESS => {"changed": false, "ping": "pong"}
```

Запуск развёртывания:

```bash
/tmp/kubespray-venv313/bin/ansible-playbook \
  -i inventory/homework4/inventory.ini \
  --private-key "$HOME/.ssh/id_ed25519" \
  -v cluster.yml
```

Итоговый `PLAY RECAP`:

```text
master1 : ok=760 changed=159 unreachable=0 failed=0 skipped=696 rescued=0 ignored=4
master2 : ok=558 changed=111 unreachable=0 failed=0 skipped=661 rescued=0 ignored=1
master3 : ok=560 changed=112 unreachable=0 failed=0 skipped=659 rescued=0 ignored=1
worker1 : ok=461 changed=76  unreachable=0 failed=0 skipped=394 rescued=0 ignored=0
```

## 20. Результат задания со звездочкой

Выполненная команда:

```bash
ssh ubuntu@192.168.122.101 \
  'sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get nodes -o wide'
```

Полученный вывод:

```text
NAME      STATUS   ROLES           AGE     VERSION   INTERNAL-IP       EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION              CONTAINER-RUNTIME
master1   Ready    control-plane   5m32s   v1.36.4   192.168.122.101   <none>        Ubuntu 24.04.5 LTS   6.8.0-142-generic (amd64)   containerd://2.3.5
master2   Ready    control-plane   4m53s   v1.36.4   192.168.122.102   <none>        Ubuntu 24.04.5 LTS   6.8.0-142-generic (amd64)   containerd://2.3.5
master3   Ready    control-plane   4m26s   v1.36.4   192.168.122.103   <none>        Ubuntu 24.04.5 LTS   6.8.0-142-generic (amd64)   containerd://2.3.5
worker1   Ready    <none>          3m47s   v1.36.4   192.168.122.104   <none>        Ubuntu 24.04.5 LTS   6.8.0-142-generic (amd64)   containerd://2.3.5
```

Исходный вывод: [`nodes-o-wide.txt`](kubespray-evidence/nodes-o-wide.txt).
