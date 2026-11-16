# Prognozowanie średnich cen transakcyjnych mieszkań w Polsce

Repozytorium publiczne: [https://github.com/przemyslawp1991-collab/Projekt_ceny_mieszkan](https://github.com/przemyslawp1991-collab/Projekt_ceny_mieszkan).

Samodzielny projekt zaliczeniowy Data Science, wydzielony15.11.2026. Zakres: **17 miast ×2rynki ×5horyzontów**. Prognozowana jest miejska średnia cena transakcyjna w PLN/m², nie wartość konkretnego lokalu. Pozostałe eksperymenty pozostają w oryginalnym projekcie.

## Najważniejsze pliki

- `reports/raport.html` — pełny raport z EDA, wykresami i interpretacją.
- `reports/raport.pdf` — wersja raportu do wydruku.
- `reports/podsumowanie_1_strona.pdf` — opis dla odbiorcy nietechnicznego.
- `reports/presentation/projekt_ceny_mieszkan.pdf` oraz `.pptx` —13slajdów, plan10minut.
- `notebooks/01_eda.ipynb`, `02_feature_engineering.ipynb`, `03_modeling.ipynb` — wykonane notebooki.
- `models/model.pkl` + `metadata.json` — wybrany model, stały snapshot badawczy.
- `models/isolated_original_rf.joblib` — oryginalny RF, zachowany jako kontrola odtworzenia.
- `docs/REQUIREMENTS_MATRIX.md` — mapowanie wymagań z PDF na artefakty i jawne braki.

## Wynik, który trzeba uczciwie pokazać

Selekcja w6czasowych foldach wybrała **Random Forest120drzew, głębokość6, min.12obserwacji w liściu, okno12dojrzałych kwartałów**. Trzy rodziny algorytmów: RF, Ridge i HistGradientBoosting;7konfiguracji,42próby.

| Ocena h4 | Wybrany RF | Średnia historyczna | Ostatnia znana cena |
|---|---:|---:|---:|
| Diagnostyka2015Q1–2025Q1 (1394grupy) |5,55% MAPE |7,00% |10,70% |
| Zablokowany dla paczki origin2025Q2 (34grupy) |13,76% MAPE |13,41% |**3,88%** |

**Model nie utrzymał przewagi w ostatnim sprawdzonym okresie.** W warunkach wyhamowania cen kontynuował wzrost zakodowany w ostatnim oknie treningowym. Nie zmienialiśmy modelu po obejrzeniu tego wyniku. Projekt dostarcza odtwarzalny eksperyment, porównanie z baseline i identyfikację ograniczeń, a nie potwierdzony system inwestycyjny. MAPE h4 dotyczy końca ścieżki, nie wszystkich horyzontów łącznie.

Oryginalny RF odtworzył wcześniejszą MAPE **5,60065856%** na41datach oraz170punktów aktualnego eksportu z różnicą poniżej1e−7PLN/m². Nowa wersja powstaje z lokalnych oryginalnych plików producentów, zawiera szerszą historię makro i jawny tuning. Nie przedstawiamy różnicy5,60→5,55jako istotnej poprawy.

**Uczciwość walidacji:** historia była wcześniej analizowana. Wynik2015–2025 jest retrospektywny i obejmuje daty użyte do wyboru parametrów. Test2025Q2zamrożono dla tej paczki, lecz nie jest dziewiczym testem prospektywnym: ceny były wcześniej dostępne w szeregach. Jedna data obejmuje wspólne makro i nie wystarcza do oceny generalizacji.

## Dane i cechy

NBP BaRN, GUS, BIS, NBP MIR/SLOOS, AMRON-SARFiN.9337surowych odczytów cen/ofert/indeksów; ceny2006Q3–2026Q2. Po konstrukcji cech:2379grup miasto–rynek–origin i11895etykiet horyzontów. **To2379wektorów, a nie11895niezależnych przypadków rynkowych.** Dane nie są syntetycznie powiększone. Formalny zbiór wielohoryzontowy ma ponad5000rekordów, ale liczba niezależnych cykli jest znacznie mniejsza. Szczegóły w macierzy wymagań.

24cechy numeryczne plus miasto i rynek: dynamika cen i jej przyspieszenie, zmienność, relacja do innych miast/rynków, hedoniczne zmiany, inflacja, poziom/zmiana stóp, płace, koszt i popyt na kredyt, liczba kredytów. [Słownik](docs/DATA_DICTIONARY.md), [źródła i warunki użycia](docs/SOURCES.md), hashe `data/raw/source_manifest.json`. Oferty nie są etykietą. Brak komercyjnych statusów rezerwacji/sprzedaży.

## Uruchomienie — Windows

Python3.13; w dostarczonym folderze istnieje gotowe lokalne `.venv`.

```powershell
cd 'C:\Users\Przemysław Pawlak\Desktop\Projekt DS gotowy\Projekt_ceny_mieszkan'
.\run.ps1 all
.\run.ps1 test
.\run.ps1 api
# W innej konsoli lub po zatrzymaniu API:
.\run.ps1 demo
```

Na czystej kopii:

```powershell
uv venv --python 3.13 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
.\run.ps1 all
.\run.ps1 test
```

W razie firmowego certyfikatu TLS można dodać do uv `--system-certs`. Nie wyłączamy sprawdzania certyfikatów.

Linux/macOS: `python3.13 -m venv .venv`, aktywacja, `pip install -r requirements.txt`, `make all`, `make test`. Alternatywa niezależna od make: **`python -m src.pipeline all`**. W świeżej kopii model i zbiór cech są identyczne bajtowo; prognozy zgadzają się z tolerancją 1e−7. Równoległe sumowanie RF może zmieniać ostatnie cyfry zmiennoprzecinkowe. Czasy i serializacja mogą różnić się między systemami. Pełny plik zależności pośrednich: requirements-lock.txt (zob. marker Windows przy kolorowaniu terminala).

## API i demo

Panel użytkownika: **http://127.0.0.1:8000/**. Zawiera wybór miasta i rynku, karty z cenami, wykres, tabelę prognoz, pobieranie CSV oraz objaśnienie wiarygodności wyników. Działa bez osobnego serwera frontendu i bez zewnętrznych bibliotek wykresów.

Dokumentacja techniczna API: http://127.0.0.1:8000/docs . Przykład:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/predict -ContentType 'application/json; charset=utf-8' -Body '{"area":"Warszawa","market":"secondary"}'
```

Schemat odrzuca nieznane miasta, niepoprawny rynek i dodatkowe pola. Wynik:5cen q…q+4 oraz źródłowy kwartał znanej ceny. Snapshot odniesienia2026Q3został przygotowany15.11.2026, już po kwartale odniesienia; **to archiwalny scenariusz badawczy, nie prognoza live**. h0 jest nowcastem, cena wejściowa2026Q1. Brak skalibrowanych przedziałów predykcji.

Streamlit: `python -m streamlit run app.py`, http://localhost:8501 . Skrypt CLI: `python -m src.predict --area Warszawa --market secondary`.

Docker: `docker build -t ceny-mieszkan .`, `docker run --rm -p 8000:8000 ceny-mieszkan`. **Plik przygotowany, obraz niezweryfikowany lokalnie: brak silnika Docker.** GitHub Actions uruchamia testy po push i pull request. Repozytorium publiczne: https://github.com/przemyslawp1991-collab/Projekt_ceny_mieszkan; zachowano rzeczywistą historię lokalnych commitów etapów. Bieżące wyniki CI są widoczne w zakładce Actions.

## Odtwarzalność, temporal split, interpretacja

`make all`: weryfikacja hashy → odczyt źródeł i EDA → cechy → tuning → zamrożona selekcja → ocena modeli → zapis modelu i raportu HTML. PDF/prezentacja są zamrożonymi materiałami wydania; po zmianie badania wymagają ponownego zbudowania zgodnie z `docs/BUILD_ARTIFACTS.md`. Notebooki odczytują wyniki tego przebiegu; nie wybierają modelu ponownie na teście.

Ceny q−2 (czasem q−1 z kalendarza), makro q−1, kredyty q−2. Etykiety całej ścieżki są dostępne umownie w origin+6 i muszą być **ściśle wcześniejsze** niż prognozowany origin. Wszystkie miasta i horyzonty tego samego origin są w jednym foldzie. Transformacje Pipeline dopasowane wyłącznie na treningu; brak imputacji etykiet, interpolacji i backward fill. Dane są zrewidowane; nie gwarantujemy historycznej dostępności każdej rewizji.

Baseline historyczna to średnia **logarytmicznych zmian ceny od znanej ceny** dla danego miasta i rynku w tym samym oknie12dojrzałych origins; dla każdego horyzontu oddzielnie. To nie średnia cen całej historii i nie przyszła informacja. Szczegóły kodu: src/train.py baselines(). Dodatkowe benchmarki: niezmieniona znana cena oraz ekstrapolacja ostatniego r/r.

Wyjaśnianie: permutacje na ostatnim foldzie walidacyjnym i lokalna analiza wrażliwości dla Warszawy. To nie wnioskowanie przyczynowe i nie SHAP. Niepewność porównania: blokowy bootstrap6kwartałów; nie jest przedziałem przyszłej ceny.

## Struktura

```text
config/config.yaml
data/raw/                 oryginały, wyciągi źródeł i SHA256
data/processed/           ceny, makro, cechy wide, dataset long
data/reference/           zamrożona kontrola oryginalnego modelu
notebooks/                01 EDA, 02 cechy, 03 modelowanie i demo
src/                      prepare_data, features, train, evaluate, predict
api/app.py                FastAPI + Pydantic
app.py                    demonstrator Streamlit
models/                   model.pkl, metadane, protokół, izolowany RF
reports/figures/           7wykresów
reports/tables/            wszystkie próby, predykcje, błędy i audyty
reports/presentation/      PDF + edytowalny PPTX
tests/                    pytest: dane, czas, model, API, odtworzenie
docs/                     wymagania, źródła, słownik, instrukcja obrony
```

`make clean` usuwa wygenerowane tabele/wykresy i dane przetworzone, zachowuje raw i modele kontrolne; potem `make all`. Pobieranie nowych wersji wyłącznie do osobnego katalogu: `python -m src.download --output data/download_candidate`. Aktualizacja live nie zachowuje automatycznie historycznego snapshotu.

## Ograniczenia i wartość projektu

Wartość: odtwarzalne łączenie publicznych danych, kontrola przecieku czasowego, jawne porównanie trzech algorytmów, badanie błędów i działające demo. Zastosowanie: scenariusze cen miejskich i monitorowanie błędu prognozy. Nie udowodniono stabilnej przewagi operacyjnej. Średnie miejskie zależą od struktury transakcji; nie znamy parametrów mieszkań i czasu ich sprzedaży. Nie potwierdzamy przyczynowego wpływu programów dopłat. Następny etap to przyszłe kwartały i autentyczna ocena prospektywna, bez strojenia pod ostatni test.

GreenIT:2wątki CPU, brak GPU, krótkie okna i120drzew; rzeczywisty czas i rozmiar w reports/tables/green_it.json. Nie szacujemy CO₂ bez pomiarów energii.

Materiały utworzono przy wsparciu narzędzi AI. Na obronie autor powinien umieć wyjaśnić konstrukcję celu, opóźnienia, purging, baseline i porażkę na ostatnim okresie; plan w docs/OBRONA.md.


PDF i slajdy dokumentują zamrożoną analizę przygotowaną przed publikacją. Bieżący status publikacji i CI znajduje się w tym README oraz w repozytorium.
