import html
import time
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation
from folium.plugins import Draw
from io import BytesIO
import math
from datetime import datetime
import base64
import re
from urllib.parse import quote
import plotly.io as pio

pio.templates["hc_dark"] = go.layout.Template(layout=dict(
    font=dict(color="#CFE3D8"), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(gridcolor="rgba(255,255,255,.07)", zerolinecolor="rgba(255,255,255,.12)"),
    yaxis=dict(gridcolor="rgba(255,255,255,.07)", zerolinecolor="rgba(255,255,255,.12)"),
    colorway=["#34D399", "#38BDF8", "#FBBF24", "#F87171", "#A78BFA", "#A3E635"]))
pio.templates.default = "plotly_dark+hc_dark"
_orig_plotly_chart = st.plotly_chart


def _hc_plotly_chart(fig, *a, **k):
    k.setdefault("theme", None)  # keep our dark template instead of Streamlit's light override
    return _orig_plotly_chart(fig, *a, **k)


st.plotly_chart = _hc_plotly_chart

st.set_page_config(page_title="Hyperclimate – Smart Crop & Field Intelligence", page_icon="🛰️", layout="wide")

st.sidebar.caption("🛰️ Hyperclimate • Satellite + Weather + AI")

st.markdown("""
<style>
.loc-card {
    padding: 12px 12px 10px 12px;
    margin: 4px 0 12px 0;
    border: 1px solid rgba(128,128,128,.25);
    border-radius: 12px;
    background: rgba(128,128,128,.06);
}
.loc-title { font-size: 1.05rem; font-weight: 700; }
.loc-subtitle { font-size: .78rem; opacity: .72; margin-top: 3px; line-height: 1.35; }
</style>
<style>
/* ===== Farmer-friendly Hyperclimate visual redesign ===== */
:root {
  --hc-radius: 16px;
}
.block-container {padding-top: 1.2rem; padding-bottom: 2.5rem;}
.hc-hero {
  padding: 22px 24px;
  border-radius: 22px;
  background: linear-gradient(135deg, rgba(31,122,78,.16), rgba(76,175,80,.07));
  border: 1px solid rgba(31,122,78,.22);
  margin-bottom: 14px;
}
.hc-hero h1 {margin:0; font-size:2rem; letter-spacing:-.5px;}
.hc-hero p {margin:.45rem 0 0; opacity:.78; font-size:1rem;}
.hc-card {
  border: 1px solid rgba(128,128,128,.20);
  border-radius: var(--hc-radius);
  padding: 15px 16px;
  min-height: 112px;
  background: rgba(128,128,128,.045);
}
.hc-card .icon {font-size:1.55rem; margin-bottom:5px;}
.hc-card .label {font-size:.78rem; opacity:.68;}
.hc-card .value {font-size:1.42rem; font-weight:750; margin-top:3px;}
.hc-card .help {font-size:.75rem; opacity:.68; margin-top:3px;}
.hc-section {
  margin: 18px 0 9px;
  font-size: 1.08rem;
  font-weight: 750;
}
.hc-alert {
  padding: 14px 16px;
  border-radius: 15px;
  border: 1px solid rgba(128,128,128,.22);
  background: rgba(128,128,128,.055);
}
.hc-simple {
  padding: 12px 14px;
  border-radius: 13px;
  background: rgba(128,128,128,.05);
  border-left: 4px solid rgba(31,122,78,.65);
  margin: 7px 0;
}
.small-muted {font-size:.78rem; opacity:.68;}

.hc-title {font-size:2.15rem; font-weight:800; letter-spacing:-.7px; margin:0;}
.hc-subtitle {font-size:.95rem; opacity:.72; margin-top:4px;}
.hc-status {display:inline-block; padding:6px 11px; border-radius:999px; font-size:.76rem; font-weight:750; background:rgba(34,197,94,.12); border:1px solid rgba(34,197,94,.25);}
.hc-mini {font-size:.72rem; opacity:.68; margin-top:2px;}
.hc-definition {padding:9px 12px; border-radius:12px; background:rgba(128,128,128,.045); border:1px solid rgba(128,128,128,.16); margin:6px 0;}
.hc-definition b {font-size:.92rem;}
</style>

""", unsafe_allow_html=True)


# ================= Language =================
lang_choice = st.sidebar.radio("Language / மொழி", ["English", "தமிழ்"], horizontal=True)
LANG = 0 if lang_choice == "English" else 1
LANG_CODE = "en" if LANG == 0 else "ta"

TR = {
    "title": ("🛰️ Hyperclimate – Smart Crop & Field Intelligence", "🛰️ Hyperclimate – ஸ்மார்ட் பயிர் & நில கண்காணிப்பு"),
    "your_field": ("Your field", "உங்கள் வயல்"),
    "loc_mode": ("How to set the location?", "இடத்தை எப்படி கொடுக்க வேண்டும்?"),
    "by_name": ("Place name", "ஊர் பெயர்"),
    "by_coords": ("Latitude / Longitude", "அட்சரேகை / தீர்க்கரேகை"),
    "by_map": ("Click on satellite map", "செயற்கைக்கோள் வரைபடத்தில் தேர்வு"),
    "by_gps": ("📱 My current location (GPS)", "📱 என் தற்போதைய இடம் (GPS)"),
    "go": ("Go", "செல்"),
    "map_hint": (
        "Click anywhere on the satellite map to select your field. Use + / - to zoom in.",
        "உங்கள் வயலை தேர்வு செய்ய செயற்கைக்கோள் வரைபடத்தில் கிளிக் செய்யுங்கள். + / - மூலம் zoom செய்யலாம்.",
    ),
    "selected": ("Selected: {p}", "தேர்வு: {p}"),
    "gps_hint": (
        "Tap the button below and allow location access in your browser.",
        "கீழே உள்ள பட்டனை அழுத்தி, உங்கள் browser-ல் location அனுமதி கொடுங்கள்.",
    ),
    "gps_wait": (
        "Waiting for location... Turn on GPS on your phone and tap Allow.",
        "இடம் காத்திருக்கிறது... போனில் GPS ஆன் செய்து, Allow கொடுங்கள்.",
    ),
    "gps_acc": ("GPS accuracy: about {m} m", "GPS துல்லியம்: சுமார் {m} மீ"),
    "place_label": ("Place name", "ஊர் பெயர்"),
    "exact_place": ("Select the exact place", "சரியான இடத்தை தேர்வு செய்யுங்கள்"),
    "no_place": ("Place not found. Try another spelling.", "இடம் கிடைக்கவில்லை. வேறு எழுத்துப்பிழை முயற்சிக்கவும்."),
    "lat": ("Latitude", "அட்சரேகை"),
    "lon": ("Longitude", "தீர்க்கரேகை"),
    "crop_group": ("Crop type", "பயிர் வகை"),
    "all_crops": ("All crops and trees", "எல்லா பயிர்கள், மரங்கள்"),
    "crop": ("Crop / Tree (type to search)", "பயிர் / மரம் (தட்டச்சு செய்து தேடலாம்)"),
    "count": ("{n} crops and trees available", "{n} பயிர்கள், மரங்கள் உள்ளன"),
    "stage": ("Growth stage", "வளர்ச்சி நிலை"),
    "soil": ("Soil type", "மண் வகை"),
    "irrig": ("Irrigation method", "நீர்ப்பாசன முறை"),
    "acres": ("Field size (acres)", "வயல் அளவு (ஏக்கர்)"),
    "pump": ("Pump flow (litres per hour)", "மோட்டார் நீர் அளவு (லிட்டர்/மணி)"),
    "pick_place": ("Select a location in the left sidebar.", "இடது பக்கம் இடத்தை தேர்வு செய்யுங்கள்."),
    "data_err": (
        "Could not get data. Check your internet and refresh after some time.",
        "தகவல் கிடைக்கவில்லை. இணையத்தை சரிபார்த்து சிறிது நேரம் கழித்து refresh செய்யுங்கள்.",
    ),
    "tab_over": ("🏠 Overview", "🏠 முகப்பு"),
    "tab_irrig": ("💧 Irrigation plan", "💧 நீர்ப்பாசன திட்டம்"),
    "tab_charts": ("📈 Charts", "📈 வரைபடங்கள்"),
    "tab_map": ("🗺️ Map", "🗺️ வரைபடம்"),
    "updated": ("Updated {t}", "புதுப்பிப்பு {t}"),
    # KPI cards
    "soil_moist": ("🌱 Soil moisture (root zone)", "🌱 மண் ஈரம் (வேர் பகுதி)"),
    "temp": ("🌡️ Temperature", "🌡️ வெப்பநிலை"),
    "feels": ("Feels like {v} °C", "உணரும் வெப்பம் {v} °C"),
    "humidity": ("💧 Air humidity", "💧 காற்று ஈரப்பதம்"),
    "rain_chance": ("🌧️ Rain chance today", "🌧️ இன்று மழை வாய்ப்பு"),
    "soil_temp": ("🪱 Soil temperature", "🪱 மண் வெப்பநிலை"),
    "wind": ("🌬️ Wind", "🌬️ காற்று"),
    "uv_l": ("☀️ UV index", "☀️ UV குறியீடு"),
    "et_l": ("💦 Water lost today", "💦 இன்று ஆவியாகும் நீர்"),
    "status_ok": ("Healthy", "நன்றாக உள்ளது"),
    "status_dry": ("Needs water", "நீர் தேவை"),
    "status_rain": ("Rain expected", "மழை வரும்"),
    "limit": ("Irrigation limit: {v}%", "நீர் பாய்ச்ச வேண்டிய எல்லை: {v}%"),
    # advice
    "advice_h": ("What should you do today?", "இன்று என்ன செய்ய வேண்டும்?"),
    "h_water": ("Irrigation", "நீர்ப்பாசனம்"),
    "h_heat": ("Heat", "வெப்பம்"),
    "h_pest": ("Pests and disease", "பூச்சி, நோய்"),
    "h_spray": ("Spraying", "மருந்து தெளித்தல்"),
    "h_uv": ("Sun / UV", "வெயில் / UV"),
    "h_young": ("Young plants", "இளம் செடிகள்"),
    "h_deep": ("Deep roots", "ஆழ வேர்"),
    "h_sandal": ("Sandalwood", "சந்தனம்"),
    "rain_skip": (
        "About {mm} mm of rain is expected in the next 2 days. Do not irrigate now, the rain will be enough.",
        "அடுத்த 2 நாட்களில் சுமார் {mm} மி.மீ மழை வரும். இப்போது நீர் பாய்ச்ச வேண்டாம், மழையே போதும்.",
    ),
    "irrigate": (
        "Soil moisture is {m}%, low for {crop} (needs about {need}% or more). Irrigate now, early morning (6-9 am) or evening (after 5 pm), not in the midday sun.",
        "மண் ஈரம் {m}%, இது {crop} பயிருக்கு குறைவு (சுமார் {need}% அல்லது அதற்கு மேல் வேண்டும்). இப்போதே நீர் பாய்ச்சுங்கள். காலை 6-9 மணி அல்லது மாலை 5 மணிக்கு பிறகு நல்லது, நண்பகல் வெயிலில் வேண்டாம்.",
    ),
    "irrigate_hot": (
        "Soil moisture is {m}%, low for {crop} (needs about {need}% or more), and it is hot today. Irrigate right away, this is urgent!",
        "மண் ஈரம் {m}%, {crop} பயிருக்கு குறைவு (சுமார் {need}% அல்லது அதற்கு மேல் வேண்டும்), இன்று வெயிலும் அதிகம். உடனே நீர் பாய்ச்சுங்கள், இது மிக அவசரம்!",
    ),
    "soil_ok": (
        "Soil moisture is {m}%, enough for {crop}. No irrigation needed now.",
        "மண் ஈரம் {m}%, {crop} பயிருக்கு போதுமானது. இப்போது நீர் பாய்ச்ச தேவையில்லை.",
    ),
    "heat_extreme": (
        "Today's max temperature is {t}°C, far above what {crop} can take. Use mulching (straw or dry leaves), irrigate morning and evening, avoid field work at midday, and use shade net for young plants.",
        "இன்றைய அதிகபட்ச வெப்பம் {t}°C, {crop} தாங்கும் அளவை விட மிக அதிகம். வைக்கோல் / சருகு மூடாக்கு போடுங்கள், காலை மாலை நீர் பாய்ச்சுங்கள், நண்பகலில் வேலை வேண்டாம், இளம் செடிகளுக்கு நிழல் வலை போடுங்கள்.",
    ),
    "heat_high": (
        "Today's max temperature is {t}°C, a little high for {crop}. Irrigate in the evening and mulch the soil.",
        "இன்றைய அதிகபட்ச வெப்பம் {t}°C, {crop} பயிருக்கு சற்று அதிகம். மாலையில் நீர் பாய்ச்சுங்கள், மண்ணை மூடாக்கு போட்டு மூடுங்கள்.",
    ),
    "heat_ok": (
        "Temperature ({t}°C) is fine for {crop}.",
        "வெப்பநிலை ({t}°C) {crop} பயிருக்கு ஏற்றதாக உள்ளது.",
    ),
    "fungal": (
        "High humidity with mild-warm weather: risk of fungal diseases (mildew, blight, rust). Check the leaves and spray a suitable fungicide only if you see symptoms.",
        "அதிக ஈரப்பதம் + மிதமான வெப்பம்: பூஞ்சை நோய்கள் (சாம்பல் நோய், கருகல், துரு) வர வாய்ப்பு. இலைகளை பார்த்து, அறிகுறி தெரிந்தால் மட்டும் தகுந்த பூஞ்சைக்கொல்லி தெளியுங்கள்.",
    ),
    "mites": (
        "Very dry air with heat: risk of mites and sucking pests. Check the underside of leaves.",
        "மிக வறண்ட காற்று + வெப்பம்: சிவப்பு சிலந்திப்பூச்சி, சாறு உறிஞ்சும் பூச்சிகள் வர வாய்ப்பு. இலைகளின் அடிப்பகுதியை பாருங்கள்.",
    ),
    "disease_ok": ("Pest and disease risk looks low right now.", "இப்போது பூச்சி, நோய் அபாயம் குறைவு."),
    "spray_good": (
        "Good day to spray pesticide or fertilizer (low wind, no rain expected).",
        "இன்று மருந்து / உரம் தெளிக்க நல்ல நாள் (காற்று குறைவு, மழை இல்லை).",
    ),
    "spray_bad": (
        "Not a good day for spraying (strong wind or rain likely).",
        "இன்று தெளிக்க வேண்டாம் (காற்று அதிகம் அல்லது மழை வரலாம்).",
    ),
    "uv": (
        "UV index {uv} (very high). Avoid field work between 11 am and 3 pm. Wear a hat and cover your arms.",
        "UV குறியீடு {uv} (மிக அதிகம்). காலை 11 முதல் மாலை 3 மணி வரை வயல் வேலை வேண்டாம். தொப்பி அணிந்து கைகளை மூடிக்கொள்ளுங்கள்.",
    ),
    "young_note": (
        "Keep the soil moist but not waterlogged. Use mulch and shade net in hot weather.",
        "மண்ணை ஈரமாக வைத்திருங்கள், ஆனால் தண்ணீர் தேங்க விடாதீர்கள். வெயிலில் மூடாக்கு, நிழல் வலை பயன்படுத்துங்கள்.",
    ),
    "deep_note": (
        "Trees have deep roots. The soil moisture shown covers only the top 27 cm, so dig and check the deeper soil before deciding.",
        "மரங்களுக்கு வேர் ஆழமாக செல்லும். காட்டப்படும் மண் ஈரம் மேல் 27 செ.மீ மட்டுமே. முடிவெடுக்கும் முன் மண்ணை தோண்டி ஆழத்தில் ஈரம் பாருங்கள்.",
    ),
    "sandal_note": (
        "Too much water rots the roots. Irrigate lightly and only when the soil is really dry.",
        "தண்ணீர் அதிகமானால் வேர் அழுகும். மண் நன்கு காய்ந்த பிறகு மட்டும், குறைவாக நீர் பாய்ச்சுங்கள்.",
    ),
    # irrigation plan
    "water_h": ("7-day irrigation plan", "7 நாள் நீர்ப்பாசன திட்டம்"),
    "need7": ("Crop water need", "பயிர் நீர் தேவை"),
    "rain7": ("Expected rain", "எதிர்பார்க்கும் மழை"),
    "irrig_days": ("Irrigation days", "நீர் பாய்ச்ச வேண்டிய நாட்கள்"),
    "litres": ("Water for {acres} acres", "{acres} ஏக்கருக்கு தண்ணீர்"),
    "pump_h": ("Pump running time", "மோட்டார் ஓட வேண்டிய நேரம்"),
    "hours": ("{h} hours", "{h} மணி"),
    "water_caption": (
        "Rough estimate: crop need = ET0 x crop factor x growth stage factor. 80% of rain is counted, and water lost in your irrigation method is added. 1 mm over 1 acre = 4047 litres.",
        "தோராய கணக்கு: பயிர் தேவை = ET0 x பயிர் காரணி x வளர்ச்சி நிலை காரணி. மழையில் 80% கணக்கில் எடுக்கப்படுகிறது, உங்கள் பாசன முறையில் இழக்கும் நீரும் சேர்க்கப்படுகிறது. 1 ஏக்கருக்கு 1 மி.மீ = 4047 லிட்டர்.",
    ),
    "col_date": ("Day", "நாள்"),
    "col_max": ("Max °C", "அதிகபட்சம் °C"),
    "col_min": ("Min °C", "குறைந்தபட்சம் °C"),
    "col_rain": ("Rain (mm)", "மழை (மி.மீ)"),
    "col_prob": ("Rain chance %", "மழை வாய்ப்பு %"),
    "col_need": ("Crop need (mm)", "பயிர் தேவை (மி.மீ)"),
    "col_action": ("Action", "செய்ய வேண்டியது"),
    "col_litres": ("Water to give (litres)", "தர வேண்டிய நீர் (லிட்டர்)"),
    "act_irrigate": ("💧 Irrigate", "💧 நீர் பாய்ச்சவும்"),
    "act_skip": ("✅ Not needed", "✅ தேவையில்லை"),
    "act_rain": ("🌧️ Rain", "🌧️ மழை"),
    "download": ("⬇️ Download plan (CSV)", "⬇️ திட்டத்தை பதிவிறக்கு (CSV)"),
    "spray_h": ("Best days to spray", "மருந்து தெளிக்க நல்ல நாட்கள்"),
    "spray_days": ("Good days: {d}", "நல்ல நாட்கள்: {d}"),
    "no_spray": (
        "No good spraying day in the next 7 days.",
        "அடுத்த 7 நாட்களில் மருந்து தெளிக்க ஏற்ற நாள் இல்லை.",
    ),
    "litres_chart": ("Water to give per day (litres)", "நாளுக்கு தர வேண்டிய நீர் (லிட்டர்)"),
    # charts
    "c_temp": ("Temperature", "வெப்பநிலை"),
    "max": ("Max", "அதிகபட்சம்"),
    "min": ("Min", "குறைந்தபட்சம்"),
    "c_soil": (
        "Soil moisture (red dashed line = irrigation limit)",
        "மண் ஈரம் (சிவப்பு கோடு = நீர் பாய்ச்ச வேண்டிய எல்லை)",
    ),
    "soil_pct": ("Soil moisture (%)", "மண் ஈரம் (%)"),
    "c_water": ("Water balance: rain vs water lost to air", "நீர் கணக்கு: மழை vs ஆவியாகும் நீர்"),
    "et0": ("Water lost to air (mm)", "ஆவியாகும் நீர் (மி.மீ)"),
    "rain_mm": ("Rain (mm)", "மழை (மி.மீ)"),
    "type": ("Type", "வகை"),
    "date": ("Date", "தேதி"),
    "footer": (
        "Weather: Open-Meteo (model-based, approximate). Satellite: Sentinel-2 L2A via Microsoft Planetary Computer. Crop values are rough averages. Always check your field in person and confirm with your local agriculture office (TNAU).",
        "வானிலை: Open-Meteo (மாதிரி அடிப்படையிலான, தோராயமானது). செயற்கைக்கோள்: Microsoft Planetary Computer வழியாக Sentinel-2 L2A. பயிர் மதிப்புகள் சராசரி தோராய அளவுகள். எப்போதும் உங்கள் வயலை நேரில் பார்த்து, உங்கள் பகுதி வேளாண் அலுவலகம் / TNAU-வில் உறுதி செய்யுங்கள்.",
    ),
}


def t(key, **kw):
    s = TR[key][LANG]
    return s.format(**kw) if kw else s


def L(en, ta):
    """Inline English / Tamil text for the new v2 sections."""
    return ta if LANG == 1 else en


# ================= Options =================
STAGES = {
    "seedling": ("Seedling / young sapling", "நாற்று / இளம் செடி", 0.6),
    "growing": ("Growing", "வளரும் நிலை", 1.0),
    "mature": ("Mature / flowering / fruiting", "முதிர்ந்த / பூ, காய் பருவம்", 1.1),
}

# (English, Tamil, moisture factor, irrigate when this many mm are used up)
SOILS = {
    "red": ("Red soil", "செம்மண்", 0.95, 15),
    "black": ("Black soil (clay)", "கரிசல் மண்", 1.15, 25),
    "sandy": ("Sandy soil", "மணல் மண்", 0.80, 10),
    "loam": ("Loamy / alluvial soil", "வண்டல் / கலப்பு மண்", 1.00, 20),
}

# (English, Tamil, efficiency)
IRRIGS = {
    "flood": ("Flood / channel", "வாய்க்கால் பாசனம்", 0.50),
    "furrow": ("Furrow", "சால் பாசனம்", 0.60),
    "sprinkler": ("Sprinkler", "தெளிப்பு நீர்ப்பாசனம்", 0.75),
    "drip": ("Drip", "சொட்டு நீர்ப்பாசனம்", 0.90),
}

# (English, Tamil, kc, max temp limit C, min soil moisture)  -- rough average values
CROPS = {
    "grains": ("Grains", "தானியங்கள்", [
        ("Paddy", "நெல்", 1.20, 35, 0.35),
        ("Maize", "மக்காச்சோளம்", 1.10, 35, 0.22),
        ("Pearl millet", "கம்பு", 0.80, 38, 0.15),
        ("Sorghum", "சோளம்", 0.90, 38, 0.15),
        ("Finger millet (Ragi)", "கேழ்வரகு", 0.85, 35, 0.18),
        ("Small millets (Thinai, Samai)", "தினை / சாமை", 0.80, 38, 0.15),
        ("Wheat", "கோதுமை", 1.00, 32, 0.22),
    ]),
    "pulses": ("Pulses", "பயறு வகைகள்", [
        ("Pigeon pea", "துவரை", 0.95, 36, 0.18),
        ("Black gram", "உளுந்து", 0.90, 36, 0.20),
        ("Green gram", "பாசிப்பயறு", 0.90, 36, 0.20),
        ("Chickpea", "கொண்டைக்கடலை", 0.90, 33, 0.18),
        ("Horse gram", "கொள்ளு", 0.80, 38, 0.15),
        ("Field bean (Avarai, Mochai)", "அவரை / மொச்சை", 0.90, 34, 0.20),
        ("Cowpea", "தட்டைப்பயறு", 0.95, 36, 0.20),
    ]),
    "oilseeds": ("Oilseeds", "எண்ணெய் வித்துக்கள்", [
        ("Groundnut", "நிலக்கடலை", 0.90, 35, 0.18),
        ("Sesame", "எள்", 0.80, 37, 0.15),
        ("Sunflower", "சூரியகாந்தி", 0.95, 36, 0.20),
        ("Castor", "ஆமணக்கு", 0.90, 38, 0.15),
        ("Soybean", "சோயா", 1.00, 35, 0.20),
        ("Mustard", "கடுகு", 0.90, 32, 0.20),
    ]),
    "cash": ("Cash crops", "பணப் பயிர்கள்", [
        ("Cotton", "பருத்தி", 1.00, 36, 0.20),
        ("Sugarcane", "கரும்பு", 1.15, 38, 0.28),
        ("Tobacco", "புகையிலை", 0.95, 35, 0.22),
        ("Turmeric", "மஞ்சள்", 1.05, 35, 0.28),
        ("Ginger", "இஞ்சி", 1.00, 32, 0.28),
        ("Jute", "சணல்", 1.00, 36, 0.25),
    ]),
    "veg": ("Vegetables", "காய்கறிகள்", [
        ("Tomato", "தக்காளி", 1.05, 33, 0.25),
        ("Chilli", "மிளகாய்", 0.95, 34, 0.22),
        ("Brinjal", "கத்தரிக்காய்", 1.00, 34, 0.25),
        ("Okra (Ladies finger)", "வெண்டைக்காய்", 1.00, 36, 0.25),
        ("Onion", "வெங்காயம்", 0.95, 32, 0.22),
        ("Garlic", "பூண்டு", 0.90, 30, 0.22),
        ("Potato", "உருளைக்கிழங்கு", 0.95, 30, 0.25),
        ("Sweet potato", "சர்க்கரைவள்ளிக்கிழங்கு", 0.95, 35, 0.22),
        ("Cabbage", "முட்டைக்கோஸ்", 0.95, 28, 0.25),
        ("Cauliflower", "காலிஃபிளவர்", 0.95, 28, 0.25),
        ("Carrot", "கேரட்", 0.90, 30, 0.22),
        ("Beetroot", "பீட்ரூட்", 0.90, 30, 0.22),
        ("Radish", "முள்ளங்கி", 0.90, 30, 0.22),
        ("French beans", "பீன்ஸ்", 0.95, 32, 0.22),
        ("Broad beans", "அவரைக்காய்", 0.95, 33, 0.22),
        ("Cluster beans", "கொத்தவரங்காய்", 0.90, 36, 0.18),
        ("Drumstick", "முருங்கை", 0.80, 38, 0.15),
        ("Bitter gourd", "பாகற்காய்", 0.95, 35, 0.25),
        ("Bottle gourd", "சுரைக்காய்", 0.95, 35, 0.25),
        ("Snake gourd", "புடலங்காய்", 0.95, 35, 0.25),
        ("Ridge gourd", "பீர்க்கங்காய்", 0.95, 35, 0.25),
        ("Ash gourd", "வெண்பூசணி", 0.95, 35, 0.22),
        ("Cucumber", "வெள்ளரி", 1.00, 34, 0.25),
        ("Pumpkin", "பூசணிக்காய்", 0.95, 35, 0.22),
        ("Capsicum", "குடைமிளகாய்", 1.00, 30, 0.25),
        ("Leafy greens", "கீரை வகைகள்", 0.90, 35, 0.28),
        ("Coriander", "கொத்தமல்லி", 0.90, 30, 0.25),
        ("Mint", "புதினா", 1.00, 32, 0.28),
        ("Tubers (Yam, Colocasia)", "கிழங்கு வகைகள் (சேனை, சேப்பங்கிழங்கு)", 0.95, 35, 0.25),
    ]),
    "fruit": ("Fruits", "பழ வகைகள்", [
        ("Banana", "வாழை", 1.10, 36, 0.28),
        ("Mango", "மா", 0.90, 40, 0.18),
        ("Guava", "கொய்யா", 0.90, 38, 0.18),
        ("Sapota (Chikoo)", "சப்போட்டா", 0.85, 38, 0.20),
        ("Lemon", "எலுமிச்சை", 0.90, 38, 0.20),
        ("Orange / Sweet orange", "ஆரஞ்சு / சாத்துக்குடி", 0.90, 36, 0.22),
        ("Papaya", "பப்பாளி", 1.05, 36, 0.25),
        ("Pomegranate", "மாதுளை", 0.85, 38, 0.18),
        ("Grapes", "திராட்சை", 0.80, 38, 0.20),
        ("Jackfruit", "பலா", 0.90, 38, 0.20),
        ("Custard apple", "சீதாப்பழம்", 0.80, 38, 0.15),
        ("Amla (Gooseberry)", "நெல்லிக்காய்", 0.80, 40, 0.15),
        ("Pineapple", "அன்னாசி", 0.50, 35, 0.20),
        ("Watermelon", "தர்பூசணி", 1.00, 36, 0.20),
        ("Muskmelon", "முலாம்பழம்", 0.95, 35, 0.20),
        ("Dragon fruit", "டிராகன் பழம்", 0.60, 38, 0.15),
        ("Avocado", "அவகாடோ (வெண்ணெய் பழம்)", 0.85, 34, 0.25),
        ("Jujube (Ber)", "இலந்தை", 0.80, 40, 0.15),
        ("Fig", "அத்தி", 0.80, 38, 0.18),
        ("Wood apple", "விளாம்பழம்", 0.80, 40, 0.12),
    ]),
    "plantation": ("Plantation crops", "தோட்டப் பயிர்கள்", [
        ("Coconut", "தென்னை", 1.00, 38, 0.22),
        ("Arecanut", "பாக்கு", 1.05, 36, 0.28),
        ("Cashew", "முந்திரி", 0.80, 40, 0.15),
        ("Pepper", "மிளகு", 1.00, 35, 0.28),
        ("Cardamom", "ஏலக்காய்", 1.05, 32, 0.30),
        ("Coffee", "காபி", 1.00, 30, 0.25),
        ("Tea", "தேயிலை", 1.00, 30, 0.30),
        ("Rubber", "ரப்பர்", 1.00, 36, 0.28),
        ("Oil palm", "எண்ணெய்ப் பனை", 1.10, 38, 0.28),
        ("Betel vine", "வெற்றிலை", 1.00, 35, 0.30),
        ("Cocoa", "கோகோ", 1.00, 34, 0.28),
        ("Palmyra palm", "பனை", 0.70, 42, 0.10),
    ]),
    "trees": ("Timber trees", "மர வகைகள்", [
        ("Sandalwood", "சந்தனம்", 0.70, 40, 0.12),
        ("Teak", "தேக்கு", 0.80, 40, 0.15),
        ("Neem", "வேம்பு", 0.70, 42, 0.10),
        ("Mahogany", "மகோகனி", 0.80, 38, 0.18),
        ("Eucalyptus", "தைலமரம்", 0.90, 40, 0.15),
        ("Casuarina", "சவுக்கு", 0.90, 40, 0.15),
        ("Bamboo", "மூங்கில்", 1.00, 38, 0.22),
        ("Melia dubia", "மலைவேம்பு", 0.80, 40, 0.12),
        ("Rosewood", "ஈட்டி", 0.75, 38, 0.15),
        ("Pongamia", "புங்கன்", 0.70, 40, 0.12),
        ("Kino tree (Vengai)", "வேங்கை", 0.75, 40, 0.12),
        ("Tamarind", "புளிய மரம்", 0.75, 42, 0.12),
        ("Silver oak", "சில்வர் ஓக்", 0.80, 38, 0.15),
        ("Banyan / Peepal", "ஆல் / அரசு", 0.80, 40, 0.15),
        ("Agathi (Sesbania)", "அகத்தி", 0.85, 38, 0.20),
    ]),
    "flowers": ("Flowers", "பூ வகைகள்", [
        ("Jasmine", "மல்லிகை", 0.95, 36, 0.22),
        ("Rose", "ரோஜா", 1.00, 32, 0.25),
        ("Chrysanthemum (Samanthi)", "சாமந்தி", 0.95, 30, 0.25),
        ("Marigold", "செண்டுமல்லி", 0.95, 34, 0.22),
        ("Crossandra (Kanakambaram)", "கனகாம்பரம்", 0.90, 36, 0.22),
        ("Tuberose (Sampangi)", "சம்பங்கி", 0.95, 34, 0.22),
        ("Oleander (Arali)", "அரளி", 0.85, 38, 0.18),
        ("Hibiscus", "செம்பருத்தி", 0.90, 36, 0.22),
    ]),
    "fodder": ("Fodder & medicinal", "தீவனம் & மூலிகை", [
        ("Napier grass", "நேப்பியர் புல்", 1.00, 38, 0.22),
        ("Subabul", "சுபாபுல்", 0.85, 38, 0.18),
        ("Aloe vera", "கற்றாழை", 0.50, 40, 0.10),
        ("Nilavembu (Andrographis)", "நிலவேம்பு", 0.85, 36, 0.22),
        ("Ashwagandha", "அஸ்வகந்தா", 0.80, 36, 0.15),
        ("Tulsi (Holy basil)", "துளசி", 0.85, 36, 0.22),
        ("Senna (Nilavarai)", "நிலவாரை", 0.80, 38, 0.15),
        ("Lemongrass", "எலுமிச்சைப் புல்", 0.90, 36, 0.20),
    ]),
}
DEEP_ROOT_GROUPS = {"fruit", "plantation", "trees"}
TA_WD = ["திங்", "செவ்", "புத", "வியா", "வெள்", "சனி", "ஞாயி"]


def pick(item):
    return item[LANG]


def crop_label(c):
    return f"{c[0]} ({c[1]})" if LANG == 0 else f"{c[1]} ({c[0]})"


def day_label(d):
    wd = d.strftime("%a") if LANG == 0 else TA_WD[d.weekday()]
    return f"{wd} {d.day}/{d.month}"


# ================= Look and feel (CSS + small HTML helpers) =================
st.markdown(
    """
<style>
.stApp { background:#F3F6F4; }
[data-testid="stSidebar"] { background:#FFFFFF; border-right:1px solid #E3EAE5; }
header[data-testid="stHeader"] { background:transparent; }
.block-container { padding-top:1.2rem; padding-bottom:2rem; max-width:1400px; }
.brand { display:flex; align-items:center; gap:10px; font-weight:800; font-size:1.2rem; color:#14532D; margin:0 0 .6rem 0; }
.brand .logo { background:#16A34A; color:#fff; border-radius:12px; padding:5px 9px; font-size:1.1rem; }
.page-title { font-size:1.9rem; font-weight:800; color:#0F2A1D; line-height:1.2; }
.page-sub { color:#5F6F66; font-size:.95rem; margin-top:2px; }
.pill { display:inline-block; background:#E7F6EC; color:#166534; border-radius:999px; padding:5px 12px; font-size:.8rem; font-weight:700; }
.card { background:#fff; border-radius:18px; padding:16px 18px; border:1px solid #E8EEEA; box-shadow:0 1px 3px rgba(16,24,40,.05); min-height:118px; }
.card .lbl { color:#5F6F66; font-size:.82rem; font-weight:600; }
.card .val { font-size:1.9rem; font-weight:800; color:#0F2A1D; line-height:1.25; margin-top:4px; }
.card .sub { color:#5F6F66; font-size:.8rem; margin-top:4px; }
.card.hero { background:linear-gradient(135deg,#14532D 0%,#22A559 100%); border:none; }
.card.hero .lbl, .card.hero .sub { color:#D1FAE5; }
.card.hero .val { color:#fff; }
.sec { font-size:1.1rem; font-weight:800; color:#0F2A1D; margin:1.1rem 0 .6rem 0; }
.tile { background:#fff; border-radius:14px; padding:12px 16px; margin-bottom:10px; border:1px solid #E8EEEA; border-left:6px solid #16A34A; color:#1F2937; font-size:.93rem; }
.tile .th { font-weight:800; color:#0F2A1D; margin-bottom:2px; }
.tile.warn { border-left-color:#F59E0B; }
.tile.bad { border-left-color:#DC2626; }
.tile.info { border-left-color:#3B82F6; }
div[data-testid="stVerticalBlockBorderWrapper"] { border-radius:18px; background:#fff; }
</style>
""",
    unsafe_allow_html=True,
)



st.markdown(
    """
<style>
/* ===== Hyperclimate v2 professional theme ===== */
html, body, [class*="css"] { font-family: "Inter","Segoe UI",system-ui,sans-serif; }
.stApp { background: radial-gradient(1200px 500px at 85% -10%, #DDF3E4 0%, rgba(243,246,244,0) 60%), #F3F6F4; }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#FFFFFF 0%,#F2FAF5 100%); border-right:1px solid #DCE9E1; }
[data-testid="stSidebar"] .block-container { padding-top: .6rem; }

/* sidebar brand + summary */
.sb-brand { display:flex; align-items:center; gap:12px; padding:14px 14px; border-radius:18px; color:#fff; margin:2px 0 14px 0;
  background: linear-gradient(135deg,#0B3D26 0%,#14683F 60%,#2FA362 100%); box-shadow:0 6px 16px rgba(20,83,45,.22); }
.sb-brand .sb-logo { font-size:1.7rem; background:rgba(255,255,255,.16); border-radius:14px; padding:6px 10px; }
.sb-brand .sb-name { font-weight:800; font-size:1.15rem; letter-spacing:-.3px; line-height:1.1; }
.sb-brand .sb-tag { font-size:.72rem; opacity:.85; margin-top:2px; }
.sb-sum { border:1px solid #DCE9E1; background:#fff; border-radius:16px; padding:12px 14px; margin:10px 0; box-shadow:0 1px 3px rgba(16,24,40,.05); }
.sb-sum .sb-h { font-weight:800; font-size:.9rem; color:#0F2A1D; margin-bottom:6px; }
.sb-sum .sb-r { display:flex; justify-content:space-between; font-size:.8rem; color:#4B5B52; padding:3px 0; border-bottom:1px dashed #E6EEE9; }
.sb-sum .sb-r:last-child { border-bottom:none; }
.sb-sum .sb-r b { color:#0F2A1D; text-align:right; }
.sb-src { display:flex; flex-wrap:wrap; gap:5px; margin-top:8px; }
.sb-src span { font-size:.66rem; font-weight:700; background:#E7F6EC; color:#166534; border-radius:999px; padding:3px 8px; }

/* hero */
.hero2 { position:relative; overflow:hidden; border-radius:26px; padding:26px 30px; color:#fff; margin-bottom:16px;
  background: linear-gradient(120deg,#0B3D26 0%,#14683F 55%,#2FA362 100%); box-shadow:0 10px 28px rgba(20,83,45,.25); }
.hero2::after { content:""; position:absolute; inset:0; pointer-events:none; opacity:1;
  background-image:url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cg fill='none' stroke='white' stroke-opacity='.09' stroke-width='1.3'%3E%3Ccircle cx='90' cy='90' r='30'/%3E%3Ccircle cx='90' cy='90' r='58'/%3E%3Ccircle cx='90' cy='90' r='88'/%3E%3C/g%3E%3C/svg%3E"); }
.hero2-top { position:relative; z-index:1; display:flex; justify-content:space-between; align-items:flex-start; gap:12px; flex-wrap:wrap; }
.hero2-title { font-size:2.1rem; font-weight:800; letter-spacing:-.8px; line-height:1.1; }
.hero2-sub { font-size:.95rem; opacity:.88; margin-top:5px; }
.hero2-pill { background:rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.3); border-radius:999px; padding:6px 13px; font-size:.76rem; font-weight:800; letter-spacing:.4px; }
.hero2-pill i { display:inline-block; width:8px; height:8px; border-radius:50%; background:#4ADE80; margin-right:6px; box-shadow:0 0 0 4px rgba(74,222,128,.25); }
.hero2-chips { position:relative; z-index:1; display:flex; flex-wrap:wrap; gap:8px; margin-top:16px; }
.hero2-chips span { background:rgba(255,255,255,.14); border:1px solid rgba(255,255,255,.22); border-radius:999px; padding:5px 12px; font-size:.8rem; font-weight:600; }

/* tabs */
.stTabs [data-baseweb="tab-list"] { gap:6px; background:#fff; padding:6px; border-radius:16px; border:1px solid #E1ECE5; overflow-x:auto; }
.stTabs [data-baseweb="tab"] { border-radius:11px; padding:9px 15px; height:auto; font-weight:700; color:#41524A; white-space:nowrap; }
.stTabs [aria-selected="true"] { background:#E1F5E8; color:#14532D; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display:none; }

/* native metrics become cards */
[data-testid="stMetric"] { background:#fff; border:1px solid #E6EEE9; border-radius:16px; padding:14px 16px; box-shadow:0 1px 3px rgba(16,24,40,.05); }
[data-testid="stMetricLabel"] p { color:#5F6F66; font-weight:600; font-size:.82rem; }
[data-testid="stMetricValue"] { color:#0F2A1D; font-weight:800; }

/* insight cards */
.ins-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:12px; margin:8px 0 14px; }
.ins { display:flex; gap:12px; background:#fff; border:1px solid #E6EEE9; border-left:6px solid #16A34A; border-radius:16px; padding:14px 15px; box-shadow:0 1px 3px rgba(16,24,40,.05); }
.ins.warn { border-left-color:#F59E0B; } .ins.bad { border-left-color:#DC2626; } .ins.info { border-left-color:#3B82F6; }
.ins-ic { font-size:1.8rem; line-height:1; }
.ins-t { font-size:.76rem; color:#5F6F66; font-weight:700; text-transform:uppercase; letter-spacing:.4px; }
.ins-v { font-size:1.2rem; font-weight:800; color:#0F2A1D; margin:2px 0; }
.ins-n { font-size:.78rem; color:#5F6F66; line-height:1.35; }

/* 7-day strip */
.wx-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(112px,1fr)); gap:10px; margin:6px 0 14px; }
.wx { background:#fff; border:1px solid #E6EEE9; border-radius:16px; padding:11px 8px; text-align:center; box-shadow:0 1px 3px rgba(16,24,40,.05); }
.wx-d { font-size:.76rem; font-weight:800; color:#41524A; } .wx-i { font-size:1.9rem; margin:3px 0; }
.wx-t { font-weight:800; color:#0F2A1D; font-size:.92rem; } .wx-r { font-size:.74rem; color:#5F6F66; margin-top:2px; }
.wx-b { margin-top:6px; font-size:.7rem; font-weight:800; border-radius:999px; padding:3px 6px; background:#EEF6F1; color:#166534; }
.wx-b.irr { background:#DBEAFE; color:#1D4ED8; } .wx-b.rain { background:#E0E7FF; color:#4338CA; }

/* chips + landing */
.chip-row { display:flex; flex-wrap:wrap; gap:8px; margin:4px 0 12px; }
.chip { background:#E7F6EC; color:#166534; border:1px solid #CFE9D8; border-radius:999px; padding:4px 11px; font-size:.78rem; font-weight:700; }
.feat-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:14px; margin:14px 0; }
.feat { background:#fff; border:1px solid #E6EEE9; border-radius:20px; padding:18px; box-shadow:0 2px 6px rgba(16,24,40,.05); }
.feat .f-ic { font-size:2rem; } .feat .f-t { font-weight:800; color:#0F2A1D; margin-top:6px; } .feat .f-d { font-size:.85rem; color:#5F6F66; margin-top:4px; line-height:1.4; }
.step-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:12px; margin-top:6px; }
.step { background:#F0FAF4; border:1px dashed #A7D9B8; border-radius:16px; padding:14px; font-size:.88rem; color:#14532D; font-weight:600; }
.step b { display:inline-block; background:#16A34A; color:#fff; border-radius:50%; width:24px; height:24px; text-align:center; line-height:24px; margin-right:8px; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<style>
/* ===== Hyperclimate v3: dark glass + bento theme (reference: Dribbble climate / agri dashboards) ===== */
:root { --glass:rgba(255,255,255,.055); --line:rgba(255,255,255,.10); --tx:#E8F5EE; --mut:#93AA9D; --acc:#34D399; }
.stApp { background: radial-gradient(900px 520px at 92% -8%, rgba(52,211,153,.20), transparent 60%),
                     radial-gradient(700px 500px at -8% 35%, rgba(163,230,53,.09), transparent 60%), #07110D !important; color: var(--tx); }
header[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#0B1A14 0%,#08130F 100%) !important; border-right:1px solid var(--line) !important; }
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li, .stApp label, .stApp label p { color: var(--tx); }
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 { color:#F1FBF5 !important; letter-spacing:-.4px; }
[data-testid="stCaptionContainer"], .stApp small { color: var(--mut) !important; }
hr { border-color: var(--line) !important; }

/* inputs */
[data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-baseweb="textarea"], .stNumberInput input, .stTextInput input, textarea {
  background: rgba(255,255,255,.06) !important; color: var(--tx) !important; border-color: var(--line) !important; border-radius: 12px !important; }
[data-baseweb="select"] span, [data-baseweb="select"] div { color: var(--tx); }
ul[role="listbox"], [data-baseweb="popover"] > div { background:#10201A !important; }
li[role="option"] { color: var(--tx) !important; }
.stButton > button, .stDownloadButton > button, [data-testid="stLinkButton"] a, [data-testid="stFormSubmitButton"] button {
  background: rgba(52,211,153,.12) !important; color:#D1FAE5 !important; border:1px solid rgba(52,211,153,.35) !important; border-radius:12px !important; font-weight:700; }
.stButton > button:hover, [data-testid="stLinkButton"] a:hover { background: rgba(52,211,153,.24) !important; }
.stButton > button[kind="primary"] { background: linear-gradient(135deg,#10B981,#34D399) !important; color:#052E1B !important; border:none !important; font-weight:800; }
[data-testid="stExpander"] { background: var(--glass); border:1px solid var(--line); border-radius:16px; }
[data-testid="stAlert"] { background: rgba(255,255,255,.06) !important; border:1px solid var(--line); border-radius:14px; }
[data-testid="stAlert"] p { color: var(--tx) !important; }
[data-testid="stDataFrame"] { border-radius:14px; overflow:hidden; border:1px solid var(--line); }

/* glass cards / bento */
div[data-testid="stVerticalBlockBorderWrapper"] { background: var(--glass) !important; border:1px solid var(--line) !important; border-radius:22px !important; backdrop-filter: blur(14px); }
[data-testid="stMetric"] { background: var(--glass); border:1px solid var(--line); box-shadow:none; backdrop-filter: blur(14px); }
[data-testid="stMetricLabel"] p { color: var(--mut) !important; }
[data-testid="stMetricValue"] { color:#F1FBF5 !important; }
.card { position:relative; overflow:hidden; background: var(--glass); border:1px solid var(--line); box-shadow:none; backdrop-filter: blur(14px); }
.card .lbl, .card .sub { color: var(--mut); } .card .val { color:#F1FBF5; }
.card.hero { background: linear-gradient(135deg,#0F766E 0%,#10B981 58%,#A3E635 100%); border:none; }
.card.hero .val { color:#04210F; } .card.hero .lbl, .card.hero .sub { color: rgba(4,33,15,.75); }
.card .spark { position:absolute; right:12px; bottom:10px; opacity:.95; }
.sec { color:#F1FBF5; }
.tile { background: var(--glass); border:1px solid var(--line); border-left:6px solid #34D399; color:#CFE3D8; }
.tile .th { color:#F1FBF5; } .tile.warn { border-left-color:#F59E0B; } .tile.bad { border-left-color:#EF4444; } .tile.info { border-left-color:#38BDF8; }
.ins, .wx, .feat, .sb-sum { background: var(--glass); border-color: var(--line); box-shadow:none; backdrop-filter: blur(14px); }
.ins-t, .ins-n, .wx-d, .wx-r, .feat .f-d, .sb-sum .sb-r { color: var(--mut); }
.ins-v, .wx-t, .feat .f-t, .sb-sum .sb-h, .sb-sum .sb-r b { color:#F1FBF5; }
.sb-sum .sb-r { border-bottom-color: rgba(255,255,255,.08); }
.wx-b { background: rgba(52,211,153,.14); color:#86EFAC; } .wx-b.irr { background: rgba(56,189,248,.18); color:#7DD3FC; } .wx-b.rain { background: rgba(129,140,248,.2); color:#C7D2FE; }
.chip, .sb-src span { background: rgba(52,211,153,.12); color:#86EFAC; border-color: rgba(52,211,153,.30); }
.step { background: rgba(52,211,153,.07); border-color: rgba(52,211,153,.35); color:#BBF7D0; }
.loc-card { background: var(--glass); border-color: var(--line); }
.stTabs [data-baseweb="tab-list"] { background: var(--glass); border-color: var(--line); backdrop-filter: blur(14px); }
.stTabs [data-baseweb="tab"] { color: var(--mut); }
.stTabs [aria-selected="true"] { background: rgba(52,211,153,.18); color:#A7F3D0; }
.hero2 { background: linear-gradient(120deg,#052E1B 0%,#0F6B45 55%,#22A06B 100%); border:1px solid rgba(255,255,255,.12); }

/* satellite bento tile */
.bsat { position:relative; border-radius:24px; overflow:hidden; min-height:340px; background-size:cover; background-position:center; border:1px solid var(--line); box-shadow:0 14px 34px rgba(0,0,0,.45); }
.bsat::before { content:""; position:absolute; inset:0; background: linear-gradient(180deg, rgba(0,0,0,.40), transparent 35%, rgba(0,0,0,.78)); }
.bsat-top { position:absolute; top:14px; left:14px; right:14px; display:flex; justify-content:space-between; gap:8px; z-index:1; flex-wrap:wrap; }
.bsat-pill { background: rgba(7,17,13,.62); backdrop-filter: blur(8px); border:1px solid rgba(255,255,255,.2); border-radius:999px; padding:5px 11px; font-size:.74rem; font-weight:700; color:#E8F5EE; }
.bsat-bot { position:absolute; left:16px; right:16px; bottom:14px; z-index:1; display:flex; justify-content:space-between; align-items:flex-end; gap:10px; flex-wrap:wrap; }
.bsat-place { font-weight:800; font-size:1.15rem; color:#fff; } .bsat-sub { font-size:.78rem; color:#C9DDD1; }
.bsat-stats { display:flex; gap:8px; flex-wrap:wrap; }
.bsat-stat { background: rgba(7,17,13,.64); backdrop-filter: blur(8px); border:1px solid rgba(255,255,255,.18); border-radius:14px; padding:7px 12px; text-align:center; }
.bsat-stat b { display:block; font-size:1.05rem; color:#A7F3D0; } .bsat-stat span { font-size:.66rem; color:#C9DDD1; }
.flood-badge { display:inline-block; padding:6px 14px; border-radius:999px; font-weight:800; font-size:.85rem; }
.flood-badge.ok { background:rgba(34,197,94,.18); color:#86EFAC; } .flood-badge.warn { background:rgba(245,158,11,.2); color:#FCD34D; } .flood-badge.bad { background:rgba(239,68,68,.22); color:#FCA5A5; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<style>
/* ===== Hyperclimate v5: reference-driven redesign (Cedarstone / TreeForge / Geoweather dark-green dashboards) ===== */
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
:root { --ink:#06100B; --panel:#0C1A13; --panel2:#11241A; --line:rgba(255,255,255,.085); --tx:#EAF6EF; --mut:#8FA89A;
        --mint:#34D399; --lime:#A3E635; --amber:#F59E0B; --sky:#38BDF8; --glass:rgba(255,255,255,.045); }
html, body, [class*="css"], .stApp { font-family: "Inter","Segoe UI",system-ui,sans-serif; }
.stApp { background: radial-gradient(1000px 560px at 88% -12%, rgba(52,211,153,.17), transparent 62%),
                     radial-gradient(800px 520px at -10% 40%, rgba(163,230,53,.06), transparent 60%), var(--ink) !important; }
.block-container { max-width: 1480px; padding-top: 1rem; }
.stApp h1, .stApp h2, .stApp h3 { font-family: "Sora","Inter",sans-serif; font-weight: 700; letter-spacing: -.5px; }
.stApp h2 { font-size: 1.45rem; }

/* top bar */
.topbar { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; flex-wrap:wrap; margin:2px 0 16px; }
.tb-hello { font-family:"Sora",sans-serif; font-size:2rem; font-weight:700; letter-spacing:-.9px; line-height:1.12; color:#F1FBF5; }
.tb-sub { color:var(--mut); font-size:.92rem; margin-top:6px; }
.tb-right { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.tb-live { display:inline-flex; align-items:center; gap:8px; padding:8px 14px; border-radius:999px; background:var(--glass); border:1px solid var(--line); font-size:.78rem; font-weight:700; color:#BBF7D0; }
.tb-live i { width:8px; height:8px; border-radius:50%; background:#4ADE80; box-shadow:0 0 0 4px rgba(74,222,128,.22); }
.tb-date { padding:8px 14px; border-radius:999px; background:var(--glass); border:1px solid var(--line); font-size:.78rem; color:var(--mut); }
.tb-chips { display:flex; flex-wrap:wrap; gap:8px; width:100%; }
.tb-chips span { background:var(--glass); border:1px solid var(--line); border-radius:999px; padding:6px 13px; font-size:.8rem; font-weight:600; color:#CFE3D8; }

/* pill navigation (tabs) */
.stTabs [data-baseweb="tab-list"] { background: var(--panel); border:1px solid var(--line); border-radius:999px; padding:6px; gap:4px; }
.stTabs [data-baseweb="tab"] { border-radius:999px; padding:9px 16px; font-weight:600; font-size:.9rem; color:var(--mut); }
.stTabs [data-baseweb="tab"]:hover { color:#EAF6EF; }
.stTabs [aria-selected="true"] { background:#EAF6EF !important; color:#06241A !important; font-weight:700; }
.stTabs [aria-selected="true"] p { color:#06241A !important; }

/* story cards (Cedarstone-style) */
.stories { display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:14px; margin:8px 0 16px; }
.story { position:relative; overflow:hidden; border-radius:22px; padding:18px 20px 16px; min-height:182px; border:1px solid var(--line);
         display:flex; flex-direction:column; justify-content:space-between; box-shadow:0 14px 30px rgba(0,0,0,.35); }
.story.a { background:linear-gradient(150deg,#0F4230 0%,#0A2A1E 55%,#08150F 100%); }
.story.b { background:linear-gradient(150deg,#46350F 0%,#271E0A 55%,#0F0B05 100%); }
.story.c { background:linear-gradient(150deg,#0D3A49 0%,#0A2331 55%,#07121A 100%); }
.story .topo { position:absolute; inset:0; width:100%; height:100%; pointer-events:none; }
.story > div { position:relative; z-index:1; }
.st-top { display:flex; justify-content:space-between; align-items:center; gap:8px; }
.st-name { font-size:.9rem; font-weight:600; color:#CFE3D8; }
.st-arrow { width:28px; height:28px; border-radius:50%; background:rgba(255,255,255,.10); display:flex; align-items:center; justify-content:center; font-size:.9rem; }
.st-val { font-family:"Sora",sans-serif; font-size:2.5rem; font-weight:700; letter-spacing:-1.4px; color:#fff; line-height:1.05; margin-top:14px; }
.st-val small { font-size:1.1rem; font-weight:600; color:#BFD8CA; letter-spacing:0; margin-left:3px; }
.st-foot { display:flex; justify-content:space-between; align-items:flex-end; gap:8px; margin-top:12px; font-size:.78rem; color:#C3D8CC; }
.st-chip { padding:4px 10px; border-radius:999px; font-weight:700; font-size:.72rem; background:rgba(52,211,153,.18); color:#A7F3D0; border:1px solid rgba(52,211,153,.35); white-space:nowrap; }
.st-chip.warn { background:rgba(245,158,11,.18); color:#FCD34D; border-color:rgba(245,158,11,.4); }
.st-chip.bad { background:rgba(239,68,68,.2); color:#FCA5A5; border-color:rgba(239,68,68,.4); }
.st-chip.info { background:rgba(56,189,248,.18); color:#7DD3FC; border-color:rgba(56,189,248,.4); }

/* big-number panel + alert list */
.panel { border-radius:22px; border:1px solid var(--line); background:linear-gradient(180deg,rgba(255,255,255,.05),rgba(255,255,255,.02)); padding:16px 18px; }
.pn-label { font-size:.85rem; color:var(--mut); font-weight:600; }
.pn-big { font-family:"Sora",sans-serif; font-size:2.6rem; font-weight:700; letter-spacing:-1.5px; color:#F1FBF5; line-height:1.1; }
.pn-delta { display:inline-block; margin-left:10px; padding:3px 10px; border-radius:8px; font-size:.78rem; font-weight:700; vertical-align:middle; background:rgba(52,211,153,.16); color:#86EFAC; }
.pn-delta.dn { background:rgba(245,158,11,.16); color:#FCD34D; }
.alist { display:flex; flex-direction:column; gap:9px; margin-top:10px; }
.al-row { display:flex; align-items:center; gap:12px; padding:10px 12px; border-radius:14px; background:rgba(255,255,255,.04); border:1px solid var(--line); }
.al-dot { width:10px; height:10px; border-radius:50%; background:#34D399; flex:none; box-shadow:0 0 0 4px rgba(52,211,153,.16); }
.al-dot.on { background:#F59E0B; box-shadow:0 0 0 4px rgba(245,158,11,.2); }
.al-t { font-weight:600; font-size:.88rem; color:#EAF6EF; } .al-v { font-size:.76rem; color:var(--mut); }
.al-s { margin-left:auto; font-size:.7rem; font-weight:700; padding:3px 9px; border-radius:999px; background:rgba(52,211,153,.14); color:#86EFAC; white-space:nowrap; }
.al-s.on { background:rgba(245,158,11,.16); color:#FCD34D; }

/* refined existing components */
.card { border-radius:20px; min-height:112px; }
.card .val { font-family:"Sora",sans-serif; letter-spacing:-.8px; }
.card.hero { background: linear-gradient(140deg,#0E7A5A 0%,#1FB67A 60%,#A3E635 130%); }
.ins, .wx, .feat, .tile { border-radius:18px; }
.stButton > button[kind="primary"] { background: linear-gradient(135deg,#F59E0B,#FBBF24) !important; color:#2A1800 !important; border:none !important; font-weight:800; }
.stButton > button[kind="primary"]:hover { filter:brightness(1.07); }
.sec { font-family:"Sora",sans-serif; font-size:1.08rem; letter-spacing:-.3px; }
@media (max-width: 640px) { .tb-hello { font-size:1.5rem; } .st-val { font-size:2.1rem; } }
@media (prefers-reduced-motion: reduce) { * { transition:none !important; animation:none !important; } }
</style>
""",
    unsafe_allow_html=True,
)


def topo_svg(seed=1, w=340, h=170, color="#A7F3D0"):
    """Decorative topographic contour lines (Cedarstone-style card art) - pure SVG, no network."""
    import random
    rnd = random.Random(seed)
    cx, cy = w * rnd.uniform(.6, .88), h * rnd.uniform(.2, .55)
    ph = [rnd.uniform(0, 6.28) for _ in range(3)]
    paths = []
    for k in range(1, 12):
        r = 8 + k * 12
        pts = []
        for i in range(73):
            th = i / 72 * 2 * math.pi
            rr = r * (1 + .10 * math.sin(3 * th + ph[0]) + .06 * math.sin(5 * th + ph[1]) + .03 * math.sin(2 * th + ph[2]))
            pts.append(f"{cx + rr * 1.55 * math.cos(th):.1f},{cy + rr * math.sin(th):.1f}")
        paths.append(f'<polyline points="{" ".join(pts)}"/>')
    return (f'<svg class="topo" viewBox="0 0 {w} {h}" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">'
            f'<g fill="none" stroke="{color}" stroke-opacity=".17" stroke-width="1.1">{"".join(paths)}</g></svg>')


def story_card(cls, seed, name, icon, value, unit, chip, chip_cls, left, topo_color="#A7F3D0"):
    return (f'<div class="story {cls}">{topo_svg(seed, color=topo_color)}'
            f'<div class="st-top"><span class="st-name">{esc(name)}</span><span class="st-arrow">{icon}</span></div>'
            f'<div><div class="st-val">{esc(value)}<small>{esc(unit)}</small></div>'
            f'<div class="st-foot"><span>{esc(left)}</span><span class="st-chip {chip_cls}">{esc(chip)}</span></div></div></div>')


def greeting_text(name=""):
    h = datetime.now().hour
    if LANG == 1:
        g = "காலை வணக்கம்" if h < 12 else ("மதிய வணக்கம்" if h < 16 else ("மாலை வணக்கம்" if h < 20 else "இரவு வணக்கம்"))
    else:
        g = "Good morning" if h < 12 else ("Good afternoon" if h < 17 else "Good evening")
    return f"{g}, {name.strip()}" if str(name).strip() else g


def esc(x):
    return html.escape(str(x))


def kpi(label, value, sub="", hero=False, spark=None):
    cls = "card hero" if hero else "card"
    sp = spark_svg(spark, "#052E1B" if hero else "#4ADE80") if spark is not None and len(spark) > 1 else ""
    return (
        f'<div class="{cls}"><div class="lbl">{esc(label)}</div>'
        f'<div class="val">{esc(value)}</div><div class="sub">{esc(sub)}</div>{sp}</div>'
    )


def tile(level, head, text):
    return (
        f'<div class="tile {level}"><div class="th">{esc(head)}</div>{esc(text)}</div>'
    )


def style_fig(fig, height=340):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#CFE3D8"),
        legend_title_text="",
        title=dict(font=dict(size=16)),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,.08)")
    return fig


def location_map(lat, lon, label, key, clickable=True, height=520, search_enabled=True):
    """Fast exact-field picker. Place names only move the map; a map click is the final field point."""
    m = folium.Map(
        location=[float(lat), float(lon)],
        zoom_start=18,
        tiles=None,
        max_zoom=21,
        control_scale=True,
        prefer_canvas=True,
    )
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery", name="🛰️ Satellite", overlay=False, show=True,
        max_zoom=21, max_native_zoom=19,
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Street Map", name="🗺️ Street", overlay=False, show=False,
        max_zoom=21,
    ).add_to(m)
    folium.TileLayer("OpenStreetMap", name="🗺️ OpenStreetMap", overlay=False, show=False).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Place labels", overlay=True, show=True, max_zoom=21,
    ).add_to(m)

    folium.Marker(
        [float(lat), float(lon)],
        tooltip="Current field point",
        popup=f"<b>{html.escape(str(label))}</b><br>Lat: {float(lat):.6f}<br>Lon: {float(lon):.6f}",
        icon=folium.Icon(color="green", icon="leaf", prefix="fa"),
    ).add_to(m)

    # Visible instruction marker near the selected point.
    folium.Circle(
        [float(lat), float(lon)], radius=12, color="#22A559", fill=True,
        fill_opacity=0.12, weight=2, tooltip="Selected field point",
    ).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    out = st_folium(
        m, height=height, use_container_width=True,
        returned_objects=["last_clicked", "zoom"] if clickable else [], key=key,
    )
    if clickable and out and out.get("last_clicked"):
        c = out["last_clicked"]
        try:
            click = (round(float(c["lat"]), 6), round(float(c["lng"]), 6))
        except (TypeError, ValueError, KeyError):
            click = None
        if click and st.session_state.get("last_click") != click:
            st.session_state.last_click = click
            st.session_state.lat, st.session_state.lon = click
            st.session_state.place_label = f"📍 Exact field point"
            st.session_state.location_accuracy_m = 10
            st.rerun()


# ================= Tamil Nadu district -> sub-place picker =================
TN_DISTRICTS = [
    "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri",
    "Dindigul", "Erode", "Kallakurichi", "Kancheepuram", "Karur", "Krishnagiri",
    "Madurai", "Mayiladuthurai", "Nagapattinam", "Kanniyakumari", "Namakkal", "Perambalur",
    "Pudukkottai", "Ramanathapuram", "Ranipet", "Salem", "Sivaganga", "Tenkasi",
    "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli", "Tirupathur",
    "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore", "Viluppuram",
    "Virudhunagar", "The Nilgiris"
]
FALLBACK_SUBPLACES = {
    "Theni": ["Theni", "Periyakulam", "Bodinayakanur", "Uthamapalayam", "Cumbum", "Andipatti", "Chinnamanur"],
    "Virudhunagar": ["Virudhunagar", "Aruppukkottai", "Sivakasi", "Rajapalayam", "Srivilliputhur", "Sattur", "Tiruchuli", "Watrap"],
    "Madurai": ["Madurai", "Melur", "Usilampatti", "Thirumangalam", "Peraiyur", "Vadipatti"],
    "Dindigul": ["Dindigul", "Palani", "Oddanchatram", "Kodaikanal", "Vedasandur", "Natham", "Nilakottai"],
    "Coimbatore": ["Coimbatore", "Pollachi", "Mettupalayam", "Sulur", "Annur", "Valparai"],
    "Chennai": ["Chennai"],
    "Tiruchirappalli": ["Tiruchirappalli", "Manapparai", "Musiri", "Lalgudi", "Thuraiyur", "Srirangam"],
    "Perambalur": ["Perambalur", "Kunnam", "Veppanthattai", "Alathur"],
}
@st.cache_data(ttl=86400, show_spinner=False)
def get_district_subplaces(district):
    """Fast village/area lookup. Uses Open-Meteo geocoding instead of slow Overpass."""
    try:
        data = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": district, "count": 20, "language": "en", "format": "json", "countryCode": "IN"},
            timeout=8,
        ).json()
        rows = []
        for r in data.get("results", []):
            if str(r.get("country_code", "")).upper() != "IN":
                continue
            if str(r.get("admin1", "")).lower() not in {"tamil nadu", "tamilnadu"}:
                continue
            if r.get("latitude") is None or r.get("longitude") is None:
                continue
            rows.append({
                "name": r.get("name", district),
                "place_type": r.get("feature_code", "place"),
                "lat": float(r["latitude"]),
                "lon": float(r["longitude"]),
            })
        # Always include known useful nearby anchors for districts where geocoding returns only the district centre.
        known = FALLBACK_SUBPLACES.get(district, [])
        names = {x["name"].lower() for x in rows}
        for name in known:
            if name.lower() not in names:
                rows.append({"name": name, "place_type": "town", "lat": None, "lon": None})
        if rows:
            return rows[:30]
    except Exception:
        pass
    return [{"name": n, "place_type": "town", "lat": None, "lon": None} for n in FALLBACK_SUBPLACES.get(district, [district])]

@st.cache_data(ttl=3600, show_spinner=False)
def exact_place_lookup(place, district):
    """Fast exact place geocoding, restricted to Tamil Nadu, India."""
    try:
        data = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": f"{place}, {district}",
                "count": 10,
                "language": "en",
                "format": "json",
                "countryCode": "IN",
            },
            timeout=8,
        ).json()
        results = data.get("results", [])
        for r in results:
            if str(r.get("country_code", "")).upper() == "IN" and str(r.get("admin1", "")).lower() in {"tamil nadu", "tamilnadu"}:
                return r
        return results[0] if results else None
    except Exception:
        return None


# ================= Data =================
def get_json(url, params):
    for _ in range(5):
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException:
            time.sleep(2)
    return None


@st.cache_data(ttl=600)
def search_place(name, lang_code):
    """Global place search. Open-Meteo geocoding is not restricted to Theni."""
    data = get_json(
        "https://geocoding-api.open-meteo.com/v1/search",
        {
            "name": name.strip(),
            "count": 20,
            "language": lang_code,
            "format": "json",
        },
    )
    if not data or "results" not in data:
        return []
    return data["results"]


# ================= Sentinel-2 Satellite Analysis =================
def _satellite_packages_ok():
    try:
        import pystac_client  # noqa: F401
        import planetary_computer  # noqa: F401
        import rasterio  # noqa: F401
        return True, ""
    except Exception as e:
        return False, str(e)


@st.cache_data(ttl=3600, show_spinner=False)
def find_sentinel_items(lat, lon, days_back=90, cloud_max=40, limit=12):
    """Find Sentinel-2 L2A scenes covering the selected point."""
    import pystac_client
    import planetary_computer

    end = pd.Timestamp.now(tz="UTC").tz_localize(None)
    start = end - pd.Timedelta(days=days_back)
    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1/",
        modifier=planetary_computer.sign_inplace,
    )
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        intersects={"type": "Point", "coordinates": [float(lon), float(lat)]},
        datetime=f"{start.date().isoformat()}/{end.date().isoformat()}",
        query={"eo:cloud_cover": {"lt": float(cloud_max)}},
        max_items=limit,
    )
    items = list(search.items())
    items.sort(key=lambda x: x.datetime or pd.Timestamp.min.to_pydatetime(), reverse=True)
    return items


def _read_asset_area(asset, lat, lon, buffer_m=100, out_size=120):
    """Read a small safe window around the location; never reduce an empty array."""
    import planetary_computer
    import rasterio
    from rasterio.windows import Window
    from rasterio.warp import transform

    href = planetary_computer.sign(asset.href)
    with rasterio.open(href) as src:
        x, y = transform("EPSG:4326", src.crs, [float(lon)], [float(lat)])
        x, y = x[0], y[0]
        px = abs(src.transform.a)
        py = abs(src.transform.e)
        half_w = max(2, int(buffer_m / px))
        half_h = max(2, int(buffer_m / py))
        col, row = src.index(x, y)
        c0 = max(0, col - half_w)
        r0 = max(0, row - half_h)
        c1 = min(src.width, col + half_w + 1)
        r1 = min(src.height, row + half_h + 1)
        if c1 <= c0 or r1 <= r0:
            raise ValueError("Selected location is outside the satellite raster.")
        window = Window(c0, r0, c1 - c0, r1 - r0)
        data = src.read(1, window=window, boundless=False).astype("float32")
        if data.size == 0:
            raise ValueError("Satellite window contains zero pixels.")
        profile = src.profile
        return data, profile, window


def _scale_s2(a):
    """Sentinel-2 L2A reflectance is stored with a scale factor."""
    a = a.astype("float32")
    return a / 10000.0


def _safe_index(a, b):
    den = a + b
    with np.errstate(divide="ignore", invalid="ignore"):
        out = (a - b) / den
    return np.where(np.isfinite(out), out, np.nan)


def _resize_nearest(arr, shape):
    """Small dependency-free nearest-neighbour resize for the 20 m SCL/B11 to 10 m grid."""
    if arr.shape == shape:
        return arr
    y_idx = np.linspace(0, arr.shape[0] - 1, shape[0]).round().astype(int)
    x_idx = np.linspace(0, arr.shape[1] - 1, shape[1]).round().astype(int)
    return arr[np.ix_(y_idx, x_idx)]


def _valid_stats(a):
    a = a[np.isfinite(a)]
    if a.size == 0:
        return np.nan
    return float(np.nanmedian(a))


def _rgb_image(red, green, blue, scl=None):
    rgb = np.stack([red, green, blue], axis=-1)
    rgb = np.clip(rgb * 3.0, 0, 1)
    if scl is not None:
        bad = np.isin(scl, [3, 8, 9, 10, 11])
        rgb[bad] = np.nan
    finite = np.isfinite(rgb)
    if not finite.any():
        return None
    fill = np.nanmedian(rgb, axis=(0, 1))
    for c in range(3):
        rgb[..., c] = np.where(np.isfinite(rgb[..., c]), rgb[..., c], fill[c])
    return (np.clip(rgb, 0, 1) * 255).astype(np.uint8)


def analyze_sentinel_item(item, lat, lon, buffer_m=100):
    """Calculate crop health, plant water status, surface wetness and a true-colour image safely."""
    assets = item.assets
    required = ["B02", "B03", "B04", "B08", "B11", "SCL"]
    missing = [k for k in required if k not in assets]
    if missing:
        raise ValueError("Missing Sentinel-2 bands: " + ", ".join(missing))

    red, _, _ = _read_asset_area(assets["B04"], lat, lon, buffer_m)
    green, _, _ = _read_asset_area(assets["B03"], lat, lon, buffer_m)
    blue, _, _ = _read_asset_area(assets["B02"], lat, lon, buffer_m)
    nir, _, _ = _read_asset_area(assets["B08"], lat, lon, buffer_m)
    swir, _, _ = _read_asset_area(assets["B11"], lat, lon, buffer_m)
    scl, _, _ = _read_asset_area(assets["SCL"], lat, lon, buffer_m)

    shape = red.shape
    green = _resize_nearest(green, shape)
    blue = _resize_nearest(blue, shape)
    nir = _resize_nearest(nir, shape)
    swir = _resize_nearest(swir, shape)
    scl = _resize_nearest(scl, shape).astype("uint8")

    red, green, blue, nir, swir = map(_scale_s2, [red, green, blue, nir, swir])
    cloud_bad = np.isin(scl, [3, 8, 9, 10, 11])
    red[cloud_bad] = np.nan
    green[cloud_bad] = np.nan
    blue[cloud_bad] = np.nan
    nir[cloud_bad] = np.nan
    swir[cloud_bad] = np.nan

    ndvi = _safe_index(nir, red)
    ndmi = _safe_index(nir, swir)
    ndwi = _safe_index(green, nir)

    # --- v2 extra indices (farmer-facing): chlorophyll/nitrogen, canopy density, soil-adjusted greenness ---
    ndre = np.full(shape, np.nan, dtype="float32")
    try:
        if "B05" in assets:  # red-edge band, 20 m
            rededge, _, _ = _read_asset_area(assets["B05"], lat, lon, buffer_m)
            rededge = _scale_s2(_resize_nearest(rededge, shape))
            rededge[cloud_bad] = np.nan
            ndre = _safe_index(nir, rededge)
    except Exception:
        pass
    with np.errstate(divide="ignore", invalid="ignore"):
        evi = 2.5 * (nir - red) / (nir + 6.0 * red - 7.5 * blue + 1.0)
        savi = 1.5 * (nir - red) / (nir + red + 0.5)
    evi = np.where(np.isfinite(evi), np.clip(evi, -1, 2), np.nan)
    savi = np.where(np.isfinite(savi), np.clip(savi, -1, 1.5), np.nan)

    if not np.isfinite(ndvi).any():
        raise ValueError("All pixels were removed by the cloud/shadow mask. Try another date or a larger area.")

    return {
        "date": item.datetime.date().isoformat() if item.datetime else item.properties.get("datetime", "Unknown")[:10],
        "cloud": float(item.properties.get("eo:cloud_cover", np.nan)),
        "id": item.id,
        "ndvi": ndvi,
        "ndmi": ndmi,
        "ndwi": ndwi,
        "rgb": _rgb_image(red, green, blue, scl),
        "ndvi_median": _valid_stats(ndvi),
        "ndmi_median": _valid_stats(ndmi),
        "ndwi_median": _valid_stats(ndwi),
        "ndre": ndre,
        "evi": evi,
        "savi": savi,
        "ndre_median": _valid_stats(ndre),
        "evi_median": _valid_stats(evi),
        "savi_median": _valid_stats(savi),
    }


def satellite_stress(current, history):
    """0-100 risk score; higher means more unusual/stressed."""
    if not history:
        return 0, "No historical satellite baseline yet."
    ndvi_hist = np.array([x["ndvi_median"] for x in history], dtype=float)
    ndmi_hist = np.array([x["ndmi_median"] for x in history], dtype=float)
    ndvi_hist = ndvi_hist[np.isfinite(ndvi_hist)]
    ndmi_hist = ndmi_hist[np.isfinite(ndmi_hist)]
    score = 0.0
    reasons = []
    if ndvi_hist.size >= 2:
        base = float(np.median(ndvi_hist))
        drop = base - current["ndvi_median"]
        if drop > 0:
            score += min(45, drop * 180)
            if drop > 0.10:
                reasons.append(f"Crop green health is {drop:.2f} below the recent normal level")
    if ndmi_hist.size >= 2:
        base = float(np.median(ndmi_hist))
        drop = base - current["ndmi_median"]
        if drop > 0:
            score += min(35, drop * 140)
            if drop > 0.10:
                reasons.append(f"Plant water status is {drop:.2f} below the recent normal level")
    if current["ndwi_median"] < -0.15:
        score += 10
        reasons.append("low vegetation/water index")
    score = int(max(0, min(100, round(score))))
    msg = "; ".join(reasons) if reasons else "Satellite indices are close to the recent baseline."
    return score, msg


@st.cache_data(ttl=3600, show_spinner=False)
def get_satellite_analysis(lat, lon):
    ok, err = _satellite_packages_ok()
    if not ok:
        return {"ok": False, "error": "Install satellite packages first: pip install pystac-client planetary-computer rasterio numpy\n" + err}
    try:
        items = find_sentinel_items(lat, lon, days_back=180, cloud_max=50, limit=12)
        if not items:
            return {"ok": False, "error": "No Sentinel-2 L2A scene found for this location in the last 180 days."}
        results = []
        for item in items[:8]:
            try:
                results.append(analyze_sentinel_item(item, lat, lon, buffer_m=100))
            except Exception:
                continue
        if not results:
            return {"ok": False, "error": "Scenes were found, but no usable cloud-free pixels were available at this location. Try again with a larger field area or another date."}
        current = results[0]
        history = results[1:]
        score, reason = satellite_stress(current, history)
        return {"ok": True, "current": current, "history": history, "score": score, "reason": reason}
    except Exception as e:
        return {"ok": False, "error": f"Satellite analysis failed: {type(e).__name__}: {e}"}


@st.cache_data(ttl=600, show_spinner=False)

@st.cache_data(ttl=21600, show_spinner=False)
def get_multiyear_satellite_analysis(lat, lon, years=3, cloud_max=35, limit=24):
    """Build a practical multi-year Sentinel-2 comparison from cloud-screened scenes.
    This is a same-month historical comparison, not a certified crop-yield model.
    """
    ok, err = _satellite_packages_ok()
    if not ok:
        return {"ok": False, "error": err}
    try:
        items = find_sentinel_items(lat, lon, days_back=365*int(years), cloud_max=cloud_max, limit=limit)
        if not items:
            return {"ok": False, "error": "No multi-year Sentinel-2 scenes found."}
        rows=[]
        for item in items:
            try:
                r=analyze_sentinel_item(item, lat, lon, buffer_m=100)
                rows.append(r)
            except Exception:
                continue
        if len(rows)<3:
            return {"ok":False,"error":"Too few usable cloud-free scenes for a multi-year comparison."}
        df=pd.DataFrame([{"date":r["date"],"year":pd.to_datetime(r["date"]).year,"month":pd.to_datetime(r["date"]).month,
                          "NDVI":r["ndvi_median"],"NDMI":r["ndmi_median"],"🌊 Surface Wetness":r["ndwi_median"],"cloud":r["cloud"]} for r in rows])
        current=rows[0]
        cm=pd.to_datetime(current["date"]).month
        same=df[(df["month"]==cm) & (df["date"]!=current["date"])]
        if len(same)<2:
            same=df[df["date"]!=current["date"]]
        ndvi_base=float(same["NDVI"].median()) if not same.empty else np.nan
        ndmi_base=float(same["NDMI"].median()) if not same.empty else np.nan
        ndwi_base=float(same["🌊 Surface Wetness"].median()) if not same.empty else np.nan
        return {"ok":True,"current":current,"history":rows,"table":df.sort_values("date"),
                "baseline":{"ndvi":ndvi_base,"ndmi":ndmi_base,"ndwi":ndwi_base},
                "ndvi_anomaly":float(current["ndvi_median"]-ndvi_base) if _finite(ndvi_base) else np.nan,
                "ndmi_anomaly":float(current["ndmi_median"]-ndmi_base) if _finite(ndmi_base) else np.nan}
    except Exception as e:
        return {"ok":False,"error":f"Multi-year satellite analysis failed: {type(e).__name__}: {e}"}


def build_alerts(fusion, drought, flood, crop_risk, ndvi_anom=np.nan, ndmi_anom=np.nan):
    """Farmer-facing alert engine. It creates local dashboard alerts; no external SMS is sent."""
    alerts=[]
    if fusion>=70: alerts.append(("🔴", "HIGH LAND STRESS", "Multiple signals show significant abnormal conditions."))
    elif fusion>=45: alerts.append(("🟠", "LAND STRESS WATCH", "Monitor the field more frequently."))
    if drought>=60: alerts.append(("☀️", "DROUGHT WATCH", "Rainfall/heat/vegetation signals suggest water stress."))
    if flood>=60: alerts.append(("🌊", "WATERLOGGING WATCH", "Wetness and rainfall signals suggest possible excess water."))
    if crop_risk>=60: alerts.append(("🌱", "CROP RISK", "Crop-specific stress conditions need field verification."))
    if _finite(ndvi_anom) and ndvi_anom < -0.10: alerts.append(("📉", "VEGETATION DROP", f"Crop green health is {ndvi_anom:+.2f} versus the historical comparison."))
    if _finite(ndmi_anom) and ndmi_anom < -0.10: alerts.append(("💧", "WATER-STRESS DROP", f"Plant water status is {ndmi_anom:+.2f} versus the historical comparison."))
    if not alerts: alerts.append(("🟢", "NORMAL WATCH", "No major automated alert threshold is crossed right now."))
    return alerts

def map_search_place(query):
    """Search an exact place robustly, even when the user enters a full address."""
    query = query.strip()
    if not query:
        return []

    results = search_place(query, "en")
    if results:
        return results

    parts = [x.strip() for x in query.split(",") if x.strip()]
    candidates = []
    for part in parts[:4]:
        candidates.extend(search_place(part, "en")[:5])

    unique = {}
    for r in candidates:
        try:
            key = (
                round(float(r.get("latitude", 0)), 5),
                round(float(r.get("longitude", 0)), 5),
                r.get("name", ""),
            )
        except (TypeError, ValueError):
            continue
        unique[key] = r
    return list(unique.values())

@st.cache_data(ttl=600)
def get_weather(lat, lon):
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,precipitation",
        "hourly": "soil_moisture_3_to_9cm,soil_moisture_9_to_27cm,soil_temperature_6cm",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,et0_fao_evapotranspiration,wind_speed_10m_max,uv_index_max",
        "forecast_days": 7,
        "timezone": "auto",
    }
    data = get_json("https://api.open-meteo.com/v1/forecast", params)
    if data is None:
        raise RuntimeError("No data")
    return data


# ================= Sidebar =================
with st.sidebar:
    st.markdown(
        '<div class="sb-brand"><div class="sb-logo">🛰️</div><div><div class="sb-name">Hyperclimate</div>'
        '<div class="sb-tag">Satellite · Weather · AI for farmers</div></div></div>',
        unsafe_allow_html=True,
    )
    st.subheader(t("your_field"))

    # No default location. The user must explicitly choose a location.
    if "lat" not in st.session_state:
        st.session_state.lat = None
        st.session_state.lon = None
        st.session_state.place_label = None
        st.session_state.sig = None
        st.session_state.last_gps = None
        st.session_state.last_click = None
        st.session_state.location_accuracy_m = None
        st.session_state.gps_candidate = None
        st.session_state.gps_accuracy = None

    # ================= Redesigned location selector =================
    st.markdown("""
    <div class="loc-card">
        <div class="loc-title">📍 Set your field location</div>
        <div class="loc-subtitle">Choose a reference place, then select the exact field point.</div>
    </div>
    """, unsafe_allow_html=True)

    LOCATION_MODES = {
        "search": "🔎 Search",
        "map": "🛰️ Satellite Map",
        "gps": "📱 GPS",
        "coords": "📌 Coordinates",
    }

    # Keep the selected method in session state so it does not jump around.
    if "location_method" not in st.session_state:
        st.session_state.location_method = "search"

    mode = st.radio(
        "Location method",
        list(LOCATION_MODES.keys()),
        index=list(LOCATION_MODES.keys()).index(st.session_state.location_method),
        format_func=lambda x: LOCATION_MODES[x],
        horizontal=True,
        label_visibility="collapsed",
        key="location_method_radio",
    )
    st.session_state.location_method = mode

    if mode == "search":
        st.markdown("**Step 1 · District**")
        district_options = ["-- Select District --"] + TN_DISTRICTS
        district = st.selectbox(
            "District",
            district_options,
            index=0,
            key="district_select",
            label_visibility="collapsed",
        )

        st.markdown("**Step 2 · Village / area**")
        st.caption("First choose your village or nearby area. Then the satellite map will open so you can select the exact field.")
        subplaces = [] if district == "-- Select District --" else get_district_subplaces(district)
        sub_names = [x["name"] for x in subplaces] or (["-- Select Village / Area --"] if district != "-- Select District --" else ["-- Select District first --"])
        sub_i = st.selectbox(
            "Village / area",
            range(len(sub_names)),
            format_func=lambda k: sub_names[k],
            key=f"village_{district}",
            label_visibility="collapsed",
        )
        selected_sub = subplaces[sub_i] if subplaces else {"name": "", "lat": None, "lon": None}

        if st.button("🛰️ Select exact field on satellite map", use_container_width=True, key="open_village_map"):
            if district == "-- Select District --" or not subplaces:
                st.warning("Select a district and village / area first.")
            else:
                # Resolve the village centre if Overpass did not provide coordinates.
                anchor_lat = selected_sub.get("lat")
                anchor_lon = selected_sub.get("lon")
                if anchor_lat is None or anchor_lon is None:
                    exact = exact_place_lookup(selected_sub["name"], district)
                    if exact:
                        anchor_lat = float(exact["latitude"])
                        anchor_lon = float(exact["longitude"])
                if anchor_lat is not None and anchor_lon is not None:
                    st.session_state.village_anchor_lat = float(anchor_lat)
                    st.session_state.village_anchor_lon = float(anchor_lon)
                    st.session_state.village_anchor_label = f"{selected_sub['name']}, {district}, Tamil Nadu"
                    st.session_state.location_picker_open = True
                    st.session_state.last_click = None
                    st.rerun()
                else:
                    st.warning("Could not find this village. Try another village / area.")

        # The village is only the map starting point. It is NOT saved as the exact field.
        if st.session_state.get("location_picker_open") and st.session_state.get("village_anchor_lat") is not None:
            anchor_lat = st.session_state.village_anchor_lat
            anchor_lon = st.session_state.village_anchor_lon
            anchor_label = st.session_state.get("village_anchor_label", "Selected village")

            st.markdown("**Step 3 · Exact field location**")
            st.info("Zoom in on the satellite image and click the exact field/plot. The clicked point becomes your final location.")
            location_map(
                anchor_lat,
                anchor_lon,
                anchor_label,
                key="village_exact_picker",
                clickable=True,
                height=430,
                search_enabled=False,
            )

            if st.session_state.get("place_label") and str(st.session_state.place_label).startswith("Map point"):
                st.success(f"✅ Exact field selected: {st.session_state.place_label}")
                if st.button("🔄 Choose another exact point", use_container_width=True, key="reset_exact_picker"):
                    st.session_state.lat = None
                    st.session_state.lon = None
                    st.session_state.place_label = None
                    st.session_state.last_click = None
                    st.rerun()
        else:
            st.caption("Select a village / area first. The satellite map will appear here for exact field selection.")

    elif mode == "map":
        st.markdown("**Step 1 · Search or move to the area**")
        st.caption("Search a village/town/landmark, then click the exact field on the satellite map.")
        map_q = st.text_input(
            "Map search",
            value="",
            placeholder="Example: Ramaswamy Nagar, Aruppukkottai",
            key="sidebar_map_search",
            label_visibility="collapsed",
        )
        if map_q.strip():
            map_results = search_place(f"{map_q.strip()}, Tamil Nadu", LANG_CODE)[:8]
            if map_results:
                labels = [f"{r.get('name','Unknown')}, {r.get('admin1','Tamil Nadu')}" for r in map_results]
                mi = st.selectbox("Map result", range(len(map_results)), format_func=lambda k: labels[k], key="sidebar_map_result")
                if st.button("📍 Go to result", use_container_width=True, key="sidebar_go_map_result"):
                    rr = map_results[mi]
                    st.session_state.lat = float(rr["latitude"])
                    st.session_state.lon = float(rr["longitude"])
                    st.session_state.place_label = labels[mi]
                    st.session_state.map_anchor_label = labels[mi]
                    st.session_state.last_click = None
                    st.session_state.location_accuracy_m = None
                    st.session_state.location_picker_open = True
                    st.rerun()

        if st.session_state.get("location_picker_open") and st.session_state.get("lat") is not None and st.session_state.get("lon") is not None:
            lat2 = st.session_state.lat
            lon2 = st.session_state.lon
            st.markdown("**Step 2 · Exact field point**")
            st.caption("Zoom in as much as possible and click the centre of your field. The clicked point becomes the final location.")
            location_map(lat2, lon2, st.session_state.get("place_label") or "Map search result", key="fast_map_picker", clickable=True, height=420, search_enabled=False)
            if st.session_state.get("place_label") == "📍 Exact field point":
                st.success(f"✅ Exact field selected · {st.session_state.lat:.6f}, {st.session_state.lon:.6f}")
        else:
            st.info("Search a village / road / landmark first. The satellite map will open at that place.")

    elif mode == "gps":
        st.markdown("**📱 Use phone / browser GPS**")
        st.caption("Allow location access. GPS accuracy depends on your phone, browser and surroundings.")
        loc = streamlit_geolocation()
        if loc and loc.get("latitude") is not None and loc.get("longitude") is not None:
            acc = float(loc.get("accuracy") or 9999)
            g = (round(float(loc["latitude"]), 6), round(float(loc["longitude"]), 6))
            st.session_state.gps_candidate = g
            st.session_state.gps_accuracy = acc
            if acc <= 30:
                st.success(f"🟢 Good GPS accuracy: about {acc:.0f} m")
            elif acc <= 100:
                st.warning(f"🟡 GPS accuracy: about {acc:.0f} m. For a field-level point, use the satellite map after GPS.")
            else:
                st.warning(f"🔴 GPS accuracy is about {acc:.0f} m. Move outdoors / enable precise location and try again.")
            if st.button("📍 Use this GPS point", use_container_width=True, key="use_gps_point"):
                st.session_state.last_gps = g
                st.session_state.lat, st.session_state.lon = g
                st.session_state.place_label = "📍 GPS location"
                st.session_state.location_accuracy_m = acc
                st.session_state.last_click = None
                st.rerun()
            st.caption(f"Coordinates: {g[0]:.6f}, {g[1]:.6f}")
        else:
            st.info("Press the location button above and allow browser location permission. On a phone, keep Location/GPS enabled.")

    else:  # coords
        st.markdown("**📌 Enter exact coordinates**")
        with st.form("coord_form"):
            la = st.number_input("Latitude", value=None, placeholder="Enter latitude", format="%.6f")
            lo = st.number_input("Longitude", value=None, placeholder="Enter longitude", format="%.6f")
            go_btn = st.form_submit_button("✅ Set location", use_container_width=True)
        if go_btn:
            if la is None or lo is None:
                st.warning("Enter both latitude and longitude.")
                st.stop()
            st.session_state.lat, st.session_state.lon = la, lo
            st.session_state.place_label = f"📍 {la:.6f}, {lo:.6f}"
            st.session_state.last_click = None
            st.rerun()

    lat = st.session_state.lat
    lon = st.session_state.lon
    place_label = st.session_state.place_label
    location_accuracy_m = st.session_state.get("location_accuracy_m")

    # ---- ONE list with ALL crops (group filter is optional) ----
    group_key = st.selectbox(
        t("crop_group"),
        ["all"] + list(CROPS.keys()),
        format_func=lambda k: t("all_crops") if k == "all" else pick(CROPS[k]),
    )
    flat = [
        (gk, c)
        for gk, g in CROPS.items()
        for c in g[2]
        if group_key in ("all", gk)
    ]
    ci = st.selectbox(
        t("crop"), range(len(flat)), format_func=lambda k: crop_label(flat[k][1])
    )
    st.caption(t("count", n=len(flat)))
    crop_group_of, crop = flat[ci]

    stage_key = st.selectbox(t("stage"), list(STAGES.keys()), index=1, format_func=lambda k: pick(STAGES[k]))
    soil_key = st.selectbox(t("soil"), list(SOILS.keys()), format_func=lambda k: pick(SOILS[k]))
    irrig_key = st.selectbox(t("irrig"), list(IRRIGS.keys()), index=2, format_func=lambda k: pick(IRRIGS[k]))
    acres = st.number_input(t("acres"), min_value=0.1, value=1.0, step=0.5)
    flow = st.number_input(t("pump"), min_value=0, value=10000, step=1000)

    if lat is not None:
        st.markdown(
            f"""<div class="sb-sum"><div class="sb-h">📋 {esc(L("Field summary", "வயல் சுருக்கம்"))}</div>
            <div class="sb-r"><span>🌱 {esc(L("Crop", "பயிர்"))}</span><b>{esc(pick(crop))}</b></div>
            <div class="sb-r"><span>🪴 {esc(L("Stage", "நிலை"))}</span><b>{esc(pick(STAGES[stage_key]))}</b></div>
            <div class="sb-r"><span>🧱 {esc(L("Soil", "மண்"))}</span><b>{esc(pick(SOILS[soil_key]))}</b></div>
            <div class="sb-r"><span>📐 {esc(L("Size", "அளவு"))}</span><b>{acres:g} acre</b></div>
            <div class="sb-r"><span>📍 GPS</span><b>{lat:.4f}, {lon:.4f}</b></div>
            <div class="sb-src"><span>Sentinel-2</span><span>Sentinel-1</span><span>Landsat</span><span>NASA POWER</span><span>Open-Meteo</span></div></div>""",
            unsafe_allow_html=True,
        )
        if st.button("🔄 " + L("Refresh all satellite & weather data", "அனைத்து தகவலையும் புதுப்பி"), use_container_width=True, key="sb_refresh_all"):
            st.cache_data.clear()
            st.rerun()

if lat is None:
    st.markdown(
        f"""
        <div class="hero2"><div class="hero2-top"><div>
          <div class="hero2-title">🛰️ HYPERCLIMATE</div>
          <div class="hero2-sub">{esc(L("Smart Crop & Field Intelligence — your field, seen from space.", "ஸ்மார்ட் பயிர் & நில கண்காணிப்பு — விண்ணிலிருந்து உங்கள் வயல்."))}</div>
        </div><div class="hero2-pill"><i></i>{esc(L("READY", "தயார்"))}</div></div>
        <div class="hero2-chips"><span>🛰️ Sentinel-2</span><span>📡 Sentinel-1 Radar</span><span>🌡️ Landsat Thermal</span><span>🌦️ NASA POWER</span><span>🇮🇳 ISRO Bhuvan · VEDAS · MOSDAC</span></div></div>
        <div class="feat-grid">
          <div class="feat"><div class="f-ic">🌱</div><div class="f-t">{esc(L("Crop health from space", "விண்வெளியிலிருந்து பயிர் ஆரோக்கியம்"))}</div><div class="f-d">{esc(L("Green health, plant water and chlorophyll maps of your own field.", "உங்கள் வயலின் பசுமை, தாவர நீர், குளோரோஃபில் வரைபடங்கள்."))}</div></div>
          <div class="feat"><div class="f-ic">💧</div><div class="f-t">{esc(L("Smart irrigation", "ஸ்மார்ட் நீர்ப்பாசனம்"))}</div><div class="f-d">{esc(L("7-day water plan in litres and pump hours.", "7 நாள் நீர்த்திட்டம் — லிட்டர், மோட்டார் மணி நேரம்."))}</div></div>
          <div class="feat"><div class="f-ic">🚨</div><div class="f-t">{esc(L("Early warnings", "முன்னெச்சரிக்கை"))}</div><div class="f-d">{esc(L("Drought, waterlogging, heat and pest-watch alerts.", "வறட்சி, நீர்த்தேக்கம், வெப்பம், பூச்சி எச்சரிக்கை."))}</div></div>
          <div class="feat"><div class="f-ic">👨‍🌾</div><div class="f-t">{esc(L("Farmer advisory", "விவசாயி ஆலோசனை"))}</div><div class="f-d">{esc(L("Problem zones, growth phase, schemes and helplines.", "பிரச்சனை பகுதிகள், வளர்ச்சி நிலை, திட்டங்கள், உதவி எண்கள்."))}</div></div>
        </div>
        <div class="step-row">
          <div class="step"><b>1</b>{esc(L("Pick your location in the left sidebar", "இடது பக்கம் இடத்தை தேர்வு செய்யுங்கள்"))}</div>
          <div class="step"><b>2</b>{esc(L("Choose crop, stage, soil and field size", "பயிர், நிலை, மண், அளவை தேர்வு செய்யுங்கள்"))}</div>
          <div class="step"><b>3</b>{esc(L("Read the dashboard and follow the advice", "dashboard-ஐ பார்த்து ஆலோசனையை பின்பற்றுங்கள்"))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

try:
    w = get_weather(lat, lon)
except Exception:
    st.error(t("data_err"))
    st.stop()

# ================= Crop settings =================
crop_name = pick(crop)
kc, tmax_limit, mmin = crop[2], crop[3], crop[4]
stage_f = STAGES[stage_key][2]
soil_f, thr = SOILS[soil_key][2], SOILS[soil_key][3]
eff = IRRIGS[irrig_key][2]
mmin_adj = mmin * soil_f
tmax_eff = tmax_limit - 2 if stage_key == "seedling" else tmax_limit

# ================= Weather data =================
cur = w["current"]
hourly = pd.DataFrame(w["hourly"])
hourly["time"] = pd.to_datetime(hourly["time"])
daily = pd.DataFrame(w["daily"])
daily["time"] = pd.to_datetime(daily["time"])
daily = daily.fillna(0)

now = pd.to_datetime(cur["time"])
row = hourly.loc[(hourly["time"] - now).abs().idxmin()]
root = pd.Series([row["soil_moisture_3_to_9cm"], row["soil_moisture_9_to_27cm"]]).mean()
soil_temp = row["soil_temperature_6cm"]

temp = cur["temperature_2m"]
humidity = cur["relative_humidity_2m"]
wind = cur["wind_speed_10m"]
tmax_today = daily["temperature_2m_max"].iloc[0]
rain_prob = daily["precipitation_probability_max"].iloc[0]
rain2 = daily["precipitation_sum"].iloc[:2].sum()
uv = daily["uv_index_max"].iloc[0]
et0_today = daily["et0_fao_evapotranspiration"].iloc[0]

if rain2 >= 10:
    status = t("status_rain")
elif root < mmin_adj:
    status = t("status_dry")
else:
    status = t("status_ok")

# ================= 7-day irrigation plan (calculation) =================
daily["need"] = daily["et0_fao_evapotranspiration"] * kc * stage_f
daily["eff_rain"] = daily["precipitation_sum"] * 0.8

cum = thr if root < mmin_adj else 0.0  # soil already dry -> irrigate on day 1
actions, amounts = [], []
for _, r in daily.iterrows():
    cum = max(0.0, cum + r["need"] - r["eff_rain"])
    if r["precipitation_sum"] >= 10:
        actions.append("rain")
        amounts.append(0.0)
        cum = 0.0
    elif cum >= thr:
        actions.append("irrigate")
        amounts.append(cum)
        cum = 0.0
    else:
        actions.append("skip")
        amounts.append(0.0)

litres_each = [a * 4047 * acres / eff for a in amounts]
need_total = daily["need"].sum()
rain_total = daily["precipitation_sum"].sum()
irrig_days = actions.count("irrigate")
total_litres = sum(litres_each)
pump_hours = total_litres / flow if flow > 0 else 0
day_labels = [day_label(d) for d in daily["time"]]


# ================= Advanced Land Intelligence helpers =================
def _finite(v):
    try:
        return v is not None and np.isfinite(float(v))
    except Exception:
        return False


def _median(values):
    vals = [float(v) for v in values if _finite(v)]
    return float(np.median(vals)) if vals else float("nan")


@st.cache_data(ttl=1800, show_spinner=False)
def nasa_power_history(lat, lon, days=365):
    """Fetch daily agricultural weather history from NASA POWER for anomaly baselines."""
    end = pd.Timestamp.utcnow().normalize()
    start = end - pd.Timedelta(days=days)
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "T2M,PRECTOTCORR,RH2M,ALLSKY_SFC_SW_DWN",
        "community": "AG",
        "longitude": float(lon),
        "latitude": float(lat),
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "format": "JSON",
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    js = r.json()
    p = js["properties"]["parameter"]
    df = pd.DataFrame({
        "date": pd.to_datetime(list(p["T2M"].keys()), format="%Y%m%d", errors="coerce"),
        "temp": list(p["T2M"].values()),
        "rain": list(p["PRECTOTCORR"].values()),
        "humidity": list(p["RH2M"].values()),
        "solar": list(p["ALLSKY_SFC_SW_DWN"].values()),
    })
    for c in ["temp", "rain", "humidity", "solar"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").replace(-999, np.nan)
    df = df.dropna(subset=["date"]).sort_values("date")
    df["month"] = df["date"].dt.month
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def get_elevation(lat, lon):
    """Global elevation fallback using OpenTopoData ASTER 30m."""
    url = "https://api.opentopodata.org/v1/aster30m"
    r = requests.get(url, params={"locations": f"{lat},{lon}"}, timeout=20)
    r.raise_for_status()
    data = r.json()
    return float(data["results"][0]["elevation"])


@st.cache_data(ttl=3600, show_spinner=False)
def get_terrain_slope(lat, lon, delta=0.001):
    """Estimate local slope from a 3x3 ASTER elevation sample (degrees)."""
    pts = [(lat, lon), (lat+delta, lon), (lat-delta, lon), (lat, lon+delta), (lat, lon-delta)]
    url = "https://api.opentopodata.org/v1/aster30m"
    r = requests.get(url, params={"locations":"|".join(f"{a},{b}" for a,b in pts)}, timeout=20)
    r.raise_for_status()
    vals = [x.get("elevation") for x in r.json().get("results", [])]
    if len(vals) != 5 or any(v is None for v in vals):
        return float("nan")
    center,n,s,e,w = map(float, vals)
    dy = 2*delta*110540.0
    dx = 2*delta*111320.0*math.cos(math.radians(lat))
    dzdx=(e-w)/dx; dzdy=(n-s)/dy
    return float(math.degrees(math.atan(math.sqrt(dzdx**2+dzdy**2))))


def terrain_class(elevation, slope=None):
    if not _finite(elevation):
        return "Unknown"
    if slope is not None and _finite(slope):
        if slope < 2: return "Very flat"
        if slope < 5: return "Gentle slope"
        if slope < 12: return "Moderate slope"
        return "Steep slope"
    return "Low / medium elevation" if elevation < 300 else "Higher elevation"


def polygon_area_m2(coords):
    """Approximate polygon area from [lon, lat] vertices."""
    if not coords or len(coords) < 3:
        return 0.0
    lat0 = np.mean([float(y) for x, y in coords])
    xy = []
    for lon, lat in coords:
        x = float(lon) * 111320.0 * math.cos(math.radians(lat0))
        y = float(lat) * 110540.0
        xy.append((x, y))
    area = 0.0
    for i in range(len(xy)):
        x1, y1 = xy[i]
        x2, y2 = xy[(i + 1) % len(xy)]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def extract_last_polygon(drawings):
    if not drawings:
        return None
    polys = [d for d in drawings if d.get("geometry", {}).get("type") in ("Polygon", "MultiPolygon")]
    if not polys:
        return None
    geom = polys[-1]["geometry"]
    if geom["type"] == "Polygon":
        ring = geom["coordinates"][0]
    else:
        ring = geom["coordinates"][0][0]
    return [(float(x), float(y)) for x, y in ring]


def field_boundary_map(lat, lon, label, key="field_boundary"):
    m = folium.Map(location=[lat, lon], zoom_start=17, tiles=None, max_zoom=20, control_scale=True)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery", name="🛰️ Satellite", show=True, max_zoom=20, max_native_zoom=19
    ).add_to(m)
    folium.TileLayer("OpenStreetMap", name="🗺️ Street", show=False).add_to(m)
    folium.Marker([lat, lon], tooltip="Selected field reference").add_to(m)
    Draw(export=False, draw_options={"polyline": False, "rectangle": True, "circle": False, "marker": False, "circlemarker": False, "polygon": True},
         edit_options={"edit": True, "remove": True}).add_to(m)
    folium.LayerControl().add_to(m)
    return st_folium(m, height=520, use_container_width=True, returned_objects=["all_drawings"], key=key)


@st.cache_data(ttl=3600, show_spinner=False)
def landsat_lst(lat, lon, days_back=180):
    """Latest usable Landsat Collection-2 Level-2 surface temperature near the point."""
    ok, err = _satellite_packages_ok()
    if not ok:
        return {"ok": False, "error": err}
    try:
        import pystac_client, planetary_computer
        catalog = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
        search = catalog.search(
            collections=["landsat-c2-l2"],
            intersects={"type":"Point","coordinates":[float(lon), float(lat)]},
            datetime=f"{(pd.Timestamp.utcnow()-pd.Timedelta(days=days_back)).strftime('%Y-%m-%d')}/{pd.Timestamp.utcnow().strftime('%Y-%m-%d')}",
            query={"eo:cloud_cover":{"lt":60}},
            max_items=20,
        )
        items = list(search.items())
        items.sort(key=lambda x: x.datetime or pd.Timestamp.min.to_pydatetime(), reverse=True)
        for item in items:
            signed = planetary_computer.sign(item)
            if "ST_B10" not in signed.assets:
                continue
            arr, transform = _read_asset_area(signed.assets["ST_B10"].href, lat, lon, buffer_m=150, out_size=120)
            if arr.size == 0:
                continue
            qa = None
            if "ST_QA" in signed.assets:
                try:
                    qa, _ = _read_asset_area(signed.assets["ST_QA"].href, lat, lon, buffer_m=150, out_size=120)
                except Exception:
                    qa = None
            arr = arr.astype("float32") * 0.00341802 + 149.0 - 273.15
            arr[~np.isfinite(arr)] = np.nan
            if qa is not None and qa.size == arr.size:
                arr[qa <= 0] = np.nan
            vals = arr[np.isfinite(arr)]
            if vals.size:
                return {"ok":True,"date":item.datetime.date().isoformat() if item.datetime else "unknown","lst":float(np.median(vals)),"cloud":float(item.properties.get("eo:cloud_cover", np.nan)),"id":item.id,"array":arr}
        return {"ok":False,"error":"No usable Landsat thermal scene found in the selected period."}
    except Exception as e:
        return {"ok":False,"error":f"Landsat LST unavailable: {type(e).__name__}: {e}"}


def satellite_health_class(ndvi, ndmi, score):
    if score >= 70: return "Severe stress"
    if score >= 45: return "High stress"
    if score >= 25: return "Moderate stress"
    if _finite(ndvi) and ndvi < 0.25: return "Low vegetation"
    if _finite(ndmi) and ndmi < -0.05: return "Water stress watch"
    return "Healthy / near baseline"


def fusion_score(sat_score, rain_anom, temp_anom, humidity):
    """Transparent rule-based fusion score; this is a risk indicator, not a diagnosis."""
    score = float(sat_score) * 0.55
    score += max(0.0, -float(rain_anom)) * 0.25
    score += max(0.0, float(temp_anom)) * 2.0
    if humidity > 85: score += 5
    return int(max(0, min(100, round(score))))


def risk_class(score):
    return "🔴 Severe" if score >= 70 else ("🟠 High" if score >= 45 else ("🟡 Moderate" if score >= 25 else "🟢 Low"))


def land_cover_indicator(ndvi, ndwi):
    if not _finite(ndvi): return "Unknown"
    if _finite(ndwi) and ndwi > 0.25: return "Open water / very wet surface"
    if ndvi < 0.15: return "Bare soil / built-up / sparse vegetation"
    if ndvi < 0.35: return "Sparse or stressed vegetation"
    if ndvi < 0.60: return "Moderate vegetation / cropland"
    return "Dense vegetation / tree canopy"



def land_cover_clusters(sat, n_clusters=5):
    """Unsupervised spectral-index clustering; labels are indicative, not certified LULC."""
    if not sat or not sat.get("ok"): return None
    a=sat["current"];
    arrays=[a.get("ndvi"),a.get("ndmi"),a.get("ndwi")]
    if any(x is None for x in arrays): return None
    h,w=arrays[0].shape
    X=np.column_stack([x.reshape(-1) for x in arrays]).astype(float)
    good=np.isfinite(X).all(axis=1)
    if good.sum()<max(20,n_clusters*4): return None
    try:
        from sklearn.cluster import KMeans
        km=KMeans(n_clusters=min(n_clusters,int(good.sum())),random_state=42,n_init=10)
        labels=np.full(len(X),-1,int); labels[good]=km.fit_predict(X[good])
        centers=km.cluster_centers_
        names=[]
        for ndv,nm,nw in centers:
            if nw>0.25: name="Water / wet surface"
            elif ndv<0.15: name="Bare / built-up / sparse"
            elif ndv<0.35: name="Stressed vegetation"
            elif ndv<0.60: name="Cropland / moderate vegetation"
            else: name="Dense vegetation / canopy"
            names.append(name)
        return {"labels":labels.reshape(h,w),"centers":centers,"names":names}
    except Exception:
        return None


def sentinel1_sar_analysis(lat, lon, days_back=365):
    """Sentinel-1 RTC VV/VH backscatter near the field. Uses open STAC when available."""
    ok, err = _satellite_packages_ok()
    if not ok: return {"ok":False,"error":err}
    try:
        import pystac_client, planetary_computer
        catalog=pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=planetary_computer.sign_inplace)
        end=pd.Timestamp.utcnow().tz_localize(None); start=end-pd.Timedelta(days=days_back)
        search=catalog.search(collections=["sentinel-1-rtc"], intersects={"type":"Point","coordinates":[float(lon),float(lat)]}, datetime=f"{start.date()}/{end.date()}", max_items=30)
        items=list(search.items()); items.sort(key=lambda x:x.datetime or pd.Timestamp.min.to_pydatetime(), reverse=True)
        rows=[]
        for item in items[:12]:
            a=item.assets
            vv=a.get("vv"); vh=a.get("vh")
            if not vv: continue
            arr,_,_= _read_asset_area(vv,lat,lon,buffer_m=150,out_size=80)
            vvvals=arr[np.isfinite(arr)]
            if not vvvals.size: continue
            if not rows: first_arr=arr  # keep the LATEST scene for the radar map
            # RTC assets are normally linear power; convert to dB when values are positive.
            vvdb=float(np.median(10*np.log10(np.maximum(vvvals,1e-8))))
            vhdb=np.nan
            if vh:
                va,_,_=_read_asset_area(vh,lat,lon,buffer_m=150,out_size=80); vv2=va[np.isfinite(va)]
                if vv2.size: vhdb=float(np.median(10*np.log10(np.maximum(vv2,1e-8))))
            rows.append({"date":item.datetime.date().isoformat() if item.datetime else "unknown","vv":vvdb,"vh":vhdb,"id":item.id})
        if not rows: return {"ok":False,"error":"No usable Sentinel-1 scene found."}
        current=rows[0]; base=np.nanmedian([r["vv"] for r in rows[1:]]) if len(rows)>1 else np.nan
        change=float(current["vv"]-base) if np.isfinite(base) else np.nan
        return {"ok":True,"current":current,"history":rows,"vv_change_db":change,"vv_array":first_arr if "first_arr" in locals() else None}
    except Exception as e: return {"ok":False,"error":f"Sentinel-1 unavailable: {type(e).__name__}: {e}"}


def drought_flood_indicators(nasa_df, sat, lst, sar):
    rain_anom=temp_anom=0.0
    if nasa_df is not None and not nasa_df.empty:
        d=nasa_df.copy()
        if "month" in d:
            d["rain_base"]=d.groupby("month")["rain"].transform("median")
            d["temp_base"]=d.groupby("month")["temp"].transform("median")
            r=d.iloc[-1]
            if r["rain_base"]>0: rain_anom=float((r["rain"]-r["rain_base"])/r["rain_base"]*100)
            temp_anom=float(r["temp"]-r["temp_base"])
    ndvi=ndmi=lstv=np.nan
    if sat and sat.get("ok"):
        ndvi=sat["current"]["ndvi_median"]; ndmi=sat["current"]["ndmi_median"]
    if lst and lst.get("ok"): lstv=lst["lst"]
    drought=0
    drought += min(40,max(0,-rain_anom)*0.5)
    drought += min(30,max(0,temp_anom)*6)
    drought += min(20,max(0,-(ndmi+0.05))*100)
    drought += min(10,max(0,(0.35-ndvi)*30)) if np.isfinite(ndvi) else 0
    flood=0
    flood += min(35,max(0,rain_anom)*0.35)
    flood += 20 if np.isfinite(ndmi) and ndmi>0.25 else 0
    flood += 15 if np.isfinite(sar) and sar< -2 else 0
    return int(min(100,round(drought))), int(min(100,round(flood))), rain_anom,temp_anom



def crop_specific_profile(crop_name, crop_group, crop_tuple=None):
    """Return crop-adjusted interpretation thresholds. These are advisory ranges, not disease diagnosis."""
    name=(crop_name or "").lower()
    group=(crop_group or "").lower()
    kc=float(crop_tuple[2]) if crop_tuple is not None else 1.0
    heat=float(crop_tuple[3]) if crop_tuple is not None else 38.0
    moisture=float(crop_tuple[4])*100 if crop_tuple is not None else 20.0

    # Broad crop-family satellite interpretation. Optical satellite values are
    # still measured from the field; these thresholds only change how they are interpreted.
    group_ndvi = {
        "grains":0.35, "pulses":0.30, "oilseeds":0.30, "cash":0.35,
        "veg":0.35, "fruit":0.40, "plantation":0.45, "trees":0.35,
        "flowers":0.35, "fodder":0.40
    }
    ndvi_min=group_ndvi.get(group,0.35)

    # More water-demanding crops get a slightly stricter plant-water warning.
    ndmi_min = -0.05 + max(0.0, min(0.10, (kc-0.8)*0.10))

    # Crop/family watch-list for farmer-facing pest/disease monitoring.
    fungal_crops={"paddy","rice","tomato","chilli","brinjal","potato","grapes","banana","cucumber","cabbage","cauliflower","rose","jasmine","cardamom","coffee","tea","pepper","ginger","turmeric","coconut"}
    mite_crops={"coconut","banana","chilli","brinjal","cotton","groundnut","lemon","mango","papaya","grapes"}
    water_sensitive={"onion","garlic","potato","chickpea","groundnut","sandalwood","neem","cashew"}
    if name in fungal_crops:
        watch="fungal / leaf disease conditions"
    elif name in mite_crops:
        watch="sucking-pest / mite conditions"
    elif group in {"veg","flowers"}:
        watch="leaf disease and sucking-pest conditions"
    elif group in {"fruit","plantation"}:
        watch="leaf disease and sucking-pest conditions"
    else:
        watch="crop pest / disease conditions"

    return {"kc":kc,"heat_limit":heat,"moisture_min":moisture,"ndvi_min":ndvi_min,
            "ndmi_min":ndmi_min,"watch":watch,"water_sensitive":name in water_sensitive}


def crop_specific_satellite_interpretation(crop_name, crop_group, crop_tuple, sat, rain_anom=0.0, temp_anom=0.0, humidity=0.0):
    """Interpret the same satellite observation differently for the selected crop."""
    p=crop_specific_profile(crop_name,crop_group,crop_tuple)
    if not sat or not sat.get("ok"):
        return {"score":0,"level":"No satellite result","reasons":[],"pest":"Satellite observation unavailable."}
    c=sat["current"]
    score=0; reasons=[]
    ndvi=float(c.get("ndvi_median",np.nan)); ndmi=float(c.get("ndmi_median",np.nan)); ndwi=float(c.get("ndwi_median",np.nan))
    history=sat.get("history",[])
    hist_ndvi=np.array([x.get("ndvi_median",np.nan) for x in history],dtype=float)
    hist_ndmi=np.array([x.get("ndmi_median",np.nan) for x in history],dtype=float)
    hist_ndvi=hist_ndvi[np.isfinite(hist_ndvi)]; hist_ndmi=hist_ndmi[np.isfinite(hist_ndmi)]

    # 1) Crop-adjusted vegetation level.
    if _finite(ndvi) and ndvi < p["ndvi_min"]:
        score += 20
        reasons.append(f"{crop_name}: crop green health is below the normal range for this crop type")
    # 2) Recent change is more important than an absolute universal threshold.
    if hist_ndvi.size >= 2 and _finite(ndvi):
        base=float(np.median(hist_ndvi)); drop=base-ndvi
        if drop > 0.05:
            score += min(25, int(drop*160))
            reasons.append(f"{crop_name}: crop green health has fallen {drop:.2f} from the recent field normal")
    # 3) Crop-adjusted plant-water signal.
    if _finite(ndmi) and ndmi < p["ndmi_min"]:
        score += 25
        reasons.append(f"{crop_name}: plant water status is low")
    if hist_ndmi.size >= 2 and _finite(ndmi):
        base=float(np.median(hist_ndmi)); drop=base-ndmi
        if drop > 0.05:
            score += min(20, int(drop*120))
            reasons.append(f"{crop_name}: plant water status has fallen {drop:.2f} from the recent field normal")
    # 4) Weather is interpreted against the selected crop's limits.
    if temp_anom > 2:
        score += min(15,int(temp_anom*3))
        reasons.append(f"Temperature is {temp_anom:+.1f}°C above the local normal for the selected period")
    if humidity > 85 and (_finite(ndwi) and ndwi > 0.05):
        score += 8
        reasons.append(f"High humidity + wet surface may favour {p['watch']}")
    if rain_anom < -20 and p["kc"] >= 0.9:
        score += 10
        reasons.append(f"Rainfall is {abs(rain_anom):.0f}% below normal; {crop_name} has relatively high water demand")

    score=int(max(0,min(100,round(score))))
    level="🟢 Low" if score<25 else ("🟡 Moderate" if score<45 else ("🟠 High" if score<70 else "🔴 Severe"))

    # Pest/disease warning is a field-check signal, never a diagnosis.
    pest_score=0; pest_reasons=[]
    if humidity>=85 and (_finite(ndwi) and ndwi>0.0):
        pest_score += 55 if p["watch"].startswith("fungal") else 40
        pest_reasons.append(f"High humidity + wet vegetation: check for {p['watch']}")
    if humidity<50 and (temp_anom>2 or (_finite(ndmi) and ndmi<p["ndmi_min"])):
        pest_score += 35
        pest_reasons.append(f"Dry/heat conditions: check leaves for {p['watch']}")
    if not pest_reasons:
        pest_reasons.append(f"Current weather does not strongly favour {p['watch']}")
    pest_level="🔴 Field check priority" if pest_score>=60 else ("🟠 Monitor" if pest_score>=35 else "🟢 Low watch")

    return {"score":score,"level":level,"reasons":reasons,"pest_score":min(100,pest_score),
            "pest_level":pest_level,"pest_reasons":pest_reasons,"profile":p}


def crop_risk_model(crop, sat, nasa_df, lst, sar, crop_group=None, crop_tuple=None):
    """Crop-specific transparent risk rules; not a disease diagnosis."""
    c=(crop or "").lower(); group=(crop_group or "").lower()
    p=crop_specific_profile(crop,group,crop_tuple)
    score=0; reasons=[]
    if sat and sat.get("ok"):
        cc=sat["current"]
        if _finite(cc.get("ndvi_median")) and cc["ndvi_median"]<p["ndvi_min"]:
            score+=25; reasons.append(f"{crop}: crop green health is low for this crop type")
        if _finite(cc.get("ndmi_median")) and cc["ndmi_median"]<p["ndmi_min"]:
            score+=25; reasons.append(f"{crop}: plant water status is low")
        if sat.get("score",0)>40: score+=20; reasons.append("Recent satellite change is unusual")
    if nasa_df is not None and not nasa_df.empty:
        r=nasa_df.iloc[-1]
        if float(r.get("temp",0))>p["heat_limit"]: score+=15; reasons.append(f"Temperature is above {crop}'s selected heat limit")
        if float(r.get("humidity",0))>85: score+=10; reasons.append("High humidity needs crop-specific disease monitoring")
    return min(100,score), reasons


def ai_anomaly_score(sat):
    """Unsupervised satellite anomaly score using recent Sentinel-2 feature history."""
    if not sat or not sat.get("ok"): return None
    rows=[sat["current"]]+sat.get("history",[])
    X=[]
    for r in rows:
        vals=[r.get("ndvi_median"),r.get("ndmi_median"),r.get("ndwi_median")]
        if all(np.isfinite(v) for v in vals): X.append(vals)
    if len(X)<5: return sat.get("score",0)
    try:
        from sklearn.ensemble import IsolationForest
        model=IsolationForest(random_state=42,contamination="auto",n_estimators=150)
        pred=model.fit_predict(np.array(X)); return 80 if pred[0]==-1 else 20
    except Exception:
        z=np.abs((np.array(X[0])-np.median(np.array(X[1:]),axis=0))/(np.std(np.array(X[1:]),axis=0)+1e-6)); return int(min(100,round(np.mean(z)*35)))


def zone_table(sat, crop, zones=4):
    if not sat or not sat.get("ok"): return pd.DataFrame()
    a=sat["current"]["ndvi"]; m=sat["current"]["ndmi"]
    h,w=a.shape; out=[]
    for zi,(r0,r1,c0,c1) in enumerate([(0,h//2,0,w//2),(0,h//2,w//2,w),(h//2,h,0,w//2),(h//2,h,w//2,w)],1):
        av=a[r0:r1,c0:c1]; mv=m[r0:r1,c0:c1]
        nv=float(np.nanmedian(av)); nm=float(np.nanmedian(mv));
        priority="High" if (nv<.30 or nm<.05) else ("Medium" if nv<.50 else "Low")
        out.append({"Zone":f"Zone {zi}","Crop Green Health":round(nv,3),"Plant Water Status":round(nm,3),"Irrigation priority":priority})
    return pd.DataFrame(out)


def make_pdf_report(path, report_text, place, crop, sat=None, lst=None, area=None, risk=0):
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    doc=SimpleDocTemplate(path,pagesize=A4,rightMargin=36,leftMargin=36,topMargin=36,bottomMargin=36)
    styles=getSampleStyleSheet(); story=[Paragraph("HYPERCLIMATE — LAND HEALTH REPORT",styles["Title"]),Paragraph(f"{place} • {crop}",styles["Heading2"]),Spacer(1,12)]
    data=[["Indicator","Value"],["Field area",f"{area:.1f} m²" if area else "Not drawn"],["Overall risk",f"{risk}/100"]]
    if sat and sat.get("ok"):
        c=sat["current"]; data += [["Crop Green Health",f"{c['ndvi_median']:.3f}"],["Plant Water Status",f"{c['ndmi_median']:.3f}"],["🌊 Surface Wetness",f"{c['ndwi_median']:.3f}"],["Satellite date",str(c['date'])]]
    if lst and lst.get("ok"): data.append(["Land Surface Temperature",f"{lst['lst']:.1f} °C ({lst['date']})"])
    table=Table(data,colWidths=[180,300]); table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.lightgrey),("GRID",(0,0),(-1,-1),.5,colors.grey),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("PADDING",(0,0),(-1,-1),7)])); story += [table,Spacer(1,14)]
    for line in report_text.splitlines(): story.append(Paragraph(line.replace("&","&amp;"),styles["BodyText"]))
    doc.build(story)

def build_report_text(place, crop, lat, lon, sat, lst, nasa, elevation, area_m2, fusion):
    lines = [
        "HYPERCLIMATE - LAND INTELLIGENCE REPORT",
        "=" * 50,
        f"Location: {place}", f"Crop: {crop}", f"Latitude: {lat:.6f}", f"Longitude: {lon:.6f}",
        f"நிலத்தின் பரப்பளவு: {area_m2:.1f} m² ({area_m2/4046.856:.3f} acres)" if area_m2 else "நிலத்தின் பரப்பளவு: not drawn",
        f"நில உயரம்: {elevation:.1f} m" if _finite(elevation) else "நில உயரம்: unavailable",
    ]
    if sat and sat.get("ok"):
        c = sat["current"]
        lines += [f"Sentinel-2 date: {c['date']}", f"Crop Green Health: {c['ndvi_median']:.3f}", f"Plant Water Status: {c['ndmi_median']:.3f}", f"Surface Wetness: {c['ndwi_median']:.3f}", f"Satellite நில அழுத்தம்: {sat['score']}/100"]
    if lst and lst.get("ok"):
        lines += [f"Land Surface Temperature: {lst['lst']:.1f} °C ({lst['date']})"]
    if nasa is not None and not nasa.empty:
        r = nasa.iloc[-1]
        lines += [f"NASA POWER recent temperature: {r['temp']:.1f} °C", f"NASA POWER recent rainfall: {r['rain']:.1f} mm"]
    lines += [f"மொத்த நில ஆபத்து குறியீடு: {fusion}/100", "Note: Remote sensing indices are indicators and do not by themselves confirm a pest/disease diagnosis."]
    return "\n".join(lines)

# ================= Hyperclimate v2: farmer-facing satellite insight helpers =================
NDVI_CLASSES = [
    ("Bare / very weak", -1.0, 0.20, "#B45309"),
    ("Weak growth", 0.20, 0.40, "#F59E0B"),
    ("Moderate growth", 0.40, 0.60, "#84CC16"),
    ("Healthy / dense", 0.60, 1.01, "#15803D"),
]


def chips(items):
    return '<div class="chip-row">' + "".join(f'<span class="chip">{esc(i)}</span>' for i in items) + "</div>"


def insight_card(icon, title, value, note="", level="ok"):
    cls = "ins" if level == "ok" else f"ins {level}"
    return (f'<div class="{cls}"><div class="ins-ic">{icon}</div><div>'
            f'<div class="ins-t">{esc(title)}</div><div class="ins-v">{esc(value)}</div>'
            f'<div class="ins-n">{esc(note)}</div></div></div>')


def ndvi_class_breakdown(ndvi):
    arr = np.asarray(ndvi, dtype=float)
    valid = arr[np.isfinite(arr)]
    if valid.size == 0:
        return None
    return [{"class": n, "pct": float(((valid >= lo) & (valid < hi)).sum()) / valid.size * 100, "color": c}
            for n, lo, hi, c in NDVI_CLASSES]


def ndvi_class_map(ndvi):
    arr = np.asarray(ndvi, dtype=float)
    out = np.full(arr.shape, np.nan)
    for i, (_, lo, hi, _) in enumerate(NDVI_CLASSES):
        out[(arr >= lo) & (arr < hi)] = i
    return out


def field_uniformity(ndvi):
    v = np.asarray(ndvi, dtype=float)
    v = v[np.isfinite(v)]
    if v.size < 10 or abs(float(np.mean(v))) < 1e-6:
        return None
    cv = float(np.std(v) / abs(np.mean(v)) * 100)
    if cv < 12:
        return cv, "Very uniform", "ok"
    if cv < 22:
        return cv, "Fairly uniform", "info"
    return cv, "Patchy — scout weak spots", "warn"


def weakest_quadrant(ndvi):
    a = np.asarray(ndvi, dtype=float)
    if a.ndim != 2 or min(a.shape) < 4:
        return None
    h, w = a.shape
    quads = {"North-West": a[:h // 2, :w // 2], "North-East": a[:h // 2, w // 2:],
             "South-West": a[h // 2:, :w // 2], "South-East": a[h // 2:, w // 2:]}
    meds = {k: _valid_stats(v) for k, v in quads.items()}
    meds = {k: v for k, v in meds.items() if _finite(v)}
    if len(meds) < 2:
        return None
    worst, best = min(meds, key=meds.get), max(meds, key=meds.get)
    return worst, meds[worst], best, meds[best]


def satellite_growth_phase(sat):
    pts = sorted((x["date"], x["ndvi_median"]) for x in [sat["current"]] + list(sat.get("history", []))
                 if _finite(x.get("ndvi_median")))
    if len(pts) < 2:
        return None
    vals = [v for _, v in pts]
    cur, peak = vals[-1], max(vals)
    delta = cur - float(np.mean(vals[:-1][-3:]))
    if cur < 0.25:
        return "Bare / very early", "🌰", "Little green cover yet — land preparation or just sown.", "info"
    if delta > 0.04 and cur < 0.65:
        return "Rapid growth", "🌱", "Canopy is building fast — keep water and nutrients steady.", "ok"
    if cur >= 0.6 and abs(delta) <= 0.06:
        return "Peak canopy", "🌳", "Full green cover — protect from pests, avoid water stress.", "ok"
    if delta < -0.05 and peak >= 0.5:
        return "Ripening / decline", "🌾", "Greenness is falling. Normal near harvest — if the crop is young, check for stress.", "warn"
    return "Steady growth", "🌿", "Crop is growing at a normal pace.", "ok"


def canopy_potential_index(sat, ref=0.75):
    vals = [x["ndvi_median"] for x in [sat["current"]] + list(sat.get("history", [])) if _finite(x.get("ndvi_median"))]
    if not vals:
        return None
    return int(round(min(100, max(0, max(vals) / ref * 100))))


def field_health_index(sat, root_m, moist_min, tmax_now, tmax_lim):
    score = 100 - float(sat.get("score", 0)) * 0.6
    nd = sat["current"].get("ndvi_median")
    if _finite(nd):
        score += (min(max(nd, 0.0), 0.8) - 0.4) * 25
    if root_m < moist_min:
        score -= min(20, (moist_min - root_m) * 100 * 1.5)
    if tmax_now >= tmax_lim:
        score -= 8
    score = int(max(0, min(100, round(score))))
    if score >= 70:
        return score, "Good", "ok"
    if score >= 45:
        return score, "Watch closely", "warn"
    return score, "Needs attention", "bad"


def hc_gauge(value, title, height=230, suffix=""):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value, number={"suffix": suffix},
        title={"text": title, "font": {"size": 14}},
        gauge={"axis": {"range": [0, 100]}, "bar": {"color": "#34D399"},
               "steps": [{"range": [0, 40], "color": "rgba(239,68,68,.35)"}, {"range": [40, 70], "color": "rgba(245,158,11,.32)"},
                         {"range": [70, 100], "color": "rgba(34,197,94,.30)"}]}))
    fig.update_layout(height=height, margin=dict(l=20, r=20, t=50, b=10), paper_bgcolor="rgba(0,0,0,0)")
    return fig


def class_donut(rows, height=270):
    fig = go.Figure(go.Pie(labels=[r["class"] for r in rows], values=[r["pct"] for r in rows], hole=0.62,
                           marker=dict(colors=[r["color"] for r in rows]), sort=False, textinfo="percent"))
    fig.update_layout(height=height, margin=dict(l=5, r=5, t=10, b=5), paper_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=-0.08), font=dict(color="#CFE3D8"))
    return fig


def ndvi_map_fig(ndvi, height=300):
    fig = px.imshow(ndvi, color_continuous_scale="RdYlGn", zmin=-0.1, zmax=0.9, aspect="equal")
    fig.update_layout(height=height, margin=dict(l=0, r=0, t=6, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      coloraxis_colorbar=dict(title="NDVI", thickness=10, len=0.8))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def class_map_fig(ndvi, height=320):
    cols = [c for *_, c in NDVI_CLASSES]
    scale = []
    for i, c in enumerate(cols):
        scale += [[i / 4, c], [(i + 1) / 4, c]]
    fig = px.imshow(ndvi_class_map(ndvi), color_continuous_scale=scale, zmin=-0.5, zmax=3.5, aspect="equal")
    fig.update_layout(height=height, margin=dict(l=0, r=0, t=6, b=0), paper_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def ndvi_trend_fig(sat, ndvi_min=0.35, height=330, title=""):
    rows = [sat["current"]] + list(sat.get("history", []))
    df = pd.DataFrame([{"date": pd.to_datetime(x["date"]), "NDVI": x["ndvi_median"], "NDMI": x["ndmi_median"]} for x in rows])
    df = df.dropna(subset=["NDVI"]).sort_values("date")
    fig = go.Figure()
    fig.add_hrect(y0=0.6, y1=1.0, fillcolor="#16A34A", opacity=0.08, line_width=0)
    fig.add_hrect(y0=-0.1, y1=ndvi_min, fillcolor="#DC2626", opacity=0.07, line_width=0)
    fig.add_trace(go.Scatter(x=df["date"], y=df["NDVI"], mode="lines+markers", name="Crop green health (NDVI)",
                             line=dict(color="#15803D", width=3), marker=dict(size=8)))
    fig.add_trace(go.Scatter(x=df["date"], y=df["NDMI"], mode="lines+markers", name="Plant water (NDMI)",
                             line=dict(color="#2563EB", width=2, dash="dot"), marker=dict(size=6)))
    fig.update_layout(title=title, yaxis_title="Index value", legend=dict(orientation="h", y=1.12))
    return style_fig(fig, height)


def wx_icon(rain_mm, prob, tmax, tmax_lim):
    if rain_mm >= 20:
        return "⛈️"
    if rain_mm >= 5 or prob >= 60:
        return "🌧️"
    if prob >= 35:
        return "🌦️"
    if tmax >= tmax_lim:
        return "🔥"
    if tmax >= 32:
        return "☀️"
    return "⛅"


def next_satellite_passes(last_date, revisit=5, n=3):
    try:
        d = pd.to_datetime(last_date).normalize()
    except Exception:
        return []
    today = pd.Timestamp.now().normalize()
    while d <= today:
        d += pd.Timedelta(days=revisit)
    return [(d + pd.Timedelta(days=revisit * i)).strftime("%d %b %Y") for i in range(n)]


# ================= Hyperclimate v3: flood watch + ISRO hub + bento helpers =================
def spark_svg(values, color="#4ADE80", w=118, h=34):
    v = [float(x) for x in values if _finite(x)]
    if len(v) < 2:
        return ""
    lo, hi = min(v), max(v)
    rngv = (hi - lo) or 1.0
    pts = [(i / (len(v) - 1) * (w - 4) + 2, h - 3 - (x - lo) / rngv * (h - 8)) for i, x in enumerate(v)]
    path = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(pts))
    area = path + f" L{pts[-1][0]:.1f},{h} L{pts[0][0]:.1f},{h} Z"
    return (f'<svg class="spark" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><path d="{area}" fill="{color}" fill-opacity=".16"/>'
            f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="3" fill="{color}"/></svg>')


def rgb_data_uri(rgb, width=720):
    try:
        from PIL import Image
        from io import BytesIO as _BIO
        im = Image.fromarray(np.asarray(rgb, dtype="uint8"))
        h = int(width * im.height / max(1, im.width))
        im = im.resize((width, max(1, h)), Image.BICUBIC)
        buf = _BIO()
        im.save(buf, format="JPEG", quality=88)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return None


def sat_tile_html(rgb, place, date, cloud, ndvi_v, extra_stats=()):
    uri = rgb_data_uri(rgb) if rgb is not None else None
    bg = f"background-image:url('{uri}');" if uri else "background:linear-gradient(135deg,#0F3D2A,#14683F);"
    stats = [("NDVI", f"{ndvi_v:.2f}" if _finite(ndvi_v) else "N/A")] + list(extra_stats)
    stat_html = "".join(f'<div class="bsat-stat"><b>{esc(v)}</b><span>{esc(k)}</span></div>' for k, v in stats)
    return (f'<div class="bsat" style="{bg}"><div class="bsat-top"><span class="bsat-pill">🛰️ Sentinel-2 L2A</span>'
            f'<span class="bsat-pill">📅 {esc(date)} · ☁️ {cloud:.0f}%</span></div>'
            f'<div class="bsat-bot"><div><div class="bsat-place">📍 {esc(place)}</div><div class="bsat-sub">True-colour · 10 m resolution</div></div>'
            f'<div class="bsat-stats">{stat_html}</div></div></div>')


@st.cache_data(ttl=3600, show_spinner=False)
def load_s1_stack(lat, lon, days_back=150, buffer_m=400, n_px=110, max_scenes=8):
    """Latest Sentinel-1 RTC VV scenes (dB) resampled to one common grid."""
    ok, err = _satellite_packages_ok()
    if not ok:
        return {"ok": False, "error": err}
    try:
        import pystac_client, planetary_computer
        cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=planetary_computer.sign_inplace)
        end = pd.Timestamp.now(tz="UTC").tz_localize(None)
        start = end - pd.Timedelta(days=days_back)
        items = list(cat.search(collections=["sentinel-1-rtc"], intersects={"type": "Point", "coordinates": [float(lon), float(lat)]},
                                datetime=f"{start.date()}/{end.date()}", max_items=40).items())
        items.sort(key=lambda x: x.datetime or pd.Timestamp.min.to_pydatetime(), reverse=True)
        scenes = []
        for item in items:
            vv = item.assets.get("vv")
            if not vv:
                continue
            try:
                arr, _, _ = _read_asset_area(vv, lat, lon, buffer_m=buffer_m)
            except Exception:
                continue
            arr = _resize_nearest(np.asarray(arr, dtype="float32"), (n_px, n_px))
            arr[~np.isfinite(arr) | (arr <= 0)] = np.nan
            if not np.isfinite(arr).any():
                continue
            scenes.append({"date": item.datetime.date().isoformat() if item.datetime else "unknown",
                           "db": (10 * np.log10(np.maximum(arr, 1e-6))).astype("float32"), "id": item.id})
            if len(scenes) >= max_scenes:
                break
        if len(scenes) < 3:
            return {"ok": False, "error": "Fewer than 3 usable Sentinel-1 scenes found for a change comparison."}
        return {"ok": True, "scenes": scenes, "buffer_m": buffer_m, "n_px": n_px}
    except Exception as e:
        return {"ok": False, "error": f"Sentinel-1 unavailable: {type(e).__name__}: {e}"}


def flood_from_stack(stack, water_db=-16.0, drop_db=3.0):
    """Change-detection flood mapping: water now (low VV) that was NOT water in the baseline."""
    import warnings
    sc = stack["scenes"]
    cur = sc[0]["db"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        base = np.nanmedian(np.stack([s["db"] for s in sc[1:]]), axis=0)
    change = cur - base
    water_now = np.isfinite(cur) & (cur < water_db)
    water_base = np.isfinite(base) & (base < water_db)
    new_flood = water_now & ~water_base & (change < -drop_db)
    permanent = water_now & water_base
    valid = np.isfinite(cur)
    n = max(1, int(valid.sum()))
    win_ha = (2 * stack["buffer_m"]) ** 2 / 10000.0
    mask = np.full(cur.shape, np.nan)
    mask[valid] = 0
    mask[permanent] = 1
    mask[new_flood] = 2
    series = [{"date": s["date"], "VV median (dB)": float(np.nanmedian(s["db"])),
               "Water %": float((s["db"][np.isfinite(s["db"])] < water_db).mean() * 100)} for s in reversed(sc)]
    return {"cur": cur, "base": base, "change": change, "mask": mask, "date": sc[0]["date"],
            "water_pct": water_now.sum() / n * 100, "new_pct": new_flood.sum() / n * 100, "perm_pct": permanent.sum() / n * 100,
            "new_ha": new_flood.sum() / n * win_ha, "win_ha": win_ha, "chg_med": float(np.nanmedian(change)),
            "series": pd.DataFrame(series)}


@st.cache_data(ttl=3600, show_spinner=False)
def nisar_search_asf(lat, lon, days_back=120, max_results=25):
    """Search NISAR L-band granules over the field via the public ASF DAAC search API (search is free; download needs Earthdata login)."""
    start = (pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%SZ")
    params = {"dataset": "NISAR", "intersectsWith": f"POINT({float(lon):.5f} {float(lat):.5f})", "start": start,
              "maxResults": max_results, "output": "geojson"}
    try:
        r = requests.get("https://api.daac.asf.alaska.edu/services/search/param", params=params, timeout=45)
        if r.status_code != 200:
            return {"ok": False, "error": f"ASF search returned HTTP {r.status_code}: {r.text[:200]}"}
        feats = r.json().get("features", [])
        rows = []
        for f in feats:
            p = f.get("properties", {}) or {}
            rows.append({"Acquired": str(p.get("startTime", ""))[:19].replace("T", " "),
                         "Level": p.get("processingLevel", ""),
                         "Product": p.get("sceneName") or p.get("fileName") or p.get("fileID") or "",
                         "Download (needs Earthdata login)": p.get("url", "")})
        return {"ok": True, "rows": rows}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


# ================= Hyperclimate v4: farmer alerts (Tamil voice, WhatsApp/SMS) =================
# --- ALERT COMPOSER START ---
def compose_alert(lang, c):
    """Build a short farmer message. `c` is a plain dict (no Streamlit objects) so the same code runs in the scheduled worker."""
    ta = (lang == "ta")
    sec = set(c.get("sections") or ["water", "heat", "pest", "spray", "sat", "flood"])

    def T(en, tamil):
        return tamil if ta else en

    lines = [T(f"🌾 Hyperclimate Farm Alert\n📍 {c['place']} · 🌱 {c['crop']}",
               f"🌾 Hyperclimate விவசாயி எச்சரிக்கை\n📍 {c['place']} · 🌱 {c['crop']}")]
    lit = float(c.get("litres") or 0)
    if "water" in sec:
        if c["rain2"] >= 10:
            lines.append(T(f"🌧️ Rain expected: {c['rain2']:.0f} mm in 2 days — do NOT irrigate today.",
                           f"🌧️ அடுத்த 2 நாளில் {c['rain2']:.0f} மி.மீ மழை வாய்ப்பு — இன்று நீர் பாய்ச்ச வேண்டாம்."))
        elif c["root_pct"] < c["moist_min_pct"]:
            amt_en = f" (~{lit:,.0f} L)" if lit > 0 else ""
            amt_ta = f" (சுமார் {lit:,.0f} லிட்டர்)" if lit > 0 else ""
            lines.append(T(f"💧 Soil moisture {c['root_pct']:.0f}% (needs ≥{c['moist_min_pct']:.0f}%). Irrigate today{amt_en}.",
                           f"💧 மண் ஈரம் {c['root_pct']:.0f}% (குறைந்தபட்சம் {c['moist_min_pct']:.0f}%). இன்று நீர் பாய்ச்சவும்{amt_ta}."))
        else:
            lines.append(T(f"✅ Soil moisture {c['root_pct']:.0f}% — no irrigation needed today.",
                           f"✅ மண் ஈரம் {c['root_pct']:.0f}% — இன்று நீர் பாய்ச்ச தேவையில்லை."))
    if "heat" in sec and c["tmax"] >= c["tmax_lim"]:
        lines.append(T(f"🔥 Hot day: {c['tmax']:.0f}°C (crop limit {c['tmax_lim']:.0f}°C). Irrigate early morning or evening.",
                       f"🔥 இன்று வெப்பம் {c['tmax']:.0f}°C (பயிர் வரம்பு {c['tmax_lim']:.0f}°C). காலை அல்லது மாலையில் நீர் பாய்ச்சவும்."))
    if "pest" in sec:
        if c["humidity"] >= 80 and 20 <= c["temp"] <= 32:
            lines.append(T("🐛 High humidity: check leaves for fungal spots / disease today.",
                           "🐛 ஈரப்பதம் அதிகம் — இலைப்புள்ளி / பூஞ்சை நோய் உள்ளதா என்று வயலை பாருங்கள்."))
        elif c["humidity"] <= 35 and c["temp"] >= 35:
            lines.append(T("🕷️ Hot and dry: check for mites / thrips.", "🕷️ வறண்ட வெப்பம் — சிவப்பு சிலந்தி / இலைப்பேன் உள்ளதா என்று பாருங்கள்."))
    if "spray" in sec:
        if c["wind"] <= 15 and c["rain_prob"] < 30:
            lines.append(T("🧴 Good day for spraying.", "🧴 இன்று மருந்து தெளிக்க ஏற்ற நாள்."))
        else:
            lines.append(T("🚫 Wind or rain risk — avoid spraying today.", "🚫 காற்று / மழை வாய்ப்பு — இன்று மருந்து தெளிக்க வேண்டாம்."))
    if "sat" in sec and c.get("health") is not None:
        lines.append(T(f"🛰️ Satellite field health: {c['health']}/100 ({c.get('health_label', '')}).",
                       f"🛰️ செயற்கைக்கோள் வயல் ஆரோக்கியம்: {c['health']}/100 ({c.get('health_label', '')})."))
    if "flood" in sec and c.get("flood") in ("bad", "warn"):
        lines.append(T("🌊 New water/flood signal on radar — check drainage; inform insurer within 72 h (14447).",
                       "🌊 ரேடாரில் புதிய நீர்/வெள்ள அறிகுறி — வடிகாலை பாருங்கள்; 72 மணி நேரத்தில் காப்பீடு (14447)."))
    lines.append(T("☎️ Kisan Call Centre: 1800-180-1551", "☎️ கிசான் கால் சென்டர்: 1800-180-1551"))
    return "\n".join(lines)
# --- ALERT COMPOSER END ---


def voice_text(msg):
    """Strip emojis/symbols so a text-to-speech engine reads clean sentences."""
    t_ = re.sub(r"[\U00010000-\U0010ffff\u2600-\u27BF\uFE0F\u200d]", "", msg)
    t_ = t_.replace("°C", " டிகிரி" if re.search(r"[\u0B80-\u0BFF]", t_) else " degrees").replace("%", " சதவீதம்" if re.search(r"[\u0B80-\u0BFF]", t_) else " percent")
    t_ = re.sub(r"[·]", ",", t_)
    return re.sub(r"\s*\n\s*", ". ", t_).strip()


@st.cache_data(ttl=3600, show_spinner=False)
def make_voice_mp3(text, lang_code):
    from gtts import gTTS
    buf = BytesIO()
    gTTS(text=text, lang=lang_code).write_to_fp(buf)
    return buf.getvalue()


def twilio_send(to_number, body, channel="whatsapp"):
    """Send via Twilio REST (no SDK). Credentials come from .streamlit/secrets.toml, never from the code."""
    try:
        sid, tok = st.secrets["TWILIO_SID"], st.secrets["TWILIO_TOKEN"]
        frm = st.secrets["TWILIO_WHATSAPP_FROM"] if channel == "whatsapp" else st.secrets["TWILIO_SMS_FROM"]
    except Exception:
        return False, "Twilio secrets not configured (see the setup box below)."
    to = to_number.strip()
    if channel == "whatsapp":
        to, frm = "whatsapp:" + to, ("whatsapp:" + frm if not str(frm).startswith("whatsapp:") else frm)
    try:
        r = requests.post(f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                          data={"From": frm, "To": to, "Body": body}, auth=(sid, tok), timeout=30)
        if r.status_code in (200, 201):
            return True, "Sent ✔"
        return False, f"Twilio error {r.status_code}: {r.text[:180]}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


# ================= Hyperclimate v5: bulk alerts from a farmers CSV =================
HC_BULK_COLS = ["name", "phone", "lat", "lon", "crop", "kc", "heat_limit", "moist_min", "acres", "lang", "channel", "place"]
HC_BULK_REQUIRED = ["name", "phone", "lat", "lon", "crop"]


def hc_bulk_sample_csv():
    return ("name,phone,lat,lon,crop,kc,heat_limit,moist_min,acres,lang,channel,place\n"
            "Ravi,+919876543210,10.8231,78.6853,Paddy,1.15,38,0.30,2,ta,whatsapp,Tiruchirappalli\n"
            "Meena,+919812345678,8.7139,77.7567,Banana,1.10,36,0.30,1.5,en,sms,Tirunelveli\n").encode("utf-8")


@st.cache_data(ttl=900, show_spinner=False)
def hc_bulk_weather(lat, lon):
    """Same light weather-only call as hyperclimate_alert_worker.py (cached 15 min so re-previews are instant)."""
    p = {"latitude": lat, "longitude": lon, "timezone": "auto", "forecast_days": 2,
         "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
         "hourly": "soil_moisture_3_to_9cm,soil_moisture_9_to_27cm",
         "daily": "temperature_2m_max,precipitation_sum,precipitation_probability_max,et0_fao_evapotranspiration"}
    r = requests.get("https://api.open-meteo.com/v1/forecast", params=p, timeout=30)
    r.raise_for_status()
    return r.json()


def _hc_num(v, default):
    try:
        x = float(str(v).strip())
        return x if np.isfinite(x) else default
    except Exception:
        return default


def hc_bulk_ctx(f, w):
    cur_, hr, d = w["current"], w["hourly"], w["daily"]
    times = hr["time"]
    i = min(range(len(times)), key=lambda k: abs(datetime.fromisoformat(times[k]) - datetime.fromisoformat(cur_["time"])))
    root_ = ((hr["soil_moisture_3_to_9cm"][i] or 0) + (hr["soil_moisture_9_to_27cm"][i] or 0)) / 2
    kc_, ac_ = _hc_num(f.get("kc"), 1.0), _hc_num(f.get("acres"), 1.0)
    et0 = d["et0_fao_evapotranspiration"][0] or 0.0
    return dict(place=(str(f.get("place") or "").strip() or f"{f['lat']},{f['lon']}"), crop=str(f["crop"]).strip(),
                root_pct=root_ * 100, moist_min_pct=_hc_num(f.get("moist_min"), 0.25) * 100,
                tmax=d["temperature_2m_max"][0], tmax_lim=_hc_num(f.get("heat_limit"), 38.0),
                rain2=sum(x or 0 for x in d["precipitation_sum"][:2]), rain_prob=d["precipitation_probability_max"][0] or 0,
                humidity=cur_["relative_humidity_2m"], temp=cur_["temperature_2m"], wind=cur_["wind_speed_10m"],
                litres=et0 * kc_ * 4047 * ac_ / 0.75, sections=["water", "heat", "pest", "spray"])


def hc_bulk_needs_attention(c):
    return (c["rain2"] >= 10 or c["root_pct"] < c["moist_min_pct"] or c["tmax"] >= c["tmax_lim"]
            or (c["humidity"] >= 80 and 20 <= c["temp"] <= 32) or (c["humidity"] <= 35 and c["temp"] >= 35))


def hc_bulk_prepare(df, only_attention=True, max_rows=200):
    """Build one message per farmer row. Returns a list of dicts (status: ready | skip | error)."""
    out = []
    for _, r in df.head(max_rows).iterrows():
        f = {k: ("" if pd.isna(v) else str(v).strip()) for k, v in r.items()}
        item = {"name": f.get("name", ""), "phone": f.get("phone", ""), "channel": (f.get("channel") or "whatsapp").lower(),
                "lang": (f.get("lang") or "ta").lower(), "status": "ready", "info": "", "message": ""}
        try:
            c = hc_bulk_ctx(f, hc_bulk_weather(float(f["lat"]), float(f["lon"])))
            if only_attention and not hc_bulk_needs_attention(c):
                item.update(status="skip", info=L("Nothing urgent", "அவசரம் இல்லை"))
            else:
                item["lang"] = "en" if item["lang"] == "en" else "ta"
                item["channel"] = "sms" if item["channel"] == "sms" else "whatsapp"
                m = compose_alert(item["lang"], c)
                item["message"] = ("வணக்கம் " if item["lang"] == "ta" else "Hello ") + item["name"] + ",\n" + m
        except Exception as e:
            item.update(status="error", info=f"{type(e).__name__}: {e}"[:140])
        out.append(item)
    return out


# ================= Header =================
_who = str(st.session_state.get("al_name", "") or "").strip()
st.markdown(
    f"""
    <div class="topbar">
      <div>
        <div class="tb-hello">{esc(greeting_text(_who))} 🌾</div>
        <div class="tb-sub">🛰️ HYPERCLIMATE · {esc(L("Smart Crop & Field Intelligence · Satellite + Weather + AI", "ஸ்மார்ட் பயிர் & நில கண்காணிப்பு · செயற்கைக்கோள் + வானிலை + AI"))}</div>
      </div>
      <div class="tb-right">
        <span class="tb-live"><i></i>{esc(L("LIVE MONITORING", "நேரடி கண்காணிப்பு"))}</span>
        <span class="tb-date">🕒 {datetime.now().strftime("%d %b %Y, %H:%M")}</span>
      </div>
      <div class="tb-chips">
        <span>📍 {esc(place_label)}</span><span>🌱 {esc(crop_label(crop))}</span>
        <span>🪴 {esc(pick(STAGES[stage_key]))}</span><span>🧱 {esc(pick(SOILS[soil_key]))}</span>
        <span>📐 {acres:g} acre</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---- Satellite map picker (shown on top only in "map click" mode) ----
if mode == "map":
    st.markdown(f'<div class="sec">{esc(t("by_map"))}</div>', unsafe_allow_html=True)
    st.caption(t("map_hint"))
    location_map(lat, lon, place_label, key="picker", clickable=True)
    st.caption(t("selected", p=place_label))

tab_over, tab_adv, tab_alert, tab_irrig, tab_charts, tab_sat, tab_land, tab_maps, tab_flood, tab_isro, tab_ai, tab_report, tab_map = st.tabs(
    [
        "🏠 Home",
        "👨‍🌾 Farmer Advisory",
        "📣 Alert Center",
        "💧 Water",
        "🌦️ Weather",
        "🛰️ Satellite",
        "🌍 Field Health",
        "🗺️ Risk Maps",
        "🌊 Flood Watch",
        "🇮🇳 ISRO Hub",
        "🧠 AI & Alerts",
        "📄 Reports",
        "📍 Field Map",
    ]
)

# ================= TAB 1: Overview =================
with tab_over:
    st.markdown("## 🏠 Home — Field Health at a Glance")
    st.caption("One-screen view of your field, weather, crop health and current alerts.")

    # ---- v5: story cards (water / heat / rain) ----
    _need_lit = float(litres_each[0]) if litres_each else 0.0
    if rain2 >= 10:
        _wa_chip, _wa_cls, _wa_left = L("Skip irrigation", "நீர் வேண்டாம்"), "info", L(f"Rain {rain2:.0f} mm due", f"{rain2:.0f} மி.மீ மழை")
    elif root < mmin_adj:
        _wa_chip, _wa_cls = L("Irrigate today", "இன்று நீர் பாய்ச்சு"), "warn"
        _wa_left = L(f"~{_need_lit:,.0f} L needed", f"சுமார் {_need_lit:,.0f} லி தேவை") if _need_lit > 0 else L(f"Min {mmin_adj*100:.0f}%", f"குறைந்தது {mmin_adj*100:.0f}%")
    else:
        _wa_chip, _wa_cls, _wa_left = L("Moisture OK", "ஈரம் சரி"), "", L(f"Min needed {mmin_adj*100:.0f}%", f"குறைந்தது {mmin_adj*100:.0f}%")
    if tmax_today >= tmax_eff + 3:
        _he_chip, _he_cls = L("Extreme heat", "கடும் வெப்பம்"), "bad"
    elif tmax_today >= tmax_eff:
        _he_chip, _he_cls = L("Heat stress", "வெப்ப அழுத்தம்"), "warn"
    else:
        _he_chip, _he_cls = L("Safe range", "பாதுகாப்பான அளவு"), ""
    st.markdown(
        '<div class="stories">'
        + story_card("a", 3, t("soil_moist"), "💧", f"{root * 100:.0f}", "%", _wa_chip, _wa_cls, _wa_left, "#A7F3D0")
        + story_card("b", 8, L("Today's heat", "இன்றைய வெப்பம்"), "🌡️", f"{tmax_today:.0f}", "°C", _he_chip, _he_cls,
                     L(f"{crop_name} limit {tmax_eff:.0f}°C", f"{crop_name} வரம்பு {tmax_eff:.0f}°C"), "#FDE68A")
        + story_card("c", 5, L("Rain ahead (2 days)", "மழை (2 நாள்)"), "🌧️", f"{rain2:.0f}", " mm",
                     L(f"{rain_prob:.0f}% chance", f"{rain_prob:.0f}% வாய்ப்பு"), "info" if rain_prob >= 50 else "",
                     L(f"Wind {wind} km/h", f"காற்று {wind} கி.மீ/ம"), "#7DD3FC")
        + "</div>",
        unsafe_allow_html=True,
    )

    # ---- v5: soil-moisture trend (big number) + live trigger list ----
    _hs = hourly.copy()
    _hs["soil_pct"] = (_hs["soil_moisture_3_to_9cm"] + _hs["soil_moisture_9_to_27cm"]) / 2 * 100
    _i_now = int((_hs["time"] - now).abs().idxmin())
    _i_fut = min(_i_now + 24, len(_hs) - 1)
    _d24 = float(_hs["soil_pct"].iloc[_i_fut] - _hs["soil_pct"].iloc[_i_now])
    g1, g2 = st.columns([2.3, 1])
    with g1:
        _arrow = "▲" if _d24 >= 0 else "▼"
        st.markdown(
            f'<div class="panel"><div class="pn-label">{esc(L("Root-zone moisture · next 7 days", "வேர் மண்டல ஈரம் · அடுத்த 7 நாள்"))}</div>'
            f'<div class="pn-big">{root * 100:.1f}%<span class="pn-delta {"" if _d24 >= 0 else "dn"}">{_arrow} {abs(_d24):.1f} pts · 24h</span></div></div>',
            unsafe_allow_html=True,
        )
        _fig = go.Figure()
        _fig.add_trace(go.Scatter(x=_hs["time"], y=_hs["soil_pct"], mode="lines", name=L("Soil moisture %", "மண் ஈரம் %"),
                                  line=dict(color="#34D399", width=3, shape="spline"), fill="tozeroy", fillcolor="rgba(52,211,153,.14)"))
        _fig.add_hline(y=mmin_adj * 100, line_dash="dot", line_color="#F59E0B",
                       annotation_text=L(f"Irrigate below {mmin_adj*100:.0f}%", f"{mmin_adj*100:.0f}% கீழ் நீர் பாய்ச்சு"), annotation_font_color="#FCD34D")
        _fig.add_shape(type="line", x0=now, x1=now, yref="paper", y0=0, y1=1, line=dict(color="rgba(255,255,255,.35)", width=1))
        style_fig(_fig, 270)
        _fig.update_layout(margin=dict(l=6, r=6, t=10, b=6), showlegend=False)
        st.plotly_chart(_fig, use_container_width=True)
    with g2:
        _fl = st.session_state.get("flood_level")
        _trg = [
            ("💧", L("Soil moisture", "மண் ஈரம்"), f"{root*100:.0f}% / min {mmin_adj*100:.0f}%", root < mmin_adj),
            ("🌧️", L("Rain next 2 days", "அடுத்த 2 நாள் மழை"), f"{rain2:.0f} mm", rain2 >= 10),
            ("🔥", L("Heat", "வெப்பம்"), f"{tmax_today:.0f}°C / limit {tmax_eff:.0f}°C", tmax_today >= tmax_eff),
            ("🐛", L("Fungal weather", "பூஞ்சை வானிலை"), f"RH {humidity:.0f}%, {temp:.0f}°C", humidity >= 80 and 20 <= temp <= 32),
            ("🌊", L("Flood radar", "வெள்ள ரேடார்"), str(_fl or L("not scanned", "ஸ்கேன் இல்லை")), _fl in ("bad", "warn")),
        ]
        _rows = "".join(
            f'<div class="al-row"><span class="al-dot {"on" if on else ""}"></span><div><div class="al-t">{ic} {esc(ti)}</div><div class="al-v">{esc(va)}</div></div>'
            f'<span class="al-s {"on" if on else ""}">{esc(L("Active", "செயல்") if on else L("Normal", "இயல்பு"))}</span></div>'
            for ic, ti, va, on in sorted(_trg, key=lambda z: not z[3])
        )
        st.markdown(f'<div class="panel"><div class="pn-label">{esc(L("Live alerts", "நேரடி எச்சரிக்கைகள்"))}</div><div class="alist">{_rows}</div></div>', unsafe_allow_html=True)

    _sp_soil = ((hourly["soil_moisture_3_to_9cm"] + hourly["soil_moisture_9_to_27cm"]) / 2 * 100).iloc[::6].tolist()
    _sp_temp = daily["temperature_2m_max"].tolist()
    _sp_rain = daily["precipitation_probability_max"].tolist()
    _sp_et = daily["et0_fao_evapotranspiration"].tolist()
    r1 = st.columns(4)
    r1[0].markdown(kpi(t("soil_moist"), f"{root * 100:.0f} %", status, hero=True, spark=_sp_soil), unsafe_allow_html=True)
    r1[1].markdown(kpi(t("temp"), f"{temp} °C", t("feels", v=cur["apparent_temperature"]), spark=_sp_temp), unsafe_allow_html=True)
    r1[2].markdown(kpi(t("humidity"), f"{humidity} %"), unsafe_allow_html=True)
    r1[3].markdown(kpi(t("rain_chance"), f"{rain_prob:.0f} %", spark=_sp_rain), unsafe_allow_html=True)

    st.write("")
    r2 = st.columns(4)
    r2[0].markdown(kpi(t("soil_temp"), f"{soil_temp} °C"), unsafe_allow_html=True)
    r2[1].markdown(kpi(t("wind"), f"{wind} km/h"), unsafe_allow_html=True)
    r2[2].markdown(kpi(t("uv_l"), f"{uv}"), unsafe_allow_html=True)
    r2[3].markdown(kpi(t("et_l"), f"{et0_today:.1f} mm", spark=_sp_et), unsafe_allow_html=True)

    # ---- 7-day outlook strip ----
    st.markdown(f'<div class="sec">📅 {esc(L("7-day outlook & water plan", "7 நாள் வானிலை & நீர் திட்டம்"))}</div>', unsafe_allow_html=True)
    _badge = {"irrigate": ("💧 " + L("Irrigate", "நீர் பாய்ச்சு"), "irr"), "rain": ("🌧️ " + L("Rain – skip", "மழை – வேண்டாம்"), "rain"), "skip": ("✅ " + L("No water", "தேவையில்லை"), "")}
    _strip = []
    for _i in range(len(daily)):
        _ic = wx_icon(float(daily["precipitation_sum"].iloc[_i]), float(daily["precipitation_probability_max"].iloc[_i]), float(daily["temperature_2m_max"].iloc[_i]), tmax_eff)
        _bt, _bc = _badge[actions[_i]]
        _strip.append(
            f'<div class="wx"><div class="wx-d">{esc(day_labels[_i])}</div><div class="wx-i">{_ic}</div>'
            f'<div class="wx-t">{daily["temperature_2m_max"].iloc[_i]:.0f}° / {daily["temperature_2m_min"].iloc[_i]:.0f}°</div>'
            f'<div class="wx-r">🌧 {daily["precipitation_sum"].iloc[_i]:.1f} mm · {daily["precipitation_probability_max"].iloc[_i]:.0f}%</div>'
            f'<div class="wx-b {_bc}">{esc(_bt)}</div></div>'
        )
    st.markdown('<div class="wx-row">' + "".join(_strip) + "</div>", unsafe_allow_html=True)

    # ---- Satellite Eye ----
    st.markdown(f'<div class="sec">🛰️ {esc(L("Satellite Eye — your field from space", "செயற்கைக்கோள் பார்வை — விண்ணிலிருந்து உங்கள் வயல்"))}</div>', unsafe_allow_html=True)
    with st.spinner(L("Fetching the latest Sentinel-2 scene...", "சமீபத்திய Sentinel-2 படம் பெறப்படுகிறது...")):
        sat_home = get_satellite_analysis(lat, lon)
    if sat_home.get("ok"):
        _ch = sat_home["current"]
        _hi, _hl, _hlev = field_health_index(sat_home, root, mmin_adj, tmax_today, tmax_eff)
        _prof = crop_specific_profile(crop_name, crop_group_of, crop)
        e1, e2 = st.columns([1.55, 1])
        with e1:
            st.markdown(sat_tile_html(_ch.get("rgb"), place_label, _ch["date"], _ch["cloud"], _ch.get("ndvi_median"),
                                      [("NDMI", f"{_ch['ndmi_median']:.2f}" if _finite(_ch.get('ndmi_median')) else "N/A"), ("Stress", f"{sat_home['score']}/100")]),
                        unsafe_allow_html=True)
        with e2:
            with st.container(border=True):
                st.plotly_chart(hc_gauge(_hi, L("Field Health Index", "வயல் ஆரோக்கிய குறியீடு"), 215), use_container_width=True)
                st.markdown(f'<div style="text-align:center"><span class="chip">{esc(_hl)}</span></div>', unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("**" + L("Crop health map", "பயிர் ஆரோக்கிய வரைபடம்") + "**")
                st.plotly_chart(ndvi_map_fig(_ch["ndvi"], 175), use_container_width=True)

        _cards = []
        _ph = satellite_growth_phase(sat_home)
        if _ph:
            _cards.append(insight_card(_ph[1], L("Growth phase (from space)", "வளர்ச்சி நிலை"), _ph[0], _ph[2], _ph[3]))
        _nd = _ch.get("ndre_median")
        if _finite(_nd):
            _lv, _tx = ("ok", "Good chlorophyll / nitrogen level") if _nd >= 0.35 else (("info", "Moderate — watch leaf colour") if _nd >= 0.20 else ("warn", "Low — check nutrition (soil test first)"))
            _cards.append(insight_card("🍃", L("Leaf chlorophyll (NDRE)", "இலை பச்சையம்"), f"{_nd:.2f}", _tx, _lv))
        _un = field_uniformity(_ch["ndvi"])
        if _un:
            _cards.append(insight_card("🧩", L("Field uniformity", "வயல் சீர்தன்மை"), _un[1], f"Variation {_un[0]:.0f}%", _un[2]))
        _cp = canopy_potential_index(sat_home)
        if _cp is not None:
            _cards.append(insight_card("📈", L("Canopy potential", "பயிர் வளம் குறியீடு"), f"{_cp}/100", "Peak greenness vs healthy reference (not tonnes)", "ok" if _cp >= 70 else "warn"))
        if _cards:
            st.markdown('<div class="ins-grid">' + "".join(_cards) + "</div>", unsafe_allow_html=True)
    else:
        st.info(L("Satellite scene not available right now — weather advice below still works.", "செயற்கைக்கோள் படம் இப்போது கிடைக்கவில்லை — கீழே உள்ள வானிலை ஆலோசனை செயல்படும்."))

    left, right = st.columns([1, 2])

    with left:
        st.markdown(f'<div class="sec">{esc(t("soil_moist"))}</div>', unsafe_allow_html=True)
        with st.container(border=True):
            limit_pct = mmin_adj * 100
            top = max(60, root * 100 + 10, limit_pct + 20)
            gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=round(root * 100, 1),
                    number={"suffix": " %"},
                    gauge={
                        "axis": {"range": [0, top]},
                        "bar": {"color": "#34D399"},
                        "steps": [
                            {"range": [0, limit_pct], "color": "rgba(239,68,68,.35)"},
                            {"range": [limit_pct, top], "color": "rgba(34,197,94,.30)"},
                        ],
                    },
                )
            )
            gauge.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(gauge, use_container_width=True)
            st.caption(t("limit", v=f"{limit_pct:.0f}"))

    with right:
        st.markdown(f'<div class="sec">{esc(t("advice_h"))}</div>', unsafe_allow_html=True)
        m_pct = f"{root * 100:.0f}"
        need_pct = f"{mmin_adj * 100:.0f}"
        out = []

        if rain2 >= 10:
            out.append(tile("info", t("h_water"), t("rain_skip", mm=f"{rain2:.0f}")))
        elif root < mmin_adj:
            if tmax_today >= tmax_eff:
                out.append(tile("bad", t("h_water"), t("irrigate_hot", m=m_pct, crop=crop_name, need=need_pct)))
            else:
                out.append(tile("warn", t("h_water"), t("irrigate", m=m_pct, crop=crop_name, need=need_pct)))
        else:
            out.append(tile("", t("h_water"), t("soil_ok", m=m_pct, crop=crop_name)))

        if tmax_today >= tmax_eff + 3:
            out.append(tile("bad", t("h_heat"), t("heat_extreme", t=tmax_today, crop=crop_name)))
        elif tmax_today >= tmax_eff:
            out.append(tile("warn", t("h_heat"), t("heat_high", t=tmax_today, crop=crop_name)))
        else:
            out.append(tile("", t("h_heat"), t("heat_ok", t=tmax_today, crop=crop_name)))

        if humidity >= 80 and 20 <= temp <= 32:
            out.append(tile("warn", t("h_pest"), t("fungal")))
        elif humidity <= 35 and temp >= 35:
            out.append(tile("warn", t("h_pest"), t("mites")))
        else:
            out.append(tile("", t("h_pest"), t("disease_ok")))

        if wind <= 15 and rain_prob < 30:
            out.append(tile("", t("h_spray"), t("spray_good")))
        else:
            out.append(tile("info", t("h_spray"), t("spray_bad")))

        if uv >= 8:
            out.append(tile("warn", t("h_uv"), t("uv", uv=uv)))
        if stage_key == "seedling":
            out.append(tile("info", t("h_young"), t("young_note")))
        if crop_group_of in DEEP_ROOT_GROUPS:
            out.append(tile("info", t("h_deep"), t("deep_note")))
        if crop[0] == "Sandalwood":
            out.append(tile("warn", t("h_sandal"), t("sandal_note")))

        st.markdown("".join(out), unsafe_allow_html=True)

# ================= TAB: Farmer Advisory (satellite-driven) =================
with tab_adv:
    st.markdown("## 👨‍🌾 " + L("Farmer Advisory — What the satellite says about my field", "விவசாயி ஆலோசனை — செயற்கைக்கோள் என் வயலைப் பற்றி என்ன சொல்கிறது"))
    st.caption(L("Plain-language insights from Sentinel-2 + weather. Every number is an indicator — confirm in the field before spending money.",
                 "Sentinel-2 + வானிலை அடிப்படையிலான எளிய விளக்கங்கள். செலவு செய்யும் முன் வயலில் நேரில் உறுதி செய்யுங்கள்."))
    sat_adv = get_satellite_analysis(lat, lon)
    if not sat_adv.get("ok"):
        st.warning(L("Satellite scene unavailable. Open the Satellite tab to see the error details.", "செயற்கைக்கோள் படம் கிடைக்கவில்லை. Satellite tab-ல் விவரம் பார்க்கலாம்."))
    else:
        ca = sat_adv["current"]
        prof_a = crop_specific_profile(crop_name, crop_group_of, crop)
        cards = []
        ph = satellite_growth_phase(sat_adv)
        if ph:
            cards.append(insight_card(ph[1], L("Growth phase", "வளர்ச்சி நிலை"), ph[0], ph[2], ph[3]))
        ndre_v = ca.get("ndre_median")
        if _finite(ndre_v):
            lv, tx = ("ok", "Leaves look nutrient-rich") if ndre_v >= 0.35 else (("info", "Moderate — compare with leaf colour") if ndre_v >= 0.20 else ("warn", "Low chlorophyll — do a soil test before adding fertiliser"))
            cards.append(insight_card("🍃", L("Leaf chlorophyll (NDRE)", "இலை பச்சையம் (NDRE)"), f"{ndre_v:.2f}", tx, lv))
        else:
            cards.append(insight_card("🍃", L("Leaf chlorophyll (NDRE)", "இலை பச்சையம் (NDRE)"), "N/A", "Red-edge band not available in this scene", "info"))
        evi_v = ca.get("evi_median")
        if _finite(evi_v):
            cards.append(insight_card("🌳", L("Canopy density (EVI)", "இலை அடர்த்தி (EVI)"), f"{evi_v:.2f}", "Higher = denser leaf cover", "ok" if evi_v >= 0.35 else "info"))
        un = field_uniformity(ca["ndvi"])
        if un:
            cards.append(insight_card("🧩", L("Field uniformity", "வயல் சீர்தன்மை"), un[1], f"Variation {un[0]:.0f}% across the imaged area", un[2]))
        brk = ndvi_class_breakdown(ca["ndvi"])
        if brk:
            bare = brk[0]["pct"]
            cards.append(insight_card("🟫", L("Bare / weak patches", "வெற்று / பலவீன பகுதி"), f"{bare + brk[1]['pct']:.0f}%", f"{bare:.0f}% almost bare soil", "ok" if bare + brk[1]['pct'] < 20 else "warn"))
        cp = canopy_potential_index(sat_adv)
        if cp is not None:
            cards.append(insight_card("📈", L("Canopy potential", "பயிர் வளம்"), f"{cp}/100", "Peak greenness vs healthy reference — not a tonnes/acre forecast", "ok" if cp >= 70 else "warn"))
        if ph and ph[0].startswith("Ripening") and _finite(ca.get("ndvi_median")) and ca["ndvi_median"] < 0.5:
            cards.append(insight_card("🚜", L("Harvest signal", "அறுவடை சமிக்ஞை"), "Approaching maturity", "Plan labour, drying and storage", "info"))
        try:
            age_days = (pd.Timestamp.now().normalize() - pd.to_datetime(ca["date"])).days
            cards.append(insight_card("🛰️", L("Satellite freshness", "படத்தின் புதுமை"), f"{age_days} days old", f"Scene {ca['date']} · cloud {ca['cloud']:.0f}%", "ok" if age_days <= 10 else "warn"))
        except Exception:
            pass
        st.markdown('<div class="ins-grid">' + "".join(cards) + "</div>", unsafe_allow_html=True)

        st.markdown(f'<div class="sec">📈 {esc(L("Crop growth curve", "பயிர் வளர்ச்சி வளைவு"))}</div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.plotly_chart(ndvi_trend_fig(sat_adv, prof_a["ndvi_min"], 340, L("Green health & plant water over recent satellite passes", "சமீபத்திய செயற்கைக்கோள் பதிவுகளில் பசுமை & தாவர நீர்")), use_container_width=True)
            st.caption(L("Green band = healthy range · red band = below this crop's warning level. A falling line before harvest time needs a field check.",
                         "பச்சை பகுதி = ஆரோக்கிய வரம்பு · சிவப்பு பகுதி = எச்சரிக்கை நிலை. அறுவடைக்கு முன் கோடு இறங்கினால் வயலை பாருங்கள்."))

        st.markdown(f'<div class="sec">🗺️ {esc(L("Where is the problem in my field?", "என் வயலில் பிரச்சனை எங்கே?"))}</div>', unsafe_allow_html=True)
        z1, z2 = st.columns([1.3, 1])
        with z1:
            with st.container(border=True):
                st.plotly_chart(class_map_fig(ca["ndvi"], 330), use_container_width=True)
                st.caption(L("🟫 bare · 🟧 weak · 🟩 moderate · 🌳 healthy (≈100 m window around the selected point)", "🟫 வெற்று · 🟧 பலவீனம் · 🟩 நடுத்தரம் · 🌳 ஆரோக்கியம் (தேர்ந்த இடத்தைச் சுற்றி ≈100 மீ)"))
        with z2:
            with st.container(border=True):
                if brk:
                    st.plotly_chart(class_donut(brk, 250), use_container_width=True)
                wq = weakest_quadrant(ca["ndvi"])
                if wq:
                    st.markdown(f"🔎 **{L('Scout first', 'முதலில் பார்க்க')}:** {wq[0]} {L('part of the image (weakest, NDVI', 'பகுதி (மிகக் குறைவு, NDVI')} {wq[1]:.2f}). {L('Strongest', 'சிறந்தது')}: {wq[2]} ({wq[3]:.2f}).")

        st.markdown(f'<div class="sec">🗓️ {esc(L("This week’s action calendar", "இந்த வார செயல் நாட்காட்டி"))}</div>', unsafe_allow_html=True)
        cal = []
        for i in range(len(daily)):
            wind_ok = float(daily["wind_speed_10m_max"].iloc[i]) <= 25 and float(daily["precipitation_probability_max"].iloc[i]) < 30
            todo = {"irrigate": "💧 Irrigate ~{:,.0f} L".format(litres_each[i]), "rain": "🌧️ Rain — skip irrigation", "skip": "✅ No irrigation"}[actions[i]]
            cal.append(f'<div class="wx"><div class="wx-d">{esc(day_labels[i])}</div><div class="wx-i">{wx_icon(float(daily["precipitation_sum"].iloc[i]), float(daily["precipitation_probability_max"].iloc[i]), float(daily["temperature_2m_max"].iloc[i]), tmax_eff)}</div>'
                       f'<div class="wx-r">{esc(todo)}</div><div class="wx-b {"irr" if wind_ok else ""}">{"🧴 Good spray day" if wind_ok else "🚫 Avoid spraying"}</div></div>')
        st.markdown('<div class="wx-row">' + "".join(cal) + "</div>", unsafe_allow_html=True)

        p1, p2 = st.columns(2)
        with p1:
            with st.container(border=True):
                st.markdown("**🛰️ " + L("Next satellite look at your field (approx.)", "அடுத்த செயற்கைக்கோள் பார்வை (தோராயமாக)") + "**")
                nxt = next_satellite_passes(ca["date"], 5, 3)
                st.write(" · ".join(nxt) if nxt else "—")
                st.caption(L("Sentinel-2 revisits about every 5 days; cloudy passes may be unusable. Sentinel-1 radar sees through clouds.", "Sentinel-2 சுமார் 5 நாட்களுக்கு ஒருமுறை வரும்; மேகம் இருந்தால் பயன்படாது. Sentinel-1 ரேடார் மேகத்தையும் ஊடுருவும்."))
        with p2:
            with st.container(border=True):
                st.markdown("**📞 " + L("Farmer helplines", "விவசாயி உதவி எண்கள்") + "**")
                st.write(L("Kisan Call Centre: **1800-180-1551** · Crop-insurance helpline: **14447**", "கிசான் கால் சென்டர்: **1800-180-1551** · பயிர் காப்பீடு உதவி: **14447**"))
                st.caption(L("For crop loss from flood/hail/cyclone, inform the insurer within 72 hours.", "வெள்ளம்/ஆலங்கட்டி/புயல் இழப்புக்கு 72 மணி நேரத்தில் காப்பீட்டாளருக்கு தெரிவிக்கவும்."))

    st.markdown(f'<div class="sec">🏛️ {esc(L("Schemes & market links for farmers", "விவசாயிகளுக்கான திட்டங்கள் & சந்தை இணைப்புகள்"))}</div>', unsafe_allow_html=True)
    sc = st.columns(3)
    links = [("PM-KISAN", "https://pmkisan.gov.in/"), ("PMFBY Crop Insurance", "https://pmfby.gov.in/"), ("Soil Health Card", "https://soilhealth.dac.gov.in/"),
             ("e-NAM Market", "https://enam.gov.in/"), ("Agmarknet Prices", "https://agmarknet.gov.in/"), ("TN Agrisnet", "https://tnagrisnet.tn.gov.in/")]
    for i, (nm, url) in enumerate(links):
        sc[i % 3].link_button(nm, url, use_container_width=True)

# ================= TAB: Alert Center (Tamil voice + WhatsApp/SMS) =================
with tab_alert:
    st.markdown("## 📣 " + L("Alert Center — message, voice & WhatsApp for the farmer", "எச்சரிக்கை மையம் — செய்தி, குரல், WhatsApp"))
    st.caption(L("Turns today’s satellite + weather analysis into a short message a farmer can read, hear in Tamil, or receive on WhatsApp/SMS.",
                 "இன்றைய செயற்கைக்கோள் + வானிலை ஆய்வை, விவசாயி படிக்க / தமிழில் கேட்க / WhatsApp-SMS-ல் பெற சுருக்கமான செய்தியாக மாற்றும்."))
    st.markdown("""<style>
    .wa-chat{background:#0B141A;border:1px solid rgba(255,255,255,.1);border-radius:22px;padding:18px;background-image:radial-gradient(rgba(255,255,255,.04) 1px,transparent 1px);background-size:18px 18px;}
    .wa-bub{background:#005C4B;color:#E9EDEF;border-radius:14px 14px 4px 14px;padding:10px 13px;max-width:92%;margin-left:auto;font-size:.9rem;line-height:1.5;box-shadow:0 1px 2px rgba(0,0,0,.4);}
    .wa-meta{text-align:right;font-size:.68rem;color:#8FB5AC;margin-top:4px;}
    .wa-head{display:flex;align-items:center;gap:10px;color:#E9EDEF;font-weight:700;margin-bottom:12px;}
    .wa-av{background:#25D366;border-radius:50%;width:34px;height:34px;display:flex;align-items:center;justify-content:center;}
    </style>""", unsafe_allow_html=True)

    sat_al = get_satellite_analysis(lat, lon)
    health_v, health_l = None, ""
    if sat_al.get("ok"):
        health_v, health_l, _ = field_health_index(sat_al, root, mmin_adj, tmax_today, tmax_eff)
    s1, s2 = st.columns([1, 1.25])
    with s1:
        with st.container(border=True):
            st.markdown("**⚙️ " + L("Message settings", "செய்தி அமைப்பு") + "**")
            al_lang = st.radio(L("Message language", "செய்தி மொழி"), ["தமிழ்", "English"], index=0 if LANG == 1 else 1, horizontal=True, key="al_lang")
            all_sec = {"water": "💧 Water", "heat": "🔥 Heat", "pest": "🐛 Pest watch", "spray": "🧴 Spray day", "sat": "🛰️ Satellite health", "flood": "🌊 Flood"}
            chosen = st.multiselect(L("Include", "சேர்க்க"), list(all_sec), default=list(all_sec), format_func=lambda k: all_sec[k], key="al_sections")
            farmer = st.text_input(L("Farmer name (optional)", "விவசாயி பெயர் (விருப்பம்)"), "", key="al_name")
            phone = st.text_input(L("Phone with country code", "நாட்டு குறியீட்டுடன் எண்"), "+91", key="al_phone", help="Example: +919876543210")
    ctx = dict(place=str(place_label).replace("📍", "").strip(), crop=crop_name, root_pct=float(root * 100), moist_min_pct=float(mmin_adj * 100),
               tmax=float(tmax_today), tmax_lim=float(tmax_eff), rain2=float(rain2), rain_prob=float(rain_prob), humidity=float(humidity),
               temp=float(temp), wind=float(wind), litres=float(litres_each[0]), health=health_v, health_label=health_l,
               flood=st.session_state.get("flood_level"), sections=chosen or ["water"])
    lcode = "ta" if al_lang == "தமிழ்" else "en"
    msg = compose_alert(lcode, ctx)
    if farmer.strip():
        msg = (("வணக்கம் " if lcode == "ta" else "Hello ") + farmer.strip() + ",\n") + msg
    with s2:
        st.markdown(
            '<div class="wa-chat"><div class="wa-head"><div class="wa-av">🌾</div>Hyperclimate</div>'
            f'<div class="wa-bub">{esc(msg).replace(chr(10), "<br>")}<div class="wa-meta">{datetime.now().strftime("%H:%M")} ✓✓</div></div></div>',
            unsafe_allow_html=True)

    st.markdown(f'<div class="sec">🔊 {esc(L("Tamil voice message", "தமிழ் குரல் செய்தி"))}</div>', unsafe_allow_html=True)
    with st.container(border=True):
        spoken = voice_text(msg)
        v1, v2 = st.columns(2)
        if v1.button("🔊 " + L("Generate voice (MP3)", "குரல் உருவாக்கு (MP3)"), key="al_voice", use_container_width=True):
            try:
                st.session_state.al_mp3 = make_voice_mp3(spoken, lcode)
            except ImportError:
                st.session_state.al_mp3 = None
                st.warning("Install once:  python -m pip install gTTS")
            except Exception as e:
                st.session_state.al_mp3 = None
                st.warning(f"Voice service unavailable: {type(e).__name__}: {e}. Use the browser voice button instead.")
        with v2:
            import streamlit.components.v1 as components
            js_text = spoken.replace("\\", " ").replace("`", " ").replace('"', " ")
            components.html(
                f'<button onclick="var u=new SpeechSynthesisUtterance(`{js_text}`);u.lang=\'{"ta-IN" if lcode == "ta" else "en-IN"}\';u.rate=.92;speechSynthesis.cancel();speechSynthesis.speak(u);" '
                'style="width:100%;padding:9px;border-radius:12px;border:1px solid rgba(52,211,153,.4);background:rgba(52,211,153,.14);color:#D1FAE5;font-weight:700;cursor:pointer;font-family:sans-serif">'
                '🗣️ Browser voice (no install)</button>', height=48)
        if st.session_state.get("al_mp3"):
            st.audio(st.session_state.al_mp3, format="audio/mp3")
            st.download_button("⬇️ MP3", st.session_state.al_mp3, file_name="hyperclimate_alert.mp3", mime="audio/mpeg")
        st.caption(L("MP3 uses Google text-to-speech (needs internet). Browser voice needs a Tamil voice on the phone/PC — most Android phones have it.",
                     "MP3 Google text-to-speech மூலம் (இணையம் தேவை). Browser குரலுக்கு போனில் தமிழ் குரல் வேண்டும் — பெரும்பாலான Android போன்களில் உள்ளது."))

    st.markdown(f'<div class="sec">📲 {esc(L("Send to the farmer", "விவசாயிக்கு அனுப்பு"))}</div>', unsafe_allow_html=True)
    digits = re.sub(r"\D", "", phone)
    wa_url = f"https://wa.me/{digits}?text={quote(msg)}" if len(digits) >= 10 else f"https://wa.me/?text={quote(msg)}"
    sms_url = f"sms:+{digits}?body={quote(msg)}" if len(digits) >= 10 else f"sms:?body={quote(msg)}"
    with st.container(border=True):
        st.markdown("**" + L("1 · One-tap share (no account needed)", "1 · ஒரு தொடுதல் பகிர்வு (கணக்கு தேவையில்லை)") + "**")
        b1, b2, b3 = st.columns(3)
        b1.link_button("🟢 WhatsApp", wa_url, use_container_width=True)
        b2.markdown(f'<a href="{sms_url}" style="display:block;text-align:center;padding:.45rem;border-radius:12px;border:1px solid rgba(52,211,153,.35);background:rgba(52,211,153,.12);color:#D1FAE5;font-weight:700;text-decoration:none">💬 SMS</a>', unsafe_allow_html=True)
        b3.download_button("📄 .txt", msg.encode("utf-8"), file_name="hyperclimate_alert.txt", mime="text/plain", use_container_width=True)
        st.code(msg, language=None)
    with st.container(border=True):
        st.markdown("**" + L("2 · Automatic send (Twilio WhatsApp / SMS)", "2 · தானியங்கி அனுப்புதல் (Twilio WhatsApp / SMS)") + "**")
        ch = st.radio("Channel", ["whatsapp", "sms"], horizontal=True, key="al_channel", format_func=lambda x: "WhatsApp" if x == "whatsapp" else "SMS")
        if st.button("🚀 " + L("Send now", "இப்போது அனுப்பு"), key="al_send", type="primary"):
            okk, info_ = twilio_send(phone, msg, ch)
            st.session_state.setdefault("al_log", []).append({"Time": datetime.now().strftime("%d %b %H:%M"), "To": phone, "Channel": ch, "Result": info_})
            (st.success if okk else st.error)(info_)
        with st.expander("🔧 " + L("One-time Twilio setup", "ஒருமுறை Twilio அமைப்பு")):
            st.markdown("Create `.streamlit/secrets.toml` (never commit it to GitHub):")
            st.code('TWILIO_SID = "ACxxxxxxxx"\nTWILIO_TOKEN = "xxxxxxxx"\nTWILIO_WHATSAPP_FROM = "+14155238886"   # Twilio WhatsApp sandbox number\nTWILIO_SMS_FROM = "+1xxxxxxxxxx"', language="toml")
            st.caption("WhatsApp sandbox: the farmer must first send the join code shown in your Twilio console. SMS to Indian numbers needs sender/DLT registration — WhatsApp is easier for a college demo.")
    with st.container(border=True):
        st.markdown("**" + L("3 · Farmers CSV — alert many farmers at once", "3 · விவசாயிகள் CSV — பலருக்கு ஒரே நேரத்தில்") + "**")
        st.caption(L("Upload a CSV, preview every message, then send. Each farmer gets weather-based advice for their own lat/lon (same rules as the scheduled worker).",
                     "CSV பதிவேற்றி, ஒவ்வொரு செய்தியையும் பார்த்த பின் அனுப்புங்கள். ஒவ்வொரு விவசாயிக்கும் அவரவர் இடத்தின் வானிலை அடிப்படையில் ஆலோசனை."))
        bu1, bu2 = st.columns([2, 1])
        bulk_up = bu1.file_uploader(L("farmers.csv", "farmers.csv"), type=["csv"], key="bulk_csv")
        bu2.download_button("⬇️ " + L("Sample CSV", "மாதிரி CSV"), hc_bulk_sample_csv(), file_name="farmers_sample.csv", mime="text/csv", use_container_width=True)
        bu2.caption("name, phone, lat, lon, crop (required) · kc, heat_limit, moist_min, acres, lang, channel, place (optional)")
        if bulk_up is not None:
            try:
                bdf = pd.read_csv(bulk_up, dtype=str, encoding="utf-8-sig").fillna("")
                bdf.columns = [str(c_).strip().lower() for c_ in bdf.columns]
            except Exception as e:
                bdf = None
                st.error(f"CSV: {type(e).__name__}: {e}")
            if bdf is not None:
                miss = [c_ for c_ in HC_BULK_REQUIRED if c_ not in bdf.columns]
                if miss:
                    st.error(L(f"Missing columns: {', '.join(miss)}", f"இந்த நெடுவரிசைகள் இல்லை: {', '.join(miss)}"))
                else:
                    st.dataframe(bdf, hide_index=True, use_container_width=True)
                    only_att = st.checkbox(L("Only farmers who need attention today", "இன்று கவனம் தேவைப்படும் விவசாயிகளுக்கு மட்டும்"), True, key="bulk_only")
                    pb1, pb2 = st.columns(2)
                    if pb1.button("👁️ " + L("Preview messages (dry run)", "செய்திகளை முன்னோட்டம்"), key="bulk_prev", use_container_width=True):
                        with st.spinner(L("Fetching weather for each farmer...", "ஒவ்வொரு விவசாயிக்கும் வானிலை பெறப்படுகிறது...")):
                            st.session_state.bulk_items = hc_bulk_prepare(bdf, only_att)
                    items = st.session_state.get("bulk_items")
                    if items:
                        ready = [x for x in items if x["status"] == "ready"]
                        st.dataframe(pd.DataFrame([{"Farmer": x["name"], "Phone": x["phone"], "Channel": x["channel"], "Lang": x["lang"],
                                                    "Status": {"ready": "✅ Ready", "skip": "⏭️ Skip", "error": "❌ Error"}[x["status"]], "Note": x["info"]} for x in items]),
                                     hide_index=True, use_container_width=True)
                        for x in ready[:20]:
                            with st.expander(f"{x['name']} · {x['phone']} · {x['channel']}"):
                                st.code(x["message"], language=None)
                        if ready:
                            ok_send = st.checkbox(L(f"I confirm sending {len(ready)} message(s)", f"{len(ready)} செய்திகள் அனுப்ப உறுதி"), key="bulk_ok")
                            if pb2.button("🚀 " + L(f"Send to {len(ready)} farmer(s)", f"{len(ready)} பேருக்கு அனுப்பு"), key="bulk_send", type="primary",
                                          use_container_width=True, disabled=not ok_send):
                                prog = st.progress(0.0)
                                for n_, x in enumerate(ready, 1):
                                    okk, info_ = twilio_send(x["phone"], x["message"], x["channel"])
                                    st.session_state.setdefault("al_log", []).append({"Time": datetime.now().strftime("%d %b %H:%M"), "To": x["phone"], "Channel": x["channel"], "Result": f"{x['name']}: {info_}"})
                                    prog.progress(n_ / len(ready))
                                    if not okk and "secrets not configured" in info_:
                                        st.error(info_)
                                        break
                                st.success(L("Done — see the send log below.", "முடிந்தது — கீழே அனுப்பிய பதிவு."))
                        else:
                            st.info(L("No farmer needs a message right now.", "இப்போது யாருக்கும் செய்தி தேவையில்லை."))
    if st.session_state.get("al_log"):
        st.dataframe(pd.DataFrame(st.session_state.al_log), hide_index=True, use_container_width=True)

    st.markdown(f'<div class="sec">🚦 {esc(L("Alert triggers right now", "இப்போதைய எச்சரிக்கை நிலை"))}</div>', unsafe_allow_html=True)
    trig = [
        ("💧 Soil moisture", f"{root*100:.0f}% vs min {mmin_adj*100:.0f}%", root < mmin_adj),
        ("🌧️ Rain next 2 days", f"{rain2:.0f} mm", rain2 >= 10),
        ("🔥 Heat", f"{tmax_today:.0f}°C vs limit {tmax_eff:.0f}°C", tmax_today >= tmax_eff),
        ("🐛 Fungal weather", f"RH {humidity:.0f}%, {temp:.0f}°C", humidity >= 80 and 20 <= temp <= 32),
        ("🛰️ Field health", f"{health_v}/100" if health_v is not None else "n/a", health_v is not None and health_v < 45),
        ("🌊 Flood radar", str(st.session_state.get("flood_level") or "not scanned"), st.session_state.get("flood_level") in ("bad", "warn")),
    ]
    st.dataframe(pd.DataFrame([{"Trigger": a, "Value": b, "Status": "🟠 Active" if c_ else "🟢 Normal"} for a, b, c_ in trig]), hide_index=True, use_container_width=True)
    st.caption(L("For automatic daily messages without opening this page, use the scheduled worker script (hyperclimate_alert_worker.py).", "இந்த பக்கத்தை திறக்காமல் தினமும் தானாக அனுப்ப hyperclimate_alert_worker.py பயன்படுத்தலாம்."))

# ================= TAB 2: Irrigation plan =================
with tab_irrig:
    st.markdown("## 💧 Water Management — Where Should I Irrigate?")
    st.caption("Soil-moisture estimate, rainfall, ET₀ and crop-stage based irrigation guidance")
    st.markdown(f'<div class="sec">{esc(t("water_h"))}</div>', unsafe_allow_html=True)
    k = st.columns(5)
    k[0].markdown(kpi(t("need7"), f"{need_total:.0f} mm", hero=True), unsafe_allow_html=True)
    k[1].markdown(kpi(t("rain7"), f"{rain_total:.0f} mm"), unsafe_allow_html=True)
    k[2].markdown(kpi(t("irrig_days"), f"{irrig_days}"), unsafe_allow_html=True)
    k[3].markdown(kpi(t("litres", acres=acres), f"{total_litres:,.0f} L"), unsafe_allow_html=True)
    k[4].markdown(kpi(t("pump_h"), t("hours", h=f"{pump_hours:.1f}")), unsafe_allow_html=True)
    st.caption(t("water_caption"))

    plan = pd.DataFrame({
        t("col_date"): day_labels,
        t("col_max"): daily["temperature_2m_max"].round(1),
        t("col_min"): daily["temperature_2m_min"].round(1),
        t("col_rain"): daily["precipitation_sum"].round(1),
        t("col_prob"): daily["precipitation_probability_max"].round(0),
        t("col_need"): daily["need"].round(1),
        t("col_action"): [t("act_" + a) for a in actions],
        t("col_litres"): [round(x) for x in litres_each],
    })
    with st.container(border=True):
        st.dataframe(plan, hide_index=True)
        st.download_button(
            t("download"),
            plan.to_csv(index=False).encode("utf-8-sig"),
            file_name="irrigation_plan.csv",
            mime="text/csv",
        )

    c_left, c_right = st.columns([2, 1])
    with c_left:
        with st.container(border=True):
            lit = pd.DataFrame({"day": day_labels, "litres": [round(x) for x in litres_each]})
            figl = px.bar(lit, x="day", y="litres", title=t("litres_chart"),
                          labels={"day": t("date"), "litres": "L"},
                          color_discrete_sequence=["#16A34A"])
            st.plotly_chart(style_fig(figl, 300), use_container_width=True)
    with c_right:
        st.markdown(f'<div class="sec" style="margin-top:0">{esc(t("spray_h"))}</div>', unsafe_allow_html=True)
        good_days = [
            day_labels[i]
            for i in range(len(daily))
            if daily["wind_speed_10m_max"].iloc[i] <= 25
            and daily["precipitation_probability_max"].iloc[i] < 30
        ]
        if good_days:
            st.markdown(tile("", t("h_spray"), t("spray_days", d=", ".join(good_days))), unsafe_allow_html=True)
        else:
            st.markdown(tile("info", t("h_spray"), t("no_spray")), unsafe_allow_html=True)

# ================= TAB 3: Charts =================
with tab_charts:
    st.markdown("## 🌦️ Weather & Normal Conditions")
    st.caption("Current weather, NASA POWER history and crop-month baseline")
    ch1, ch2 = st.columns(2)

    with ch1:
        with st.container(border=True):
            tt = daily[["time", "temperature_2m_max", "temperature_2m_min"]].rename(
                columns={"temperature_2m_max": t("max"), "temperature_2m_min": t("min")}
            )
            fig1 = px.line(
                tt.melt("time", var_name=t("type"), value_name="°C"),
                x="time", y="°C", color=t("type"), markers=True, title=t("c_temp"),
                labels={"time": t("date")},
                color_discrete_map={t("max"): "#F97316", t("min"): "#3B82F6"},
            )
            st.plotly_chart(style_fig(fig1), use_container_width=True)

    with ch2:
        with st.container(border=True):
            hourly["date"] = hourly["time"].dt.date
            sm = hourly.groupby("date")[["soil_moisture_3_to_9cm", "soil_moisture_9_to_27cm"]].mean().reset_index()
            sm[t("soil_pct")] = sm[["soil_moisture_3_to_9cm", "soil_moisture_9_to_27cm"]].mean(axis=1) * 100
            fig2 = px.line(
                sm, x="date", y=t("soil_pct"), markers=True, title=t("c_soil"),
                labels={"date": t("date")}, color_discrete_sequence=["#16A34A"],
            )
            fig2.add_hline(y=mmin_adj * 100, line_dash="dash", line_color="red")
            st.plotly_chart(style_fig(fig2), use_container_width=True)

    with st.container(border=True):
        wb = daily[["time", "et0_fao_evapotranspiration", "precipitation_sum"]].rename(
            columns={"et0_fao_evapotranspiration": t("et0"), "precipitation_sum": t("rain_mm")}
        )
        fig3 = px.bar(
            wb.melt("time", var_name=t("type"), value_name="mm"),
            x="time", y="mm", color=t("type"), barmode="group", title=t("c_water"),
            labels={"time": t("date")},
            color_discrete_map={t("et0"): "#F59E0B", t("rain_mm"): "#3B82F6"},
        )
        st.plotly_chart(style_fig(fig3), use_container_width=True)

# ================= TAB 4: Satellite analysis =================
with tab_sat:
    st.markdown("## 🛰️ Satellite Crop Health — What is the Field Telling Us?")
    st.caption("Latest usable satellite observation + crop/water condition + scene catalogue")
    st.markdown(chips(['🌱 Crop Green Health', '💧 Plant Water Status', '🌊 Surface Wetness', '📉 Crop Health Change — Current vs Normal', '🛰️ Latest Satellite Observation']), unsafe_allow_html=True)
    st.caption("This is real satellite analysis, not only the map background. The selected place is analysed using Sentinel-2 Level-2A surface-reflectance imagery.")

    if st.button("🔄 Get latest satellite analysis", key="sat_refresh"):
        get_satellite_analysis.clear()
        st.rerun()

    with st.spinner("Checking satellite scenes and calculating crop health, plant water status and surface wetness..."):
        sat = get_satellite_analysis(lat, lon)

    if not sat.get("ok"):
        st.error("Satellite analysis could not run.")
        st.code(sat.get("error", "Unknown error"))
        st.info("Install once: python -m pip install pystac-client planetary-computer rasterio scikit-learn reportlab")
    else:
        cur_sat = sat["current"]
        score = sat["score"]
        if score >= 60:
            risk_text = "🔴 High satellite stress risk"
        elif score >= 30:
            risk_text = "🟠 Moderate satellite stress risk"
        else:
            risk_text = "🟢 Low satellite stress risk"

        a, b, c, d = st.columns(4)
        a.metric("🌱 Crop Green Health", f"{cur_sat['ndvi_median']:.3f}")
        b.metric("💧 Plant Water Status", f"{cur_sat['ndmi_median']:.3f}")
        c.metric("🌊 Surface Wetness", f"{cur_sat['ndwi_median']:.3f}")
        d.metric("Stress score", f"{score}/100")
        st.caption(f"{risk_text} · Scene date: {cur_sat['date']} · Cloud cover: {cur_sat['cloud']:.1f}%")

        if cur_sat.get("rgb") is not None:
            st.markdown("#### 🛰️ True-colour satellite view")
            st.image(cur_sat["rgb"], use_container_width=True)

        st.markdown("#### 📊 What do these satellite measurements mean?")
        st.markdown('''<div class="hc-definition"><b>🌱 Crop Green Health</b><br>Shows how green and vigorous the vegetation is.</div><div class="hc-definition"><b>💧 Plant Water Status</b><br>Shows whether vegetation is showing signs of water stress.</div><div class="hc-definition"><b>🌊 Surface Wetness</b><br>Helps indicate water/wetness conditions around the observed area.</div><div class="hc-definition"><b>🌡️ Land Surface Temperature</b><br>Shows how hot the land surface is.</div><div class="hc-definition"><b>📡 Radar Surface Signal</b><br>Radar-based monitoring that can work even when clouds affect optical images.</div>''', unsafe_allow_html=True)
        st.info("🧠 " + sat["reason"])

        hist = sat["history"]
        if hist:
            hist_df = pd.DataFrame([{
                "date": x["date"],
                "Crop Green Health": x["ndvi_median"],
                "Plant Water Status": x["ndmi_median"],
                "🌊 Surface Wetness": x["ndwi_median"],
            } for x in [cur_sat] + hist]).sort_values("date")
            st.markdown("#### 📈 Recent satellite trend")
            long_df = hist_df.melt("date", var_name="Measurement", value_name="Value")
            fig_sat = px.line(long_df, x="date", y="Value", color="Measurement", markers=True, title="Recent satellite condition history")
            st.plotly_chart(style_fig(fig_sat, 380), use_container_width=True)

        st.caption(f"Scene: {cur_sat['id']} · Search area: approximately 100 m around the selected location.")
        st.markdown("#### 🛰️ Satellite scene catalogue")
        cat=pd.DataFrame([{"Date":x["date"],"Satellite":"Sentinel-2","Cloud %":round(x.get("cloud",np.nan),1),"Crop Green Health":round(x.get("ndvi_median",np.nan),3),"Plant Water Status":round(x.get("ndmi_median",np.nan),3)} for x in [cur_sat]+hist])
        st.dataframe(cat, use_container_width=True, hide_index=True)


# ================= TAB 5: Land Intelligence =================
with tab_land:
    st.markdown("## 🌍 Your Field — Land, Area & Terrain")
    st.caption("Field boundary, area, terrain, land-cover indicators and historical environmental baseline")
    st.markdown(chips(['📐 Field Boundary & Area', '⛰️ Land Height & Slope', '🌳 Land Type & Vegetation Map', '📅 What is Normal for This Place?']), unsafe_allow_html=True)
    st.caption("One selected land parcel → satellite, weather, terrain, vegetation, தண்ணீர் பற்றாக்குறை, heat, anomaly and management indicators.")

    load_land = st.button("🚀 Load advanced land intelligence", type="primary", key="load_land_intel")
    if load_land:
        st.session_state.advanced_land_loaded = True

    if not st.session_state.get("advanced_land_loaded", False):
        st.info("Click **Load advanced land intelligence** to fetch NASA POWER history, terrain and Landsat thermal information.")
    else:
        with st.spinner("Collecting NASA POWER + terrain + thermal satellite information..."):
            try:
                nasa_df = nasa_power_history(lat, lon, days=365)
            except Exception as e:
                nasa_df = pd.DataFrame()
                st.warning(f"NASA POWER history unavailable right now: {type(e).__name__}: {e}")
            try:
                elevation = get_elevation(lat, lon)
            except Exception:
                elevation = float("nan")
            try:
                lst_data = landsat_lst(lat, lon, days_back=180)
            except Exception as e:
                lst_data = {"ok":False,"error":str(e)}

        # Persist small outputs so other tabs can reuse them without another request.
        st.session_state.nasa_df = nasa_df
        st.session_state.elevation = elevation
        st.session_state.lst_data = lst_data

        sat_local = get_satellite_analysis(lat, lon)
        c_sat = sat_local.get("current") if sat_local.get("ok") else {}
        ndvi = c_sat.get("ndvi_median", float("nan"))
        ndmi = c_sat.get("ndmi_median", float("nan"))
        ndwi = c_sat.get("ndwi_median", float("nan"))
        sat_score = sat_local.get("score", 0) if sat_local.get("ok") else 0
        lc = land_cover_indicator(ndvi, ndwi)
        health = satellite_health_class(ndvi, ndmi, sat_score)

        k = st.columns(6)
        k[0].metric("🌱 Crop Green Health", f"{ndvi:.3f}" if _finite(ndvi) else "N/A")
        k[1].metric("💧 Plant Water Status", f"{ndmi:.3f}" if _finite(ndmi) else "N/A")
        k[2].metric("🌊 Surface Wetness", f"{ndwi:.3f}" if _finite(ndwi) else "N/A")
        k[3].metric("🌡️ Land Temperature", f"{lst_data['lst']:.1f} °C" if lst_data.get("ok") else "N/A")
        k[4].metric("நில உயரம்", f"{elevation:.1f} m" if _finite(elevation) else "N/A")
        k[5].metric("Satellite health", health)

        st.markdown("#### 🧭 Land profile")
        p1, p2, p3 = st.columns(3)
        p1.info(f"**Indicative land cover:** {lc}\n\nThis is an index-based indicator, not a certified LULC classification.")
        p2.info(f"**பயிர் / தாவர வளர்ச்சி condition:** {health}\n\nCrop green health and plant water status are compared with recent satellite scenes.")
        p3.info(f"**Terrain:** {terrain_class(elevation)}\n\nநில உயரம் source: global elevation service. For engineering-grade terrain, use an official DEM product.")

        clusters = land_cover_clusters(sat_local)
        if clusters is not None:
            st.markdown("#### 🗺️ Land type zones — vegetation / wet / bare areas")
            lcfig=px.imshow(clusters["labels"], aspect="auto", color_continuous_scale="Viridis", title="Unsupervised land-cover pattern (index clustering)")
            lcfig.update_layout(height=320, margin=dict(l=5,r=5,t=45,b=5), coloraxis_showscale=False)
            st.plotly_chart(lcfig, use_container_width=True)
            st.caption("This is an unsupervised spectral-index classification for project analysis; it is not an official ISRO LULC map.")

        st.markdown("#### 📐 Draw the actual field boundary")
        st.caption("Use rectangle or polygon on the satellite image. This makes the project plot-level instead of only point-level.")
        draw_result = field_boundary_map(lat, lon, place_label, key="advanced_field_boundary")
        drawings = draw_result.get("all_drawings") if draw_result else None
        polygon = extract_last_polygon(drawings)
        area_m2 = polygon_area_m2(polygon) if polygon else float("nan")
        if _finite(area_m2) and area_m2 > 0:
            st.session_state.field_area_m2 = area_m2
            st.session_state.field_polygon = polygon
            a1, a2, a3 = st.columns(3)
            a1.metric("நிலத்தின் பரப்பளவு", f"{area_m2:,.1f} m²")
            a2.metric("Acres", f"{area_m2/4046.856:.3f}")
            a3.metric("Hectares", f"{area_m2/10000:.3f}")

        if not nasa_df.empty:
            st.markdown("#### 🌦️ 1-year NASA POWER baseline")
            nasa_df["temp_anom"] = nasa_df["temp"] - nasa_df.groupby("month")["temp"].transform("median")
            nasa_df["rain_month_median"] = nasa_df.groupby("month")["rain"].transform("median")
            nasa_df["rain_anom_pct"] = np.where(nasa_df["rain_month_median"] > 0, (nasa_df["rain"] - nasa_df["rain_month_median"]) / nasa_df["rain_month_median"] * 100, np.nan)
            n1, n2, n3, n4 = st.columns(4)
            latest_n = nasa_df.iloc[-1]
            n1.metric("NASA temp", f"{latest_n['temp']:.1f} °C")
            n2.metric("NASA rain", f"{latest_n['rain']:.1f} mm")
            n3.metric("Temp anomaly", f"{latest_n['temp_anom']:+.1f} °C")
            n4.metric("Rain anomaly", f"{latest_n['rain_anom_pct']:+.0f}%" if _finite(latest_n['rain_anom_pct']) else "N/A")
            fign = px.line(nasa_df, x="date", y=["temp", "rain"], title="NASA POWER 365-day weather history")
            st.plotly_chart(style_fig(fign, 360), use_container_width=True)

        if lst_data.get("ok"):
            st.success(f"🌡️ Landsat thermal observation: {lst_data['lst']:.1f} °C on {lst_data['date']} (cloud {lst_data['cloud']:.1f}%).")
        else:
            st.warning("Landsat land-temperature data is unavailable for this run. Sentinel-2 is used for vegetation/water condition, while land temperature comes from thermal satellite data.")

# ================= TAB 6: Zone / anomaly / disaster maps =================
with tab_maps:
    st.markdown("## 🗺️ Field Maps — Health, Heat, Water & Risk")
    st.caption("Each map is shown as a separate analytical layer so the reason for stress is easy to understand.")
    st.markdown(chips(['🌱 Crop Green Health Map', '💧 Plant Water Stress Map', '🌡️ Land Temperature / Heat Stress Map', '📡 Radar Surface Monitoring', '🌊 Excess Water / Waterlogging Risk', '☀️ Dryness / Drought Risk', '🔲 Field Health Zones', '💦 Irrigation Priority — Where to Water First', '📅 Long-Term Crop Health Change', '⛰️ Slope & Terrain Risk']), unsafe_allow_html=True)
    st.caption("Satellite + weather + terrain data-வை சேர்த்து நிலத்தின் stress zones, drought/flood indicators மற்றும் irrigation priority-ஐ காட்டுகிறது.")
    sat_m=get_satellite_analysis(lat,lon)
    nasa_m=st.session_state.get("nasa_df",pd.DataFrame())
    lst_m=st.session_state.get("lst_data",{"ok":False})
    sar_m=sentinel1_sar_analysis(lat,lon,365)
    if sat_m.get("ok"):
        c=sat_m["current"]
        base=np.nanmedian([x["ndvi"] for x in sat_m.get("history",[]) if x.get("ndvi") is not None],axis=0) if sat_m.get("history") else np.nan
        ndvi_anom=c["ndvi"]-base if np.ndim(base)==2 else c["ndvi"]*np.nan
        ndmi=c["ndmi"]
        # Visual heatmaps: redder cells mean lower vegetation/water signal; this is an analytical raster, not a basemap.
        a,b=st.columns(2)
        with a:
            st.markdown("#### 🌱 Crop Green Health — பயிர் வளர்ச்சி வரைபடம்")
            fig=px.imshow(c["ndvi"],color_continuous_scale="RdYlGn",zmin=-0.2,zmax=0.9,aspect="auto",labels={"color":"Crop health"})
            fig.update_layout(height=330,margin=dict(l=5,r=5,t=35,b=5),title="பச்சை = நல்ல வளர்ச்சி • சிவப்பு = குறைவு")
            st.plotly_chart(fig,use_container_width=True)
        with b:
            st.markdown("#### 💧 Plant Water Status — தாவர தண்ணீர் நிலை")
            fig=px.imshow(ndmi,color_continuous_scale="BrBG",zmin=-0.5,zmax=0.5,aspect="auto",labels={"color":"Plant water status"})
            fig.update_layout(height=330,margin=dict(l=5,r=5,t=35,b=5),title="குறைந்த மதிப்பு = water-stress watch")
            st.plotly_chart(fig,use_container_width=True)
        if np.isfinite(ndvi_anom).any():
            st.markdown("#### 📉 Crop Health Change — வழக்கமான நிலை ஒப்பீடு")
            fig=px.imshow(ndvi_anom,color_continuous_scale="RdBu",zmin=-0.35,zmax=0.35,aspect="auto",labels={"color":"Change"})
            fig.update_layout(height=320,margin=dict(l=5,r=5,t=35,b=5),title="நீலம் = வளர்ச்சி குறைவு • சிவப்பு = அதிகரிப்பு")
            st.plotly_chart(fig,use_container_width=True)
        zones=zone_table(sat_m,crop_name,4)
        if not zones.empty:
            st.markdown("#### 🚜 Field zones — irrigation priority")
            st.dataframe(zones,use_container_width=True,hide_index=True)
            st.caption("Zone recommendation is a satellite-based priority indicator. Check actual soil moisture before irrigation.")
    else: st.warning("Satellite scene unavailable; advanced maps cannot be generated yet.")
    st.markdown("#### 📅 Multi-year satellite change detection")
    if st.button("🔎 Compare recent scene with previous years", key="multi_year_btn"):
        with st.spinner("Searching previous-year Sentinel-2 scenes..."):
            my=get_multiyear_satellite_analysis(lat,lon,years=3,cloud_max=35,limit=24)
        st.session_state.multi_year_result=my
    my=st.session_state.get("multi_year_result")
    if my and my.get("ok"):
        mb=my["baseline"]
        z=st.columns(4)
        z[0].metric("3-year Crop Health Change", f"{my['ndvi_anomaly']:+.3f}")
        z[1].metric("3-year Plant Water Change", f"{my['ndmi_anomaly']:+.3f}")
        z[2].metric("Normal Crop Health", f"{mb['ndvi']:.3f}")
        z[3].metric("Scenes used", f"{len(my['history'])}")
        st.dataframe(my["table"],use_container_width=True,hide_index=True)
    elif my and not my.get("ok"):
        st.warning(my.get("error","Multi-year comparison unavailable."))

    # Actual thermal/SAR raster views when the source scene exposes a usable array.
    if lst_m.get("ok") and lst_m.get("array") is not None:
        st.markdown("#### 🌡️ Land Temperature / Heat-Stress Map")
        lf=px.imshow(lst_m["array"],color_continuous_scale="Turbo",aspect="auto",labels={"color":"°C"},title="Landsat surface temperature")
        lf.update_layout(height=330,margin=dict(l=5,r=5,t=40,b=5))
        st.plotly_chart(lf,use_container_width=True)
    if sar_m.get("ok") and sar_m.get("vv_array") is not None:
        st.markdown("#### 📡 Radar Surface Signal Map")
        sf=px.imshow(sar_m["vv_array"],color_continuous_scale="RdBu",aspect="auto",labels={"color":"Radar signal"},title="Sentinel-1 VV backscatter")
        sf.update_layout(height=330,margin=dict(l=5,r=5,t=40,b=5))
        st.plotly_chart(sf,use_container_width=True)

    drought,flood,rain_a,temp_a=drought_flood_indicators(nasa_m,sat_m,lst_m,float(sar_m.get("vv_change_db",np.nan)) if sar_m.get("ok") else np.nan)
    st.markdown("#### 🌦️ Drought / flood / heat indicators")
    q=st.columns(4); q[0].metric("Drought risk",f"{drought}/100"); q[1].metric("Waterlogging risk",f"{flood}/100"); q[2].metric("Rain anomaly",f"{rain_a:+.0f}%"); q[3].metric("Temp anomaly",f"{temp_a:+.1f} °C")
    if lst_m.get("ok"): st.info(f"🌡️ Landsat heat observation: {lst_m['lst']:.1f} °C — {lst_m['date']}")
    if sar_m.get("ok"):
        st.markdown("#### 📡 Radar Monitoring")
        st.write(f"Latest radar signal: **{sar_m['current']['vv']:.1f} dB** · change from recent normal: **{sar_m['vv_change_db']:+.1f} dB** · {sar_m['current']['date']}")
    else: st.caption("Radar satellite data was not available for this run. Radar is useful when clouds affect normal optical satellite images.")
    st.markdown("#### 🗻 Terrain")
    elev=st.session_state.get("elevation",float("nan"))
    try: slope=get_terrain_slope(lat,lon)
    except Exception: slope=float("nan")
    st.session_state.terrain_slope=slope
    slope_txt=f"{slope:.2f}°" if _finite(slope) else "N/A"
    st.info(f"Elevation: {elev:.1f} m • Slope: {slope_txt} • Terrain: {terrain_class(elev,slope)}")

# ================= TAB: Flood Watch (Sentinel-1 radar) =================
with tab_flood:
    st.markdown("## 🌊 " + L("Flood Watch — radar sees water even through clouds", "வெள்ள கண்காணிப்பு — மேகத்தையும் ஊடுருவும் ரேடார்"))
    st.caption(L("Sentinel-1 radar change detection: water looks dark to radar. A pixel that is water now but was not water in earlier scenes = new flooding.",
                 "Sentinel-1 ரேடார் மாற்ற ஆய்வு: தண்ணீர் ரேடாரில் கருமையாக தெரியும். முன்பு இல்லாமல் இப்போது தண்ணீர் இருந்தால் = புதிய வெள்ளம்."))
    fc1, fc2, fc3 = st.columns([1, 1, 1])
    win_m = fc1.selectbox(L("Area around field", "வயலைச் சுற்றிய பரப்பு"), [300, 400, 600], index=1, format_func=lambda m: f"{2*m} m × {2*m} m", key="flood_win")
    water_thr = fc2.slider(L("Water threshold (dB)", "நீர் வரம்பு (dB)"), -22.0, -12.0, -16.0, 0.5, key="flood_thr")
    drop_thr = fc3.slider(L("Min. drop vs normal (dB)", "சாதாரணத்தை விட குறைவு (dB)"), 1.0, 6.0, 3.0, 0.5, key="flood_drop")
    if st.button("🛰️ " + L("Run flood scan", "வெள்ள ஸ்கேன் செய்"), type="primary", key="flood_run"):
        st.session_state.flood_scan = True
    if not st.session_state.get("flood_scan"):
        st.info(L("Press **Run flood scan** — it reads the latest Sentinel-1 scenes (takes ~20–60 s the first time).", "**வெள்ள ஸ்கேன் செய்** அழுத்துங்கள் — சமீபத்திய Sentinel-1 படங்களை படிக்கும் (முதல் முறை ~20–60 வினாடி)."))
    else:
        with st.spinner(L("Reading Sentinel-1 radar scenes...", "Sentinel-1 ரேடார் படங்கள் படிக்கப்படுகின்றன...")):
            stk = load_s1_stack(lat, lon, 150, win_m, 110, 8)
        if not stk.get("ok"):
            st.error(stk.get("error", "Radar data unavailable."))
        else:
            fr = flood_from_stack(stk, water_thr, drop_thr)
            if fr["new_pct"] >= 10:
                lvl, txt = "bad", L("FLOODING LIKELY", "வெள்ளம் வாய்ப்பு அதிகம்")
            elif fr["new_pct"] >= 2:
                lvl, txt = "warn", L("POSSIBLE FLOODING", "வெள்ளம் இருக்கலாம்")
            else:
                lvl, txt = "ok", L("NO FLOOD SIGNAL", "வெள்ள அறிகுறி இல்லை")
            st.session_state.flood_level = lvl
            st.markdown(f'<span class="flood-badge {lvl}">{esc(txt)}</span> &nbsp; <span class="small-muted">{esc(L("Latest radar scene", "சமீபத்திய ரேடார் படம்"))}: {fr["date"]} · {len(stk["scenes"])} {esc(L("scenes used", "படங்கள்"))}</span>', unsafe_allow_html=True)
            k = st.columns(4)
            k[0].markdown(kpi(L("💧 Water now", "💧 இப்போது நீர்"), f"{fr['water_pct']:.1f} %", f"{L('permanent', 'நிரந்தர')}: {fr['perm_pct']:.1f}%", hero=True), unsafe_allow_html=True)
            k[1].markdown(kpi(L("🌊 New flooding", "🌊 புதிய வெள்ளம்"), f"{fr['new_pct']:.1f} %", f"≈ {fr['new_ha']:.1f} ha of {fr['win_ha']:.0f} ha"), unsafe_allow_html=True)
            k[2].markdown(kpi(L("📉 Radar change", "📉 ரேடார் மாற்றம்"), f"{fr['chg_med']:+.1f} dB", L("median vs normal", "சாதாரணத்துடன்")), unsafe_allow_html=True)
            k[3].markdown(kpi(L("🌧️ Rain next 7 days", "🌧️ அடுத்த 7 நாள் மழை"), f"{rain_total:.0f} mm", L("forecast", "முன்னறிவிப்பு")), unsafe_allow_html=True)
            st.write("")
            m1, m2, m3 = st.columns(3)
            with m1:
                with st.container(border=True):
                    st.markdown("**" + L("Radar backscatter (VV, dB)", "ரேடார் பிரதிபலிப்பு (VV, dB)") + "**")
                    f1 = px.imshow(fr["cur"], color_continuous_scale="Greys_r", zmin=-25, zmax=0, aspect="equal")
                    f1.update_layout(height=270, margin=dict(l=0, r=0, t=4, b=0), coloraxis_colorbar=dict(thickness=8, len=.8))
                    f1.update_xaxes(visible=False); f1.update_yaxes(visible=False)
                    st.plotly_chart(f1, use_container_width=True)
            with m2:
                with st.container(border=True):
                    st.markdown("**" + L("Change vs normal (blue = wetter)", "சாதாரணத்துடன் மாற்றம் (நீலம் = ஈரம் அதிகம்)") + "**")
                    f2 = px.imshow(fr["change"], color_continuous_scale="RdBu", zmin=-8, zmax=8, aspect="equal")
                    f2.update_layout(height=270, margin=dict(l=0, r=0, t=4, b=0), coloraxis_colorbar=dict(thickness=8, len=.8))
                    f2.update_xaxes(visible=False); f2.update_yaxes(visible=False)
                    st.plotly_chart(f2, use_container_width=True)
            with m3:
                with st.container(border=True):
                    st.markdown("**" + L("Flood map", "வெள்ள வரைபடம்") + "**")
                    f3 = px.imshow(fr["mask"], color_continuous_scale=[[0, "#1F2A24"], [1/3, "#1F2A24"], [1/3, "#38BDF8"], [2/3, "#38BDF8"], [2/3, "#EF4444"], [1, "#EF4444"]],
                                   zmin=-0.5, zmax=2.5, aspect="equal")
                    f3.update_layout(height=270, margin=dict(l=0, r=0, t=4, b=0), coloraxis_showscale=False)
                    f3.update_xaxes(visible=False); f3.update_yaxes(visible=False)
                    st.plotly_chart(f3, use_container_width=True)
                    st.caption("⬛ " + L("land", "நிலம்") + " · 🟦 " + L("permanent water", "நிரந்தர நீர்") + " · 🟥 " + L("new flooding", "புதிய வெள்ளம்"))
            with st.container(border=True):
                sdf = fr["series"]
                fts = go.Figure()
                fts.add_trace(go.Bar(x=sdf["date"], y=sdf["Water %"], name="Water %", marker_color="rgba(56,189,248,.65)", yaxis="y2"))
                fts.add_trace(go.Scatter(x=sdf["date"], y=sdf["VV median (dB)"], name="VV median (dB)", mode="lines+markers", line=dict(color="#34D399", width=3)))
                fts.update_layout(title=L("Radar history of the field", "வயலின் ரேடார் வரலாறு"), yaxis=dict(title="dB"),
                                  yaxis2=dict(title="Water %", overlaying="y", side="right", showgrid=False), legend=dict(orientation="h", y=1.15))
                st.plotly_chart(style_fig(fts, 300), use_container_width=True)
            if lvl == "bad":
                st.error(L("Likely new flooding in the imaged area. Check drainage, move produce/equipment, and inform your insurer within 72 hours (helpline 14447). Save this screen + date as evidence.",
                           "புதிய வெள்ளம் இருக்க வாய்ப்பு. வடிகால் பாருங்கள், பொருட்களை பாதுகாப்பாக மாற்றுங்கள், 72 மணி நேரத்தில் காப்பீட்டாளருக்கு (14447) தெரிவியுங்கள்."))
            elif lvl == "warn":
                st.warning(L("Some new water signal. Walk the low-lying parts of the field and check drainage channels.", "சிறிய புதிய நீர் அறிகுறி. பள்ளமான பகுதிகளை நேரில் பாருங்கள்."))
            else:
                st.success(L("No new flood signal in the radar window.", "ரேடாரில் புதிய வெள்ள அறிகுறி இல்லை."))
            if rain_total >= 80:
                st.warning(L(f"Forecast rain is high ({rain_total:.0f} mm in 7 days) — keep drains clear even if radar shows no flood now.", f"7 நாளில் {rain_total:.0f} மி.மீ மழை முன்னறிவிப்பு — இப்போது வெள்ளம் இல்லாவிட்டாலும் வடிகாலை சுத்தமாக வைக்கவும்."))
            st.download_button("⬇️ " + L("Download flood scan (CSV)", "வெள்ள ஸ்கேன் (CSV)"), fr["series"].to_csv(index=False).encode("utf-8-sig"), file_name="hyperclimate_flood_scan.csv", mime="text/csv")
            st.caption(L("Limits: radar water detection can be fooled by very smooth dry soil/tarmac (false water) or wind-roughened water (missed water). Rice paddies are naturally flooded — check “permanent water”. Indicator only, not an official flood assessment; official layers: Bhuvan Disaster Services.",
                         "வரம்புகள்: மிக மென்மையான உலர் மண்/தார் சாலை தவறாக நீர் எனக் காட்டலாம். நெல் வயல் இயல்பாகவே நீர் தேங்கியிருக்கும். இது குறியீடு மட்டுமே; அதிகாரப்பூர்வ மதிப்பீடு அல்ல."))
            st.link_button("🇮🇳 Bhuvan Disaster Services (ISRO)", "https://bhuvan-app1.nrsc.gov.in/bhuvandisaster/")

# ================= TAB: ISRO Hub =================
with tab_isro:
    st.markdown("## 🇮🇳 " + L("ISRO Hub — Indian satellite data for this field", "ISRO மையம் — இந்த வயலுக்கான இந்திய செயற்கைக்கோள் தரவு"))
    st.caption(L("What is connected live, what needs a free login, and what is only linked. Nothing here is fabricated.", "எது நேரடியாக இணைந்துள்ளது, எதற்கு இலவச login தேவை, எது இணைப்பு மட்டும் — எதுவும் போலியாக உருவாக்கப்படவில்லை."))

    st.markdown(f'<div class="sec">📡 {esc(L("NISAR (NASA–ISRO radar) — coverage over your field", "NISAR (NASA–ISRO ரேடார்) — உங்கள் வயல் மேல் தரவு"))}</div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.write(L("NISAR launched on 30 July 2025. Its L-band products are public through NASA’s ASF DAAC (free Earthdata login to download); limited S-band samples are on ISRO’s Bhoonidhi.",
                   "NISAR 30 ஜூலை 2025-ல் ஏவப்பட்டது. L-band தரவு ASF DAAC வழியாக இலவசம் (பதிவிறக்க Earthdata login தேவை); S-band மாதிரிகள் ISRO Bhoonidhi-ல்."))
        if st.button("🔎 " + L("Search NISAR scenes over my field (last 120 days)", "என் வயல் மேல் NISAR படங்களை தேடு (120 நாள்)"), key="nisar_btn"):
            with st.spinner("Searching ASF DAAC..."):
                st.session_state.nisar_res = nisar_search_asf(lat, lon, 120, 25)
        nres = st.session_state.get("nisar_res")
        if nres:
            if nres.get("ok") and nres["rows"]:
                ndf = pd.DataFrame(nres["rows"])
                st.success(f"{len(ndf)} NISAR products found")
                st.dataframe(ndf, hide_index=True, use_container_width=True,
                             column_config={"Download (needs Earthdata login)": st.column_config.LinkColumn("Download (needs Earthdata login)", display_text="open")})
            elif nres.get("ok"):
                st.info(L("No NISAR product over this exact point in the last 120 days (or not yet released for this area).", "கடந்த 120 நாட்களில் இந்த இடத்தில் NISAR தரவு இல்லை."))
            else:
                st.warning("NISAR search failed — " + nres.get("error", "") + ". Use the links below.")
        b1, b2, b3 = st.columns(3)
        b1.link_button("ASF Vertex (NISAR)", "https://search.asf.alaska.edu/#/?dataset=NISAR", use_container_width=True)
        b2.link_button("NISAR data guide", "https://nisar-docs.asf.alaska.edu/availability-overview/", use_container_width=True)
        b3.link_button("Bhoonidhi (S-band)", "https://bhoonidhi.nrsc.gov.in/NISAR/", use_container_width=True)

    st.markdown(f'<div class="sec">🗺️ {esc(L("Bhuvan (ISRO) thematic layer on your field", "உங்கள் வயலில் Bhuvan (ISRO) அடுக்கு"))}</div>', unsafe_allow_html=True)
    with st.container(border=True):
        w1, w2, w3 = st.columns([2, 1.4, 1])
        wms_url = w1.text_input("Bhuvan WMS URL", "https://bhuvan-vec2.nrsc.gov.in/bhuvan/wms", key="bh_url")
        wms_layer = w2.text_input("Layer", "lulc:TN_LULC50K_1516", key="bh_layer", help="Pattern lulc:<STATE>_LULC50K_<years>, e.g. lulc:KA_LULC50K_0506. Confirm the exact Tamil Nadu layer name in Bhuvan Thematic Services.")
        wms_op = w3.slider("Opacity", 0.1, 1.0, 0.65, 0.05, key="bh_op")
        try:
            hm = folium.Map(location=[float(lat), float(lon)], zoom_start=13, tiles=None, control_scale=True)
            folium.TileLayer(tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri World Imagery", name="Satellite").add_to(hm)
            folium.raster_layers.WmsTileLayer(url=wms_url, layers=wms_layer, name="Bhuvan " + wms_layer, fmt="image/png", transparent=True, version="1.1.1", opacity=wms_op, overlay=True).add_to(hm)
            folium.Marker([float(lat), float(lon)], tooltip="Your field", icon=folium.Icon(color="green", icon="leaf", prefix="fa")).add_to(hm)
            folium.LayerControl(collapsed=True).add_to(hm)
            st_folium(hm, height=430, use_container_width=True, returned_objects=[], key="bhuvan_overlay_map")
            st.caption(L("If the overlay stays blank, the layer name or server is different today — open Bhuvan Thematic Services, copy the exact layer name, and paste it above. Land-use data is from ISRO/NRSC (Resourcesat LISS-III based).", "Overlay வெறுமையாக இருந்தால் layer பெயர்/server வேறு — Bhuvan Thematic Services-ல் சரியான பெயரை copy செய்து மேலே ஒட்டுங்கள்."))
        except Exception as e:
            st.warning(f"Bhuvan overlay could not be drawn: {type(e).__name__}: {e}")
        st.link_button("Bhuvan Thematic Services", "https://bhuvan-app1.nrsc.gov.in/thematic", use_container_width=False)

    st.markdown(f'<div class="sec">🛰️ {esc(L("ISRO satellites → what they give a farmer", "ISRO செயற்கைக்கோள்கள் → விவசாயிக்கு பயன்"))}</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame([
        {"Satellite": "Resourcesat-2/2A (LISS-III, LISS-IV, AWiFS)", "Type": "Optical", "Farmer value": "Crop area, crop type, land-use maps (Bhuvan LULC, FASAL)"},
        {"Satellite": "Cartosat-3 / Cartosat series", "Type": "High-res optical", "Farmer value": "Field boundaries, farm-pond & infrastructure mapping"},
        {"Satellite": "RISAT-1A (EOS-04)", "Type": "C-band radar", "Farmer value": "Kharif crop & flood mapping through clouds"},
        {"Satellite": "INSAT-3D / 3DR / 3DS", "Type": "Weather", "Farmer value": "Rainfall, cloud, temperature products (MOSDAC)"},
        {"Satellite": "NISAR (NASA–ISRO)", "Type": "L + S-band radar", "Farmer value": "Crop biomass, soil moisture, flood & land change"},
    ]), hide_index=True, use_container_width=True)

    st.markdown(f'<div class="sec">🔌 {esc(L("Integration status in this dashboard", "இந்த dashboard-ல் இணைப்பு நிலை"))}</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame([
        {"Source": "Sentinel-2 / Sentinel-1 / Landsat", "Status": "🟢 Live", "Needs": "Internet (Planetary Computer)"},
        {"Source": "NASA POWER + Open-Meteo", "Status": "🟢 Live", "Needs": "Internet"},
        {"Source": "NISAR L-band search (ASF DAAC)", "Status": "🟢 Live search", "Needs": "Free NASA Earthdata login only to download"},
        {"Source": "Bhuvan thematic WMS (LULC)", "Status": "🟡 Overlay, layer name editable", "Needs": "Correct layer name for your state"},
        {"Source": "MOSDAC INSAT rainfall / products", "Status": "🔵 Linked", "Needs": "Free MOSDAC registration"},
        {"Source": "Bhoonidhi (Resourcesat, NISAR S-band)", "Status": "🔵 Linked", "Needs": "Bhoonidhi account / authorised access"},
    ]), hide_index=True, use_container_width=True)
    p1, p2, p3, p4 = st.columns(4)
    p1.link_button("MOSDAC", "https://www.mosdac.gov.in/", use_container_width=True)
    p2.link_button("Bhoonidhi", "https://bhoonidhi.nrsc.gov.in/bhoonidhi/home.html", use_container_width=True)
    p3.link_button("VEDAS", "https://vedas.sac.gov.in/vcms/en/", use_container_width=True)
    p4.link_button("Bhuvan", "https://bhuvan.nrsc.gov.in/", use_container_width=True)

# ================= TAB 6: AI / Multi-source risk =================
with tab_ai:
    st.markdown("## 🧠 AI Crop Health — Crop-specific Risk & Action")
    st.caption(f"Selected crop: **{crop_name}** · The satellite image is measured from the field, then weather + satellite signals are interpreted specifically for this crop.")
    st.markdown(chips([f'🌾 {crop_name} — Crop Stress Risk', '🐛 Pest / Disease Warning — Field Check Needed', '📉 AI Unusual Field Condition', '🧠 Why is this Crop Showing Risk?', '🚨 What Should the Farmer Do Now?']), unsafe_allow_html=True)
    st.caption("This is a transparent crop-specific indicator. Satellite data cannot confirm a pest or disease by itself; field inspection is required.")

    sat_ai = get_satellite_analysis(lat, lon)
    if sat_ai.get("ok"):
        cc = sat_ai["current"]
        sat_score_ai = float(sat_ai["score"])
        unsup_ai = ai_anomaly_score(sat_ai)
        nasa_ai = st.session_state.get("nasa_df", pd.DataFrame())
        if not nasa_ai.empty:
            latest = nasa_ai.iloc[-1]
            rain_anom = float(latest.get("rain_anom_pct", 0))
            temp_anom = float(latest.get("temp_anom", 0))
            hum_now = float(latest.get("humidity", humidity))
        else:
            rain_anom, temp_anom, hum_now = 0.0, 0.0, float(humidity)

        # The selected crop now controls the interpretation of satellite + weather signals.
        crop_ai = crop_specific_satellite_interpretation(
            crop_name, crop_group_of, crop, sat_ai,
            rain_anom=rain_anom, temp_anom=temp_anom, humidity=hum_now
        )
        crop_risk, crop_reasons = crop_risk_model(
            crop_name, sat_ai, nasa_ai,
            st.session_state.get("lst_data", {"ok":False}),
            float(sentinel1_sar_analysis(lat,lon,365).get("vv_change_db",np.nan)),
            crop_group=crop_group_of, crop_tuple=crop
        )
        # Blend the crop-adjusted interpretation into the final crop risk.
        crop_risk = int(round((crop_risk + crop_ai["score"]) / 2))
        fusion = int(round((sat_score_ai * 0.45) + (crop_ai["score"] * 0.40) +
                           (max(0,-rain_anom) * 0.10) + (max(0,temp_anom) * 2.0)))
        if hum_now > 85:
            fusion += 4
        fusion = max(0, min(100, fusion))
        st.session_state.fusion_score = fusion

        p = crop_ai["profile"]
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("🌱 Crop Green Health", f"{cc['ndvi_median']:.2f}")
        c2.metric("💧 Plant Water Status", f"{cc['ndmi_median']:.2f}")
        c3.metric("🌾 Crop Stress Risk", f"{crop_risk}/100")
        c4.metric("🧠 AI Unusual Condition", f"{unsup_ai if unsup_ai is not None else 0}/100")

        a1,a2,a3 = st.columns(3)
        a1.metric("🌡️ Crop heat limit", f"{p['heat_limit']:.0f} °C")
        a2.metric("💧 Soil moisture target", f"≥ {p['moisture_min']:.0f}%")
        a3.metric("💦 Crop water factor", f"{p['kc']:.2f}")

        st.markdown(f"### {crop_ai['level']} — {crop_name}")
        if crop_ai["reasons"]:
            for r in crop_ai["reasons"]:
                st.markdown(f"• {r}")
        else:
            st.success(f"{crop_name}: current satellite + weather signals are close to the recent normal.")

        st.markdown("#### 🐛 Pest / Disease Warning")
        pc1,pc2 = st.columns([1,2])
        pc1.metric("Field-check level", crop_ai["pest_level"])
        with pc2:
            for r in crop_ai["pest_reasons"]:
                st.write("• " + r)
        st.caption("This warning only tells the farmer when to inspect the crop. It does **not** identify a disease from satellite data alone.")

        st.markdown("#### 🔎 Why is this crop-specific warning shown?")
        reasons=[]
        if _finite(cc.get("ndvi_median")) and cc["ndvi_median"] < p["ndvi_min"]:
            reasons.append(f"{crop_name} uses a crop-family vegetation threshold, and the current green-health value is below it.")
        if _finite(cc.get("ndmi_median")) and cc["ndmi_median"] < p["ndmi_min"]:
            reasons.append(f"{crop_name} has a selected plant-water warning level of {p['ndmi_min']:.2f}.")
        if rain_anom < -20:
            reasons.append(f"Rainfall is {abs(rain_anom):.0f}% below the local normal; this matters more for a crop with water factor {p['kc']:.2f}.")
        if temp_anom > 2 or temp > p["heat_limit"]:
            reasons.append(f"Temperature is elevated for {crop_name}; selected heat limit is about {p['heat_limit']:.0f}°C.")
        if hum_now > 85:
            reasons.append(f"High humidity means the farmer should inspect for {p['watch']}.")
        if not reasons:
            reasons.append(f"No major crop-specific warning threshold is crossed for {crop_name} right now.")
        for r in reasons:
            st.write("• " + r)

        st.markdown("#### 👨‍🌾 What should I do now?")
        if crop_risk >= 70:
            st.error(f"{crop_name}: inspect the field today. Check soil moisture, leaves, pests/disease symptoms and drainage before taking action.")
        elif crop_risk >= 45:
            st.warning(f"{crop_name}: increase monitoring. Use the irrigation plan and inspect the crop before spraying anything.")
        elif crop_ai["pest_score"] >= 35:
            st.warning(f"{crop_name}: field-check priority is higher because weather conditions may favour {p['watch']}.")
        else:
            st.success(f"{crop_name}: continue normal monitoring. Avoid unnecessary irrigation or pesticide application.")

        drought_a,flood_a,_,_=drought_flood_indicators(
            nasa_ai,sat_ai,st.session_state.get("lst_data",{"ok":False}),
            float(sentinel1_sar_analysis(lat,lon,365).get("vv_change_db",np.nan))
        )
        my_alert=st.session_state.get("multi_year_result") or {}
        alerts=build_alerts(fusion,drought_a,flood_a,crop_risk,my_alert.get("ndvi_anomaly",np.nan),my_alert.get("ndmi_anomaly",np.nan))
        st.markdown("#### 🚨 Farmer Alert System")
        for icon,title,msg in alerts:
            if icon=="🔴": st.error(f"{icon} **{title}** — {msg}")
            elif icon in ("🟠","☀️","🌊","🌱","📉","💧"): st.warning(f"{icon} **{title}** — {msg}")
            else: st.success(f"{icon} **{title}** — {msg}")
        alert_df=pd.DataFrame([{"Alert":a,"Title":b,"Message":c} for a,b,c in alerts])
        st.download_button("⬇️ Download alert log",alert_df.to_csv(index=False).encode("utf-8-sig"),file_name="hyperclimate_alerts.csv",mime="text/csv")
    else:
        st.info("Satellite analysis is not available yet. Open the Satellite tab first or check the satellite package installation.")

# ================= TAB 7: Report + ISRO ecosystem =================
with tab_report:
    st.markdown("## 📄 8. Land Report, ISRO Ecosystem & Satellite Catalogue")
    st.caption("Downloadable report + official Indian EO data ecosystem + satellite acquisition history")
    st.markdown(chips(['📄 Download Field Report', '🇮🇳 ISRO / NRSC Data & Services', '📡 NISAR Radar Data Status', '🛰️ Satellite Observation History']), unsafe_allow_html=True)
    sat_rep = get_satellite_analysis(lat, lon)
    nasa_rep = st.session_state.get("nasa_df", pd.DataFrame())
    lst_rep = st.session_state.get("lst_data", {"ok":False})
    elev_rep = st.session_state.get("elevation", float("nan"))
    area_rep = st.session_state.get("field_area_m2", float("nan"))
    fusion_rep = st.session_state.get("fusion_score", sat_rep.get("score",0) if sat_rep.get("ok") else 0)

    report = build_report_text(place_label, crop_name, lat, lon, sat_rep, lst_rep, nasa_rep, elev_rep, area_rep, fusion_rep)
    st.text_area("Report preview", report, height=360)
    st.download_button("⬇️ Download land intelligence report", report.encode("utf-8"), file_name="hyperclimate_land_report.txt", mime="text/plain")
    try:
        import os, tempfile
        pdf_path=os.path.join(tempfile.gettempdir(),"hyperclimate_land_report.pdf")
        make_pdf_report(pdf_path, report, place_label, crop_name, sat_rep, lst_rep, area_rep, int(fusion_rep))
        with open(pdf_path,"rb") as fh: st.download_button("📄 Download PDF land report", fh, file_name="hyperclimate_land_report.pdf", mime="application/pdf")
    except Exception as e:
        st.info("PDF export needs reportlab: python -m pip install reportlab")

    st.markdown("#### 🛰️ 🛰️ சமீபத்திய Satellite தகவல்")
    st.info("Earth-observation satellites are not continuous live video. Hyperclimate uses the latest usable scene and its acquisition date. For operational/near-real-time context, use official ISRO/NASA portals and record the scene date in the dashboard.")
    st.markdown("- **ISRO/NRSC Bhoonidhi** — Indian and international EO data catalogue")
    st.markdown("- **MOSDAC LIVE** — satellite/weather visualisation and operational products")
    st.markdown("- **VEDAS** — vegetation, crop monitoring, drought and land applications")
    st.markdown("- **Bhuvan** — ISRO geospatial visualisation and thematic layers")
    st.markdown("- **NISAR** — radar-based Earth observation; access depends on product/data availability")
    st.markdown("- **Sentinel-1/2 + Landsat** — open EO datasets used by the current prototype")

    st.markdown("#### 📡 NISAR / ISRO data status")
    st.info("NISAR L-band products are public through NASA ASF DAAC (free Earthdata login) and limited S-band samples are on ISRO Bhoonidhi. Use the 🇮🇳 ISRO Hub tab to search NISAR scenes over your field; values are never fabricated.")
    st.link_button("Open Bhoonidhi NISAR", "https://bhoonidhi.nrsc.gov.in/NISAR/")

    st.markdown("#### 🔗 Official portals")
    st.link_button("ISRO Land Resources", "https://www.isro.gov.in/LandResources.html")
    st.link_button("Bhoonidhi (NRSC)", "https://bhoonidhi.nrsc.gov.in/bhoonidhi/home.html")
    st.link_button("MOSDAC", "https://www.mosdac.gov.in/")
    st.link_button("MOSDAC LIVE", "https://mosdac.gov.in/mosdac-live")
    st.link_button("VEDAS", "https://vedas.sac.gov.in/vcms/en/")
    st.link_button("ISRO Earth Observation Satellites", "https://www.isro.gov.in/EarthObservationSatellites.html")

    st.markdown("#### 🇮🇳 ISRO / EO data ecosystem")
    e1,e2,e3,e4,e5=st.columns(5)
    e1.metric("Bhoonidhi","EO Catalogue")
    e2.metric("MOSDAC","Weather / LIVE")
    e3.metric("VEDAS","Crop / Vegetation")
    e4.metric("Bhuvan","GIS / Layers")
    e5.metric("NISAR","Radar / Change")
    st.caption("These official portals are linked below. NISAR/Resourcesat product access depends on the authorised ISRO/NRSC data route; the dashboard does not pretend to download restricted products.")

    st.markdown("#### 🧩 Proposed ISRO-grade architecture")
    st.code("FIELD POLYGON → EO DATA CATALOG → Sentinel-2 / Sentinel-1 / Landsat / ISRO EO → WEATHER → FEATURE ENGINE → ANOMALY MODEL → LAND HEALTH → ALERT → REPORT", language="text")
    st.caption("Current calculations: field area, satellite crop health, plant water status, surface wetness and change, Landsat land temperature, NASA POWER baseline, elevation/slope, Sentinel-1 SAR when available, drought/flood indicators, land-cover clustering, zone/irrigation priorities, multi-year comparison, crop-risk + explainable AI + farmer alerts. NISAR/Resourcesat values are never fabricated; authorised Bhoonidhi access is linked for direct future integration.")

    with st.expander("🎓 " + L("Methodology — indices, formulas & limitations", "செயல்முறை — குறியீடுகள், சூத்திரங்கள், வரம்புகள்")):
        st.dataframe(pd.DataFrame([
            {"Index": "NDVI", "Formula": "(NIR − Red) / (NIR + Red)", "Sentinel-2 bands": "B08, B04", "Farmer meaning": "Crop greenness / vigour"},
            {"Index": "NDMI", "Formula": "(NIR − SWIR) / (NIR + SWIR)", "Sentinel-2 bands": "B08, B11", "Farmer meaning": "Water inside plant leaves"},
            {"Index": "NDWI", "Formula": "(Green − NIR) / (Green + NIR)", "Sentinel-2 bands": "B03, B08", "Farmer meaning": "Surface wetness / open water"},
            {"Index": "NDRE", "Formula": "(NIR − RedEdge) / (NIR + RedEdge)", "Sentinel-2 bands": "B08, B05", "Farmer meaning": "Chlorophyll / nitrogen status"},
            {"Index": "EVI", "Formula": "2.5(NIR−Red)/(NIR+6Red−7.5Blue+1)", "Sentinel-2 bands": "B08, B04, B02", "Farmer meaning": "Canopy density (less saturation)"},
            {"Index": "SAVI", "Formula": "1.5(NIR−Red)/(NIR+Red+0.5)", "Sentinel-2 bands": "B08, B04", "Farmer meaning": "Greenness corrected for bare soil"},
            {"Index": "ET₀ water balance", "Formula": "ET₀ × Kc × stage factor − 0.8 × rain", "Sentinel-2 bands": "Open-Meteo", "Farmer meaning": "Irrigation need in mm → litres"},
            {"Index": "Field Health Index", "Formula": "100 − 0.6·stress + greenness bonus − moisture/heat penalties", "Sentinel-2 bands": "Fusion", "Farmer meaning": "One-number field summary"},
        ]), hide_index=True, use_container_width=True)
        st.caption(L("Limitations: 10 m optical pixels, cloud masking via SCL, indicators ≠ diagnosis, canopy potential ≠ yield forecast, NISAR/Resourcesat values are never fabricated.",
                     "வரம்புகள்: 10 மீ பிக்சல், மேக நீக்கம் SCL மூலம், குறியீடுகள் நோய் கண்டறிதல் அல்ல, canopy potential விளைச்சல் கணிப்பு அல்ல."))

# ================= TAB 4: Map (view only, satellite) =================
with tab_map:
    st.markdown("## 📍 Select Your Exact Field & Satellite Map")
    st.caption("Select the exact field first; the selected point/polygon becomes the basis for satellite analysis.")
    st.markdown(chips(['🔎 Search Your Area', '🛰️ Click Your Exact Field on Satellite Map', '📐 Draw Field Boundary & Calculate Area']), unsafe_allow_html=True)
    st.caption("District / sub-place gives a reference point. Search the location or click directly on the satellite map to choose the exact field.")
    map_q = st.text_input("🔎 Search location on map", value="", placeholder="Example: Ramaswamy Nagar, Aruppukkottai, Tamil Nadu", key="map_search_box")
    if map_q.strip():
        map_results = map_search_place(map_q.strip())
        if map_results:
            map_results = map_results[:10]
            map_labels = [f"{r['name']}, {r.get('admin1','')}, {r.get('country','')}" for r in map_results]
            mi = st.selectbox("Choose map result", range(len(map_results)), format_func=lambda k: map_labels[k], key="map_result_select")
            if st.button("📍 Go to this map result", key="go_map_result"):
                rr = map_results[mi]
                st.session_state.lat = rr["latitude"]
                st.session_state.lon = rr["longitude"]
                st.session_state.place_label = map_labels[mi]
                st.session_state.last_click = None
                st.rerun()
        else:
            st.warning("Location not found. Try a nearby town, village, road, or landmark name.")
    if lat is not None and lon is not None:
        with st.container(border=True):
            location_map(lat, lon, place_label, key="view", clickable=True, height=560)
        st.success(f"Current map point: {place_label} · {lat:.6f}, {lon:.6f}")
    else:
        st.info("No location selected yet. Use Search, GPS, or Coordinates first, then open the map to choose the exact field point.")

st.caption(t("footer"))
