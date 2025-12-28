#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema Apex AI
"""

import requests
import json
import sys
from time import sleep

BASE_URL = "http://localhost:8000"

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_success(text):
    print(f"✓ {text}")

def print_error(text):
    print(f"✗ {text}")

def print_info(text):
    print(f"ℹ {text}")

def test_health():
    """Probar endpoint de health"""
    print_header("TEST 1: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Backend activo - Status: {data.get('status')}")
            print_info(f"RAG disponible: {data.get('rag_available')}")
            print_info(f"Vector DB: {data.get('vectorstore_status')}")
            return True
        else:
            print_error(f"Health check falló: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("No se puede conectar al backend. ¿Está corriendo en el puerto 8000?")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_agents():
    """Probar endpoint de agentes"""
    print_header("TEST 2: Obtener Agentes")
    try:
        response = requests.get(f"{BASE_URL}/api/agents", timeout=5)
        if response.status_code == 200:
            agents = response.json()
            print_success(f"Se encontraron {len(agents)} agentes:")
            for agent in agents:
                print(f"  - {agent['name']} ({agent['id']})")
            return True
        else:
            print_error(f"Error obteniendo agentes: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_query(agent_id="general", query="¿Qué es un sistema RAG?"):
    """Probar endpoint de consulta"""
    print_header(f"TEST 3: Consulta RAG (Agente: {agent_id})")
    print_info(f"Query: {query}")
    
    try:
        payload = {
            "query": query,
            "agent": agent_id,
            "max_sources": 3
        }
        
        response = requests.post(
            f"{BASE_URL}/api/query",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Respuesta recibida")
            print("\nRespuesta del agente:")
            print("-" * 60)
            print(data['answer'][:300] + "..." if len(data['answer']) > 300 else data['answer'])
            print("-" * 60)
            
            if data.get('sources'):
                print(f"\nFuentes consultadas ({len(data['sources'])}):")
                for i, source in enumerate(data['sources'], 1):
                    print(f"  {i}. {source.get('title')} - Score: {source.get('score', 0):.2f}")
            
            return True
        else:
            print_error(f"Error en consulta: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_stats():
    """Probar endpoint de estadísticas"""
    print_header("TEST 4: Estadísticas del Sistema")
    try:
        response = requests.get(f"{BASE_URL}/api/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print_success("Estadísticas obtenidas:")
            print(f"  - Documentos totales: {stats.get('total_documents')}")
            print(f"  - Chunks totales: {stats.get('total_chunks')}")
            print(f"  - Agentes disponibles: {stats.get('agents_available')}")
            print(f"  - Estado Vector DB: {stats.get('vector_db_status')}")
            return True
        else:
            print_error(f"Error obteniendo stats: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_all_agents():
    """Probar consulta con todos los agentes"""
    print_header("TEST 5: Probar Todos los Agentes")
    
    queries = {
        "general": "¿Qué puedes hacer?",
        "hr": "¿Cuáles son los requisitos de la Ley Karin?",
        "legal": "¿Qué es el compliance?",
        "technical": "Explica qué es un sistema RAG",
        "training": "¿Cómo diseñar un buen curso de capacitación?"
    }
    
    results = []
    for agent_id, query in queries.items():
        print(f"\n→ Probando agente: {agent_id}")
        print(f"  Query: {query}")
        
        try:
            payload = {"query": query, "agent": agent_id, "max_sources": 2}
            response = requests.post(f"{BASE_URL}/api/query", json=payload, timeout=30)
            
            if response.status_code == 200:
                print_success(f"Agente {agent_id} respondió correctamente")
                results.append(True)
            else:
                print_error(f"Agente {agent_id} falló")
                results.append(False)
                
            sleep(1)  # Pequeña pausa entre requests
            
        except Exception as e:
            print_error(f"Error con agente {agent_id}: {e}")
            results.append(False)
    
    success_rate = (sum(results) / len(results)) * 100
    print(f"\n→ Tasa de éxito: {success_rate:.0f}% ({sum(results)}/{len(results)} agentes)")
    return all(results)

def run_all_tests():
    """Ejecutar todos los tests"""
    print("\n" + "🚀 APEX AI - SUITE DE PRUEBAS".center(60))
    print("="*60)
    
    tests = [
        ("Health Check", test_health),
        ("Obtener Agentes", test_agents),
        ("Consulta Simple", lambda: test_query("general", "Hola, ¿cómo estás?")),
        ("Estadísticas", test_stats),
        ("Todos los Agentes", test_all_agents),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
            sleep(1)
        except KeyboardInterrupt:
            print("\n\n⚠ Tests interrumpidos por el usuario")
            sys.exit(1)
        except Exception as e:
            print_error(f"Error ejecutando {name}: {e}")
            results.append((name, False))
    
    # Resumen
    print_header("RESUMEN DE PRUEBAS")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {name}")
    
    print("\n" + "-"*60)
    print(f"Total: {passed}/{total} tests pasaron ({(passed/total)*100:.0f}%)")
    
    if passed == total:
        print_success("¡Todos los tests pasaron! Sistema funcionando correctamente 🎉")
        return 0
    else:
        print_error("Algunos tests fallaron. Revisar logs para más detalles.")
        return 1

def interactive_mode():
    """Modo interactivo para probar consultas"""
    print_header("MODO INTERACTIVO")
    print("Escribe 'exit' para salir\n")
    
    # Obtener agentes disponibles
    try:
        response = requests.get(f"{BASE_URL}/api/agents")
        agents = response.json()
        agent_ids = [a['id'] for a in agents]
    except:
        print_error("No se pudieron obtener los agentes")
        return
    
    print("Agentes disponibles:", ", ".join(agent_ids))
    print()
    
    while True:
        try:
            # Seleccionar agente
            agent = input("Agente (default: general): ").strip() or "general"
            if agent == "exit":
                break
            
            if agent not in agent_ids:
                print_error(f"Agente '{agent}' no válido")
                continue
            
            # Ingresar query
            query = input("Tu consulta: ").strip()
            if query == "exit":
                break
            
            if not query:
                continue
            
            # Hacer consulta
            print("\n⏳ Procesando...\n")
            payload = {"query": query, "agent": agent, "max_sources": 3}
            response = requests.post(f"{BASE_URL}/api/query", json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print("-" * 60)
                print(data['answer'])
                print("-" * 60)
                
                if data.get('sources'):
                    print(f"\nFuentes: {len(data['sources'])}")
                    for i, s in enumerate(data['sources'], 1):
                        print(f"  {i}. {s['title']} ({s.get('score', 0):.0%})")
            else:
                print_error(f"Error: {response.status_code}")
            
            print()
            
        except KeyboardInterrupt:
            print("\n")
            break
        except Exception as e:
            print_error(f"Error: {e}")
    
    print("¡Hasta luego!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        exit_code = run_all_tests()
        sys.exit(exit_code)
