import streamlit as st
import pandas as pd
from src.predict import predict, load

st.set_page_config(page_title="Ceny mieszkań — projekt DS", layout="wide")
st.title("Prognoza średnich cen transakcyjnych mieszkań")
st.caption("Projekt badawczy • stały snapshot2026Q3 • przygotowano15.11.2026")
_, f = load()
area = st.selectbox("Miasto", sorted(f.area_clean.unique()))
market = st.selectbox(
    "Rynek",
    ["secondary", "primary"],
    format_func=lambda x: "Wtórny" if x == "secondary" else "Pierwotny",
)
r = predict(area, market)
st.write(
    "Ostatnia cena wejściowa:",
    r["known_price_pln_m2"],
    "PLN/m²,",
    r["known_price_quarter"],
)
table = pd.DataFrame(r["forecasts"])
st.line_chart(table.set_index("target_quarter").prediction_pln_m2)
st.dataframe(table, hide_index=True)
st.info(r["warning"])
st.caption(
    "Dane: NBP, GUS, BIS, AMRON-SARFiN. Model dotyczy średniej miejskiej, która zależy też od struktury sprzedanych mieszkań."
)
