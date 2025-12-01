#!/usr/bin/env python3
"""
Script de prueba rápida del backend
Simula llamadas sin necesidad de Supabase
"""

import json
import requests
from time import sleep

BASE_URL = "http://localhost:8000"

def test_health():
    """Test de health check."""
    print("\n🏥 Test: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_login():
    """Test de login."""
    print("\n🔐 Test: Login")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": "demo@dolmen.com",
                "password": "demo123"
            }
        )
        print(f"✅ Status: {response.status_code}")
        data = response.json()
        print(f"Access Token: {data.get('access_token')[:20]}...")
        print(f"Expires in: {data.get('expires_in')} segundos")
        return data.get('access_token')
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_query(token):
    """Test de query RAG."""
    print("\n🤖 Test: Query RAG")
    try:
        response = requests.post(
            f"{BASE_URL}/query",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "pregunta": "¿Qué pintura recomiendan para paredes exteriores?"
            }
        )
        print(f"✅ Status: {response.status_code}")
        data = response.json()
        print(f"Respuesta: {data.get('respuesta')[:100]}...")
        print(f"Fuente: {data.get('fuente')}")
        print(f"Confianza: {data.get('confianza')}")
        print(f"PDF Link: {data.get('pdf_link')}")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_me(token):
    """Test de obtener info del usuario."""
    print("\n👤 Test: Get User Info")
    try:
        response = requests.get(
            f"{BASE_URL}/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"✅ Status: {response.status_code}")
        print(f"User: {response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_logout(token):
    """Test de logout."""
    print("\n🚪 Test: Logout")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"✅ Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 PRUEBAS DE BACKEND - DOLMEN RAG")
    print("=" * 60)
    
    # Test health
    test_health()
    sleep(1)
    
    # Test login
    token = test_login()
    sleep(1)
    
    if token:
        # Test query
        test_query(token)
        sleep(1)
        
        # Test me
        test_me(token)
        sleep(1)
        
        # Test logout
        test_logout(token)
    
    print("\n" + "=" * 60)
    print("✅ Pruebas completadas")
    print("=" * 60)
