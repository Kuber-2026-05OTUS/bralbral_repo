# prepare env

sudo apt update
sudo apt install -y uvtool uvtool-libvirt

virsh -c qemu:///system list

test -f ~/.ssh/id_ed25519.pub || ssh-keygen -t ed25519



# create vm
uvt-simplestreams-libvirt sync release=noble arch=amd64

```
for vm in master worker1 worker2; do
  uvt-kvm create \
    --memory 2048 \
    --cpu 2 \
    --disk 20 \
    --ssh-public-key-file "$HOME/.ssh/id_ed25519.pub" \
    "$vm" release=noble arch=amd64
done
```

# list addresses
```
for vm in master worker1 worker2; do
  uvt-kvm wait "$vm"
  echo "$vm: $(uvt-kvm ip "$vm")"
done
```

# set static ip

```
chmod +x set-static-ips.sh
./set-static-ips.sh
```

# connect through Remmina

`--ssh-public-key-file` передаёт в VM только **публичный** ключ. Образ Ubuntu
создаёт пользователя `ubuntu`, а вход выполняется соответствующим приватным
ключом `~/.ssh/id_ed25519`; пароль для него не задаётся.

После назначения статических адресов создайте в Remmina три подключения типа
**SSH**:

| VM | Server | Username | Authentication |
|---|---|---|---|
| `master` | `192.168.122.101` | `ubuntu` | Public key: `~/.ssh/id_ed25519` |
| `worker1` | `192.168.122.102` | `ubuntu` | Public key: `~/.ssh/id_ed25519` |
| `worker2` | `192.168.122.103` | `ubuntu` | Public key: `~/.ssh/id_ed25519` |

Порт — `22`. До назначения статических адресов используйте адрес, показанный
командой `uvt-kvm ip <имя-vm>`.
