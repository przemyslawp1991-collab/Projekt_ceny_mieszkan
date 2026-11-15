from pathlib import Path
import json, textwrap, os
import nbformat as nbf
from nbclient import NotebookClient

setup = """from pathlib import Path
import sys,json
ROOT=Path.cwd()
if ROOT.name=='notebooks':ROOT=ROOT.parent
assert (ROOT/'config/config.yaml').exists(),'Uruchom z folderu projektu lub notebooks'
if str(ROOT)not in sys.path:sys.path.insert(0,str(ROOT))
import pandas as pd,numpy as np
from IPython.display import display,Image
from src.common import FEATURES,TARGETS
"""
P = Path(__file__).resolve().parents[1]
notebooks = {
    "01_eda": [
        (
            "m",
            "# EDA: ceny mieszkań i kontekst makro\nCel: ocenić jakość, zakres oraz zależności publicznych danych przed prognozą miejskich średnich cen. Nie analizujemy statusów rezerwacji deweloperów.",
        ),
        ("c", setup),
        (
            "c",
            "audit=json.loads((ROOT/'reports/tables/source_audit.json').read_text());display(audit)\nprices=pd.read_csv(ROOT/'data/processed/prices_long.csv');display(prices.groupby(['market','series_type']).agg(n=('value','size'),min_quarter=('quarter','min'),max_quarter=('quarter','max')))",
        ),
        (
            "m",
            "Ceny transakcyjne są etykietą. Ceny ofertowe służą wyłącznie opisowi. Indeks hedoniczny ma inną jednostkę niż PLN/m²; nie mieszamy ich w jednej kolumnie celu.",
        ),
        (
            "c",
            "display(prices.head());display(prices.groupby('series_type').value.describe());print('Duplikaty klucza:',prices.duplicated(['quarter','area','market','series_type']).sum())",
        ),
        ("c", "display(Image(filename=str(ROOT/'reports/figures/01_prices.png')))"),
        (
            "m",
            "Trend poziomu ceny nie jest stacjonarny. Wspólny kierunek miast nie dowodzi przyczynowości inflacji lub dopłat. Średnia zmienia się także wraz ze strukturą sprzedanych lokali.",
        ),
        (
            "c",
            "f=pd.read_csv(ROOT/'data/processed/training_wide.csv');display(f[FEATURES].describe().T);display(f[FEATURES].isna().mean().sort_values(ascending=False).to_frame('missing_fraction'))",
        ),
        (
            "c",
            "display(Image(filename=str(ROOT/'reports/figures/02_missing.png')));display(Image(filename=str(ROOT/'reports/figures/03_correlations.png')))",
        ),
        (
            "m",
            "Braki indeksów dla rynku pierwotnego i wcześniejszego kredytu są strukturalne. Nie uzupełniamy ich z przyszłości. Nie usuwamy automatycznie skrajnych cen: mogą reprezentować zmianę cyklu. Wysokie korelacje i wspólne makro oznaczają mniejszą niezależność obserwacji niż sama liczba wierszy.",
        ),
        (
            "c",
            "display(json.loads((ROOT/'reports/tables/dataset_audit.json').read_text()))",
        ),
        (
            "m",
            "Wniosek EDA:11895etykiet horyzontów współdzieli2379wektorów. To wystarcza do demonstracji panelowego forecastingu, ale nie dostarcza tysięcy niezależnych załamań rynku. Nie imputujemy ceny docelowej ani nie interpolujemy brakujących etykiet.",
        ),
    ],
    "02_feature_engineering": [
        (
            "m",
            "# Konstrukcja cech i ochrona przed przeciekiem\nCały kod przygotowania: src/prepare_data.py oraz src/features.py. Notebook dokumentuje wynik i sprawdza kontrakt czasowy.",
        ),
        ("c", setup),
        (
            "c",
            "wide=pd.read_csv(ROOT/'data/processed/training_wide.csv');long=pd.read_csv(ROOT/'data/processed/supervised_long.csv');print(wide.shape,long.shape);display(wide[['origin','series_id','known_price_quarter','price_lag','label_available_ord']].tail())",
        ),
        (
            "m",
            "Cechy lokalne korzystają ze znanej ceny q−2lub q−1z kalendarza. Makro używa q−1, liczby kredytów q−2. Nazwa known2 jest odziedziczona; rzeczywisty lag jest w price_lag. Nie posiadamy wszystkich autentycznych vintages rewizji danych.",
        ),
        (
            "c",
            "display(pd.DataFrame({'feature':FEATURES}));assert len(FEATURES)==24;assert not set(FEATURES)&set(TARGETS)\nassert (pd.PeriodIndex(wide.known_price_quarter,freq='Q').asi8<wide.origin_ord).all()",
        ),
        (
            "c",
            "sample=wide.iloc[[-1]];display(sample[['origin','area','market','known_price']+TARGETS]);display(np.log(sample[TARGETS].to_numpy()/sample.known_price.to_numpy()[:,None]))",
        ),
        (
            "m",
            "Model ma5wyjść log(Pq+h/Pknown). Wersja long to naturalna reprezentacja5zadań horyzontowych, a nie powiększanie liczby niezależnych miast. Wszystkie5horyzontów pozostają w tym samym foldzie.",
        ),
        (
            "c",
            "from src.train import split,build\nfrom src.common import CONFIG\ntr,te=split(wide,'2023Q3',12)\nprint('Train origins:',tr.origin.min(),tr.origin.max(),'max dostępność etykiet:',tr.label_available_ord.max())\nprint('Decision ordinal:',pd.Period('2023Q3').ordinal,'test rows:',len(te))\nassert tr.label_available_ord.max()<pd.Period('2023Q3').ordinal\nassert not set(tr.origin)&set(te.origin)\ndisplay(build(CONFIG['trials'][0]))",
        ),
        (
            "m",
            "Medianę, wskaźniki braków, skalowanie i OneHot dopasowujemy dopiero po podziale. Etykieta pełnej ścieżki dojrzewa umownie w origin+6i musi być ściśle wcześniejsza niż chwila prognozy. Brak losowego train_test_split.",
        ),
        (
            "c",
            "display(long[['origin','series_id','horizon','target_quarter','target_price_pln_m2']].head(10));assert not long.duplicated(['origin','series_id','horizon']).any();assert long.groupby(['origin','series_id']).size().eq(5).all()",
        ),
        (
            "m",
            "Cechy obejmują płace, kredyt, stopy i CPI, ale nie pełną politykę dopłat ani mikrodane lokali. Traktujemy te braki jako ograniczenie, nie zastępujemy ich sztucznymi kwartałami.",
        ),
    ],
    "03_modeling": [
        (
            "m",
            "# Modelowanie, walidacja i demo\nRF, Ridge i HistGradientBoosting. Selekcja została zapisana przed oceną końcową; notebook odczytuje zamrożone wyniki. Historia była wcześniej analizowana — nie jest to dziewiczy test prospektywny.",
        ),
        ("c", setup),
        (
            "c",
            "trials=pd.read_csv(ROOT/'reports/tables/tuning_all_trials.csv');display(trials);display(pd.read_csv(ROOT/'reports/tables/tuning_summary.csv'));display(json.loads((ROOT/'models/selection.json').read_text()))",
        ),
        (
            "m",
            "7konfiguracji ×6foldów czasowych. Kryterium: MAPE h4. Wszystkie próby są jawne, nie wybrano modelu po wyniku2025Q2. Baseline historyczna to średnia lokalnych logzmian w tym samym oknie dojrzałych etykiet, osobno per horyzont.",
        ),
        (
            "c",
            "scores=pd.read_csv(ROOT/'reports/tables/scores.csv');display(scores[scores.horizon.eq(4)]);display(json.loads((ROOT/'reports/tables/paired_bootstrap.json').read_text()))",
        ),
        (
            "c",
            "display(Image(filename=str(ROOT/'reports/figures/04_comparison.png')));display(Image(filename=str(ROOT/'reports/figures/05_stability.png')))",
        ),
        (
            "m",
            "**Najważniejsze ograniczenie:** RF5,55%vs7,00%historycznie, ale13,76%vs3,88%dla utrzymania ostatniej ceny na2025Q2. Model ekstrapoluje wzrost z niedawnego okna i przeszacowuje w okresie wyhamowania. Nie ma podstaw do deklaracji stabilnej przewagi operacyjnej. Bootstrap opisuje historyczną różnicę błędów, nie niepewność przyszłej ceny.",
        ),
        (
            "c",
            "display(pd.read_csv(ROOT/'reports/tables/permutation_importance.csv'));display(pd.read_csv(ROOT/'reports/tables/local_sensitivity.csv').head());display(Image(filename=str(ROOT/'reports/figures/06_importance.png')))",
        ),
        (
            "m",
            "Permutacja mierzy użyteczność predykcyjną przy współzależnych cechach. Analiza mediany jest lokalną wrażliwością, nie SHAP i nie przyczynowym efektem polityki pieniężnej.",
        ),
        (
            "c",
            "from fastapi.testclient import TestClient\nfrom api.app import app\nclient=TestClient(app)\nresponse=client.post('/predict',json={'area':'Warszawa','market':'secondary'})\nassert response.status_code==200\ndisplay(response.json())\nprint('Nieznane miasto:',client.post('/predict',json={'area':'Atlantyda','market':'secondary'}).status_code)",
        ),
        (
            "c",
            "display(json.loads((ROOT/'models/metadata.json').read_text()));display(json.loads((ROOT/'reports/tables/green_it.json').read_text()));display(json.loads((ROOT/'reports/tables/legacy_reproduction.json').read_text()))",
        ),
        (
            "m",
            "Zastosowanie: badawczy scenariusz średnich cen w miastach, porównanie benchmarków, wykrywanie okresów porażki modelu. Snapshot2026Q3wystawiono po kwartale odniesienia, więc nie jest to prawdziwy historyczny forecast issued-at-time. Nie wycenia konkretnego lokalu, nie ocenia płynności i nie podaje sygnału sprzedaży. Następny krok walidacyjny: nowe kwartały, bez strojenia pod ostatni test.",
        ),
    ],
}


def build_notebooks():
    from ipykernel.kernelspec import install

    install(
        prefix=str(P / ".jupyter"),
        kernel_name="price-project",
        display_name="Projekt cen mieszkań",
    )
    os.environ["JUPYTER_PATH"] = str(P / ".jupyter/share/jupyter")
    for name, cells in notebooks.items():
        nb = nbf.v4.new_notebook(
            cells=[
                nbf.v4.new_markdown_cell(s) if typ == "m" else nbf.v4.new_code_cell(s)
                for typ, s in cells
            ],
            metadata={
                "kernelspec": {
                    "display_name": "Projekt cen mieszkań",
                    "language": "python",
                    "name": "price-project",
                },
                "language_info": {"name": "python", "version": "3.13.3"},
            },
        )
        NotebookClient(
            nb,
            timeout=180,
            kernel_name="price-project",
            resources={"metadata": {"path": str(P)}},
        ).execute()
        nbf.write(nb, P / "notebooks" / f"{name}.ipynb")
        print("Executed", name, flush=True)


if __name__ == "__main__":
    build_notebooks()
