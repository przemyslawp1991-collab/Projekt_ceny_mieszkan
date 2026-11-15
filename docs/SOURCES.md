# Źródła, pochodzenie i zasady użycia

Kod oraz statystyki producentów mają odrębny status. Projekt nie nadaje plikom producentów licencji MIT/CC0. Przed zewnętrzną dystrybucją należy respektować aktualne warunki każdego producenta. Zawarte liczby AMRON są faktami przepisanymi z raportów, z zachowanym numerem strony; nie dołączamy pełnych raportów AMRON.

| Źródło | Zmienna | Plik / adres i warunki |
|---|---|---|
| NBP BaRN | Średnie ceny transakcyjne i indeksy hedoniczne; oferty tylko EDA | https://static.nbp.pl/dane/rynek-nieruchomosci/ceny_mieszkan.xlsx ; https://nbp.pl/publikacje/cykliczne-materialy-analityczne-nbp/rynek-nieruchomosci/informacja-kwartalna/ |
| GUS | Przeciętna płaca brutto w gospodarce narodowej | Pełny URL pliku w source_manifest.json; https://stat.gov.pl/copyright/ dopuszcza kopiowanie z podaniem źródła |
| BIS | Miesięczna stopa polityki pieniężnej i CPI Polski | https://data.bis.org/topics/CBPOL ; https://data.bis.org/topics/CPI ; https://data.bis.org/help/legal ; https://www.bis.org/about/terms-conditions |
| NBP MIR | Nowe kredyty mieszkaniowe: wartość i średnie oprocentowanie | https://static.nbp.pl/dane/statystyka/inne/stopy_proc_pl_srdW.xlsx |
| NBP SLOOS | Bankowa ocena popytu i łagodzenia standardów | https://static.nbp.pl/dane/rynek-kredytowy/zrodlo-net.xlsx |
| AMRON-SARFiN | Liczba udzielonych kredytów mieszkaniowych | https://amron.pl/raporty/ ; oryginalne raporty chronione, udostępniony wyciąg faktów z pochodzeniem |

Manifest zawiera SHA256 i adresy. Pliki BIS są surowym wyciągiem wszystkich częstotliwości dla Polski z pierwotnego bulk CSV: filtr PL, bez zmian wartości. Manifest podaje również hash pliku macierzystego. XLSX to oryginalne pliki. Dodatkowe CSV AMRON i kalendarz NBP to jawnie oznaczone wyciągi audytowane. Nie traktujemy ich jak pełnych plików producenta.

`python -m src.download --output data/download_candidate` pobiera nowe pliki do osobnego katalogu i zachowuje dotychczasowy snapshot. Live URL może dziś zwrócić zmieniony plik. Odtwarzalność wyników zapewniają **dołączone zamrożone dane**, nie założenie, że historyczny URL jest niezmienny. Audytowanych wyciągów AMRON/kalendarza nie odtwarza się automatycznie z HTML; zachowano nazwy raportów, strony i odnośniki.

Wartości są zrewidowaną historią dostępną podczas wcześniejszej zbiórki. Założone opóźnienia nie zamieniają ich w autentyczne dane point-in-time. Identyfikator Gdynia** w pierwotnym arkuszu pozostaje kategorią modelu; interfejs wyświetla Gdynia. Z tego powodu historycznie stosowany iloraz rynków może mieć brak dla Gdyni; to jawnie zachowana cecha izolowanego modelu.
