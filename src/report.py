"Reproducible EDA figures and a self-contained HTML report."

import json, html
import numpy as np, pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from .common import *

FIG = ROOT / "reports/figures"


def finish(name):
    plt.tight_layout()
    plt.savefig(FIG / name, dpi=160, bbox_inches="tight")
    plt.close()


def main():
    prices = pd.read_csv(PROCESSED / "prices_long.csv")
    f = pd.read_csv(PROCESSED / "training_wide.csv")
    z = pd.read_csv(TABLES / "predictions.csv")
    scores = pd.read_csv(TABLES / "scores.csv")
    audit = json.loads((TABLES / "dataset_audit.json").read_text())
    selection = json.loads((ROOT / "models/selection.json").read_text())
    ci = json.loads((TABLES / "paired_bootstrap.json").read_text())
    plt.rcParams.update(
        {
            "figure.figsize": (10, 5),
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.2,
            "font.size": 11,
        }
    )
    t = prices[prices.series_type.eq("transaction") & prices.area_clean.eq("Warszawa")]
    for market, g in t.groupby("market"):
        plt.plot(
            pd.PeriodIndex(g.quarter, freq="Q").to_timestamp(), g.value, label=market
        )
    plt.legend()
    plt.ylabel("PLN/m²")
    plt.title("Warszawa: średnie ceny transakcyjne NBP")
    finish("01_prices.png")
    miss = f[FEATURES].isna().mean().sort_values()
    plt.figure(figsize=(10, 8))
    plt.barh(miss.index, miss.values * 100)
    plt.xlabel("Braki (%)")
    plt.title("Braki przed imputacją — cecha to nie brak ceny")
    finish("02_missing.png")
    plt.figure(figsize=(12, 9))
    corr = f[FEATURES].corr()
    plt.imshow(corr, vmin=-1, vmax=1, cmap="RdBu_r")
    plt.colorbar(label="Korelacja Pearsona")
    plt.xticks(range(24), [str(i + 1) for i in range(24)])
    plt.yticks(range(24), FEATURES, fontsize=8)
    plt.title("Korelacje cech — wspólne makro i zależności panelowe")
    finish("03_correlations.png")
    hist = scores[
        scores.phase.eq("historical_diagnostic") & scores.horizon.eq(4)
    ].sort_values("MAPE_pct")
    plt.barh(hist.model, hist.MAPE_pct)
    plt.xlabel("MAPE (%)")
    plt.title("Historyczna diagnostyka 2015Q1–2025Q1, koniec ścieżki")
    finish("04_comparison.png")
    err = z[z.phase.eq("historical_diagnostic") & z.horizon.eq(4)].copy()
    err["APE"] = np.abs(err.prediction / err.actual - 1) * 100
    for name in ["selected_model", "historical_mean"]:
        g = err[err.model.eq(name)].groupby("origin").APE.mean()
        plt.plot(pd.PeriodIndex(g.index, freq="Q").to_timestamp(), g.values, label=name)
    plt.legend()
    plt.ylabel("MAPE (%)")
    plt.title("Błąd zależy od fazy cyklu — każda data to 34 segmenty")
    finish("05_stability.png")
    g = (
        pd.read_csv(TABLES / "permutation_importance.csv")
        .head(12)
        .sort_values("delta_MAPE_pp")
    )
    plt.figure(figsize=(10, 6))
    plt.barh(g.feature, g.delta_MAPE_pp)
    plt.xlabel("Zmiana MAPE po permutacji (pp)")
    plt.title("Znaczenie cech na ostatnim foldzie walidacyjnym")
    finish("06_importance.png")
    g = pd.read_csv(TABLES / "current_forecasts.csv")
    g = g[g.area.eq("Warszawa")]
    for market, a in g.groupby("market"):
        plt.plot(a.target_quarter, a.prediction_pln_m2, marker="o", label=market)
    plt.legend()
    plt.ylabel("PLN/m²")
    plt.title("Warszawa: archiwalna prognoza przy odniesieniu 2026Q3")
    finish("07_forecast.png")

    def table(x):
        return x.to_html(index=False, float_format=lambda v: f"{v:.3f}", border=0)

    text = f"""<!doctype html><html lang="pl"><meta charset="utf-8"><title>Prognoza cen mieszkań — raport</title><style>body{{font:17px/1.6 system-ui;max-width:1100px;margin:45px auto;padding:0 24px;color:#172c40}}h1,h2{{color:#123e60}}table{{border-collapse:collapse;font-size:14px}}th,td{{padding:8px 12px;border-bottom:1px solid #cbd5df}}img{{max-width:100%}}aside{{background:#eef4fa;padding:20px}}</style>
 <h1>Prognozowanie średnich cen transakcyjnych mieszkań</h1><p>Samodzielny projekt zaliczeniowy Data Science •15.11.2026</p>
 <aside>Cel: prognoza średniej miejskiej PLN/m² dla17 miast i2 rynków w pięciu punktach q…q+4. h0 jest nowcastem. Projekt nie wycenia pojedynczego lokalu i nie dostarcza sygnału sprzedaży.</aside>
 <h2>Dane i jednostka obserwacji</h2><p>NBP BaRN (ceny transakcyjne i indeksy hedoniczne), GUS (płace), BIS (inflacja i stopy), NBP MIR/SLOOS (koszt i popyt na kredyt), AMRON-SARFiN (liczby kredytów). Ceny obejmują{prices.quarter.min()}–{prices.quarter.max()}. Pliki źródłowe zachowano z hashami SHA256. Licencje i odnośniki: docs/SOURCES.md.</p>
 <p>{audit["long_rows"]} rekordów zadania wielohoryzontowego odpowiada{audit["independent_city_origin_groups"]} grupom miasto–rynek–kwartał i{audit["unique_origins"]} kwartałom. Pięć horyzontów współdzieli cechy: nie są to niezależne cykle.24 cechy liczbowe i2 kategorie. Surowych odczytów cen/indeksów:{audit["raw_price_observations"]}. Nie interpolowano cen i nie dodawano danych syntetycznych.</p>
 <h2>Przygotowanie i EDA</h2><p>Rozdzielono średnie ceny, oferty i indeksy. Oferty nie są etykietą. Zachowano skrajne wartości, bo mogą oznaczać zmianę cyklu lub strukturę transakcji; sprawdzono dodatniość, klucze i kompletność. Braki kredytu i indeksów są strukturalne; imputacja medianą i wskaźnik braków są dopasowane wyłącznie na treningu. GUS i BIS nie są danymi mikro o konkretnej nieruchomości.</p>
 <img src="figures/01_prices.png"><img src="figures/02_missing.png"><img src="figures/03_correlations.png">
 <h2>Protokół czasowy i modele</h2><p>Ceny wejściowe mają opóźnienie2 kwartałów, skracane do1 wyłącznie przy kalendarzu publikacji; makro q−1, liczby kredytów q−2. Cały komplet miasto/rynek/horyzont pozostaje w jednym foldzie. Etykiety q…q+4 uznaje się za dostępne w q+6; muszą być ściśle wcześniejsze niż chwila prognozy. Transformacje są wewnątrz Pipeline. Część założeń publikacyjnych jest przybliżona; posiadamy zrewidowane szeregi, a nie historyczne vintages.</p>
 <p>Porównano Random Forest, Ridge i wielowyjściowy HistGradientBoosting.7 konfiguracji ×6 czasowych foldów. Selekcja: średnia MAPE h4, wyłącznie walidacja. Wybrano <b>{selection["winner"]}</b>. Wszystkie próby, parametry, czasy i błędy zapisano w tuning_all_trials.csv.</p>{table(pd.read_csv(TABLES / "tuning_summary.csv"))}
 <h2>Wyniki i uczciwa interpretacja</h2><p>Poprzednie eksperymenty już oglądały znaczną część historii. Poniższy wynik2015–2025 jest diagnostyką retrospektywną, także nakładającą się na foldy wyboru. Nie stanowi niezależnego potwierdzenia przewagi. Zablokowany dla tej paczki pojedynczy origin2025Q2 to34 grupy i170 punktów ścieżki; ceny historyczne były dostępne wcześniej, więc nie jest to dziewiczy test prospektywny. Nie zmieniano wyboru modelu po tym teście.</p>{table(scores[scores.horizon.eq(4)])}
 <aside><b>Ostatnia data ujawniła utratę przewagi:</b> wybrany RF ma13,76% MAPE, podczas gdy utrzymanie ostatniej ceny ma3,88%. Prognozowany średni wzrost od znanej ceny wynosił17,1%, rzeczywisty3,1%. To obraz nadmiernej kontynuacji wzrostu, nie dowód przyczynowego wpływu konkretnego czynnika. Nie potwierdzono stabilnej przewagi operacyjnej.</aside>
 <p>Różnica historycznej MAPE model−średnia:{ci["delta_MAPE_pp"]:.3f} pp; przedział z bootstrapu bloków6kwartałów:[{ci["CI95_low"]:.3f};{ci["CI95_high"]:.3f}] pp. Ujemna różnica oznacza mniejszy błąd modelu. Nie jest to przedział przyszłej ceny ani potwierdzenie przyczynowości. Wspólne makro,17 miast i zachodzące na siebie ścieżki ograniczają niezależność.</p>
 <img src="figures/04_comparison.png"><img src="figures/05_stability.png">
 <h2>Wyjaśnianie predykcji</h2><p>Permutacja pojedynczych cech na ostatnim foldzie walidacyjnym mierzy zmianę MAPE. Współzależne cechy mogą dzielić znaczenie, a ujemne znaczenie jest możliwe. local_sensitivity.csv pokazuje zmianę prognozy Warszawy po zastąpieniu każdej cechy medianą treningową. To lokalna analiza wrażliwości, nie addytywne SHAP i nie efekt przyczynowy stóp lub dopłat.</p><img src="figures/06_importance.png">
 <h2>Prognoza i zastosowanie</h2><p>models/model.pkl to wybrany model przetrenowany dla odniesienia2026Q3. Paczka powstała w listopadzie2026, więc nie udajemy, że została wystawiona w2026Q3. Ścieżka obejmuje2026Q3–2027Q3, wejściowa cena pochodzi z2026Q1. Można porównywać miasta/rynki i budować scenariusz budżetu. Brak skalibrowanych przedziałów; nie należy traktować punktów jako gwarancji. Oryginalny RF zachowano oddzielnie jako isolated_original_rf.joblib.</p><img src="figures/07_forecast.png">
 <h2>Wdrożenie, testy, zasoby</h2><p>FastAPI/Pydantic /predict, Streamlit, testy pytest, schemat wejścia i workflow CI. make all oraz Windows run.ps1 odtwarzają tabele, model i wykresy z lokalnych niezmiennych źródeł. Wyniki czasu i rozmiaru: green_it.json. Bez GPU; dwa wątki. Nie mierzyliśmy energii ani CO₂. Obraz Docker przygotowano, ale lokalnie brak silnika Docker; workflow CI wymaga uruchomienia po publikacji repozytorium.</p>
 <h2>Ograniczenia i dalsza walidacja</h2><p>Średnia cena zmienia się wraz z miksem transakcji; brak indywidualnych cech lokali, długiej historii niezależnych załamań i pewnych vintages. Rzadkie spadki oraz interwencje polityczne mogą być trudne do uchwycenia. Kolejny rzetelny krok: zamrożony protokół i prospektywna ocena nowych kwartałów. Nie dodawano modułu płynności, alarmów sprzedaży ani sztucznych kryzysów.</p></html>"""
    (ROOT / "reports/raport.html").write_text(text, encoding="utf-8")
    save_json(
        TABLES / "report_summary.json",
        dict(
            dataset=audit,
            selection=selection,
            bootstrap=ci,
            historical_h4=hist.to_dict(orient="records"),
            locked_test_h4=scores[
                scores.phase.eq("locked_test") & scores.horizon.eq(4)
            ].to_dict(orient="records"),
        ),
    )
    print("Report and7figures saved", flush=True)


if __name__ == "__main__":
    main()
