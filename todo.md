# Lista Zadań - Projekt MOTOSPECT

## Faza 1: Inicjalizacja projektu i konfiguracja Docker

- [x] Utworzenie struktury katalogów (backend, frontend)
- [x] Stworzenie pliku `docker-compose.yml`
- [x] Stworzenie `Dockerfile` dla aplikacji backendowej (Python/FastAPI)
- [x] Stworzenie `Dockerfile` dla aplikacji frontendowej (React)
- [x] Inicjalizacja podstawowych plików aplikacji (backend i frontend)

## Faza 2: Implementacja Backendu

- [x] Utworzenie głównych modułów Pythona (`motospect_core.py`, `sensor_modules.py`, etc.)
- [x] Implementacja logiki serwera FastAPI
- [x] Definicja endpointów API (`/api/scan/start`, `/api/scan/{scan_id}/results`, `/api/scan/stop/{scan_id}`)
- [x] Implementacja komunikacji WebSocket

## Faza 3: Implementacja Frontendu

- [x] Inicjalizacja aplikacji React
- [x] Stworzenie komponentu wizualizacji 3D (`VehicleVisualization.jsx`)
- [x] Implementacja połączenia WebSocket z backendem
- [x] Stworzenie interfejsu użytkownika do sterowania skanowaniem i wyświetlania wyników (wersja rozszerzona)
- [x] Dodane podstawowe sterowanie skanem (Start/Stop) i filtr kanałów w `VehicleVisualization.jsx`

## Faza 4: Testowanie i Wdrożenie

- [x] Uruchomienie projektu za pomocą `docker-compose`
- [x] Testowanie komunikacji między backendem a frontendem
- [x] Testowanie podstawowych funkcjonalności skanowania (z mockowanymi danymi)
- [x] Przygotowanie do wdrożenia

## Faza Pilot: Bramka drive-through (budżet ≤ $2500)

- [ ] Sprzęt: lista zakupowa (Raspberry Pi 4 lub mini PC, SSD, zasilanie 12–24V, kamera RGB, MLX90640/Lepton, matryca mikrofonów, ToF/LiDAR, akcelerometry/IMU, BME280, miernik lakieru, profile alu, stojaki, kable)
- [ ] Mechanika: projekt i montaż 2 kolumn + 1 listwy dolnej; rozmieszczenie sensorów i uchwytów
- [ ] Okablowanie i zasilanie: wiązki kabli, zabezpieczenia IP54, prowadzenie przewodów, bezpieczniki
- [ ] System: instalacja OS (Raspberry Pi OS/Ubuntu), konfiguracja sieci, SSH, synchronizacja czasu
- [ ] Oprogramowanie: instalacja Docker/Compose, uruchomienie `backend/` (FastAPI+WebSocket) i `frontend/` (React)
- [ ] Integracje sensorów: sterowniki i biblioteki (V4L2/libcamera, MLX90640/Lepton, ReSpeaker, RPLIDAR/ToF, IMU, BME280)
- [ ] Pipeline danych: zbieranie strumieni, timestamping, buforowanie, publikacja przez WebSocket do UI
- [ ] Wyzwalanie przejazdu: fotoprzerzutnik/ultradźwięk; start/stop sesji i identyfikator przejazdu
- [ ] Wizualizacja: widok na żywo RGB + termika + mapa dźwięku + profil odległości + overlay anomalii
- [ ] Anomalie MVP: progi temperatury, głośności (FFT), odległości, podstawowe reguły
- [ ] Raport: snapshoty + CSV/PDF z listą „uwag” i tagami lokalizacji
- [ ] Kalibracja: macierze kamer, mapowanie termiki na RGB, kalibracja mikrofonów (pozycje), sanity-check ToF
- [ ] Testy poligonowe: 10–20 aut, logi, metadane, wnioski i iteracja sprzętowa/soft
- [ ] Bezpieczeństwo: BHP przy pracy w warsztacie, izolacja przewodów, brak ostrych krawędzi, znaki ostrzegawcze
