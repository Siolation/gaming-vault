import streamlit as st
import requests
import pandas as pd
import os
from datetime import date, datetime, timedelta
import calendar
import urllib.parse
import random

# --- SETTINGS ---
API_KEY = "e58aa9b7b165409da17d9ccfae178d9c" 
DB_FILE = "meine_liste.csv"
PASSWORT = "zocken2024"
PLACEHOLDER_IMAGE = "https://via.placeholder.com/600x400.png?text=Kein+Bild+vorhanden"

st.set_page_config(page_title="Gaming Vault Ultimate", layout="wide")

def check_password():
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if not st.session_state["authenticated"]:
        st.title("🛡️ Gaming Vault Login")
        eingabe = st.text_input("Passwort", type="password")
        if st.button("Einloggen"):
            if eingabe == PASSWORT:
                st.session_state["authenticated"] = True
                st.rerun()
            else: st.error("Falsch!")
        return False
    return True

# --- CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0d0d0d; color: #e0e0e0; }
    h1, h2, h3 { color: #00ffcc !important; text-shadow: 0px 0px 10px rgba(0, 255, 204, 0.5); }
    [data-testid="stImage"] img { height: 160px !important; object-fit: cover !important; border-radius: 8px; }
    .game-title { height: 40px; overflow: hidden; font-weight: bold; font-size: 14px; margin-top: 5px; }
    .sale-card { background: rgba(0, 255, 204, 0.1); padding: 12px; border-radius: 8px; border-left: 5px solid #00ffcc; margin-bottom: 10px; }
    .stat-card { background: #1a1c23; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #333; margin-bottom: 10px; }
    .game-card {
        background: rgba(0, 255, 204, 0.05);
        border: 1px solid #00ffcc;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
    }
    .progress-bg { background-color: #333; border-radius: 5px; width: 100%; height: 10px; }
    .progress-fill { background-color: #00ffcc; height: 10px; border-radius: 5px; box-shadow: 0 0 10px #00ffcc; }
    .card-beendet { border-left: 5px solid #00ffcc; background: rgba(0, 255, 204, 0.05); padding: 10px; border-radius: 5px; margin-bottom: 5px; }
    .card-zocken { border-left: 5px solid #ffcc00; background: rgba(255, 204, 0, 0.05); padding: 10px; border-radius: 5px; margin-bottom: 5px; }
    .stButton>button {
        background-color: transparent !important;
        color: #00ffcc !important;
        border: 2px solid #00ffcc !important;
        border-radius: 20px !important;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #00ffcc !important;
        color: #000 !important;
        box-shadow: 0px 0px 15px #00ffcc !important;
    }
    .stLinkButton>a {
        width: 100% !important;
        height: 38px !important;
        background-color: rgba(255,255,255,0.05) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 5px !important;
        font-size: 13px !important;
        text-decoration: none;
        display: flex; align-items: center; justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BACKEND ---
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        cols = ["Name", "Status", "Wunschpreis", "Kaufpreis", "Dauer", "Note", "Sprache", "Bemerkung", "Beendet_am", "Release_Datum"]
        for c in cols:
            if c not in df.columns: df[c] = "-"
        if "Preis_Check" not in df.columns:
            df["Preis_Check"] = False
        df['sort_date'] = pd.to_datetime(df['Release_Datum'], format='%d.%m.%Y', errors='coerce')
        return df
    return pd.DataFrame(columns=["Preis_Check", "Name", "Status", "Wunschpreis", "Kaufpreis", "Dauer", "Note", "Sprache", "Bemerkung", "Beendet_am", "Release_Datum"])

def save_data(df):
    if 'sort_date' in df.columns: df = df.drop(columns=['sort_date'])
    if 'Monat_Jahr' in df.columns: df = df.drop(columns=['Monat_Jahr'])
    df.to_csv(DB_FILE, index=False)

def quick_save(name, rel_date, game_id=None):
    df = load_data()
    if name not in df["Name"].values:
        hltb_query = urllib.parse.quote(name)
        new_row = pd.DataFrame([[
            False, name, "Noch zocken", "0.00 €", "0.00 €",
            "⏳ Check HLTB", "-", "Deutsch", "-", rel_date
        ]], columns=["Preis_Check", "Name", "Status", "Wunschpreis", "Kaufpreis", "Dauer", "Note", "Sprache", "Beendet_am", "Release_Datum"])
        df = pd.concat([df, new_row], ignore_index=True)
        save_data(df)
        st.toast(f"✅ {name} gemerkt!")
    else:
        st.toast("💡 Schon drin")

# --- HAUPTPROGRAMM ---
if check_password():
    df = load_data()

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🕹️ Vault Menü")
        suche = st.text_input("🔍 Spiele-Suche", "")
        alle_status = ["Noch zocken", "Zocke gerade", "Durchgezockt", "Abgebrochen", "Wunschliste"]
        filter_status = st.multiselect("Status filtern", alle_status, default=alle_status)
        st.write("---")
        st.info("Tipp: Nutze den '💰 Check?' Haken für den Sales Tracker!")

    tab_sammlung, tab_releases, tab_sales, tab_stats = st.tabs(["📋 Watchlist", "🆕 Radar", "💰 Sales Tracker", "📊 Dashboard"])

    # --- TAB 1: WATCHLIST ---
    with tab_sammlung:
        st.header("📋 Meine Watchlist")
        if not df.empty:
            if st.button("🎲 Was soll ich zocken? (Zufall)"):
                noch = df[df["Status"] == "Noch zocken"]
                if not noch.empty:
                    st.success(f"Die Würfel sind gefallen: **{random.choice(noch['Name'].values)}**!")
                else: st.info("Keine Spiele mit Status 'Noch zocken' gefunden.")

            display_df = df.copy()
            display_df['Beendet_am'] = pd.to_datetime(display_df['Beendet_am'], errors='coerce')
            display_df['Release_Datum'] = pd.to_datetime(display_df['Release_Datum'], errors='coerce')
            if filter_status:
                display_df = display_df[display_df["Status"].isin(filter_status)]
            if suche:
                display_df = display_df[display_df["Name"].str.contains(suche, case=False, na=False)]

            meine_reihenfolge = ["Name", "Preis_Check", "Status", "Kaufpreis", "Beendet_am", "Release_Datum", "Note", "Wunschpreis", "Sprache", "Dauer"]

            spalten_konfig = {
                "Name": st.column_config.TextColumn("Spielname", width="large", required=True),
                "Preis_Check": st.column_config.CheckboxColumn("💰", help="Im Sales-Tracker anzeigen"),
                "Status": st.column_config.SelectboxColumn("Status", options=alle_status),
                "Kaufpreis": st.column_config.NumberColumn("Kaufpreis", format="%.2f €"),
                "Beendet_am": st.column_config.DateColumn("Beendet am", format="DD.MM.YYYY"),
                "Release_Datum": st.column_config.DateColumn("Release", format="DD.MM.YYYY"),
                "Note": st.column_config.SelectboxColumn("Note", options=["-", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]),
                "Wunschpreis": st.column_config.NumberColumn("Wunschpreis", format="%.2f €", width="small"),
                "Sprache": st.column_config.TextColumn("Sprache", width="small"),
                "Dauer": st.column_config.TextColumn("Dauer", width="small")
            }

            edited_df = st.data_editor(
                display_df.sort_values(by='Name'),
                column_order=meine_reihenfolge,
                column_config=spalten_konfig,
                use_container_width=True,
                hide_index=True,
                key="watchlist_v4"
            )
            if st.button("💾 Alle Änderungen speichern"):
                save_df = edited_df.copy()
                for col in ['Beendet_am', 'Release_Datum']:
                    save_df[col] = pd.to_datetime(save_df[col], errors='coerce').dt.strftime('%d.%m.%Y').fillna('-')
                save_data(save_df)
                st.success("Gespeichert! Alle Spalten sind noch da.")
                st.rerun()
        else: st.info("Deine Liste ist noch leer. Geh zum Radar!")

    # --- TAB 2: RELEASE RADAR ---
    with tab_releases:
        st.header("🛰️ Kommende Highlights")
        heute = date.today()
        m_tabs = st.tabs([f"{(heute.replace(day=1)+timedelta(days=i*31)).strftime('%B %Y')}" for i in range(12)])
        for i in range(12):
            with m_tabs[i]:
                target = heute.replace(day=1) + timedelta(days=i*31)
                start = target.replace(day=1).strftime('%Y-%m-%d')
                end = target.replace(day=calendar.monthrange(target.year, target.month)[1]).strftime('%Y-%m-%d')
                url = f"https://api.rawg.io/api/games?key={API_KEY}&dates={start},{end}&ordering=-rating&page_size=21"
                try:
                    res = requests.get(url, timeout=10).json()
                    if 'results' in res and res['results']:
                        for k in range(0, len(res['results']), 3):
                            cols = st.columns(3)
                            for n in range(3):
                                if k+n < len(res['results']):
                                    g = res['results'][k+n]
                                    with cols[n]:
                                        st.image(g.get('background_image') or PLACEHOLDER_IMAGE)
                                        st.markdown(f'<div class="game-title">{g["name"]}</div>', unsafe_allow_html=True)
                                        try:
                                            rd = datetime.strptime(g['released'], '%Y-%m-%d').strftime('%d.%m.%Y')
                                        except:
                                            rd = "TBA"
                                        st.caption(f"📅 {rd}")
                                        b1, b2 = st.columns(2)
                                        if b1.button("❤️ Merken", key=f"r_{g['id']}"): quick_save(g['name'], rd, g['id'])
                                        b2.link_button("📺 Trailer", f"https://www.youtube.com/results?search_query={urllib.parse.quote(g['name'] + ' official trailer')}")
                                        st.write("---")
                    else:
                        st.info("Keine Daten für diesen Monat.")
                except: st.error("Fehler beim Abrufen der RAWG-Daten.")

    # --- TAB 3: SALES TRACKER ---
    with tab_sales:
        st.header("💰 Schneller Preis-Check")
        sales_df = df[df["Preis_Check"] == True]
        if not sales_df.empty:
            for _, row in sales_df.iterrows():
                cols = st.columns([3, 2, 1, 1, 1, 1])
                with cols[0]:
                    st.markdown(f"**{row['Name']}**")
                with cols[1]:
                    st.code(row['Name'], language=None)
                with cols[2]:
                    st.link_button("🔑KFS", "https://www.keyforsteam.de/")
                with cols[3]:
                    st.link_button("🎮IG", f"https://www.instant-gaming.com/de/suche/?q={urllib.parse.quote(row['Name'])}")
                with cols[4]:
                    st.link_button("🐧KIN", f"https://www.kinguin.net/listing?active=0&search={urllib.parse.quote(row['Name'])}")
                with cols[5]:
                    st.link_button("🔥ENE", f"https://www.eneba.com/store/all?text={urllib.parse.quote(row['Name'])}")
                st.markdown("<hr style='margin:2px 0px'>", unsafe_allow_html=True)
        else:
            st.info("Haken bei '💰 Check?' setzen!")

    # --- TAB 4: DASHBOARD ---
    with tab_stats:
        st.header("📊 Gamer Dashboard")
        if not df.empty:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Gesamt", len(df))
            with col2:
                beendet = len(df[df["Status"] == "Durchgezockt"])
                st.metric("Durchgezockt", beendet)
            with col3:
                total_hours = pd.to_numeric(df['Dauer'].str.replace('h','', regex=False).replace('-','0'), errors='coerce').sum()
                st.metric("Spielzeit Backlog", f"{int(total_hours) if not pd.isna(total_hours) else 0}h")
            with col4:
                st.metric("Offene Sales", len(df[df["Preis_Check"] == True]))

            st.write("---")
            st.subheader("🎯 Abschluss-Fortschritt")
            if len(df) > 0:
                quote = beendet / len(df)
                st.progress(quote)
                st.write(f"Du hast **{int(quote*100)}%** deiner Gaming-Bibliothek abgeschlossen!")

            st.write("---")
            st.subheader("🏆 Hall of Fame (Beendet & Bewertet)")
            beendet_df = df[df["Status"] == "Durchgezockt"]
            if not beendet_df.empty:
                hof_cols = st.columns(3)
                for index, row in beendet_df.reset_index().iterrows():
                    with hof_cols[index % 3]:
                        st.markdown(f"""
                        <div style="
                            border: 2px solid #00ffcc;
                            border-radius: 10px;
                            padding: 15px;
                            margin-bottom: 10px;
                            background-color: rgba(0, 255, 204, 0.05);
                            box-shadow: 0px 0px 10px rgba(0, 255, 204, 0.2);">
                            <h3 style="color: #00ffcc; margin: 0;">{row['Name']}</h3>
                            <p style="color: #ffcc00; font-weight: bold; margin: 5px 0;">Note: {row['Note']} ⭐</p>
                            <p style="font-size: 13px; font-style: italic;">"{row['Bemerkung'] if str(row.get('Bemerkung', '-')) not in ['-', '', 'nan'] else 'Kein Fazit.'}"</p>
                            <hr style="border-color: rgba(0, 255, 204, 0.2);">
                            <p style="font-size: 11px; color: #888;">Beendet am: {row['Beendet_am']}</p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("Noch keine Spiele als 'Durchgezockt' markiert.")
        else: st.info("Noch keine Daten vorhanden.")
