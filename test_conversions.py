#!/usr/bin/env python3
"""
Script de prueba para verificar conversiones de documentos
Ejecutar desde la raíz del proyecto: python test_conversions.py
"""

import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.file_converter import FileConverter
from pathlib import Path

def test_libreoffice_available():
    """Verificar si LibreOffice está disponible"""
    import subprocess
    try:
        result = subprocess.run(
            ['libreoffice', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✅ LibreOffice detectado: {result.stdout.strip()}")
            return True
        else:
            print("❌ LibreOffice no responde correctamente")
            return False
    except FileNotFoundError:
        print("❌ LibreOffice NO está instalado o no está en el PATH")
        print("   Instala LibreOffice para habilitar conversiones:")
        print("   - Windows: https://www.libreoffice.org/download/download/")
        print("   - macOS: brew install libreoffice")
        print("   - Linux: sudo apt-get install libreoffice")
        return False
    except subprocess.TimeoutExpired:
        print("⚠️  LibreOffice no responde (timeout)")
        return False

def test_poppler_available():
    """Verificar si poppler-utils está disponible"""
    import subprocess
    try:
        result = subprocess.run(
            ['pdfinfo', '-v'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 or 'pdfinfo' in result.stderr.lower():
            print(f"✅ poppler-utils (pdfinfo) detectado")
            return True
        else:
            print("❌ pdfinfo no responde correctamente")
            return False
    except FileNotFoundError:
        print("❌ poppler-utils NO está instalado")
        print("   Instala poppler-utils para conversiones PDF:")
        print("   - Windows: Descarga desde https://blog.alivate.com.au/poppler-windows/")
        print("   - macOS: brew install poppler")
        print("   - Linux: sudo apt-get install poppler-utils")
        return False

def test_conversion(file_path: str):
    """Probar conversión de un archivo"""
    if not os.path.exists(file_path):
        print(f"❌ Archivo no encontrado: {file_path}")
        return False
    
    converter = FileConverter()
    ext = Path(file_path).suffix.lower()
    
    try:
        print(f"\n🔄 Probando conversión de: {os.path.basename(file_path)}")
        
        if ext == '.pdf':
            result = converter.convert_pdf_to_png(file_path)
            print(f"✅ PDF procesado: {os.path.basename(result)}")
        elif ext == '.docx':
            result = converter.convert_docx_to_pdf(file_path)
            print(f"✅ DOCX → PDF: {os.path.basename(result)}")
        elif ext in ['.xlsx', '.xlsm']:
            result = converter.convert_excel_to_pdf(file_path)
            print(f"✅ Excel → PDF: {os.path.basename(result)}")
            
            # Verificar el PDF generado
            with open(result, 'rb') as f:
                header = f.read(5)
                if header.startswith(b'%PDF-'):
                    print(f"   ✅ PDF válido generado (header: {header})")
                else:
                    print(f"   ❌ PDF inválido (header: {header})")
                    return False
        else:
            print(f"❌ Extensión no soportada: {ext}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error en conversión: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("TEST DE CONVERSIONES DE DOCUMENTOS")
    print("=" * 70)
    print()
    
    # Verificar herramientas del sistema
    print("1️⃣  Verificando herramientas del sistema...")
    print("-" * 70)
    libreoffice_ok = test_libreoffice_available()
    poppler_ok = test_poppler_available()
    print()
    
    # Determinar qué conversiones están disponibles
    if not libreoffice_ok and not poppler_ok:
        print("⚠️  ADVERTENCIA: Sin LibreOffice ni poppler-utils")
        print("   Las conversiones NO funcionarán en este entorno")
        print("   Ejecuta este proyecto en Docker para tener todas las herramientas")
        sys.exit(1)
    
    if not libreoffice_ok:
        print("⚠️  Sin LibreOffice: Conversiones DOCX/XLSX deshabilitadas")
        print("   Solo funcionará procesamiento de PDFs")
        print()
    
    # Probar con archivos de ejemplo si existen
    print("2️⃣  Probando conversiones con archivos de ejemplo...")
    print("-" * 70)
    
    test_files = [
        'app/uploads/*.pdf',
        'app/uploads/*.docx',
        'app/uploads/*.xlsx',
        'app/uploads/*.xlsm'
    ]
    
    import glob
    found_files = []
    for pattern in test_files:
        found_files.extend(glob.glob(pattern))
    
    if not found_files:
        print("ℹ️  No hay archivos de prueba en app/uploads/")
        print("   Carga algunos archivos para probar las conversiones")
        print()
        print("💡 Tip: Copia archivos de prueba a app/uploads/")
        print("   - test.pdf (para probar PDF → PNG)")
        print("   - test.docx (para probar DOCX → PDF)")
        print("   - test.xlsx (para probar Excel → PDF)")
    else:
        success_count = 0
        for file_path in found_files[:3]:  # Probar máximo 3 archivos
            if test_conversion(file_path):
                success_count += 1
        
        print()
        print(f"📊 Resultado: {success_count}/{len(found_files[:3])} conversiones exitosas")
    
    print()
    print("=" * 70)
    print("✅ Tests completados")
    print("=" * 70)
    
    if libreoffice_ok and poppler_ok:
        print("🎯 Tu entorno está listo para todas las conversiones")
    elif libreoffice_ok:
        print("⚠️  Instala poppler-utils para habilitar conversión PDF → PNG")
    elif poppler_ok:
        print("⚠️  Instala LibreOffice para habilitar conversiones Office → PDF")
    else:
        print("❌ Ejecuta en Docker para tener todas las herramientas")
