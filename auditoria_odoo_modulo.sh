#!/bin/bash
MOD_PATH="$1"
BD="$2"
ODOO_BIN="/ruta/a/odoo-bin"
ODOO_CONF="/ruta/a/odoo.conf"
FECHA=$(date +'%Y-%m-%d_%H-%M-%S')
LOG="auditoria_modulo_${FECHA}.log"

echo "== Chequeo de estructura ==" > $LOG
tree -L 2 "$MOD_PATH" >> $LOG
echo "== Manifest ==" >> $LOG
python3 -m py_compile "$MOD_PATH/__manifest__.py" >> $LOG 2>&1
grep -qi "account_accountant" "$MOD_PATH/__manifest__.py" && echo "ERROR: Depende de módulo Enterprise!" >> $LOG
echo "== Modelos ==" >> $LOG
for f in $(find "$MOD_PATH/models" -name "*.py"); do python3 -m py_compile "$f" >> $LOG 2>&1; done
echo "== Vistas XML ==" >> $LOG
for f in $(find "$MOD_PATH/views" -name "*.xml"); do xmllint --noout "$f" >> $LOG 2>&1; done
echo "== Seguridad ==" >> $LOG
cat "$MOD_PATH/security/ir.model.access.csv" >> $LOG
echo "== Upgrade de módulo ==" >> $LOG
$ODOO_BIN -c "$ODOO_CONF" -d "$BD" -u $(basename $MOD_PATH) --stop-after-init >> $LOG 2>&1
echo "== Tests ==" >> $LOG
$ODOO_BIN -c "$ODOO_CONF" -d "$BD" -i $(basename $MOD_PATH) --test-enable --stop-after-init >> $LOG 2>&1
echo "== Auditoría completada ==" >> $LOG
