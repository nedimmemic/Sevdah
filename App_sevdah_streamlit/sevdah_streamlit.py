"""
Sevdah Streamlit App - Web verzija
Author: Nedim Memić, Ph.D.
"""

import streamlit as st
import json
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from textblob import TextBlob
from collections import Counter
import re

# PAGE CONFIG
st.set_page_config(
    page_title="🎵 Sevdah",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CUSTOM CSS
st.markdown("""
<style>
    .main {
        background-color: #1a1a2e;
    }
    .stButton>button {
        background-color: #e94560;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #d63850;
    }
    h1, h2, h3 {
        color: #e94560 !important;
    }
</style>
""", unsafe_allow_html=True)


# HELPER FUNCTIONS
def parsiraj_tekstove(txt_sadrzaj):
    """Parsira tekstove iz TXT fajla"""
    tekstovi = {}
    linije = txt_sadrzaj.split('\n')
    
    trenutni_naslov = None
    trenutni_tekst = []
    
    i = 0
    while i < len(linije):
        linija = linije[i]
        linija_stripped = linija.strip()
        
        if not linija_stripped or 'ORIGINALNI TEKSTOVI' in linija_stripped or '===' in linija_stripped:
            i += 1
            continue
        
        je_naslov = False
        naslov = None
        
        if '. ' in linija_stripped:
            dijelovi = linija_stripped.split('. ', 1)
            if dijelovi[0].replace(' ', '').isdigit() and len(dijelovi) == 2:
                naslov = dijelovi[1].strip().upper()
                je_naslov = True
        
        elif linija_stripped.isupper() and len(linija_stripped) > 3:
            naslov = linija_stripped
            je_naslov = True
        
        if je_naslov and naslov:
            if trenutni_naslov and trenutni_tekst:
                tekstovi[trenutni_naslov] = '\n'.join(trenutni_tekst).strip()
            
            trenutni_naslov = naslov
            trenutni_tekst = []
            i += 1
            continue
        
        if linija_stripped.startswith('---'):
            i += 1
            continue
        
        if trenutni_naslov:
            trenutni_tekst.append(linija)
        
        i += 1
    
    if trenutni_naslov and trenutni_tekst:
        tekstovi[trenutni_naslov] = '\n'.join(trenutni_tekst).strip()
    
    return tekstovi


@st.cache_data
def ucitaj_pjesme():
    """Učitava pjesme iz JSON i TXT fajla"""
    try:
        with open('sevdalinke.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            pjesme = data.get('pjesme', [])
        
        try:
            with open('sevdalinke_tekstovi.txt', 'r', encoding='utf-8') as f:
                txt_sadrzaj = f.read()
            
            tekstovi = parsiraj_tekstove(txt_sadrzaj)
            
            for pjesma in pjesme:
                naslov = pjesma['naslov'].upper()
                if naslov in tekstovi:
                    pjesma['tekst'] = tekstovi[naslov]
                else:
                    pjesma['tekst'] = f"Tekst nije pronađen"
        except FileNotFoundError:
            for pjesma in pjesme:
                pjesma['tekst'] = "Fajl sevdalinke_tekstovi.txt ne postoji"
        
        return pjesme
    
    except FileNotFoundError:
        st.error("❌ Fajl sevdalinke.json ne postoji!")
        return []


def clean_word(word):
    """Čisti riječ od interpunkcije"""
    return re.sub(r'[^\w]', '', word).lower()


def ucitaj_stopwords():
    """Učitava stopwords"""
    try:
        with open('stopwords.txt', 'r', encoding='utf-8') as f:
            raw_stopwords = f.read().splitlines()
        return set(clean_word(w) for w in raw_stopwords if w.strip())
    except FileNotFoundError:
        return set(['i', 'u', 'na', 'se', 'je', 'da', 'su', 'za', 'o', 'sa'])


def analiziraj_sentiment(tekst):
    """Sentiment analiza teksta"""
    blob = TextBlob(tekst)
    return blob.sentiment.polarity


# INICIJALIZACIJA SESSION STATE
if 'omiljene' not in st.session_state:
    st.session_state.omiljene = set()

if 'pjesme' not in st.session_state:
    st.session_state.pjesme = ucitaj_pjesme()


# MAIN APP
def main():
    # HEADER
    st.title("🎵 SEVDAH - Sevdalinke")
    st.markdown("---")
    
    pjesme = st.session_state.pjesme
    
    if not pjesme:
        st.error("Nema učitanih pjesama. Provjerite da li postoje JSON i TXT fajlovi.")
        return
    
    # SIDEBAR
    with st.sidebar:
        st.header("📋 Izbor Pjesme")
        
        # Filter
        filter_omiljene = st.checkbox("⭐ Samo omiljene", value=False)
        
        # Lista pjesama
        if filter_omiljene:
            lista_pjesama = [p for p in pjesme if p['naslov'] in st.session_state.omiljene]
        else:
            lista_pjesama = pjesme
        
        if not lista_pjesama:
            st.warning("Nema omiljenih pjesama")
            lista_pjesama = pjesme
        
        # Selectbox
        izbor = st.selectbox(
            "Izaberi pjesmu:",
            lista_pjesama,
            format_func=lambda x: f"{'★ ' if x['naslov'] in st.session_state.omiljene else '   '}{x['naslov']}"
        )
        
        st.markdown("---")
        st.info(f"📊 Ukupno: {len(pjesme)} pjesama\n\n⭐ Omiljene: {len(st.session_state.omiljene)}")
    
    # MAIN CONTENT
    if izbor:
        trenutna = izbor
        
        # TABS
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Pjesma", "💭 Sentiment", "📊 Statistika", "ℹ️ O nama"])
        
        # TAB 1: PJESMA
        with tab1:
            st.markdown(f"## {trenutna['naslov']}")
            st.markdown(f"**Autor:** {trenutna['autor']} | **Izvođač:** {trenutna['izvodjac']}")
            
            # Buttons
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("🌐 Info o pjesmi"):
                    st.markdown(f"[📖 Otvori info stranicu]({trenutna['info_url']})")
            
            with col2:
                if st.button("▶️ YouTube Video"):
                    st.markdown(f"[🎥 Otvori video]({trenutna['video_url']})")
            
            with col3:
                if trenutna['naslov'] in st.session_state.omiljene:
                    if st.button("★ Ukloni iz omiljenih"):
                        st.session_state.omiljene.remove(trenutna['naslov'])
                        st.rerun()
                else:
                    if st.button("⭐ Dodaj u omiljene"):
                        st.session_state.omiljene.add(trenutna['naslov'])
                        st.rerun()
            
            with col4:
                tekst_za_download = f"{trenutna['naslov']}\n"
                tekst_za_download += f"Autor: {trenutna['autor']}\n"
                tekst_za_download += f"Izvođač: {trenutna['izvodjac']}\n\n"
                tekst_za_download += "=" * 50 + "\n\n"
                tekst_za_download += trenutna['tekst']
                
                st.download_button(
                    label="💾 Snimi tekst",
                    data=tekst_za_download,
                    file_name=f"{trenutna['naslov'].replace(' ', '_')}.txt",
                    mime="text/plain"
                )
            
            st.markdown("---")
            
            # Tekst pjesme
            st.text_area(
                "📝 Tekst pjesme:",
                trenutna['tekst'],
                height=400,
                disabled=True
            )
        
        # TAB 2: SENTIMENT
        with tab2:
            st.header("💭 Sentiment Analiza")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 Analiziraj trenutnu pjesmu"):
                    tekst = trenutna['tekst']
                    
                    if tekst and 'nije pronađen' not in tekst:
                        sentiment = analiziraj_sentiment(tekst)
                        
                        if sentiment > 0:
                            ikona = "🟢"
                            oznaka = "POZITIVAN"
                            boja = "green"
                        elif sentiment < 0:
                            ikona = "🔴"
                            oznaka = "NEGATIVAN"
                            boja = "red"
                        else:
                            ikona = "🟡"
                            oznaka = "NEUTRALAN"
                            boja = "gray"
                        
                        st.markdown(f"### {ikona} Sentiment: **{sentiment:.3f}**")
                        st.markdown(f"**Kategorija:** :{boja}[{oznaka}]")
                        
                        # Top riječi
                        stopwords = ucitaj_stopwords()
                        words = [clean_word(w) for w in tekst.split()]
                        words = [w for w in words if w and w not in stopwords]
                        word_counts = Counter(words)
                        top_10 = word_counts.most_common(10)
                        
                        st.markdown("#### 📊 Top 10 riječi:")
                        for i, (word, count) in enumerate(top_10, 1):
                            st.text(f"{i}. {word}: {count}")
                    else:
                        st.error("Tekst nije dostupan za analizu")
            
            with col2:
                if st.button("☁️ Word Cloud"):
                    tekst = trenutna['tekst']
                    
                    if tekst and 'nije pronađen' not in tekst:
                        stopwords = ucitaj_stopwords()
                        
                        wordcloud = WordCloud(
                            width=800,
                            height=400,
                            background_color='white',
                            stopwords=stopwords,
                            colormap='viridis'
                        ).generate(tekst)
                        
                        fig, ax = plt.subplots(figsize=(10, 5))
                        ax.imshow(wordcloud, interpolation='bilinear')
                        ax.axis('off')
                        ax.set_title(f"Word Cloud: {trenutna['naslov']}", fontsize=14, fontweight='bold')
                        st.pyplot(fig)
                    else:
                        st.error("Tekst nije dostupan")
        
        # TAB 3: STATISTIKA
        with tab3:
            st.header("📊 Statistika Sevdalinki")
            
            # Osnovna statistika
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("📋 Ukupno pjesama", len(pjesme))
                st.metric("⭐ Omiljene pjesme", len(st.session_state.omiljene))
            
            with col2:
                autori = Counter([p['autor'] for p in pjesme])
                izvodjaci = Counter([p['izvodjac'] for p in pjesme])
                st.metric("✍️ Ukupno autora", len(autori))
                st.metric("🎤 Ukupno izvođača", len(izvodjaci))
            
            st.markdown("---")
            
            # Top autori
            st.subheader("✍️ Top 10 Autora")
            top_autori = autori.most_common(10)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            autori_imena = [a[0] for a in top_autori]
            autori_brojevi = [a[1] for a in top_autori]
            ax.barh(autori_imena, autori_brojevi, color='#e94560')
            ax.set_xlabel('Broj pjesama')
            ax.set_title('Top 10 Autora', fontweight='bold')
            plt.tight_layout()
            st.pyplot(fig)
            
            st.markdown("---")
            
            # Top izvođači
            st.subheader("🎤 Top 10 Izvođača")
            top_izvodjaci = izvodjaci.most_common(10)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            izvodjaci_imena = [i[0] for i in top_izvodjaci]
            izvodjaci_brojevi = [i[1] for i in top_izvodjaci]
            ax.barh(izvodjaci_imena, izvodjaci_brojevi, color='#533483')
            ax.set_xlabel('Broj pjesama')
            ax.set_title('Top 10 Izvođača', fontweight='bold')
            plt.tight_layout()
            st.pyplot(fig)
        
        # TAB 4: O NAMA
        with tab4:
            st.header("ℹ️ O Aplikaciji")
            
            try:
                with open('o_nama.txt', 'r', encoding='utf-8') as f:
                    o_nama_tekst = f.read()
                st.markdown(o_nama_tekst)
            except FileNotFoundError:
                st.warning("Fajl o_nama.txt ne postoji")
                st.markdown("""
                ### 🎵 SEVDAH - Aplikacija za Sevdalinke
                
                Ovo je moderna aplikacija za pregledanje i analizu sevdalinki.
                
                **Funkcionalnosti:**
                - 📋 Pregled tekstova sevdalinki
                - ⭐ Omiljene pjesme
                - 💭 Sentiment analiza
                - ☁️ Word Cloud vizualizacije
                - 📊 Statistika autora i izvođača
                
                **Autor:** Nedim Memić, Ph.D.
                **Email:** nedim.memic21@gmail.com
                """)


if __name__ == "__main__":
    main()
