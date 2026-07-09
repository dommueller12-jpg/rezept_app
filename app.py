import streamlit as st
import openai

# App-Design für Smartphones optimiert
st.set_page_config(page_title="Team Rezept-Manager", page_icon="🍳", layout="centered")

st.title("🍳 Team Rezept-Manager")
st.write("Digitalisiere handschriftliche Rezepte im Handumdrehen.")

# API-Schlüssel Eingabe (Sicherheits-Check)
api_key = st.text_input("OpenAI API Key eingeben:", type="password")

if api_key:
    openai.api_key = api_key

    # 1. Bild-Upload (Nutzt die Smartphone-Kamera)
    uploaded_file = st.file_uploader("Foto des Rezepts hochladen", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        st.image(uploaded_file, caption="Hochgeladenes Rezept", use_container_width=True)
        
        if st.button("📝 Zettel digitalisieren"):
            st.info("KI analysiert die Handschrift... Bitte warten...")
            # Hier wird später die Verbindung zu ChatGPT aktiviert
            st.success("Erfolg! (Hier erscheint gleich das echte Rezept)")

    # 2. Multiplikator-Funktion
    st.divider()
    st.subheader("🔢 Portionen anpassen")
    portionen = st.slider("Gewünschte Portionen:", min_value=1, max_value=10, value=2)
    st.write(f"Zutaten werden automatisch für **{portionen} Personen** berechnet.")

else:
    st.warning("Bitte gib deinen OpenAI API Key ein, um die App zu starten.")
