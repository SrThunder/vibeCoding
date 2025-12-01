#!/usr/bin/env python3
"""
Quick Verification Script - DOLMEN RAG MVP
Ejecutar: python scripts/verify_project.py

Valida:
1. Estructura de archivos
2. Sintaxis Python
3. JSON validity
4. Dependencias instaladas
5. Configuración .env
"""

import os
import sys
import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_mark(passed):
    return f"{GREEN}✅{RESET}" if passed else f"{RED}❌{RESET}"

def print_section(title):
    print(f"\n{BLUE}{'='*50}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'='*50}{RESET}")

def check_file_exists(filepath, description=""):
    full_path = PROJECT_ROOT / filepath
    passed = full_path.exists()
    status = check_mark(passed)
    desc = f" ({description})" if description else ""
    print(f"{status} {filepath}{desc}")
    return passed

def check_json_valid(filepath):
    full_path = PROJECT_ROOT / filepath
    try:
        with open(full_path, 'r') as f:
            json.load(f)
        return True
    except Exception as e:
        print(f"   {RED}Error: {e}{RESET}")
        return False

def check_python_syntax(filepath):
    full_path = PROJECT_ROOT / filepath
    try:
        with open(full_path, 'r') as f:
            compile(f.read(), filepath, 'exec')
        return True
    except SyntaxError as e:
        print(f"   {RED}Syntax Error: {e}{RESET}")
        return False

def check_import(module_name):
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

# START VERIFICATION
print(f"\n{BLUE}🔍 DOLMEN RAG MVP - Project Verification{RESET}")
print(f"Project Root: {PROJECT_ROOT}\n")

all_checks_passed = True

# ============================================================================
print_section("1. STRUCTURE VERIFICATION")

required_files = [
    ("backend/main.py", "FastAPI app"),
    ("backend/requirements.txt", "Dependencies"),
    ("backend/.env.example", "Env template"),
    ("frontend/app.py", "Streamlit UI"),
    ("rag_pipeline.py", "RAG logic"),
    ("ingest_catalog.py", "Data ingestion"),
    ("catalogo_jerarquia.json", "Product catalog"),
    ("faq_poc.json", "FAQ database"),
    ("scripts/test_backend.py", "Backend tests"),
    ("scripts/setup_supabase.py", "Supabase setup"),
    ("README.md", "Setup guide"),
    ("plan_proyecto", "Project plan"),
    ("CHECKLIST_DEPLOYMENT.md", "Deployment steps"),
    ("TROUBLESHOOTING.md", "Debug guide"),
    ("FILE_INDEX.md", "File directory"),
    (".gitignore", "Git exclusions"),
]

files_ok = 0
for filepath, desc in required_files:
    if check_file_exists(filepath, desc):
        files_ok += 1
    else:
        all_checks_passed = False

print(f"\nResult: {files_ok}/{len(required_files)} files found")

# ============================================================================
print_section("2. JSON VALIDATION")

json_files = [
    ("catalogo_jerarquia.json", "18 products"),
    ("faq_poc.json", "15 FAQs"),
]

json_ok = 0
for filepath, desc in json_files:
    full_path = PROJECT_ROOT / filepath
    if full_path.exists():
        if check_json_valid(filepath):
            status = check_mark(True)
            print(f"{status} {filepath} {desc}")
            json_ok += 1
        else:
            status = check_mark(False)
            print(f"{status} {filepath} {desc} - INVALID JSON")
            all_checks_passed = False
    else:
        print(f"{RED}❌{RESET} {filepath} - FILE NOT FOUND")
        all_checks_passed = False

print(f"\nResult: {json_ok}/{len(json_files)} JSON files valid")

# ============================================================================
print_section("3. PYTHON SYNTAX")

python_files = [
    ("backend/main.py", "FastAPI app"),
    ("backend/requirements.txt", "Will skip (txt)"),
    ("frontend/app.py", "Streamlit UI"),
    ("rag_pipeline.py", "RAG logic"),
    ("ingest_catalog.py", "Data ingestion"),
    ("scripts/test_backend.py", "Backend tests"),
    ("scripts/setup_supabase.py", "Supabase setup"),
]

syntax_ok = 0
for filepath, desc in python_files:
    if filepath.endswith(".txt"):
        print(f"⏭️  {filepath} (skipped)")
        continue
    
    full_path = PROJECT_ROOT / filepath
    if full_path.exists():
        if check_python_syntax(filepath):
            status = check_mark(True)
            print(f"{status} {filepath}")
            syntax_ok += 1
        else:
            status = check_mark(False)
            print(f"{status} {filepath} - SYNTAX ERROR")
            all_checks_passed = False
    else:
        print(f"{RED}❌{RESET} {filepath} - FILE NOT FOUND")
        all_checks_passed = False

print(f"\nResult: {syntax_ok}/{len(python_files)-1} Python files valid")

# ============================================================================
print_section("4. DEPENDENCIES CHECK")

required_packages = [
    ("fastapi", "FastAPI framework"),
    ("uvicorn", "ASGI server"),
    ("streamlit", "Frontend framework"),
    ("pydantic", "Data validation"),
    ("pyjwt", "JWT tokens"),
    ("passlib", "Password hashing"),
    ("openai", "OpenAI API"),
    ("langchain", "RAG framework"),
    ("python-dotenv", "Environment variables"),
    ("requests", "HTTP client"),
    ("psycopg2", "PostgreSQL"),
]

packages_ok = 0
print("\nChecking installed packages...")
for package, desc in required_packages:
    if check_import(package):
        status = check_mark(True)
        print(f"{status} {package:20s} {YELLOW}({desc}){RESET}")
        packages_ok += 1
    else:
        status = check_mark(False)
        print(f"{status} {package:20s} {YELLOW}({desc}) - NOT INSTALLED{RESET}")

print(f"\nResult: {packages_ok}/{len(required_packages)} packages installed")

if packages_ok < len(required_packages):
    print(f"\n{YELLOW}⚠️  Install missing packages:{RESET}")
    print(f"   pip install -r backend/requirements.txt")

# ============================================================================
print_section("5. ENVIRONMENT CONFIGURATION")

env_file = PROJECT_ROOT / "backend/.env"
env_example = PROJECT_ROOT / "backend/.env.example"

if env_file.exists():
    print(f"{GREEN}✅{RESET} .env file found")
    # Check if has required variables
    with open(env_file, 'r') as f:
        env_content = f.read()
        required_vars = ["SUPABASE_URL", "SUPABASE_KEY", "OPENAI_API_KEY", "JWT_SECRET_KEY"]
        vars_found = 0
        for var in required_vars:
            if var in env_content and f"{var}=" in env_content:
                value = env_content.split(f"{var}=")[1].split('\n')[0]
                is_set = value and not value.startswith("your-") and value != ""
                if is_set:
                    print(f"   {GREEN}✅{RESET} {var:30s} (set)")
                    vars_found += 1
                else:
                    print(f"   {YELLOW}⚠️ {RESET} {var:30s} (not configured)")
            else:
                print(f"   {RED}❌{RESET} {var:30s} (missing)")
else:
    print(f"{YELLOW}⚠️ {RESET} .env file not found")
    print(f"   Copy from .env.example: cp backend/.env.example backend/.env")
    print(f"   Then fill with real credentials")

# ============================================================================
print_section("6. DATA INVENTORY")

# Check catalogo JSON
with open(PROJECT_ROOT / "catalogo_jerarquia.json", 'r') as f:
    catalog = json.load(f)
    print(f"{GREEN}✅{RESET} Catalog: {len(catalog)} products")

# Check FAQs JSON
with open(PROJECT_ROOT / "faq_poc.json", 'r') as f:
    faqs = json.load(f)
    print(f"{GREEN}✅{RESET} FAQs: {len(faqs)} questions")

# ============================================================================
print_section("7. DOCUMENTATION")

docs = [
    ("README.md", "Setup & API documentation"),
    ("EXECUTIVE_SUMMARY.md", "Project overview"),
    ("CHECKLIST_DEPLOYMENT.md", "Deployment guide"),
    ("TROUBLESHOOTING.md", "Debug guide"),
    ("FILE_INDEX.md", "File directory"),
    ("plan_proyecto", "Project plan"),
]

docs_ok = 0
for doc, desc in docs:
    if check_file_exists(doc, desc):
        docs_ok += 1
    else:
        all_checks_passed = False

print(f"\nResult: {docs_ok}/{len(docs)} documentation files found")

# ============================================================================
print_section("FINAL RESULT")

if all_checks_passed and packages_ok == len(required_packages):
    print(f"\n{GREEN}✅ ALL CHECKS PASSED - PROJECT READY{RESET}\n")
    print("Next steps:")
    print("1. Ensure .env is configured with real credentials")
    print("2. Run: python scripts/setup_supabase.py")
    print("3. Run: python ingest_catalog.py")
    print("4. Start backend: cd backend && uvicorn main:app --reload")
    print("5. Start frontend: cd frontend && streamlit run app.py")
    print("6. Test: python scripts/test_backend.py\n")
    sys.exit(0)
else:
    print(f"\n{RED}❌ SOME CHECKS FAILED - SEE ABOVE{RESET}\n")
    if packages_ok < len(required_packages):
        print(f"Missing packages. Install with:")
        print(f"  pip install -r backend/requirements.txt\n")
    sys.exit(1)
