import streamlit as st
import time
import random

st.set_page_config(
    page_title="Nike Adapt",
    page_icon="👟",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS global ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;600;700&display=swap');

  html, body, [class*="css"] {
    background-color: #0a0a0a !important;
    color: #f0f0f0 !important;
    font-family: 'Inter', sans-serif;
  }

  .block-container { padding: 1.5rem 1.5rem 4rem; max-width: 480px; margin: auto; }

  /* Header */
  .nike-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.6rem 0 1.2rem;
  }
  .nike-logo {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.2rem; letter-spacing: 2px; color: #fff;
  }
  .connected-badge {
    background: #1a1a1a; border: 1px solid #333;
    border-radius: 20px; padding: 4px 12px;
    font-size: 0.72rem; color: #4ade80;
    display: flex; align-items: center; gap: 6px;
  }
  .dot { width:7px; height:7px; border-radius:50%; background:#4ade80; display:inline-block; }

  /* Shoe card */
  .shoe-card {
    background: linear-gradient(135deg, #161616 0%, #1e1e1e 100%);
    border: 1px solid #2a2a2a;
    border-radius: 20px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
  }
  .shoe-title {
    font-size: 0.7rem; text-transform: uppercase; letter-spacing: 3px;
    color: #888; margin-bottom: 0.3rem;
  }
  .shoe-name {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.5rem; letter-spacing: 1px; color: #fff;
    margin-bottom: 0.8rem;
  }
  .fit-display {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 4rem; line-height:1; color: #fff;
    text-align: center; margin: 0.4rem 0;
  }
  .fit-label {
    font-size: 0.68rem; color: #666; text-align: center;
    text-transform: uppercase; letter-spacing: 2px;
  }
  .battery-row {
    display: flex; align-items: center; gap: 8px;
    margin-top: 0.8rem;
  }
  .battery-bar {
    flex: 1; height: 5px; background: #2a2a2a;
    border-radius: 3px; overflow: hidden;
  }
  .battery-fill {
    height: 100%; border-radius: 3px;
    transition: width 0.5s ease;
  }
  .battery-pct { font-size: 0.72rem; color: #888; min-width: 36px; text-align:right; }

  /* Mode buttons */
  .mode-grid {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;
    margin: 1rem 0;
  }
  .mode-btn {
    background: #161616; border: 1px solid #2a2a2a;
    border-radius: 12px; padding: 10px 4px;
    text-align: center; cursor: pointer;
    transition: all 0.15s ease;
  }
  .mode-btn.active {
    background: #fff; border-color: #fff;
    color: #000 !important;
  }
  .mode-btn .mode-icon { font-size: 1.3rem; }
  .mode-btn .mode-name {
    font-size: 0.6rem; text-transform: uppercase;
    letter-spacing: 1px; margin-top: 4px; color: inherit;
  }

  /* LED section */
  .led-section {
    background: #111; border: 1px solid #222;
    border-radius: 16px; padding: 1rem 1.2rem; margin: 1rem 0;
  }
  .section-title {
    font-size: 0.68rem; text-transform: uppercase;
    letter-spacing: 3px; color: #555; margin-bottom: 0.8rem;
  }
  .color-swatches { display: flex; gap: 10px; flex-wrap: wrap; }
  .swatch {
    width: 32px; height: 32px; border-radius: 50%;
    cursor: pointer; border: 2px solid transparent;
    transition: transform 0.15s ease;
  }
  .swatch.selected { border-color: #fff; transform: scale(1.15); }

  /* Sync button */
  .sync-row {
    display: flex; justify-content: center; margin-top: 1.2rem;
  }

  /* Streamlit overrides */
  .stSlider > div > div > div > div { background: #fa5400 !important; }
  div[data-testid="stSlider"] label { color: #888 !important; font-size: 0.72rem !important; letter-spacing: 2px !important; text-transform: uppercase !important; }
  .stButton > button {
    border-radius: 30px !important; font-weight: 600 !important;
    font-size: 0.85rem !important; letter-spacing: 1px !important;
    padding: 0.55rem 1.6rem !important;
  }
  .stButton > button[kind="primary"] {
    background: #fa5400 !important; border: none !important; color: #fff !important;
  }
  .stButton > button[kind="secondary"] {
    background: #1a1a1a !important; border: 1px solid #333 !important; color: #ccc !important;
  }
  div[data-testid="stHorizontalBlock"] { gap: 0.5rem; }
  .stTabs [data-baseweb="tab-list"] { background: #111; border-radius: 12px; padding: 4px; }
  .stTabs [data-baseweb="tab"] { border-radius: 8px; color: #888 !important; }
  .stTabs [aria-selected="true"] { background: #1e1e1e !important; color: #fff !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state init ───────────────────────────────────────────────────────
defaults = {
    "left_fit": 72,
    "right_fit": 72,
    "left_battery": 84,
    "right_battery": 79,
    "fit_mode": "Snug",
    "led_color": "#fa5400",
    "is_connected": True,
    "last_synced": "Just now",
    "syncing": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Header ───────────────────────────────────────────────────────────────────
conn_color = "#4ade80" if st.session_state.is_connected else "#ef4444"
conn_text  = "Connected" if st.session_state.is_connected else "Disconnected"

st.markdown(f"""
<div class="nike-header">
  <div class="nike-logo">NIKE ADAPT</div>
  <div class="connected-badge" style="color:{conn_color}">
    <span class="dot" style="background:{conn_color}"></span>
    {conn_text}
  </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_fit, tab_led, tab_info = st.tabs(["👟  FIT", "💡  LEDS", "ℹ️  INFO"])

# ═══════════════════════════════════════════════════════════════════════════
# TAB FIT
# ═══════════════════════════════════════════════════════════════════════════
with tab_fit:

    # Fit modes
    st.markdown('<div class="section-title">Fit Mode</div>', unsafe_allow_html=True)

    modes = [
        ("🌊", "Loose"),
        ("👟", "Snug"),
        ("⚡", "Sport"),
        ("🔒", "Lock"),
    ]

    cols = st.columns(4)
    for i, (icon, name) in enumerate(modes):
        with cols[i]:
            active = st.session_state.fit_mode == name
            btn_style = "background:#fff;color:#000;border:2px solid #fff" if active else "background:#161616;color:#ccc;border:1px solid #2a2a2a"
            if st.button(f"{icon}\n{name}", key=f"mode_{name}", use_container_width=True):
                st.session_state.fit_mode = name
                if name == "Loose":
                    st.session_state.left_fit  = 20
                    st.session_state.right_fit = 20
                elif name == "Snug":
                    st.session_state.left_fit  = 65
                    st.session_state.right_fit = 65
                elif name == "Sport":
                    st.session_state.left_fit  = 85
                    st.session_state.right_fit = 85
                elif name == "Lock":
                    st.session_state.left_fit  = 100
                    st.session_state.right_fit = 100
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Left shoe
    def battery_color(pct):
        if pct > 50: return "#4ade80"
        if pct > 20: return "#facc15"
        return "#ef4444"

    def render_shoe_card(side: str, fit: int, battery: int):
        b_color = battery_color(battery)
        st.markdown(f"""
        <div class="shoe-card">
          <div class="shoe-title">{side} Shoe</div>
          <div class="shoe-name">Nike Adapt BB 2.0</div>
          <div class="fit-display">{fit}<span style="font-size:1.5rem">%</span></div>
          <div class="fit-label">Tightness</div>
          <div class="battery-row">
            <span style="font-size:0.7rem;color:#555">🔋</span>
            <div class="battery-bar">
              <div class="battery-fill" style="width:{battery}%;background:{b_color}"></div>
            </div>
            <span class="battery-pct" style="color:{b_color}">{battery}%</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    render_shoe_card("Left",  st.session_state.left_fit,  st.session_state.left_battery)
    st.session_state.left_fit = st.slider(
        "LEFT TIGHTNESS", 0, 100, st.session_state.left_fit, key="sl_left"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    render_shoe_card("Right", st.session_state.right_fit, st.session_state.right_battery)
    st.session_state.right_fit = st.slider(
        "RIGHT TIGHTNESS", 0, 100, st.session_state.right_fit, key="sl_right"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Sync button
    col_l, col_sync, col_r = st.columns([1, 2, 1])
    with col_sync:
        if st.button("⟳  SYNC BOTH", use_container_width=True, type="primary"):
            with st.spinner("Syncing with shoes…"):
                time.sleep(1.2)
            avg = (st.session_state.left_fit + st.session_state.right_fit) // 2
            st.session_state.left_fit  = avg
            st.session_state.right_fit = avg
            st.session_state.last_synced = "Just now"
            st.success("Both shoes synced!")
            time.sleep(0.8)
            st.rerun()

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("−  Loosen all", use_container_width=True, type="secondary"):
            st.session_state.left_fit  = max(0, st.session_state.left_fit  - 10)
            st.session_state.right_fit = max(0, st.session_state.right_fit - 10)
            st.rerun()
    with col_b:
        if st.button("+  Tighten all", use_container_width=True, type="secondary"):
            st.session_state.left_fit  = min(100, st.session_state.left_fit  + 10)
            st.session_state.right_fit = min(100, st.session_state.right_fit + 10)
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# TAB LED
# ═══════════════════════════════════════════════════════════════════════════
with tab_led:
    st.markdown("<br>", unsafe_allow_html=True)

    led_colors = {
        "Nike Orange":  "#fa5400",
        "Ice Blue":     "#00c8ff",
        "Electric Lime":"#aaff00",
        "Hot Pink":     "#ff2d78",
        "Pure White":   "#ffffff",
        "Off":          "#222222",
    }

    st.markdown('<div class="section-title">LED Color</div>', unsafe_allow_html=True)

    cols2 = st.columns(3)
    for idx, (label, hex_c) in enumerate(led_colors.items()):
        with cols2[idx % 3]:
            selected = st.session_state.led_color == hex_c
            border = "3px solid #fff" if selected else "2px solid #333"
            if st.button(
                f"{'✓ ' if selected else ''}{label}",
                key=f"led_{label}",
                use_container_width=True,
                type="primary" if selected else "secondary",
            ):
                st.session_state.led_color = hex_c
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    preview_hex = st.session_state.led_color
    glow = "0" if preview_hex == "#222222" else f"0 0 30px {preview_hex}88, 0 0 60px {preview_hex}44"
    st.markdown(f"""
    <div style="text-align:center; padding: 2rem;">
      <div style="
        width: 100px; height: 100px;
        border-radius: 50%; margin: 0 auto;
        background: {preview_hex};
        box-shadow: {glow};
        transition: all 0.4s ease;
      "></div>
      <div style="margin-top:1rem; font-size:0.75rem; color:#666; letter-spacing:2px; text-transform:uppercase;">
        LED Preview
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Brightness
    brightness = st.slider("BRIGHTNESS", 0, 100, 80, key="brightness")

    col_led1, col_led2 = st.columns(2)
    with col_led1:
        if st.button("Flash Mode", use_container_width=True, type="secondary"):
            st.info("Flash mode activated!")
    with col_led2:
        if st.button("Pulse Mode", use_container_width=True, type="secondary"):
            st.info("Pulse mode activated!")

# ═══════════════════════════════════════════════════════════════════════════
# TAB INFO
# ═══════════════════════════════════════════════════════════════════════════
with tab_info:
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#111;border:1px solid #222;border-radius:16px;padding:1.2rem 1.4rem;margin-bottom:1rem;">
      <div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:3px;color:#555;margin-bottom:0.6rem">Device</div>
      <table style="width:100%;font-size:0.85rem;color:#ccc;border-collapse:collapse;">
        <tr><td style="padding:6px 0;color:#666">Model</td><td style="text-align:right">Nike Adapt BB 2.0</td></tr>
        <tr><td style="padding:6px 0;color:#666">Firmware</td><td style="text-align:right">v3.1.4</td></tr>
        <tr><td style="padding:6px 0;color:#666">Connection</td><td style="text-align:right;color:#4ade80">Bluetooth 5.0</td></tr>
        <tr><td style="padding:6px 0;color:#666">Last synced</td><td style="text-align:right">Just now</td></tr>
      </table>
    </div>
    """, unsafe_allow_html=True)

    left_b  = st.session_state.left_battery
    right_b = st.session_state.right_battery
    lc = battery_color(left_b)
    rc = battery_color(right_b)

    st.markdown(f"""
    <div style="background:#111;border:1px solid #222;border-radius:16px;padding:1.2rem 1.4rem;margin-bottom:1rem;">
      <div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:3px;color:#555;margin-bottom:0.8rem">Battery</div>
      <div style="display:flex;gap:1rem;">
        <div style="flex:1;text-align:center;">
          <div style="font-family:'Bebas Neue',sans-serif;font-size:2.5rem;color:{lc}">{left_b}%</div>
          <div style="font-size:0.65rem;color:#555;letter-spacing:2px">LEFT</div>
        </div>
        <div style="width:1px;background:#222;"></div>
        <div style="flex:1;text-align:center;">
          <div style="font-family:'Bebas Neue',sans-serif;font-size:2.5rem;color:{rc}">{right_b}%</div>
          <div style="font-size:0.65rem;color:#555;letter-spacing:2px">RIGHT</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_u1, col_u2 = st.columns(2)
    with col_u1:
        if st.button("Check Update", use_container_width=True, type="secondary"):
            with st.spinner("Checking…"):
                time.sleep(1)
            st.success("Already up to date!")
    with col_u2:
        if st.button("Reset Shoes", use_container_width=True, type="secondary"):
            with st.spinner("Resetting…"):
                time.sleep(1.5)
            st.session_state.left_fit  = 72
            st.session_state.right_fit = 72
            st.success("Reset done!")
            time.sleep(0.8)
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;color:#333;font-size:0.65rem;letter-spacing:2px;text-transform:uppercase;">
      Nike Adapt App · Simulation · 2026
    </div>
    """, unsafe_allow_html=True)
