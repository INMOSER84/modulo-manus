#!/bin/bash
MOD_PATH="$(pwd)"
LOG="audit_log_$(date +%Y%m%d_%H%M%S).txt"
BACKUP_DIR="/tmp/inmoser_backup_$(date +%s)"
PORTS=(8069 8071 5432)
echo "🔐 Auditoría y blindaje de módulo: $MOD_PATH" | tee "$LOG"

# 1. Backup completo
echo -e "\n📦 Generando backup físico..." | tee -a "$LOG"
mkdir -p "$BACKUP_DIR"
cp -r "$MOD_PATH" "$BACKUP_DIR"
echo "✔️ Backup creado en: $BACKUP_DIR" | tee -a "$LOG"

# 2. Validación de puertos críticos
echo -e "\n🌐 Validando puertos..." | tee -a "$LOG"
for port in "${PORTS[@]}"; do
  if ss -tuln | grep ":$port" > /dev/null; then
    echo "✔️ Puerto $port activo" | tee -a "$LOG"
  else
    echo "⚠️ Puerto $port inactivo o bloqueado" | tee -a "$LOG"
  fi
done

# 3. Validar estructura mínima
echo -e "\n📁 Validando estructura mínima..." | tee -a "$LOG"
for f in "__manifest__.py" "__init__.py"; do
  [ -f "$MOD_PATH/$f" ] && echo "✔️ $f OK" || echo "❌ Falta $f" | tee -a "$LOG"
done
for d in "models" "views" "security"; do
  [ -d "$MOD_PATH/$d" ] && echo "✔️ $d OK" || echo "❌ Falta $d" | tee -a "$LOG"
done

# 4. Validar sintaxis Python
echo -e "\n🐍 Validando sintaxis Python..." | tee -a "$LOG"
find "$MOD_PATH/models" -name "*.py" | while read f; do
  python3 -m py_compile "$f" && echo "✔️ $f OK" || echo "❌ Error en $f" | tee -a "$LOG"
done

# 5. Validar manifest
echo -e "\n📜 Validando manifest..." | tee -a "$LOG"
python3 -c "import ast; p=ast.literal_eval(open('$MOD_PATH/__manifest__.py').read()); print('✔️ Manifest OK' if isinstance(p,dict) else '❌ Manifest ERROR')" | tee -a "$LOG"

# 6. Validar dependencias reales
echo -e "\n🔗 Validando dependencias..." | tee -a "$LOG"
awk '/depends/{flag=1;next}/]/{flag=0}flag' "$MOD_PATH/__manifest__.py" | grep -oE "'[^']+'" | sed "s/'//g" > /tmp/dep-list.txt
for dep in $(cat /tmp/dep-list.txt); do
  if ! find "$MOD_PATH/.." -type d -name "$dep" | grep -q .; then
    echo "❌ Dependencia faltante: $dep" | tee -a "$LOG"
  else
    echo "✔️ Dependencia encontrada: $dep" | tee -a "$LOG"
  fi
done

# 7. Validar vistas XML
echo -e "\n🧩 Validando vistas XML..." | tee -a "$LOG"
find "$MOD_PATH/views" -name "*.xml" | while read f; do
  xmllint --noout "$f" && echo "✔️ $f OK" || echo "❌ Error en $f" | tee -a "$LOG"
done

# 8. Validar seguridad
echo -e "\n🔐 Validando seguridad..." | tee -a "$LOG"
head -n 1 "$MOD_PATH/security/ir.model.access.csv" | grep -q "id,name,model_id:id" && echo "✔️ Cabecera OK" || echo "❌ Cabecera inválida" | tee -a "$LOG"
grep -E "access_" "$MOD_PATH/security/ir.model.access.csv" | tee -a "$LOG"

# 9. Generar changelog técnico
echo -e "\n📝 Generando changelog técnico..." | tee -a "$LOG"
echo "Modelos definidos:" | tee -a "$LOG"
grep -E '_name\s*=.*' "$MOD_PATH/models/"*.py | tee -a "$LOG"
echo "Herencias detectadas:" | tee -a "$LOG"
grep -E '_inherit\s*=.*' "$MOD_PATH/models/"*.py | tee -a "$LOG"

# 10. Simulación de evidencia fotográfica
echo -e "\n📸 Simulando evidencia fotográfica..." | tee -a "$LOG"
echo "[EVIDENCIA] Captura de estructura: $(tree -L 2)" >> "$LOG"
echo "[EVIDENCIA] Captura de permisos: $(ls -l)" >> "$LOG"

echo -e "\n✅ Auditoría completada. Log: $LOG"
