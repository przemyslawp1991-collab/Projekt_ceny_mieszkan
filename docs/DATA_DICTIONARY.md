# Słownik danych i prognozy

**Jednostka:** miasto × rynek (pierwotny/wtórny) × kwartał odniesienia × horyzont0…4. Szeroki model ma pięć wyjść. Cena: PLN/m², średnia transakcyjna NBP. `origin` to umowny kwartał decyzji, a nie data pierwszej publikacji ani data budowy paczki.

**Cel:** `price_h0`…`price_h4` = rzeczywista średnia cena w q…q+4. Uczymy `log(price_h/known_price)`, wracamy przez exp; brak korekty smearing oznacza prognozę na skali log, nie gwarantowaną średnią warunkową ceny. Porównujemy ją bezpośrednio na skali PLN/m². Wszystkie modele i baseline otrzymują te same etykiety.

**Cechy lokalne8:** dynamika r/r i k/k, zmiana dynamiki r/r, odchylenie4dynamik k/k, cena względem mediany miast, iloraz pierwotny/wtórny, średnia dynamika innych miast, log znanej ceny. Sufiks `known2` jest historyczną nazwą; rzeczywisty lag zapisuje `price_lag` (1 lub2).

**Makro8:** stopa polityki pieniężnej, zmiana stopy w4kwartały, inflacja CPI r/r, płaca r/r, oprocentowanie nowych hipotek, realna wartość kredytu r/r, ocena popytu SLOOS, łagodzenie kryteriów SLOOS. Wszystkie q−1. Stopy/dynamiki w procentach lub punktach procentowych; to nie ułamki0…1. Średnia stopa hipoteczna ważona miesięczną wartością kredytów. CPI to średnia3miesięcy; stopa polityki to ostatni miesiąc kompletnego kwartału. Realny kredyt = wartość nominalna/CPI, a następnie dynamika r/r.

**Dodatkowe4:** udział miast z ujemną dynamiką k/k i r/r, hedoniczny indeks k/k oraz r/r minus100 w znanym kwartale (tylko wtórny). Nie zastępujemy indeksu hedonicznego kwotą PLN. Nie imputujemy Gdańska/Gdyni indeksem Trójmiasta.

**Kredyty4:** liczba kredytów r/r, k/k, zmiana dynamiki r/r w4kwartały i dynamika sumy4kwartałów; zawsze q−2.

**Kategorie2:** `area` oraz `market`. `area_clean` służy wyświetlaniu i łączeniu indeksu hedonicznego. `series_id`, `origin`, ceny docelowe i label_available_ord nie są wejściami estymatora.

**Braki:** pozostają NaN do etapu Pipeline; mediana i wskaźniki braków wyłącznie z treningu. Wszystkie wyniki walidujemy na pełnej ścieżce pięciu cen. Horyzont0 jest nowcastem; h4 nie jest dokładnie rokiem od ostatniej opublikowanej ceny (odstęp lag+4).
