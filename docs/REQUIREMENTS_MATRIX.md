# Wymagania zaliczenia — status15.11.2026

Dokument odniesienia: wymagania_kursu.pdf (kopia oryginalnego PDF użytkownika). Ta tabela nie stanowi gwarancji oceny prowadzącego.

| Wymaganie | Artefakt / status |
|---|---|
| Konkretny problem i własny zbiór | README; ceny mieszkań, publiczne dane producentów |
| ≥5000wierszy, ≥8cech | supervised_long.csv:11895wierszy i24cechy+2kategorie. Wide:2379wektorów. Horyzonty nie są niezależne. **Jeśli prowadzący wymaga5000niezależnych wektorów zamiast rekordów zadania, warunek nie jest spełniony w tym zakresie; nie ukrywamy tego mnożeniem wierszy.** |
| Źródła, licencje, pobieranie | docs/SOURCES.md; manifestSHA256; src/download.py; audytowane wyciągi AMRON/kalendarza dołączone, brak pełnego automatycznego parsera raportów |
| Raw / processed, czyszczenie w kodzie | data/raw niezmieniane; src/prepare_data.py i features.py |
| EDA i jakość |01_eda.ipynb,7wykresów, source_audit.json, feature_missing.csv |
| Podział przed transformacjami | origin-grouping + label availability strict; Pipeline fit train only |
| Trzy algorytmy i tuning | RF, Ridge, HGB;7konfiguracji×6foldów; wszystkie próby CSV |
| Jednorazowa końcowa ocena | Zamrożony dla paczki origin2025Q2, selekcja przed oceną. **Brak dziewiczego testu z niezaglądaną wcześniej historią; wyniki eksplorowano we wcześniejszych etapach.** |
| Walidacja / niepewność |6purged folds;41historycznych origins; blokowy bootstrap6kwartałów; mało niezależnych cykli |
| Interpretowalność | Permutation importance oraz local_sensitivity.csv; świadomie bez etykiety SHAP |
| Metryki i segmenty | MAPE/MAE/RMSE; market/city/origin/horizon; porażka na2025Q2ujawniona |
| Model + metadane + seed | models/model.pkl, metadata.json, protocol.json, configseed42 |
| FastAPI /predict + Pydantic | api/app.py, obsługa błędów422, endpoint /health |
| Dwa elementy end-to-end | Interaktywny Streamlit + walidacja schematu Pydantic; dodatkowo workflowCI |
| Testy pytest | tests/test_project.py; raport w reports/logs |
| Makefile / one-command | all,data,train,evaluate,clean; Windowsrun.ps1; python -m src.pipeline all |
| Wersje / czysta kopia | requirements.txt i requirements-lock.txt; osobne venv; raport odtworzenia czystej kopii |
| Docker slim | Dockerfile przygotowany; **silnikDocker nie jest dostępny — build/run niezweryfikowane** |
| PublicznyGitHub + commity | Publiczne repozytorium https://github.com/przemyslawp1991-collab/Projekt_ceny_mieszkan; zachowana historia commitów |
| Prezentacja10–15slajdów PDF |13slajdów + edytowalny PPTX; notatki i plan10minut |
| Demo + podsumowanie1strona |03_modeling.ipynb API demo, app.py, podsumowanie_1_strona.pdf |
| GreenIT | Rzeczywiste czasy i rozmiary;2wątki; brak fikcyjnej emisjiCO₂ |

Nie poprawiano wyników po obejrzeniu końcowego testu. Słabszy wynik jest wnioskiem projektu, a nie powodem do ukrycia baseline.
