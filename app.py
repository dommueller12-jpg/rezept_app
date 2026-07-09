import streamlit as st
from openai import OpenAI
import base64
import re

st.set_page_config(page_title="Team Rezept-Manager", page_icon="🍳", layout="centered")

# INITIALISIERUNG DER DATENBANK (Damit Rezepte im Hintergrund gespeichert bleiben)
if 'datenbank' not in st.session_state:
    st.session_state.datenbank = [
        {"titel": "Klassische Lasagne", "kategorie": "Hauptspeisen", "zutaten": "12 Lasagneblätter\n500g Hackfleisch\n2 Zwiebeln\n400g Tomaten (Dose)\n200g Parmesan"},
        {"titel": "Schokomuffins", "kategorie": "Desserts", "zutaten": "250g Mehl\n100g Zucker\n50g Kakaopulver\n2 Eier\n100ml Milch"},
        {"titel": "Tomatensuppe", "kategorie": "Vorspeisen", "zutaten": "1kg Tomaten\n1 Zwiebel\n2 Knoblauchzehen\n500ml Gemüsebrühe"}
    ]

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

    # 📱 KAPITEL-NAVIGATION (Für Smartphones optimierte Tabs ganz oben)
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
    # KAPITEL 2: REZEPT-DATENBANK
    # ------------------------------------------------------------
    with kapitel[1]:
        st.subheader("🗂️ Geteilte Rezept-Datenbank")
        
        # Filter nach Kategorien
        kategorien = ["Alle", "Vorspeisen", "Hauptspeisen", "Desserts"]
        auswahl_kat = st.selectbox("Kategorie filtern:", kategorien)
        
        # Rezepte filtern
        if auswahl_kat == "Alle":
            gefilterte_rezepte = st.session_state.datenbank
        else:
            gefilterte_rezepte = [r for r in st.session_state.datenbank if r["kategorie"] == auswahl_kat]
        
        # Rezepte anzeigen
        if not gefilterte_rezepte:
            st.info("Noch keine Rezepte in dieser Kategorie vorhanden.")
        else:
            for r in gefilterte_rezepte:
                with st.expander(f"🍽️ {r['titel']}"):
                    st.caption(f"Kategorie: {r['kategorie']}")
                    st.markdown("**Basis-Zutaten:**")
                    st.text(r['zutaten'])
                    
                    # Auch in der Datenbank lässt sich die Menge multiplizieren!
                    db_faktor = st.slider(f"Portionen für {r['titel']}:", min_value=1, max_value=10, value=1, key=f"slider_{r['titel']}")
                    if db_faktor > 1:
                        st.markdown("**🔢 Umgerechnete Zutaten:**")
                        st.write(multipliziere_zutaten(r['zutaten'], db_faktor))

    # ------------------------------------------------------------
    # KAPITEL 3: REZEPT MANUELL HINZUFÜGEN
    # ------------------------------------------------------------
    with kapitel[2]:
        st.subheader("✍️ Neues Rezept manuell eintippen")
        neuer_titel = st.text_input("Name des Rezepts:")
        neue_kat = st.selectbox("Kategorie wählen:", ["Vorspeisen", "Hauptspeisen", "Desserts"])
        neue_zutaten = st.text_area("Zutaten (Zeile für Zeile, z.B. '200g Mehl'):")
        
        if st.button("💾 In Datenbank speichern"):
            if neuer_titel and neue_zutaten:
                neues_rezept = {"titel": neuer_titel, "kategorie": neue_kat, "zutaten": neue_zutaten}
                st.session_state.datenbank.append(neues_rezept)
                st.success(f"'{neuer_titel}' wurde erfolgreich in die Datenbank gespeichert!")
            else:
                st.error("Bitte fülle den Namen und die Zutatenliste aus.")

except Exception as e:
    st.error("Der OpenAI API Key fehlt in den Cloud-Settings! Bitte hinterlege ihn unter 'Manage app' -> 'Settings' -> 'Secrets'.")
