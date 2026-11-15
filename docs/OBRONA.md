# Plan obrony —10minut +5minut pytań

1. Problem i granice modelu (slajdy1–2,60s).
2. Dane, EDA i jednostka obserwacji (3–5,140s).
3. Opóźnienia i podział czasowy bez przyszłych etykiet (6,60s).
4. Trzy algorytmy, tuning i baseline (7,60s).
5. Wyniki historyczne oraz porażka na ostatnim okresie (8–9,100s).
6. Interpretacja, demo API i zasoby (10–12,120s).
7. Wnioski i dalsza prospektywna walidacja (13,60s).

Demo awaryjne: otwórz wykonany03_modeling.ipynb, który zawiera odpowiedź /predict. Demo na żywo: run.ps1 api, otwórz /docs, wyślij Warszawa/secondary; następnie run.ps1 demo. Nie pobieraj danych live podczas obrony.

Pytania, które trzeba rozumieć:

- Dlaczego nie dzielimy losowo wierszy? Wspólne makro, nakładające się etykiety i identyczny origin w miastach dawałyby przeciek.
- Skąd średnia historyczna? Średnie logarytmiczne zmiany względem znanej ceny w tych samych12dojrzałych origins, per miasto i rynek, osobno na horyzont.
- Dlaczego11895wierszy nie oznacza11895niezależnych przypadków?5horyzontów współdzieli2379wektorów cech.
- Dlaczego RF przegrywa z ostatnią ceną na2025Q2? Trening po silnych wzrostach koduje dalszą aprecjację, a końcowe ceny były bliższe ostatniej cenie wejściowej; to obserwacja błędu, nie dowód przyczynowego mechanizmu.
- Czy dane mają pełną historyczną dostępność? Nie; stosujemy opóźnienia, ale nie posiadamy vintages wszystkich rewizji.
- Czy to wycena konkretnego mieszkania lub rekomendacja sprzedaży? Nie; to miejska średnia i badawczy scenariusz punktowy.
- Co oznacza MAPE5,55%? Średni bezwzględny błąd względny na końcu ścieżki w retrospektywnej diagnostyce, nie gwarantowany błąd każdej prognozy.
- Co jest realną wartością projektu? Działający odtwarzalny proces, porównania, identyfikacja porażki modelu i sposób dalszej oceny; stabilna przewaga ekonomiczna nie została potwierdzona.
