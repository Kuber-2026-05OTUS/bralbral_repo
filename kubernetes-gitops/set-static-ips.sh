#!/usr/bin/env bash
set -Eeuo pipefail

URI="qemu:///system"
NETWORK="default"

# По умолчанию VM не перезагружаются.
# Запуск с перезагрузкой:
# REBOOT_VMS=true ./set-static-ips.sh
REBOOT_VMS="${REBOOT_VMS:-false}"

VIRSH=(virsh -c "$URI")

declare -A IPS=(
  [master]="192.168.122.101"
  [worker1]="192.168.122.102"
  [worker2]="192.168.122.103"
  [worker3]="192.168.122.104"
)

VMS=(
  master
  worker1
  worker2
  worker3
)

network_is_active() {
  "${VIRSH[@]}" net-list --name |
    grep -Fxq "$NETWORK"
}

# Находит старые DHCP-записи, конфликтующие:
# - по MAC
# - по имени VM
# - по назначаемому IP
find_conflicts() {
  local scope="$1"
  local mac="$2"
  local vm="$3"
  local ip="$4"

  local -a dump_command=(net-dumpxml "$NETWORK")

  if [[ "$scope" == "config" ]]; then
    dump_command=(net-dumpxml --inactive "$NETWORK")
  fi

  "${VIRSH[@]}" "${dump_command[@]}" |
    python3 -c '
import sys
import xml.etree.ElementTree as ET

mac, name, ip = sys.argv[1:4]

root = ET.parse(sys.stdin).getroot()

for host in root.findall("./ip/dhcp/host"):
    old_mac = (host.get("mac") or "").lower()
    old_name = host.get("name") or ""
    old_ip = host.get("ip") or ""

    if (
        old_mac == mac.lower()
        or old_name == name
        or old_ip == ip
    ):
        # ElementTree сохраняет отступы после элемента в host.tail.
        # Не включаем их в XML, иначе shell воспримет пробелы как
        # отдельную DHCP-запись.
        host.tail = None
        print(
            ET.tostring(
                host,
                encoding="unicode",
                short_empty_elements=True
            )
        )
' "$mac" "$vm" "$ip"
}

delete_conflicts() {
  local scope="$1"
  local mac="$2"
  local vm="$3"
  local ip="$4"

  local conflicts
  local entry

  conflicts="$(find_conflicts "$scope" "$mac" "$vm" "$ip")"

  while IFS= read -r entry; do
    [[ -z "$entry" ]] && continue

    echo "  удаляю из $scope: $entry"

    "${VIRSH[@]}" net-update \
      "$NETWORK" \
      delete \
      ip-dhcp-host \
      "$entry" \
      "--$scope"
  done <<< "$conflicts"
}

command -v virsh >/dev/null || {
  echo "Ошибка: virsh не установлен" >&2
  exit 1
}

command -v python3 >/dev/null || {
  echo "Ошибка: python3 не установлен" >&2
  exit 1
}

# Проверяем существование сети.
"${VIRSH[@]}" net-info "$NETWORK" >/dev/null

# Резервная копия постоянной конфигурации.
BACKUP="${NETWORK}-network-$(date +%Y%m%d-%H%M%S).xml"

"${VIRSH[@]}" net-dumpxml --inactive "$NETWORK" > "$BACKUP"

echo "Резервная копия: $BACKUP"

ACTIVE=false

if network_is_active; then
  ACTIVE=true
fi

for VM in "${VMS[@]}"; do
  IP="${IPS[$VM]}"

  MAC="$(
    "${VIRSH[@]}" domiflist "$VM" |
      awk -v network="$NETWORK" '
        $2 == "network" && $3 == network {
          print $5
          exit
        }
      '
  )"

  if [[ -z "$MAC" ]]; then
    echo \
      "Ошибка: у VM '$VM' нет интерфейса в сети '$NETWORK'" \
      >&2
    exit 1
  fi

  NEW_ENTRY="<host mac='$MAC' name='$VM' ip='$IP'/>"

  echo
  echo "$VM: $MAC → $IP"

  # Удаляем конфликты из работающей конфигурации.
  if [[ "$ACTIVE" == true ]]; then
    delete_conflicts live "$MAC" "$VM" "$IP"
  fi

  # Удаляем конфликты из постоянной конфигурации.
  delete_conflicts config "$MAC" "$VM" "$IP"

  # Добавляем новую запись в работающую конфигурацию.
  if [[ "$ACTIVE" == true ]]; then
    "${VIRSH[@]}" net-update \
      "$NETWORK" \
      add-last \
      ip-dhcp-host \
      "$NEW_ENTRY" \
      --live
  fi

  # Сохраняем запись после перезапуска хоста.
  "${VIRSH[@]}" net-update \
    "$NETWORK" \
    add-last \
    ip-dhcp-host \
    "$NEW_ENTRY" \
    --config

  echo "  привязка установлена"
done

echo
echo "Текущие постоянные DHCP-привязки:"

"${VIRSH[@]}" net-dumpxml --inactive "$NETWORK" |
  grep '<host ' || true

if [[ "$REBOOT_VMS" == true ]]; then
  echo
  echo "Перезагрузка работающих VM..."

  for VM in "${VMS[@]}"; do
    if "${VIRSH[@]}" list --name | grep -Fxq "$VM"; then
      echo "  перезагружаю $VM"
      "${VIRSH[@]}" reboot "$VM"
    fi
  done
else
  echo
  echo "VM не перезагружались."
  echo "Для получения новых адресов выполните:"
  echo
  echo "  REBOOT_VMS=true ./set-static-ips.sh"
fi
