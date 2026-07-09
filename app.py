import streamlit as st
from openai import OpenAI
import base64
import re

st.set_page_config(page_title="Team Rezept-Manager", page_icon="🍳", layout="centered")

st.title("🍳 Team Rezept-Manager")
st.write("Digitalisiere handschriftliche Rezepte im Handumdrehen.")

# Funktion zur Multiplikation von Zahlen im Text
def multipliziere_zutaten(text, faktor):
    if faktor == 1:
        return text
    
    def repliziere(match):
        zahl_str = match.group(1).replace(',', '.')
        try:
            zahl = float(zahl_str)
            neue_zahl = zahl * faktor
            # Schick formatieren: Wenn es eine ganze Zahl ist, kein .0 anzeigen
            if neue_zahl.is_integer():
                return f"**{int(neue_zahl)}**"
            else:
                return f"**{round(neue_zahl, 2)}**".replace('.', ',')
        except ValueError:
            return match.group(0)

    # Sucht nach Zahlen (auch Kommazahlen) im Zutatenbereich
    return re.sub(r'(\d+[\.,]\d+|\d+)', repliziere, text)

# AUTOMATISCHER KEY-CHECK
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key)
    
    # 1. Bild-Upload (Kamera)
    uploaded_file = st.file_uploader("Foto des Rezepts hochladen", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        st.image(uploaded_file, caption="Hochgeladenes Rezept", use_container_width=True)
        
        # Wir speichern das digitalisierte Rezept im "Session State", damit es beim Regler-Verschieben nicht gelöscht wird
        if 'rohes_rezept' not in st.session_state:
            st.session_state.rohes_rezept = None

        if st.button("📝 Zettel digitalisieren"):
            st.info("ChatGPT analysiert die Handschrift... Bitte warten...")
            
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
                st.success("Erfolgreich digitalisiert!")
                
            except Exception as e:
                st.error(f"Fehler beim Scannen: {e}")

        # Wenn ein Rezept eingescannt wurde, zeigen wir den Multiplikator an
        if st.session_state.rohes_rezept:
            st.divider()
            st.subheader("🔢 Zutatenmengen multiplizieren")
            st.write("Das Rezept wurde für die **Basis-Menge (1x)** eingelesen. Passe die Portionen hier an:")
            
            faktor = st.slider("Multiplikations-Faktor wählen:", min_value=1, max_value=10, value=1, step=1)
            
            st.markdown("### 📋 Deine angepasste Zutatenliste:")
            berechnetes_rezept = multipliziere_zutaten(st.session_state.rohes_rezept, faktor)
            st.write(berechnetes_rezept)

except Exception as e:
    st.error("Der OpenAI API Key fehlt in den Cloud-Settings! Bitte hinterlege ihn unter 'Manage app' -> 'Settings' -> 'Secrets'.")
