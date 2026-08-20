import streamlit as st
import pandas as pd
import kagglehub
import os
import glob
import re
import difflib
import random

# ==================== PAGE SETUP & MODERN UI ====================
st.set_page_config(
    page_title="VoyageAI — Intelligent Travel Planner",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .hero-container {
        padding: 1.4rem 1.6rem;
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 50%, #06b6d4 100%);
        border-radius: 16px;
        color: white;
        margin-bottom: 1.2rem;
        box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.3);
    }
    .hero-title { font-size: 1.85rem; font-weight: 700; margin-bottom: 0.2rem; }
    .hero-subtitle { font-size: 0.95rem; opacity: 0.92; }
    
    .dest-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1.2rem;
        margin-top: 0.8rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
        border-left: 5px solid #2563eb;
    }
    
    .badge-pill {
        display: inline-block;
        padding: 3px 10px;
        font-size: 0.78rem;
        font-weight: 600;
        border-radius: 20px;
        margin-right: 6px;
        margin-bottom: 4px;
    }
    .badge-rating { background: #fef3c7; color: #b45309; }
    .badge-category { background: #e0f2fe; color: #0369a1; }
    .badge-fee { background: #dcfce7; color: #15803d; }
    .badge-time { background: #f3e8ff; color: #7e22ce; }
    .badge-dslr { background: #f1f5f9; color: #475569; }
    
    .sidebar-kpi {
        background-color: #0f172a;
        color: #f8fafc;
        padding: 14px;
        border-radius: 12px;
        border: 1px solid #1e293b;
        margin-bottom: 1rem;
    }
    .cost-summary {
        background: #ecfdf5;
        border: 1px solid #a7f3d0;
        border-radius: 10px;
        padding: 10px 14px;
        color: #065f46;
        font-weight: 600;
        margin-top: 10px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)


# ==================== DATA PIPELINE ====================
@st.cache_data
def load_data():
    path = kagglehub.dataset_download("saketk511/travel-dataset-guide-to-indias-must-see-places")
    csv_files = glob.glob(os.path.join(path, "*.csv"))
    df = pd.read_csv(csv_files[0])
    
    df.columns = df.columns.str.strip().str.lower()
    
    text_cols = ["name", "city", "state", "zone", "type", "significance", "dslr allowed"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()
            
    if "entrance fee in inr" in df.columns:
        df["entrance fee in inr"] = pd.to_numeric(df["entrance fee in inr"], errors="coerce").fillna(0)
    if "google review rating" in df.columns:
        df["google review rating"] = pd.to_numeric(df["google review rating"], errors="coerce").fillna(0.0)
    if "time needed to visit in hrs" in df.columns:
        df["time needed to visit in hrs"] = pd.to_numeric(df["time needed to visit in hrs"], errors="coerce").fillna(1.5)
        
    return df

df = load_data()


# ==================== SIDEBAR CONTROLS ====================
with st.sidebar:
    st.markdown("### 🧭 **VoyageAI Controls**")
    
    st.markdown(f"""
    <div class="sidebar-kpi">
        <span style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; font-weight: 600;">Data Reservoir</span><br>
        <span style="font-size: 1.5rem; font-weight: 700; color: #38bdf8;">{len(df):,} Destinations</span>
        <div style="font-size: 0.75rem; color: #cbd5e1; margin-top: 4px;">Verified Indian Tourism Records</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🧹 Clear Chat History", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "✨ **Session refreshed!** Where would you like to travel next? Choose a Travel Persona below or type a destination."}
        ]
        st.session_state.last_itinerary_text = ""
        st.rerun()

    st.markdown("---")
    st.markdown("#### 🎯 **Custom Search Filters**")

    with st.form("sidebar_filter_form"):
        zones = ["All"] + sorted([z for z in df["zone"].unique() if z])
        selected_zone = st.selectbox("📍 Geographic Zone", zones)

        available_states = df[df["zone"] == selected_zone]["state"] if selected_zone != "All" else df["state"]
        states = ["All"] + sorted([s for s in available_states.unique() if s])
        selected_state = st.selectbox("🏛️ State / UT", states)

        types = ["All"] + sorted([t for t in df["type"].unique() if t])
        selected_type = st.selectbox("🏷️ Attraction Theme", types)

        significances = ["All"] + sorted([s for s in df["significance"].unique() if s]) if "significance" in df.columns else ["All"]
        selected_sig = st.selectbox("✨ Cultural Significance", significances)

        max_limit = int(df["entrance fee in inr"].max()) if "entrance fee in inr" in df.columns else 1000
        max_fee = st.slider("💰 Max Budget (Entrance Fee ₹)", min_value=0, max_value=max_limit, value=max_limit, step=50)

        min_rating = st.slider("⭐ Min Rating Threshold", min_value=1.0, max_value=5.0, value=3.5, step=0.1)

        dslr_option = st.radio("📷 Camera Rule", ["Any Policy", "DSLR Permitted Only"], horizontal=True)

        apply_filters_btn = st.form_submit_button("⚡ Apply Filters", use_container_width=True)


# ==================== NLP SEARCH & ITINERARY ENGINE ====================
GREETINGS = ["hi", "hello", "hey", "hola", "namaste", "good morning", "good evening"]
GREETING_RESPONSES = [
    "Hello! I am your AI travel guide. Tell me a destination, state, or attraction type you'd like to explore!",
    "Namaste! Planning your next journey? Search any location or select a Travel Persona above to get started.",
    "Hey there! Ready to discover top-rated destinations across India? Let me know your travel preferences!"
]

GRATITUDE = ["thank", "thanks", "thank you", "great", "awesome", "perfect", "cool"]
GRATITUDE_RESPONSES = [
    "You're very welcome! If you need more travel tips or want to explore another region, just ask. Safe travels! 🎒",
    "Glad I could help plan your journey! Let me know if you need anything else.",
    "Happy to help! Have a fantastic and memorable trip! 🌟"
]

def fuzzy_find(term, choices, cutoff=0.7):
    matches = difflib.get_close_matches(term.lower(), [c.lower() for c in choices], n=1, cutoff=cutoff)
    return matches[0] if matches else None

def generate_itinerary_and_cards(dataframe, lead_message=""):
    if dataframe.empty:
        return "I couldn't find destinations matching those exact criteria. Try lowering the minimum rating or adjusting your filters.", ""
    
    top_picks = dataframe.sort_values(by="google review rating", ascending=False).head(3)
    
    total_fee = int(top_picks["entrance fee in inr"].sum())
    total_time = round(top_picks["time needed to visit in hrs"].sum(), 1)
    
    slots = ["🌅 Slot 1: Morning (09:30 AM)", "☀️ Slot 2: Afternoon (02:00 PM)", "🌆 Slot 3: Evening (05:30 PM)"]
    
    response = f"{lead_message}\n\n"
    response += f"""
<div class="cost-summary">
    💰 <strong>Total Est. Ticket Budget:</strong> ₹{total_fee} &nbsp;|&nbsp; ⏱️ <strong>Total Sightseeing Time:</strong> ~{total_time} Hours
</div>
"""
    download_text = f"VOYAGEAI CURATED TRAVEL ITINERARY\n{'='*45}\n"
    download_text += f"Total Estimated Ticket Cost: INR {total_fee}\nTotal Exploration Time: ~{total_time} Hours\n\n"

    for i, (_, row) in enumerate(top_picks.iterrows()):
        name = row.get("name", "Tourist Destination")
        city = row.get("city", "City")
        state_name = row.get("state", "State")
        cat = row.get("type", "Attraction")
        rating = row.get("google review rating", 0.0)
        fee = int(row.get("entrance fee in inr", 0))
        time_spent = row.get("time needed to visit in hrs", 1.5)
        dslr_rule = row.get("dslr allowed", "Allowed")
        sig = row.get("significance", "Tourism")
        maps_query = f"{name} {city} {state_name}".replace(" ", "+")
        fee_label = "Free Entry" if fee == 0 else f"₹{fee}"
        slot_title = slots[i] if i < len(slots) else f"📍 Stop {i+1}"

        response += f"""
<div class="dest-card">
    <div style="font-size: 0.85rem; font-weight: 700; color: #2563eb; text-transform: uppercase; margin-bottom: 3px;">
        {slot_title}
    </div>
    <div style="font-size: 1.15rem; font-weight: 700; color: #0f172a; margin-bottom: 6px;">
        📍 {name} <span style="font-weight: 400; font-size: 0.92rem; color: #64748b;">— {city}, {state_name}</span>
    </div>
    <div style="margin-bottom: 8px;">
        <span class="badge-pill badge-rating">⭐ {rating} / 5.0</span>
        <span class="badge-pill badge-category">🏷️ {cat}</span>
        <span class="badge-pill badge-fee">🎟️ {fee_label}</span>
        <span class="badge-pill badge-time">⏱️ ~{time_spent} hrs</span>
        <span class="badge-pill badge-dslr">📷 DSLR: {dslr_rule.capitalize()}</span>
    </div>
    <div style="font-size: 0.84rem; color: #475569; margin-bottom: 8px;">
        <strong>Significance:</strong> {sig.capitalize()}
    </div>
    <div>
        <a href="https://www.google.com/maps/search/?api=1&query={maps_query}" target="_blank" style="text-decoration: none; font-size: 0.86rem; font-weight: 600; color: #2563eb;">
            🗺️ Open Route in Google Maps ➔
        </a>
    </div>
</div>
"""
        download_text += f"{slot_title}\nDestination: {name} ({city}, {state_name})\n"
        download_text += f"- Category: {cat} | Rating: {rating}/5.0\n"
        download_text += f"- Fee: {fee_label} | Duration: ~{time_spent} hrs\n"
        download_text += f"- Maps: https://www.google.com/maps/search/?api=1&query={maps_query}\n\n"

    return response, download_text

def process_query(user_input, zone, state, p_type, sig, max_cost, min_rate, dslr, is_filter_only=False):
    data = df.copy()

    # 1. Apply Sidebar Selection
    if zone != "All": data = data[data["zone"].str.lower() == zone.lower()]
    if state != "All": data = data[data["state"].str.lower() == state.lower()]
    if p_type != "All": data = data[data["type"].str.lower() == p_type.lower()]
    if sig != "All" and "significance" in data.columns:
        data = data[data["significance"].str.lower() == sig.lower()]
    
    data = data[data["entrance fee in inr"] <= max_cost]
    data = data[data["google review rating"] >= min_rate]
    
    if dslr == "DSLR Permitted Only" and "dslr allowed" in data.columns:
        data = data[data["dslr allowed"].str.lower().isin(["yes", "allowed"])]

    if is_filter_only:
        return generate_itinerary_and_cards(data, "Here is a custom plan based on your **applied filters**:")

    # 2. Text Query Processing
    if user_input:
        q = user_input.strip().lower()
        
        if any(re.search(rf"\b{re.escape(g)}\b", q) for g in GREETINGS):
            return random.choice(GREETING_RESPONSES), ""
        if any(re.search(rf"\b{re.escape(t)}\b", q) for t in GRATITUDE):
            return random.choice(GRATITUDE_RESPONSES), ""

        words = [w for w in re.findall(r'\w+', q) if w not in ["what", "where", "show", "tell", "best", "good", "place", "places", "visit", "want", "like", "explore", "itinerary", "plan"]]

        # Monument Name Check (Exact + Fuzzy)
        matched_by_name = pd.DataFrame()
        lead_note = ""
        for word in words:
            if len(word) >= 3:
                exact = data[data["name"].str.lower().str.contains(word, na=False)]
                if not exact.empty:
                    matched_by_name = pd.concat([matched_by_name, exact])
                    
        if matched_by_name.empty:
            for word in words:
                if len(word) >= 4:
                    best_match = fuzzy_find(word, df["name"].unique(), cutoff=0.65)
                    if best_match:
                        matched_by_name = df[df["name"].str.lower() == best_match.lower()]
                        lead_note = f"🔍 *Found match for **{best_match}**:*"
                        break

        if not matched_by_name.empty:
            return generate_itinerary_and_cards(matched_by_name.drop_duplicates(), lead_note if lead_note else "Here are details for that destination:")

        # City & State Matching
        matched_cities = [c for c in df["city"].unique() if len(c) > 2 and re.search(rf"\b{re.escape(c.lower())}\b", q)]
        matched_states = [s for s in df["state"].unique() if len(s) > 2 and re.search(rf"\b{re.escape(s.lower())}\b", q)]

        if not matched_cities and not matched_states:
            for word in words:
                if len(word) >= 4:
                    fc = fuzzy_find(word, df["city"].unique(), cutoff=0.75)
                    if fc: matched_cities.append(fc)
                    fs = fuzzy_find(word, df["state"].unique(), cutoff=0.75)
                    if fs: matched_states.append(fs)

        location_matches = pd.DataFrame()
        loc_name = ""
        if matched_cities:
            location_matches = data[data["city"].str.lower().isin([c.lower() for c in matched_cities])]
            loc_name = matched_cities[0]
        elif matched_states:
            location_matches = data[data["state"].str.lower().isin([s.lower() for s in matched_states])]
            loc_name = matched_states[0]

        if not location_matches.empty:
            data = location_matches

        # Category Matching
        matched_types = [t.lower() for t in df["type"].unique() if len(t) > 2 and re.search(rf"\b{re.escape(t.lower())}s?\b", q)]
        if matched_types:
            type_filtered = data[data["type"].str.lower().isin(matched_types)]
            if not type_filtered.empty:
                data = type_filtered
            elif location_matches.empty:
                data = df[df["type"].str.lower().isin(matched_types)]

        if matched_by_name.empty and not matched_cities and not matched_states and not matched_types:
            return f"I couldn't locate specific destinations matching **'{user_input}'**. Try searching for popular cities like *Hyderabad, Jaipur, Varanasi*, or monuments like *Badrinath or Taj Mahal*!", ""

        lead = f"Here is a curated 1-day exploration plan in **{loc_name.title()}**:" if loc_name else "Here is a curated exploration itinerary:"
        return generate_itinerary_and_cards(data, lead)

    return generate_itinerary_and_cards(data)


# ==================== MAIN CHAT INTERFACE ====================
st.markdown("""
<div class="hero-container">
    <div class="hero-title">✈️ VoyageAI — Intelligent Travel Planner</div>
    <div class="hero-subtitle">Automated day itineraries, budget estimations, and direct Google Maps routes across India.</div>
</div>
""", unsafe_allow_html=True)

# 1. Travel Persona Mood Selector
st.markdown("**✨ Travel Mood & Personas:**")
col_p1, col_p2, col_p3, col_p4 = st.columns(4)
persona_prompt = None

if col_p1.button("🎒 Budget Backpacker", use_container_width=True, help="Places with ₹0 entrance fee"):
    persona_prompt = "Free entrance places"
if col_p2.button("🏛️ Heritage & History", use_container_width=True, help="Historic Forts and Monuments"):
    persona_prompt = "Forts and historical monuments"
if col_p3.button("🌿 Nature & Scenic", use_container_width=True, help="Waterfalls, viewpoints, and nature"):
    persona_prompt = "Scenic nature and waterfalls"
if col_p4.button("👨‍👩‍👧 Family Friendly", use_container_width=True, help="Parks, museums, and high rated spots"):
    persona_prompt = "Temples and parks"

# 2. Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 **Hello! I'm VoyageAI, your interactive travel planner.**\n\nAsk for any city itinerary (e.g. *'1 day in Hyderabad'*), click a **Travel Mood** button above, or configure custom filters in the sidebar."}
    ]
if "last_itinerary_text" not in st.session_state:
    st.session_state.last_itinerary_text = ""

# Handle Sidebar Form Submission
if apply_filters_btn:
    tags = []
    if selected_zone != "All": tags.append(f"Zone: **{selected_zone}**")
    if selected_state != "All": tags.append(f"State: **{selected_state}**")
    if selected_type != "All": tags.append(f"Type: **{selected_type}**")
    tags.append(f"Max Fee: **₹{max_fee}**")
    tags.append(f"Min Rating: **{min_rating}⭐**")
    
    st.session_state.messages.append({"role": "user", "content": f"⚙️ *Applied Filters:* {' • '.join(tags)}"})
    reply, it_txt = process_query("", selected_zone, selected_state, selected_type, selected_sig, max_fee, min_rating, dslr_option, is_filter_only=True)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    if it_txt:
        st.session_state.last_itinerary_text = it_txt

# Handle Persona Click
if persona_prompt:
    st.session_state.messages.append({"role": "user", "content": f"Exploring Mode: **{persona_prompt}**"})
    reply, it_txt = process_query(persona_prompt, selected_zone, selected_state, selected_type, selected_sig, max_fee, min_rating, dslr_option)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    if it_txt:
        st.session_state.last_itinerary_text = it_txt

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

# 3. Export Itinerary Download Button
if st.session_state.last_itinerary_text:
    st.download_button(
        label="📥 Download This Itinerary (.txt)",
        data=st.session_state.last_itinerary_text,
        file_name="VoyageAI_Travel_Plan.txt",
        mime="text/plain",
        key="export_itinerary_btn",
        help="Download formatted itinerary with Google Maps links"
    )

# User Chat Input
if user_prompt := st.chat_input("Ask a question (e.g. '1 day in Jaipur', 'Places in Hyderabad', 'Badrinath')..."):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)
        
    bot_reply, it_txt = process_query(user_prompt, selected_zone, selected_state, selected_type, selected_sig, max_fee, min_rating, dslr_option)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    if it_txt:
        st.session_state.last_itinerary_text = it_txt
        
    with st.chat_message("assistant"):
        st.markdown(bot_reply, unsafe_allow_html=True)