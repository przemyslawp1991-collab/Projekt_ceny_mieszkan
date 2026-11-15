"""Publication PDFs derived only from the frozen coursework tables and figures."""

from pathlib import Path
import json
import pandas as pd
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib

P = (
    Path(__file__).resolve().parents[1]
    if Path(__file__).parent.name == "docs"
    else Path.home() / "Desktop/Projekt_ceny_mieszkan"
)
font = Path(matplotlib.get_data_path()) / "fonts/ttf"
pdfmetrics.registerFont(TTFont("Body", str(font / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("BodyBold", str(font / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFontFamily(
    "Body", normal="Body", bold="BodyBold", italic="Body", boldItalic="BodyBold"
)
styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="BodyPL",
        fontName="Body",
        fontSize=10.3,
        leading=15,
        spaceAfter=9,
        textColor=colors.HexColor("#25394d"),
    )
)
styles.add(
    ParagraphStyle(
        name="TitlePL",
        fontName="BodyBold",
        fontSize=24,
        leading=30,
        spaceAfter=17,
        textColor=colors.HexColor("#123e60"),
    )
)
styles.add(
    ParagraphStyle(
        name="HeadingPL",
        fontName="BodyBold",
        fontSize=15,
        leading=20,
        spaceAfter=12,
        textColor=colors.HexColor("#123e60"),
    )
)
styles.add(
    ParagraphStyle(
        name="SmallPL",
        fontName="Body",
        fontSize=8.2,
        leading=11,
        spaceAfter=6,
        textColor=colors.HexColor("#536779"),
    )
)


def para(s, style="BodyPL"):
    return Paragraph(s, styles[style])


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Body", 8)
    canvas.setFillColor(colors.HexColor("#536779"))
    canvas.drawString(44, 27, "Projekt Data Science • Ceny mieszkań • 15.11.2026")
    canvas.drawRightString(551, 27, str(doc.page))
    canvas.restoreState()


def table(rows, widths=None):
    t = Table(
        [[para(str(c), "SmallPL") for c in row] for row in rows],
        colWidths=widths,
        repeatRows=1,
        hAlign="LEFT",
    )
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6eef5")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#c8d5df")),
            ]
        )
    )
    return t


def write(name, story):
    doc = SimpleDocTemplate(
        str(P / "reports" / name),
        pagesize=(595.28, 841.89),
        rightMargin=44,
        leftMargin=44,
        topMargin=43,
        bottomMargin=45,
        title="Prognozowanie cen mieszkań — projekt zaliczeniowy",
        author="Projekt Data Science",
        allowSplitting=1,
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def fig(n, w=507, h=255):
    return Image(str(P / "reports/figures" / n), width=w, height=h, kind="proportional")


def main():
    audit = json.loads((P / "reports/tables/dataset_audit.json").read_text())
    ci = json.loads((P / "reports/tables/paired_bootstrap.json").read_text())
    green = json.loads((P / "reports/tables/green_it.json").read_text())
    summary = [
        para("Prognoza cen mieszkań", "TitlePL"),
        para("Podsumowanie projektu dla odbiorcy nietechnicznego", "HeadingPL"),
        para(
            "<b>Cel.</b> Sprawdzić, czy publiczne dane o cenach, inflacji, stopach procentowych, płacach i kredycie pomagają prognozować średnie ceny transakcyjne mieszkań. Zakres: 17 polskich miast, rynek pierwotny i wtórny, pięć punktów ścieżki q…q+4."
        ),
        para(
            "<b>Co zbudowano.</b> Samodzielny proces przygotowania i kontroli danych, trzy rodziny modeli, porównanie z prostymi prognozami oraz działające API i demonstrator. Pliki źródłowe, wyniki i model są zapisane lokalnie. Oryginalny model zachowano i odtworzono jego wyniki."
        ),
        table(
            [
                ["Błąd MAPE na końcu ścieżki", "RF", "Średnia", "Ostatnia cena"],
                ["Historia 2015–2025", "5,55%", "7,00%", "10,70%"],
                ["Ostatnia data: 2025Q2", "13,76%", "13,41%", "3,88%"],
            ],
            [240, 85, 90, 92],
        ),
        Spacer(1, 12),
        para(
            "<b>Najważniejszy wniosek.</b> Model pomaga opisać historyczne zależności, ale nie wykazał stabilnej przewagi. W ostatnim sprawdzonym okresie prognozował przeciętnie wzrost około 17,1% względem znanej ceny, podczas gdy rzeczywista zmiana wyniosła około 3,1%. Prosta prognoza utrzymania ostatniej ceny okazała się wyraźnie lepsza."
        ),
        para(
            "<b>Do czego można go wykorzystać.</b> Do porównania scenariuszy miejskich, demonstracji procesu prognozowania i monitorowania błędów. Wynik jest średnią dla rynku miejskiego; nie wycenia konkretnego mieszkania i nie określa terminu jego sprzedaży."
        ),
        para(
            "<b>Jak czytać wiarygodność.</b> Historia była wcześniej analizowana. Jedna końcowa data nie jest niezależnym testem prospektywnym, a dane podlegają rewizjom. Nie przedstawiamy przedziałów gwarantowanej przyszłej ceny. 11 895 rekordów horyzontowych współdzieli 2 379 wektorów miasto–kwartał."
        ),
        para(
            "<b>Co dalej.</b> Zachować zamrożony protokół i sprawdzić prognozy na kolejnych nowych kwartałach. Wynik ostatniego testu pokazujemy jawnie, bez zmiany modelu pod ten okres."
        ),
        para(
            "Źródła: NBP BaRN/MIR/SLOOS, GUS, BIS, AMRON-SARFiN. Pełne adresy, hashe i warunki użycia: docs/SOURCES.md oraz data/raw/source_manifest.json. Snapshot badawczy odnosi się do 2026Q3 i powstał po tym kwartale, 15.11.2026.",
            "SmallPL",
        ),
    ]
    write("podsumowanie_1_strona.pdf", summary)
    pages = []

    def page(title, content):
        if pages:
            pages.append(PageBreak())
        pages.extend([para(title, "TitlePL")] + content)

    page(
        "Ceny mieszkań: projekt zaliczeniowy",
        [
            para(
                "Cel, dane, model i ograniczenia — samodzielny projekt Data Science",
                "HeadingPL",
            ),
            para(
                "Pytanie badawcze: czy dynamika cen oraz publiczne dane makroekonomiczne i kredytowe pozwalają przewidywać przyszłe średnie ceny transakcyjne lepiej niż proste punkty odniesienia?"
            ),
            para(
                "Zakres: 17 miast × 2 rynki. Model przewiduje pięć cen q…q+4 w PLN/m². Horyzont 0 to nowcast względem opóźnionej ceny wejściowej. Wartość lokalu zależy również od jego powierzchni, położenia i standardu, których ten zbiór nie zawiera."
            ),
            para(
                "Wynik historyczny: 5,55% MAPE modelu wobec 7,00% średniej historycznej. Ostatnia sprawdzona data: 13,76% wobec 3,88% dla ostatniej ceny. Wniosek projektu obejmuje zarówno historyczną poprawę, jak i utratę przewagi w nowszym okresie."
            ),
            fig("01_prices.png", h=290),
            para(
                "To projekt badawczy, a nie zweryfikowany system inwestycyjny. Nie obejmuje alarmów sprzedaży, płynności, danych syntetycznych ani transferu między krajami.",
                "SmallPL",
            ),
        ],
    )
    page(
        "Dane i kontrola jakości",
        [
            table(
                [
                    ["Źródło", "Zastosowanie"],
                    ["NBP BaRN", "Średnie ceny transakcyjne; indeksy hedoniczne"],
                    ["GUS", "Przeciętne wynagrodzenia brutto"],
                    ["BIS", "CPI i stopa polityki pieniężnej"],
                    ["NBP MIR/SLOOS", "Koszt i wartość kredytu, ocena popytu"],
                    ["AMRON-SARFiN", "Liczba nowych kredytów mieszkaniowych"],
                ],
                [140, 367],
            ),
            Spacer(1, 10),
            para(
                "Ceny obejmują 2006Q3–2026Q2. Zapisano oryginalne XLSX, surowe wyciągi BIS i audytowane liczby z raportów AMRON. SHA256 chroni zamrożony snapshot. Wszystkie połączenia i transformacje znajdują się w src/prepare_data.py i src/features.py."
            ),
            para(
                f"{audit['raw_price_observations']:,} odczytów cen/ofert/indeksów; {audit['long_rows']:,} rekordów horyzontowych; {audit['independent_city_origin_groups']:,} wektorów miasto–rynek–kwartał. Pięć wyjść współdzieli cechy. Liczba rekordów nie mierzy liczby niezależnych cykli."
            ),
            para(
                "Sprawdzono duplikaty, dodatniość cen i zgodność rocznych sum liczby kredytów. Nie interpolowano cen ani etykiet. Oferty nie są celem uczenia. Braki indeksów na rynku pierwotnym i wcześniejszych danych kredytu pozostają NaN do treningu."
            ),
            fig("02_missing.png", w=430, h=290),
        ],
    )
    page(
        "Cechy i podział czasowy",
        [
            para(
                "24 cechy numeryczne i 2 kategorie: miasto oraz rynek. Cechy opisują dynamikę cen, jej przyspieszenie, zmienność, relację do innych miast i rynków, indeks hedoniczny, inflację, stopy, płace i kredyt."
            ),
            table(
                [
                    ["Element", "Reguła dostępności"],
                    [
                        "Ceny lokalne",
                        "q−2; q−1 tylko przy potwierdzonym kwartale publikacji",
                    ],
                    ["Makro / SLOOS", "q−1 (założenie lag), dane zrewidowane"],
                    ["Liczby kredytów", "q−2"],
                    [
                        "Etykiety Pq…Pq+4",
                        "Do treningu dopiero, gdy q+6 < origin prognozy",
                    ],
                    [
                        "Transformacje",
                        "Mediana / wskaźnik braków / skala / kategorie fit tylko train",
                    ],
                ],
                [145, 362],
            ),
            Spacer(1, 12),
            para(
                "Każdy fold obejmuje wszystkie miasta, rynki i horyzonty danej daty. Losowy podział wierszy dawałby wspólne makro i zachodzące na siebie etykiety po obu stronach podziału. Okno treningu liczymy od ostatniego dojrzałego origin, a nie od bieżącego kwartału."
            ),
            para(
                "Cel modelu: log(Pq+h/Pknown). Po prognozie wracamy do PLN/m² przez exp i znaną cenę. Nie obiecujemy warunkowej średniej ceny po transformacji logarytmicznej."
            ),
            para(
                "Istotna granica: nie posiadamy kompletnych historycznych vintages. Konserwatywne lags ograniczają przeciek publikacyjny, lecz nie usuwają wpływu późniejszych rewizji danych. Historia była wcześniej oglądana; nie nazywamy jej dziewiczym testem prospektywnym."
            ),
        ],
    )
    page(
        "Porównanie modeli i wybór",
        [
            para(
                "RF, Ridge i HistGradientBoosting; siedem konfiguracji w sześciu foldach: 2015Q1, 2017Q1, 2019Q1, 2021Q1, 2023Q1, 2023Q3. Kryterium: średnia MAPE końca ścieżki h4. Wszystkie próby, parametry, czasy i liczby wierszy zapisano do CSV."
            ),
            para(
                "Wybrano RF: 120 drzew, max_depth=6, min_samples_leaf=12, okno 12 dojrzałych kwartałów, seed=42. Dwa wątki CPU. Wyboru nie zmieniano po ocenie daty 2025Q2."
            ),
            para(
                "Baseline historyczna: dla danego miasta/rynku i horyzontu średnia logarytmicznej zmiany względem znanej ceny w tym samym oknie treningowym. Dodatkowo niezmieniona cena i kontynuacja ostatniej dynamiki r/r. Te same przypadki i cele dla każdego modelu."
            ),
            fig("04_comparison.png", h=285),
            para(
                f"Różnica historycznej MAPE model−średnia: {ci['delta_MAPE_pp']:.3f} pp. Bootstrap bloków 6 kwartałów, 2 000 losowań: [{ci['CI95_low']:.3f}; {ci['CI95_high']:.3f}] pp. To opis retrospektywny; wcześniejsza selekcja i eksploracja ograniczają interpretację potwierdzającą."
            ),
        ],
    )
    page(
        "Ostatni test: utrata przewagi",
        [
            table(
                [
                    ["Ocena końca ścieżki", "RF", "Średnia", "Ostatnia cena"],
                    ["2015Q1–2025Q1, n=1394", "5,55%", "7,00%", "10,70%"],
                    ["2025Q2, n=34", "13,76%", "13,41%", "3,88%"],
                ],
                [230, 90, 94, 93],
            ),
            Spacer(1, 13),
            para(
                "Dla ostatniego origin końcowa etykieta to 2026Q2. RF prognozował przeciętnie około 17,1% wzrostu od znanej ceny, a rzeczywista średnia zmiana wyniosła około 3,1%. Wszystkie 34 prognozy końca ścieżki były zawyżone. To zgodne z nadmierną kontynuacją wzrostu z ostatniego okna; nie jest dowodem przyczynowego mechanizmu makro."
            ),
            para(
                "Jedna data to wspólna sytuacja gospodarcza, nie 34 niezależne okresy. Nie podajemy pozornie precyzyjnego przedziału generalizacji z bootstrapu samych miast. Pełne wyniki wszystkich horyzontów i modeli zapisano w scores.csv i predictions.csv."
            ),
            fig("05_stability.png", h=260),
            para(
                "Wynik historyczny obejmuje daty strojenia i wcześniej analizowaną historię. Końcową datę zamrożono dla paczki, lecz jej dane były wcześniej dostępne. Brak przyszłej, niezaglądanej jeszcze próby — to ograniczenie jawnie wskazane w projekcie.",
                "SmallPL",
            ),
        ],
    )
    page(
        "Wyjaśnienie i prognoza",
        [
            para(
                "Permutation importance liczona na ostatnim foldzie walidacyjnym pokazuje zmianę MAPE po przemieszaniu jednej cechy. Powiązane cechy mogą dzielić znaczenie; ujemna zmiana jest możliwa. Lokalna analiza wrażliwości zastępuje jedną cechę medianą treningu. Nie są to efekty przyczynowe ani addytywne SHAP."
            ),
            fig("06_importance.png", h=270),
            para(
                "Model produkcyjny w paczce to przetrenowany zwycięzca walidacji dla odniesienia 2026Q3; ścieżka do 2027Q3, wejściowa cena 2026Q1. Wydanie powstało 15.11.2026, więc to archiwalny scenariusz badawczy, a nie prognoza wystawiona rzeczywiście w trzecim kwartale."
            ),
            para(
                "Zastosowanie: demonstracja prognoz miejskich, budżetowe scenariusze porównawcze, monitorowanie błędów. Brak skalibrowanych przedziałów predykcji. Brak wyceny lokalu, czasu sprzedaży i sygnału inwestycyjnego. Oryginalny RF jest osobnym artefaktem kontrolnym i odtwarza wynik 5,60065856%."
            ),
        ],
    )
    page(
        "Odtworzenie i demonstracja",
        [
            para(
                "Kod: config, src, api, tests. Dane: raw, processed, reference. Artefakty: model.pkl + metadata, wykonane notebooki, tabele, wykresy, raport i prezentacja. Oryginalny projekt pozostaje bez zmian."
            ),
            table(
                [
                    ["Czynność", "Polecenie z folderu projektu"],
                    [
                        "Cały eksperyment",
                        "python -m src.pipeline all / Windows: run.ps1 all",
                    ],
                    ["Testy", "python -m pytest -q"],
                    ["API", "python -m uvicorn api.app:app"],
                    ["Demo", "python -m streamlit run app.py"],
                    ["Predykcja", "POST /predict: area=Warszawa, market=secondary"],
                ],
                [120, 387],
            ),
            Spacer(1, 12),
            para(
                "FastAPI z Pydantic odrzuca błędne miasta, rynki i dodatkowe pola. Streamlit wyświetla ceny dla wybranego miasta. Testy sprawdzają hashe, schemat, purging, kompletność prognoz, zgodność eksportu i odpowiedzi API. Środowisko projektu jest osobne od starego projektu."
            ),
            para(
                f"GreenIT: dwa wątki CPU, bez GPU. Trening modelu produkcyjnego: {green['production_train_seconds']:.3f} s; plik modelu {green['model_bytes'] / 1000:.1f} kB. Czasy zależą od sprzętu. Nie mierzono energii ani emisji CO₂."
            ),
            para(
                "Dockerfile na python:3.13-slim jest przygotowany; brak silnika Docker uniemożliwił lokalny build/run. Workflow GitHub Actions przygotowany, ale nieuruchomiony zdalnie. Repozytorium ma lokalne commity; publiczny GitHub pozostaje do opublikowania."
            ),
            para(
                "Dalszy sprawdzalny krok: kolejne nowe kwartały oceniane według zamrożonego protokołu. Nie zwiększamy pozornie pewności danymi syntetycznymi i nie dobieramy parametrów pod ujawniony ostatni test."
            ),
            para(
                "Źródła i warunki: docs/SOURCES.md. Wymagania i jawne braki: docs/REQUIREMENTS_MATRIX.md. Wszystkie metryki: reports/tables. Plan obrony: docs/OBRONA.md.",
                "SmallPL",
            ),
        ],
    )
    write("raport.pdf", pages)
    print("Created summary and report PDFs")


if __name__ == "__main__":
    main()
