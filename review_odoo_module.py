import os
import re
import sys

HEADER = """
=== Odoo Module Deep Review Tool ===
"""

IGNORE_MODELS = {
    "ir.ui.view", "ir.actions.act_window", "ir.sequence",
    "mail.template", "res.groups", "ir.rule", "account.move",
    "hr.employee", "res.partner", "stock.warehouse"
}

# Regex patterns
MODEL_PATTERN = r"class\s+([A-Za-z0-9_]+)\s*\(.*?\):"
FIELD_PATTERN = r"fields\.[A-Za-z]+\("
XML_MODEL_PATTERN = r'model\s*=\s*"([^"]+)"'
XML_FIELD_PATTERN = r'name="([^"]+)"'

def scan_python_models(py_path):
    models = {}
    fields = {}

    for root, _, files in os.walk(py_path):
        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            found_models = re.findall(MODEL_PATTERN, content)
            found_fields = re.findall(r"([A-Za-z0-9_]+)\s*=\s*fields\.[A-Za-z]+\(", content)

            models[file_path] = found_models
            fields[file_path] = found_fields

    return models, fields

def scan_xml_fields(xml_path):
    xml_models = []
    xml_fields = []

    for root, _, files in os.walk(xml_path):
        for file in files:
            if not file.endswith(".xml"):
                continue

            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            xml_models += re.findall(XML_MODEL_PATTERN, content)
            xml_fields += re.findall(XML_FIELD_PATTERN, content)

    return xml_models, xml_fields

def main():
    print(HEADER)

    if len(sys.argv) < 2:
        print("❌ ERROR: Debes pasar la ruta del módulo.")
        return

    module_path = sys.argv[1]

    if not os.path.isdir(module_path):
        print(f"❌ ERROR: La ruta '{module_path}' no es un directorio válido.")
        return

    python_path = os.path.join(module_path, "models")
    xml_path = module_path

    print("▶️ Escaneando modelos Python...")
    models, fields = scan_python_models(python_path)

    print("▶️ Escaneando XML...")
    xml_models, xml_fields = scan_xml_fields(xml_path)

    # Unificar campos de modelos propios
    model_fields = set()
    for file_fields in fields.values():
        model_fields.update(file_fields)

    # Filtrar modelos XML del core de Odoo
    used_xml_models = [m for m in xml_models if m not in IGNORE_MODELS]

    # Filtrar campos XML que deben existir
    problematic_fields = []
    for field in xml_fields:
        if field not in model_fields:
            # Ignorar campos comunes de vistas
            if field in ["name", "model", "arch", "string", "id"]:
                continue
            problematic_fields.append(field)

    # Generar reporte
    report_path = "module_review_report.txt"
    with open(report_path, "w", encoding="utf-8") as r:
        r.write("=== ANALISIS COMPLETO DE MODULO ODOO ===\n\n")
        r.write(f"MÓDULO ANALIZADO: {module_path}\n\n")

        r.write("========================\nARCHIVOS PYTHON\n========================\n\n")
        for file, model_list in models.items():
            r.write(f"📌 Archivo: {file}\n")
            if not model_list:
                r.write("  ⚠️ No se encontraron modelos en este archivo.\n\n")
            else:
                r.write("  Modelos encontrados:\n")
                for m in model_list:
                    r.write(f"    - {m}\n")
                r.write("\n")

        r.write("========================\nVALIDACIÓN DE CAMPOS XML\n========================\n\n")

        if problematic_fields:
            r.write("❌ CAMPOS USADOS EN XML QUE NO EXISTEN EN MODELOS:\n")
            for f in sorted(set(problematic_fields)):
                r.write(f"   - {f}\n")
        else:
            r.write("✅ No se encontraron errores de campos faltantes.\n")

    print("\n✅ Análisis completado. Archivo generado: module_review_report.txt")


if __name__ == "__main__":
    main()
