#!/usr/bin/env python3
"""
Test wszystkich mikroserwisów MOTOSPECT
Kompleksowe testy wszystkich endpointów
"""

import requests
import json
import sys
import time
from datetime import datetime

def test_microservices():
    """Testowanie wszystkich mikroserwisów"""
    
    print("="*60)
    print("TESTY MIKROSERWISÓW MOTOSPECT")
    print(f"Czas rozpoczęcia: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    services = {
        "API Gateway": "http://localhost:8000",
        "VIN Decoder": "http://localhost:8001",
        "Fault Detector": "http://localhost:8002",
        "Diagnostic": "http://localhost:8003",
        "MQTT Bridge": "http://localhost:8004"
    }
    
    test_results = []
    test_vin = "1HGBH41JXMN109186"
    
    # Test 1: Sprawdzenie health endpointów
    print("\n📋 TEST 1: Sprawdzanie endpointów /health")
    print("-" * 40)
    
    for name, url in services.items():
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                port = data.get("port", "?")
                print(f"✅ {name}: DZIAŁA (port: {port}, status: {status})")
                test_results.append({"test": f"{name} Health", "passed": True})
            else:
                print(f"❌ {name}: Błąd HTTP {response.status_code}")
                test_results.append({"test": f"{name} Health", "passed": False})
        except Exception as e:
            print(f"❌ {name}: Nie odpowiada - {str(e)[:50]}")
            test_results.append({"test": f"{name} Health", "passed": False})
    
    # Test 2: VIN Decoder Service
    print("\n📋 TEST 2: VIN Decoder Service")
    print("-" * 40)
    
    # Walidacja VIN
    try:
        response = requests.get(f"{services['VIN Decoder']}/api/vin/validate/{test_vin}")
        data = response.json()
        if data.get("valid") == True:
            print(f"✅ Walidacja VIN: Poprawny VIN - {data.get('vin')}")
            test_results.append({"test": "VIN Validation", "passed": True})
        else:
            print(f"❌ Walidacja VIN: Błąd")
            test_results.append({"test": "VIN Validation", "passed": False})
    except Exception as e:
        print(f"❌ Walidacja VIN: {e}")
        test_results.append({"test": "VIN Validation", "passed": False})
    
    # Dekodowanie VIN
    try:
        response = requests.get(f"{services['VIN Decoder']}/api/vin/decode/{test_vin}")
        data = response.json()
        if "make" in data and "model" in data:
            print(f"✅ Dekodowanie VIN: {data.get('make')} {data.get('model')} ({data.get('year')})")
            test_results.append({"test": "VIN Decode", "passed": True})
        else:
            print(f"❌ Dekodowanie VIN: Brak danych")
            test_results.append({"test": "VIN Decode", "passed": False})
    except Exception as e:
        print(f"❌ Dekodowanie VIN: {e}")
        test_results.append({"test": "VIN Decode", "passed": False})
    
    # Test 3: Fault Detector Service
    print("\n📋 TEST 3: Fault Detector Service")
    print("-" * 40)
    
    try:
        test_data = {"rpm": 2500, "coolant_temp": 85, "oil_pressure": 40}
        response = requests.post(f"{services['Fault Detector']}/api/fault/analyze", json=test_data)
        data = response.json()
        if "health_score" in data:
            print(f"✅ Analiza usterek: Wynik zdrowia = {data.get('health_score')}")
            test_results.append({"test": "Fault Analysis", "passed": True})
        else:
            print(f"❌ Analiza usterek: Brak wyniku")
            test_results.append({"test": "Fault Analysis", "passed": False})
    except Exception as e:
        print(f"❌ Analiza usterek: {e}")
        test_results.append({"test": "Fault Analysis", "passed": False})
    
    try:
        response = requests.get(f"{services['Fault Detector']}/api/fault/codes")
        data = response.json()
        if "codes" in data:
            print(f"✅ Kody usterek: Znaleziono {len(data.get('codes', []))} kodów")
            test_results.append({"test": "Fault Codes", "passed": True})
        else:
            print(f"❌ Kody usterek: Brak kodów")
            test_results.append({"test": "Fault Codes", "passed": False})
    except Exception as e:
        print(f"❌ Kody usterek: {e}")
        test_results.append({"test": "Fault Codes", "passed": False})
    
    # Test 4: Diagnostic Service
    print("\n📋 TEST 4: Diagnostic Service")
    print("-" * 40)
    
    try:
        test_data = {"vin": test_vin, "mileage": 50000}
        response = requests.post(f"{services['Diagnostic']}/api/diagnostic/report", json=test_data)
        data = response.json()
        if "report_id" in data and "vehicle_health" in data:
            health = data.get("vehicle_health", {})
            print(f"✅ Raport diagnostyczny: ID={data.get('report_id')}, Ogólny wynik={health.get('overall_score')}")
            test_results.append({"test": "Diagnostic Report", "passed": True})
        else:
            print(f"❌ Raport diagnostyczny: Brak danych")
            test_results.append({"test": "Diagnostic Report", "passed": False})
    except Exception as e:
        print(f"❌ Raport diagnostyczny: {e}")
        test_results.append({"test": "Diagnostic Report", "passed": False})
    
    # Test 5: MQTT Bridge Service
    print("\n📋 TEST 5: MQTT Bridge Service")
    print("-" * 40)
    
    try:
        response = requests.get(f"{services['MQTT Bridge']}/api/mqtt/status")
        data = response.json()
        if "connected" in data:
            print(f"✅ Status MQTT: Połączony={data.get('connected')}, Aktywne tematy={len(data.get('active_topics', []))}")
            test_results.append({"test": "MQTT Status", "passed": True})
        else:
            print(f"❌ Status MQTT: Brak statusu")
            test_results.append({"test": "MQTT Status", "passed": False})
    except Exception as e:
        print(f"❌ Status MQTT: {e}")
        test_results.append({"test": "MQTT Status", "passed": False})
    
    try:
        test_data = {"topic": "vehicle/test", "message": "test_message"}
        response = requests.post(f"{services['MQTT Bridge']}/api/mqtt/publish", json=test_data)
        data = response.json()
        if data.get("status") == "published":
            print(f"✅ Publikacja MQTT: Wiadomość opublikowana, ID={data.get('message_id')}")
            test_results.append({"test": "MQTT Publish", "passed": True})
        else:
            print(f"❌ Publikacja MQTT: Niepowodzenie")
            test_results.append({"test": "MQTT Publish", "passed": False})
    except Exception as e:
        print(f"❌ Publikacja MQTT: {e}")
        test_results.append({"test": "MQTT Publish", "passed": False})
    
    # Test 6: API Gateway routing
    print("\n📋 TEST 6: API Gateway - routing żądań")
    print("-" * 40)
    
    try:
        response = requests.get(f"{services['API Gateway']}/services/status", timeout=10)
        data = response.json()
        healthy = sum(1 for s in data.values() if s.get("status") == "healthy")
        total = len(data)
        print(f"✅ Status usług: {healthy}/{total} usług działa poprawnie")
        test_results.append({"test": "Gateway Status", "passed": healthy == total})
    except Exception as e:
        print(f"❌ Status usług: {e}")
        test_results.append({"test": "Gateway Status", "passed": False})
    
    try:
        response = requests.get(f"{services['API Gateway']}/api/vin/decode/{test_vin}")
        if response.status_code == 200 and "make" in response.json():
            print(f"✅ Gateway VIN routing: Dekodowanie przez gateway działa")
            test_results.append({"test": "Gateway VIN Route", "passed": True})
        else:
            print(f"❌ Gateway VIN routing: Błąd routingu")
            test_results.append({"test": "Gateway VIN Route", "passed": False})
    except Exception as e:
        print(f"❌ Gateway VIN routing: {e}")
        test_results.append({"test": "Gateway VIN Route", "passed": False})
    
    try:
        test_data = {"rpm": 3000, "temp": 90}
        response = requests.post(f"{services['API Gateway']}/api/fault/analyze", json=test_data)
        if response.status_code == 200 and "health_score" in response.json():
            print(f"✅ Gateway Fault routing: Analiza przez gateway działa")
            test_results.append({"test": "Gateway Fault Route", "passed": True})
        else:
            print(f"❌ Gateway Fault routing: Błąd routingu")
            test_results.append({"test": "Gateway Fault Route", "passed": False})
    except Exception as e:
        print(f"❌ Gateway Fault routing: {e}")
        test_results.append({"test": "Gateway Fault Route", "passed": False})
    
    # Test 7: Wydajność
    print("\n📋 TEST 7: Wydajność i czasy odpowiedzi")
    print("-" * 40)
    
    response_times = []
    for name, url in services.items():
        try:
            start = time.time()
            response = requests.get(f"{url}/health", timeout=5)
            elapsed = time.time() - start
            response_times.append(elapsed)
            
            if elapsed < 1.0:
                print(f"✅ {name}: Czas odpowiedzi {elapsed:.3f}s")
                test_results.append({"test": f"{name} Performance", "passed": True})
            else:
                print(f"❌ {name}: Zbyt wolno - {elapsed:.3f}s")
                test_results.append({"test": f"{name} Performance", "passed": False})
        except Exception as e:
            print(f"❌ {name}: Błąd wydajności - {e}")
            test_results.append({"test": f"{name} Performance", "passed": False})
    
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        print(f"\n📊 Średni czas odpowiedzi: {avg_time:.3f}s")
    
    # Podsumowanie
    print("\n" + "="*60)
    print("PODSUMOWANIE TESTÓW")
    print("="*60)
    
    total = len(test_results)
    passed = sum(1 for r in test_results if r["passed"])
    failed = total - passed
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n📊 Wyniki:")
    print(f"   Wszystkie testy: {total}")
    print(f"   ✅ Zaliczone: {passed}")
    print(f"   ❌ Niezaliczone: {failed}")
    print(f"   📈 Wskaźnik sukcesu: {success_rate:.1f}%")
    
    if failed > 0:
        print(f"\n❌ Testy które nie przeszły:")
        for result in test_results:
            if not result["passed"]:
                print(f"   • {result['test']}")
    
    # Zapis wyników
    with open("test_results_polish.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "podsumowanie": {
                "wszystkie": total,
                "zaliczone": passed,
                "niezaliczone": failed,
                "wskaznik_sukcesu": success_rate
            },
            "wyniki": test_results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Wyniki zapisane do test_results_polish.json")
    
    if success_rate == 100:
        print("\n🎉 WSZYSTKIE TESTY ZALICZONE!")
        return 0
    elif success_rate >= 80:
        print("\n⚠️  Większość testów zaliczona")
        return 1
    else:
        print("\n❌ Wiele testów niezaliczonych")
        return 1

if __name__ == "__main__":
    try:
        exit_code = test_microservices()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Testy przerwane przez użytkownika")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Błąd testów: {e}")
        sys.exit(1)
