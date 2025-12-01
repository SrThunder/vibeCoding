#!/usr/bin/env python3
"""
Script de Testing Automatizado para localhost
Prueba todos los endpoints del backend
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@dolmen.com"
TEST_PASSWORD = "password123"

# Colores para terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(title):
    print(f"\n{Colors.BOLD}{Colors.HEADER}╔{'='*50}╗{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}║ {title:<48} ║{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}╚{'='*50}╝{Colors.ENDC}\n")

def print_test(name, status, details=""):
    icon = "✅" if status else "❌"
    color = Colors.OKGREEN if status else Colors.FAIL
    print(f"{icon} {color}{name}{Colors.ENDC}")
    if details:
        print(f"   {details}")

def test_health_check():
    """Test 1: Health Check"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print_test("Health Check", True, f"Status: {data.get('status', 'unknown')}")
            return True
        else:
            print_test("Health Check", False, f"Status Code: {response.status_code}")
            return False
    except Exception as e:
        print_test("Health Check", False, str(e))
        return False

def test_login_valid():
    """Test 2: Login con credenciales válidas"""
    try:
        payload = {
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        response = requests.post(f"{BASE_URL}/login", json=payload)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                print_test("Login (válido)", True, f"Token recibido: {token[:20]}...")
                return token
            else:
                print_test("Login (válido)", False, "No token en respuesta")
                return None
        else:
            print_test("Login (válido)", False, f"Status: {response.status_code}")
            return None
    except Exception as e:
        print_test("Login (válido)", False, str(e))
        return None

def test_login_invalid():
    """Test 3: Login con credenciales inválidas (debe fallar)"""
    try:
        payload = {
            "username": "invalid@test.com",
            "password": "wrongpassword"
        }
        response = requests.post(f"{BASE_URL}/login", json=payload)
        if response.status_code != 200:
            print_test("Login (inválido - esperado fallar)", True, f"Correctamente rechazado: {response.status_code}")
            return True
        else:
            print_test("Login (inválido - esperado fallar)", False, "Debería haber sido rechazado")
            return False
    except Exception as e:
        print_test("Login (inválido)", False, str(e))
        return False

def test_search(token):
    """Test 4: Búsqueda de productos"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"query": "pintura exterior"}
        response = requests.post(f"{BASE_URL}/search", json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            num_results = len(data.get("products", []))
            print_test("Search", True, f"Encontrados {num_results} productos")
            return True
        else:
            print_test("Search", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("Search", False, str(e))
        return False

def test_chat_simple(token):
    """Test 5: Chat simple"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"query": "Hola"}
        response = requests.post(f"{BASE_URL}/chat", json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            message = data.get("response", "")[:50]
            print_test("Chat Simple", True, f"Respuesta: {message}...")
            return True
        else:
            print_test("Chat Simple", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("Chat Simple", False, str(e))
        return False

def test_chat_rag(token):
    """Test 6: Chat con RAG completo"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"query": "¿Qué pintura recomiendan para exteriores?"}
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/chat", json=payload, headers=headers)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            message = data.get("response", "")[:60]
            print_test("Chat RAG Completo", True, 
                      f"Respuesta en {elapsed:.2f}s: {message}...")
            return True
        else:
            print_test("Chat RAG Completo", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("Chat RAG Completo", False, str(e))
        return False

def test_token_refresh(token):
    """Test 7: Refresh Token"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/token/refresh", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            new_token = data.get("access_token")
            if new_token:
                print_test("Token Refresh", True, f"Nuevo token: {new_token[:20]}...")
                return True
            else:
                print_test("Token Refresh", False, "No nuevo token en respuesta")
                return False
        else:
            print_test("Token Refresh", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("Token Refresh", False, str(e))
        return False

def test_concurrent_messages(token):
    """Test 8: Múltiples mensajes consecutivos"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        queries = [
            "¿Qué es Multimix?",
            "¿Bloques para muros divisorios?",
            "¿Llave Campanola especificaciones?"
        ]
        
        all_ok = True
        for i, query in enumerate(queries, 1):
            payload = {"query": query}
            response = requests.post(f"{BASE_URL}/chat", json=payload, headers=headers)
            if response.status_code != 200:
                all_ok = False
                break
        
        if all_ok:
            print_test("Múltiples Mensajes", True, f"Se procesaron {len(queries)} consultas exitosamente")
            return True
        else:
            print_test("Múltiples Mensajes", False, f"Falló en consulta {i}")
            return False
    except Exception as e:
        print_test("Múltiples Mensajes", False, str(e))
        return False

def main():
    print_header("TESTING LOCAL - DOLMEN RAG MVP")
    print(f"{Colors.OKCYAN}Iniciando pruebas en {BASE_URL}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Timestamp: {datetime.now().isoformat()}{Colors.ENDC}\n")
    
    # Verificar que backend está corriendo
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
    except:
        print(f"{Colors.FAIL}❌ ERROR: Backend no está corriendo en {BASE_URL}{Colors.ENDC}")
        print(f"{Colors.WARNING}Ejecuta en otra terminal:{Colors.ENDC}")
        print(f"  uvicorn backend.main:app --reload --port 8000")
        sys.exit(1)
    
    # Suite de tests
    results = []
    
    # Test 1: Health
    results.append(("Health Check", test_health_check()))
    
    # Test 2: Login válido
    token = test_login_valid()
    results.append(("Login (válido)", token is not None))
    
    if not token:
        print(f"\n{Colors.FAIL}❌ No se pudo obtener token. Deteniendo tests.{Colors.ENDC}")
        sys.exit(1)
    
    # Test 3: Login inválido
    results.append(("Login (inválido - esperado)", test_login_invalid()))
    
    # Test 4: Search
    results.append(("Search", test_search(token)))
    
    # Test 5: Chat simple
    results.append(("Chat Simple", test_chat_simple(token)))
    
    # Test 6: Chat RAG
    results.append(("Chat RAG", test_chat_rag(token)))
    
    # Test 7: Token refresh
    results.append(("Token Refresh", test_token_refresh(token)))
    
    # Test 8: Múltiples mensajes
    results.append(("Múltiples Mensajes", test_concurrent_messages(token)))
    
    # Resumen
    print_header("RESUMEN DE RESULTADOS")
    
    passed = sum(1 for _, status in results if status)
    total = len(results)
    
    for name, status in results:
        icon = "✅" if status else "❌"
        print(f"{icon} {name}")
    
    print(f"\n{Colors.BOLD}Resultados: {passed}/{total} ✅{Colors.ENDC}")
    
    if passed == total:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 ¡TODOS LOS TESTS PASARON!{Colors.ENDC}")
        print(f"{Colors.OKCYAN}Tu sistema está listo para producción.{Colors.ENDC}")
        return 0
    else:
        failed = total - passed
        print(f"\n{Colors.WARNING}{Colors.BOLD}⚠️  {failed} tests fallaron{Colors.ENDC}")
        print(f"{Colors.OKBLUE}Verifica los errores arriba.{Colors.ENDC}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
