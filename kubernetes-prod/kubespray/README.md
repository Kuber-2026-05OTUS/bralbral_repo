# Развёртывание Kubernetes через Kubespray

## Результат

Для задания требовался кластер из 3 master и 2 worker. Все пять виртуальных
машин были созданы с 2 vCPU, 2 ГБ RAM и диском 20 ГБ.

На локальном хосте установлено 16 ГБ RAM. При одновременном запуске пяти VM
использовалось около 15 ГБ, свободной памяти оставалось менее 400 МБ. Из-за
нехватки памяти `worker2` был остановлен. Фактически Kubespray развернул кластер
из 3 master и 1 worker.

Использованы:

- Kubespray `v2.32.0`;
- Kubernetes `v1.36.4`;
- containerd `2.3.5`;
- Calico;
- Ubuntu Server 24.04.5 LTS на узлах.

## 1. Создание виртуальных машин

Команда выполнена на локальном хосте:

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

`uvt-kvm create` не печатает результат при успешном выполнении. Проверка:

```bash
virsh -c qemu:///system list --all
```

Полученный вывод до остановки второго worker:

```text
 Id   Name      State
--------------------------
 10   master1   running
 11   master2   running
 12   master3   running
 13   worker1   running
 14   worker2   running
```

Постоянные DHCP-привязки для созданных VM:

```bash
virsh -c qemu:///system net-update default add-last ip-dhcp-host \
  "<host mac='52:54:00:53:98:f1' name='master1' ip='192.168.122.101'/>" \
  --live --config
virsh -c qemu:///system net-update default add-last ip-dhcp-host \
  "<host mac='52:54:00:c7:6d:c3' name='master2' ip='192.168.122.102'/>" \
  --live --config
virsh -c qemu:///system net-update default add-last ip-dhcp-host \
  "<host mac='52:54:00:b6:94:6e' name='master3' ip='192.168.122.103'/>" \
  --live --config
virsh -c qemu:///system net-update default add-last ip-dhcp-host \
  "<host mac='52:54:00:40:f3:c0' name='worker1' ip='192.168.122.104'/>" \
  --live --config
virsh -c qemu:///system net-update default add-last ip-dhcp-host \
  "<host mac='52:54:00:60:e9:47' name='worker2' ip='192.168.122.105'/>" \
  --live --config
```

Каждая команда вернула:

```text
Updated network default persistent config and live state
```

После перезапуска VM проверена доступность адресов:

```bash
for ip in 192.168.122.101 192.168.122.102 192.168.122.103 \
          192.168.122.104 192.168.122.105; do
  ssh-keygen -R "$ip"
  ssh-keyscan -H "$ip" >> "$HOME/.ssh/known_hosts"
  ssh "ubuntu@$ip" hostname
done
```

Полученный вывод:

```text
master1
master2
master3
worker1
worker2
```

Из-за ограничения по памяти второй worker остановлен:

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

## 2. Inventory

Для развёртывания использован файл [`inventory.ini`](inventory.ini):

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

Также использованы файлы [`homework-vars.yml`](homework-vars.yml) и
[`localhost.yml`](localhost.yml).

## 3. Установка Kubespray

Команды выполнены на локальном хосте:

```bash
sudo apt update
sudo apt install -y git python3-venv

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
```

Подготовка каталога inventory:

```bash
cp -a /tmp/kubespray-v2.32.0/inventory/sample \
  /tmp/kubespray-v2.32.0/inventory/homework4
cp kubernetes-prod/kubespray/inventory.ini \
  /tmp/kubespray-v2.32.0/inventory/homework4/inventory.ini
cp kubernetes-prod/kubespray/homework-vars.yml \
  /tmp/kubespray-v2.32.0/inventory/homework4/group_vars/k8s_cluster/homework.yml
mkdir -p /tmp/kubespray-v2.32.0/inventory/homework4/host_vars
cp kubernetes-prod/kubespray/localhost.yml \
  /tmp/kubespray-v2.32.0/inventory/homework4/host_vars/localhost.yml
```

## 4. Проверка Ansible

```bash
cd /tmp/kubespray-v2.32.0
/tmp/kubespray-venv313/bin/ansible \
  -i inventory/homework4/inventory.ini \
  all -m ping \
  --private-key "$HOME/.ssh/id_ed25519"
```

Полученный вывод:

```text
master1 | SUCCESS => {"changed": false, "ping": "pong"}
master2 | SUCCESS => {"changed": false, "ping": "pong"}
master3 | SUCCESS => {"changed": false, "ping": "pong"}
worker1 | SUCCESS => {"changed": false, "ping": "pong"}
```

## 5. Развёртывание Kubernetes

```bash
cd /tmp/kubespray-v2.32.0
/tmp/kubespray-venv313/bin/ansible-playbook \
  -i inventory/homework4/inventory.ini \
  --private-key "$HOME/.ssh/id_ed25519" \
  -v cluster.yml
```

Итоговый вывод playbook:

```text
PLAY RECAP
master1 : ok=760 changed=159 unreachable=0 failed=0 skipped=696 rescued=0 ignored=4
master2 : ok=558 changed=111 unreachable=0 failed=0 skipped=661 rescued=0 ignored=1
master3 : ok=560 changed=112 unreachable=0 failed=0 skipped=659 rescued=0 ignored=1
worker1 : ok=461 changed=76  unreachable=0 failed=0 skipped=394 rescued=0 ignored=0
```

## 6. Результат

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

Исходный вывод приложен в
[`nodes-o-wide.txt`](../kubespray-evidence/nodes-o-wide.txt).

После сохранения результатов все виртуальные машины были удалены.
