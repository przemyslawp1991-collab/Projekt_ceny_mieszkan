# API i panel w Dockerze

Docker uruchamia zapisany model wraz z Pythonem i bibliotekami we własnym środowisku. Dołączona konfiguracja obsługuje panel WWW i API w tym samym kontenerze. Nie trenuje modelu przy starcie ani nie pobiera nowych danych.

## 1. Przygotowanie Windows

Zainstaluj i uruchom Docker Desktop według oficjalnej instrukcji:
https://docs.docker.com/desktop/setup/install/windows-install/

Docker Desktop zawiera Docker Compose:
https://docs.docker.com/compose/install/

Użyj kontenerów Linux. Poczekaj na gotowość silnika i otwórz nowe okno PowerShell. Sprawdź:

```powershell
docker version
docker compose version
```

`docker version` powinno pokazywać część Client i Server. Sama instalacja programu bez uruchomienia silnika nie wystarcza. Jeśli instalator zgłosi wymagania WSL 2 lub wirtualizacji, postępuj zgodnie z oficjalną instrukcją. Nie trzeba ręcznie instalować pakietów projektu w Windows.

## 2. Uruchomienie

```powershell
cd "C:\Users\Przemysław Pawlak\Desktop\Projekt DS gotowy\Projekt_ceny_mieszkan"
docker compose up --build -d --wait
```

Pierwsze uruchomienie pobiera obraz Pythona oraz biblioteki i może potrwać kilka minut. Kolejne uruchomienia korzystają z już zbudowanego obrazu. Polecenie czeka na pozytywny health check.

- Panel: http://127.0.0.1:8000/
- Dokumentacja API: http://127.0.0.1:8000/docs
- Kontrola dostępności serwera: http://127.0.0.1:8000/health

Przykład PowerShell:

```powershell
$body = @{ area = 'Warszawa'; market = 'secondary' } | ConvertTo-Json
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/predict' -Method Post -ContentType 'application/json; charset=utf-8' -Body $body | ConvertTo-Json -Depth 5
```

Nie trzeba uruchamiać jednocześnie `run.ps1 api` ani `uvicorn` w lokalnym środowisku. Jeśli wcześniejszy serwer zajmuje port 8000, zatrzymaj go w jego konsoli przez Ctrl+C albo wybierz port 8001:

```powershell
$env:API_PORT = '8001'
docker compose up --build -d --wait
```

Wtedy panel i API będą pod http://127.0.0.1:8001/ . Port wewnątrz kontenera nadal wynosi 8000. Zmienna API_PORT obowiązuje w bieżącej sesji PowerShell.

## 3. Stan, logi i zatrzymanie

```powershell
docker compose ps
docker compose logs --tail 100 api
docker compose down
```

`down` zatrzymuje i usuwa kontener, zachowując pliki projektu i zbudowany obraz. Health check sprawdza odpowiedź serwera; pełną predykcję weryfikuje dodatkowy test HTTP.

## 4. Testy kontenera

```powershell
docker compose run --rm --no-deps api python -m pytest -q
docker compose exec api python tests/smoke_http.py
```

Druga komenda wymaga już uruchomionej usługi. Sprawdza stronę główną, CSS i JavaScript, katalog miast, dokumentację, pięć rzeczywistych prognoz i odrzucenie błędnego miasta.

Te same operacje wykonuje zadanie `docker` w GitHub Actions: walidacja Compose, budowanie obrazu, testy w obrazie, uruchomienie kontenera oraz sprawdzenie przez HTTP. Wynik należy sprawdzić w zakładce Actions, a nie utożsamiać samą obecność Dockerfile z działającym wdrożeniem.

## Zakres wdrożenia

Konfiguracja udostępnia aplikację lokalnie na 127.0.0.1. Sam Docker nie publikuje panelu w internecie. Nadal używamy zamrożonego scenariusza badawczego 2026Q3, a nie aktualizowanego na żywo modelu.
