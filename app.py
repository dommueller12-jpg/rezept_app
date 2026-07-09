import streamlit as st
from openai import OpenAI
import base64

st.set_page_config(page_title="Team Rezept-Manager", page_icon="🍳", layout="centered")

st.title("🍳 Team Rezept-Manager")
st.write("Digitalisiere handschriftliche Rezepte im Handumdrehen.")

# AUTOMATISCHER KEY-CHECK: Die App holt sich den Schlüssel aus den Streamlit Cloud Secrets
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key)
    
    # 1. Bild-Upload (Nutzt direkt die Smartphone-Kamera)
    uploaded_file = st.file_uploader("Foto des Rezepts hochladen", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        st.image(uploaded_file, caption="Hochgeladenes Rezept", use_container_width=True)
        
        if st.button("📝 Zettel digitalisieren"):
            st.info("ChatGPT analysiert die Handschrift... Bitte warten...")
            
            try:
                # Bild für die KI lesbar machen
                bytes_data = uploaded_file.getvalue()
                base64_image = base64.b64encode(bytes_data).decode('utf-8')
                
                # Anfrage an ChatGPT senden
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Lies dieses handschriftliche Rezept. Gib mir den Text perfekt strukturiert zurück. Es MUSS folgende Struktur haben:\nTitel: [Name]\nKategorie: [Zugehörige Kategorie]\nZutaten:\n- [Menge] [Zutat]\nZubereitung:\n[Schritte]"},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ]
                        }
                    ]
                )
                
                # Ergebnis anzeigen
                rezept_text = response.choices.message.content
                st.success("Erfolgreich digitalisiert!")
                st.markdown("### Das digitalisierte Rezept:")
                st.write(rezept_text)
                
            except Exception as e:
                st.error(f"Fehler beim Scannen: {e}")

    # 2. Multiplikator-Funktion
    st.divider()
    st.subheader("🔢 Portionen anpassen")
    portionen = st.slider("Gewünschte Portionen:", min_value=1, max_value=10, value=2)
    st.write(f"Zutaten werden automatisch für **{portionen} Personen** berechnet.")

except Exception as e:
    st.error("Der OpenAI API Key fehlt in den Cloud-Settings! Bitte hinterlege ihn unter 'Manage app' -> 'Settings' -> 'Secrets'.")
