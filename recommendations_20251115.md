# RECOMENDACIONES BASADAS EN ANALISIS

## Ejecutar despues de revisar el reporte completo

### 1. Eliminar repositorios OCA no usados (REVISAR PRIMERO)

```bash
# Backup primero
cp -r oca_addons/ oca_addons_backup_$(date +%Y%m%d)/

# Eliminar conservadoramente (solo si NO estan en BD)
# rm -rf oca_addons/oca-pos/
# rm -rf oca_addons/oca-agreement/
# rm -rf oca_addons/oca-repair/
# rm -rf oca_addons/oca-maintenance/
```

### 2. Crear READMEs

```bash
# Para service_order
cat > custom_addons/inmoser_service_order/README.md << 'EOF'
# Inmoser Service Order
Modulo para gestion de ordenes de servicio
EOF

# Para field_service
cat > custom_addons/inmoser_field_service/README.md << 'EOF'
# Inmoser Field Service
Extension para Field Service Management
EOF
```

### 3. Crear tests para field_service

```bash
mkdir -p custom_addons/inmoser_field_service/tests
cat > custom_addons/inmoser_field_service/tests/__init__.py << 'EOF'
from . import test_fsm_order
EOF

cat > custom_addons/inmoser_field_service/tests/test_fsm_order.py << 'EOF'
from odoo.tests import TransactionCase

class TestFSMOrder(TransactionCase):
    def setUp(self):
        super().setUp()
        self.FSMOrder = self.env['fsm.order']
    
    def test_create_fsm_order(self):
        order = self.FSMOrder.create({'name': 'Test'})
        self.assertTrue(order)
EOF
```

### 4. Optimizar docker-compose

Ver recomendaciones en el reporte principal.

