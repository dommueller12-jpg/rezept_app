import streamlit as st
from openai import OpenAI
import base64
import re

st.set_page_config(page_title="Team Rezept-Manager", page_icon="🍳", layout="centered")

# 1. DEINE NEUEN KATEGORIEN (Sinnvoll sortiert)
KATEGORIEN = [
    "Vorspeisen", 
    "Suppen",
    "Fleisch", 
    "Vegi", 
    "Vegan", 
    "Saucen", 
    "Marinaden",
    "Teige", 
    "Garnituren",
    "Dessert", 
    "Dessert gefroren"
]

# INITIALISIERUNG DER DATENBANK MIT DEN NEUEN KATEGORIEN
if 'datenbank' not in st.session_state:
    st.session_state.datenbank = [
        {"id": 0, "titel": "Tomaten-Carpaccio", "kategorie": "Vorspeisen", "zutaten": "4 grosse Tomaten\n50ml Olivenöl\n20g Basilikum\nSalz & Pfeffer"},
        {"id": 1, "titel": "Rindsfilet Marinade", "kategorie": "Marinaden", "zutaten": "100ml Olivenöl\n2 Zweige Rosmarin\n2 Knoblauchzehen\n1 TL Senf"},
        {"id": 2, "titel": "Zitronen-Sorbet", "kategorie": "Dessert gefroren", "zutaten": "200ml Zitronensaft\n150g Zucker\n200ml Wasser"}
    ]
if 'id_counter' not in st.session_state:
    st.session_state.id_counter = 3

# Hilfsfunktion zur Multiplikation von Zahlen im Text
def multipliziere_zutaten(text, faktor):
    if faktor == 1:
        return text
    def repliziere(match):
        zahl_str = match.group(1).replace(',', '.')
        try:
            zahl = float(zahl_str)
            neue_zahl = zahl * faktor
            if neue_zahl.is_integer():
                return f"**{int(neue_zahl)}**"
            else:
                return f"**{round(neue_zahl, 2)}**".replace('.', ',')
        except ValueError:
            return match.group(0)
    return re.sub(r'(\d+[\.,]\d+|\d+)', repliziere, text)

# AUTOMATISCHER KEY-CHECK
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key)

    # 📱 KAPITEL-NAVIGATION TABS
    kapitel = st.tabs(["📸 Zettel scannen", "🗂️ Rezept-Datenbank", "✍️ Neu hinzufügen"])

    # ------------------------------------------------------------
    # KAPITEL 1: ZETTEL SCANNEN
    # ------------------------------------------------------------
    with kapitel[0]:
        st.subheader("📸 Handschriftliches Rezept digitalisieren")
        uploaded_file = st.file_uploader("Foto hochladen", type=["jpg", "jpeg", "png"], key="scanner_upload")

        if uploaded_file:
            st.image(uploaded_file, caption="Hochgeladenes Foto", use_container_width=True)
            
            if 'rohes_rezept' not in st.session_state:
                st.session_state.rohes_rezept = None

            if st.button("📝 Zettel einlesen", type="primary"):
                st.info("ChatGPT liest die Handschrift... Bitte warten...")
                try:
                    bytes_data = uploaded_file.getvalue()
                    base64_image = base64.b64encode(bytes_data).decode('utf-8')
                    
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "Lies dieses handschriftliche Rezept. Extrahiere NUR die Zutatenliste mit Mengenangaben und schreibe sie sauber untereinander. Verwende Zahlen für die Mengen (z.B. '200 g Mehl', '3 Eier'). Schreibe keine Einleitung, sondern starte direkt mit den Zutaten."},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                                ]
                            }
                        ]
                    )
                    st.session_state.rohes_rezept = response.choices.message.content
                    st.success("Erfolgreich eingelesen!")
                except Exception as e:
                    st.error(f"Fehler beim Scannen: {e}")

            if st.session_state.rohes_rezept:
                st.divider()
                st.subheader("🔢 Zutatenmengen multiplizieren")
                faktor = st.slider("Menge hochrechnen (Faktor):", min_value=1, max_value=10, value=1, key="scan_slider")
                
                st.markdown("### 📋 Deine Zutatenliste:")
                berechnetes_rezept = multipliziere_zutaten(st.session_state.rohes_rezept, faktor)
                st.write(berechnetes_rezept)

    # ------------------------------------------------------------
    # KAPITEL 2: REZEPT-DATENBANK (Inklusive Bearbeiten & Löschen)
    # ------------------------------------------------------------
    with kapitel[1]:
        st.subheader("🗂️ Geteilte Rezept-Datenbank")
        
        # Filter nach den neuen Kategorien
        such_kategorien = ["Alle"] + KATEGORIEN
        auswahl_kat = st.selectbox("Kategorie filtern:", such_kategorien)
        
        # Rezepte filtern
        if auswahl_kat == "Alle":
            gefilterte_rezepte = st.session_state.datenbank
        else:
            gefilterte_rezepte = [r for r in st.session_state.datenbank if r["kategorie"] == auswahl_kat]
        
        # Rezepte anzeigen
        if not gefilterte_rezepte:
            st.info("Noch keine Rezepte in dieser Kategorie vorhanden.")
        else:
            for idx, r in enumerate(gefilterte_rezepte):
                with st.expander(f"🍽️ {r['titel']} ({r['kategorie']})"):
                    
                    edit_key = f"edit_mode_{r['id']}"
                    if edit_key not in st.session_state:
                        st.session_state[edit_key] = False

                    # MODUS A: REZEPT ANZEIGEN & MULTIPLIZIEREN
                    if not st.session_state[edit_key]:
                        st.markdown("**Basis-Zutaten:**")
                        st.text(r['zutaten'])
                        
                        db_faktor = st.slider(f"Portionen für {r['titel']}:", min_value=1, max_value=10, value=1, key=f"slider_{r['id']}")
                        if db_faktor > 1:
                            st.markdown("**🔢 Umgerechnete Zutaten:**")
                            st.write(multipliziere_zutaten(r['zutaten'], db_faktor))
                        
                        st.divider()
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✏️ Bearbeiten", key=f"btn_edit_{r['id']}"):
                                st.session_state[edit_key] = True
                                st.rerun()
                        with col2:
                            if st.button("🗑️ Löschen", key=f"btn_del_{r['id']}", type="secondary"):
                                st.session_state.datenbank = [rezept for rezept in st.session_state.datenbank if rezept["id"] != r["id"]]
                                st.success(f"'{r['titel']}' wurde gelöscht!")
                                st.rerun()

                    # MODUS B: REZEPT BEARBEITEN
                    else:
                        st.markdown("### ✏️ Rezept bearbeiten")
                        edit_titel = st.text_input("Name:", value=r['titel'], key=f"tit_{r['id']}")
                        edit_kat = st.selectbox("Kategorie:", KATEGORIEN, index=KATEGORIEN.index(r['kategorie']), key=f"kat_{r['id']}")
                        edit_zutaten = st.text_area("Zutaten:", value=r['zutaten'], key=f"zut_{r['id']}")
                        
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button("💾 Speichern", key=f"save_{r['id']}", type="primary"):
                                for original in st.session_state.datenbank:
                                    if original["id"] == r["id"]:
                                        original["titel"] = edit_titel
                                        original["kategorie"] = edit_kat
                                        original["zutaten"] = edit_zutaten
                                st.session_state[edit_key] = False
                                st.success("Änderungen gespeichert!")
                                st.rerun()
                        with b2:
                            if st.button("❌ Abbrechen", key=f"canc_{r['id']}"):
                                st.session_state[edit_key] = False
                                st.rerun()

    # ------------------------------------------------------------
    # KAPITEL 3: REZEPT MANUELL HINZUFÜGEN
    # ------------------------------------------------------------
    with kapitel[2]:
        st.subheader("✍️ Neues Rezept manuell eintippen")
        neuer_titel = st.text_input("Name des Rezepts:", key="add_titel")
        neue_kat = st.selectbox("Kategorie wählen:", KATEGORIEN, key="add_kat")
        neue_zutaten = st.text_area("Zutaten (Zeile für Zeile, z.B. '200g Mehl'):", key="add_zutaten")
        
        if st.button("💾 In Datenbank保存 speichern", key="add_save_btn"):
            if neuer_titel and neue_zutaten:
                neues_rezept = {
                    "id": st.session_state.id_counter, 
                    "titel": neuer_titel, 
                    "kategorie": neue_kat, 
                    "zutaten": neue_zutaten
                }
                st.session_state.datenbank.append(neues_rezept)
                st.session_state.id_counter += 1
                st.success(f"'{neuer_titel}' wurde erfolgreich unter '{neue_kat}' gespeichert!")
            else:
                st.error("Bitte fülle den Namen und die Zutatenliste aus.")

except Exception as e:
    st.error("Der OpenAI API Key fehlt in den Cloud-Settings! Bitte hinterlege ihn unter 'Manage app' -> 'Settings' -> 'Secrets'.")
