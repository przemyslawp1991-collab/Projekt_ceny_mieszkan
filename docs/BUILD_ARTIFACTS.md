# Artefakty wydania

Analiza, model, tabele i raportHTML odtwarzają się przez python -m src.pipeline all. Notebooki wykonano w osobnym środowisku tego projektu; podczas własnego uruchomienia wybierz kernel z .venv. Skrypt docs/build_notebooks.py odtwarza notebooki i wykonuje ich komórki.

RaportPDF i podsumowanie: python docs/build_pdf.py. Skrypt używa wyłącznie gotowych tabel i wykresów, bez ponownego strojenia modelu.

Prezentacja została zbudowana z natywnych tekstów i wykresów w @oai/artifact-tool. Źródło i dane: docs/presentation_source.mjs i docs/presentation_data.json. Wymaga środowiska z pakietem @oai/artifact-tool oraz ścieżek do runtime/finalizatora ustawionych w skrypcie; nie jest częścią zwykłego treningu Python. Dostarczone PPTX/PDF są zamrożonym materiałem wydania. Nie trzeba ich budować do predykcji ani do odtworzenia tabel/modelu. Wersję po zmianie badania należy zrenderować i sprawdzić wizualnie.

Repozytorium publiczne: https://github.com/przemyslawp1991-collab/Projekt_ceny_mieszkan. Sprawdzenie Dockerbuild pozostaje do wykonania w środowisku z silnikiem Docker. Lokalne commity zapisują rzeczywiste etapy składania paczki, bez odtwarzania fikcyjnej historii wcześniejszych prac.

Skrypt notebooków rejestruje lokalny kernel w .jupyter, wskazujący Python użyty do uruchomienia. Interakcję demonstratora Streamlit sprawdzono przez AppTest (wybór Warszawy i odczyt tabeli). Świeża kopia przeszła pełny przebieg oraz 8 testów; model i cechy są identyczne bajtowo, maksymalna różnica prognoz wyniosła 3,64e-12 PLN/m². Szczegóły w reports/logs/clean_copy_reproduction.json.
Porównanie błędu, czasu i rozmiaru wszystkich 7 konfiguracji znajduje się w reports/tables/accuracy_time_size.csv. Czasy są pomiarami lokalnymi, a nie deklaracją kosztu dowolnego serwera.
