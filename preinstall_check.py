#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import xml.etree.ElementTree as ET
import csv
import subprocess
import shutil
from collections import defaultdict

MODULE_PATH = os.getcwd()
ERRORS = []

print("🔎 Iniciando auditoría pre-instalación de inmoser_manus...\n")

# 1️⃣ Revisar archivos XML
print("1️⃣ Revisando sintaxis XML y IDs duplicados...")
xml_files = [y for x in os.walk(MODULE_PATH) for y in glob.glob(os.path.join(x[0], '*.xml'))]

xml_ids = defaultdict(list)
for xml_file in xml_files:
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        for elem in root.iter():
            if 'id' in elem.attrib:
                xml_ids[elem.attrib['id']].append(xml_file)
    except ET.ParseError as e:
        ERRORS.append(f"❌ XML mal formado: {xml_file} -> {e}")

for _id, files in xml_ids.items():
    if len(files) > 1:
        ERRORS.append(f"⚠️ ID duplicado '{_id}' en archivos: {files}")

print(f"   ✔ Revisados {len(xml_files)} archivos XML")

# 2️⃣ Revisar sintaxis Python
print("\n2️⃣ Revisando sintaxis Python...")
py_files = [y for x in os.walk(MODULE_PATH) for y in glob.glob(os.path.join(x[0], '*.py'))]

for py_file in py_files:
    result = subprocess.run(['python3', '-m', 'py_compile', py_file], capture_output=True, text=True)
    if result.returncode != 0:
        ERRORS.append(f"❌ Error sintaxis Python: {py_file} -> {result.stderr.strip()}")

print(f"   ✔ Revisados {len(py_files)} archivos Python")

# 3️⃣ Limpiar archivos .bak, .pyc y __pycache__
print("\n3️⃣ Eliminando archivos .bak, .pyc y carpetas __pycache__...")

def remove_files(patterns):
    removed = 0
    for pattern in patterns:
        files = [y for x in os.walk(MODULE_PATH) for y in glob.glob(os.path.join(x[0], pattern))]
        for f in files:
            try:
                os.remove(f)
                print(f"   🗑 Eliminado {f}")
                removed += 1
            except Exception as e:
                print(f"   ❌ No se pudo eliminar {f}: {e}")
    return removed

def remove_dirs(dir_name):
    removed = 0
    for root, dirs, files in os.walk(MODULE_PATH):
        if dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                shutil.rmtree(dir_path)
                print(f"   🗑 Eliminada carpeta {dir_path}")
                removed += 1
            except Exception as e:
                print(f"   ❌ No se pudo eliminar {dir_path}: {e}")
    return removed

total_files_removed = remove_files(['*.pyc', '*.bak', '*~'])
total_dirs_removed = remove_dirs('__pycache__')

print(f"   ✅ Eliminados {total_files_removed} archivos y {total_dirs_removed} carpetas __pycache__")

# 4️⃣ Revisar ir.model.access.csv vs modelos
print("\n4️⃣ Revisando seguridad: ir.model.access.csv vs modelos...")
access_file = os.path.join(MODULE_PATH, 'security', 'ir.model.access.csv')
models_in_module = [os.path.splitext(os.path.basename(f))[0] for f in py_files if f.startswith(os.path.join(MODULE_PATH, 'models'))]

if os.path.exists(access_file):
    with open(access_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            model_key = next((k for k in row.keys() if 'model' in k.lower()), None)
            if model_key is None:
                ERRORS.append(f"❌ No se encontró columna de modelo en CSV: {access_file}")
                break
            model_name = row[model_key].replace('model_', '').strip()
            if model_name not in models_in_module:
                ERRORS.append(f"⚠️ Modelo en ir.model.access.csv no existe en módulo: {row[model_key]}")
else:
    ERRORS.append("⚠️ No se encontró 'ir.model.access.csv' en carpeta security/")

# 5️⃣ Resumen final
print("\n5️⃣ Resumen de auditoría pre-instalación:")
if ERRORS:
    for err in ERRORS:
        print(err)
    print(f"\n❌ Auditoría finalizada con {len(ERRORS)} errores/adviertencias. Revisar antes de instalar.")
else:
    print("✅ Auditoría completada sin errores críticos. Módulo limpio y listo para instalación.")
