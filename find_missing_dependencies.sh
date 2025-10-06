#!/bin/bash
MANIFEST="$1"
awk '/depends/{flag=1;next}/]/{flag=0}flag' "$MANIFEST" | grep -oE "'[^']+'" | sed "s/'//g" > /tmp/dep-list.txt

for dep in $(cat /tmp/dep-list.txt); do
   if ! find /ruta/a/todos/los/addons -type d -name "${dep}" | grep -q .; then
      echo "Dependencia FALTANTE: ${dep}"
   fi
done
