import streamlit as st
import numpy as np
import plotly.graph_objects as go
from src.gas_models import GazParfait, GazVanDerWaals
from src.cycles import CycleOtto, CycleDiesel

# =============================================================================
# 1. CONFIGURATION & STYLES
# =============================================================================
st.set_page_config(
    page_title="ThermoSim | EPL",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Mode Professional Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary-color: #6366f1; /* Indigo 500 */
        --bg-color: #0f172a;      /* Slate 900 */
        --card-bg: #1e293b;       /* Slate 800 */
        --text-main: #f8fafc;
        --text-sub: #94a3b8;
        --border-color: #334155;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: var(--text-main);
        background-color: var(--bg-color);
    }
    
    /* Clean up default Streamlit UI */
    #MainMenu, footer, header {visibility: hidden;}
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 1400px;
    }

    /* Cards */
    div[data-testid="stMetric"] {
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: var(--primary-color);
    }
    div[data-testid="stMetricLabel"] {
        color: var(--text-sub);
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="stMetricValue"] {
        color: var(--text-main);
        font-weight: 700;
        font-size: 1.8rem;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1f2937;
    }
    
    /* Tables */
    .stTable {
        background-color: var(--card-bg);
        border-radius: 8px;
        border: 1px solid var(--border-color);
        overflow: hidden;
    }

    /* Headers */
    h1 {
        background: linear-gradient(90deg, #818cf8, #c7d2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# 2. BARRE LATÉRALE (CONTROLS)
# =============================================================================

# Logo & Branding
st.sidebar.image("assets/logo_epl.png", use_container_width=True)
st.sidebar.markdown("## ⚙️ Configuration")
st.sidebar.markdown("---")

# Section: Paramètres du Cycle
with st.sidebar.expander("🛠️ Modélisation", expanded=True):
    cycle_type = st.selectbox("Type de Cycle", ["Otto (Beau de Rochas)", "Diesel"])
    gas_model = st.selectbox("Modèle de Gaz", ["Gaz Parfait", "Van der Waals (N2)"])

with st.sidebar.expander("🌡️ Paramètres Thermodynamiques", expanded=True):
    tau = st.slider("Taux de Compression (τ)", 4.0, 25.0, 8.0, 0.1)
    t_max = st.slider("Température Max (K)", 800, 3500, 2000, 50)

# Section: Outils d'Analyse
st.sidebar.markdown("### 🔬 Outils d'Analyse")

col_ref1, col_ref2 = st.sidebar.columns(2)
if 'ref_curves' not in st.session_state:
    st.session_state['ref_curves'] = None
    st.session_state['ref_name'] = None

if col_ref1.button("📸 Figer Ref.", help="Sauvegarder la courbe actuelle en arrière-plan"):
    st.session_state['ref_capture_trigger'] = True # Logic handled later

if col_ref2.button("🗑️ Effacer", help="Supprimer la référence"):
    st.session_state['ref_curves'] = None
    st.session_state['ref_name'] = None

# Section: Exploitation Moteur
st.sidebar.markdown("### 🏎️ Exploitation Moteur")
rpm = st.sidebar.number_input("Régime (RPM)", 500, 10000, 3000, 100)
st.sidebar.caption("Pour un monocylindre de 1.0 Litre.")


# =============================================================================
# 3. BACKEND : CALCULS
# =============================================================================

# Constantes Physiques
V_MAX = 1.0e-3 # 1 Litre
P_A = 1.013e5  # 1 atm
T_A = 300.0    # 27°C
R = 8.314
n_moles = (P_A * V_MAX) / (R * T_A)

v_min = V_MAX / tau

# Instanciation Gaz
if gas_model == "Gaz Parfait":
    gaz = GazParfait(n=n_moles, gamma=1.4)
else:
    gaz = GazVanDerWaals(n=n_moles, gamma=1.4, a=0.14, b=3.9e-5) # N2 constants

# Instanciation Cycle
cycle_obj = None
if cycle_type == "Otto (Beau de Rochas)":
    cycle_obj = CycleOtto(gaz, v_min, V_MAX, T_A, P_A, float(t_max))
else:
    cycle_obj = CycleDiesel(gaz, v_min, V_MAX, T_A, P_A, float(t_max))

# Exécution des calculs
try:
    cycle_obj.calculer_points_cycle()
    res = cycle_obj.calculer_rendement()
    
    # Gestion Capture Référence
    if st.session_state.get('ref_capture_trigger'):
        st.session_state['ref_name'] = f"{cycle_type} (τ={tau})"
        # Capture raw curves
        ref_data = []
        # P-V segments
        ref_data.append(cycle_obj.obtenir_courbe_adiabatique('A', 'B'))
        ref_data.append(([cycle_obj.points['B'][0], cycle_obj.points['C'][0]], 
                         [cycle_obj.points['B'][1], cycle_obj.points['C'][1]]))
        ref_data.append(cycle_obj.obtenir_courbe_adiabatique('C', 'D'))
        ref_data.append(([cycle_obj.points['D'][0], cycle_obj.points['A'][0]], 
                         [cycle_obj.points['D'][1], cycle_obj.points['A'][1]]))
        st.session_state['ref_curves'] = ref_data
        st.session_state['ref_capture_trigger'] = False
        st.toast(f"Référence '{st.session_state['ref_name']}' sauvegardée !", icon="📸")

    # Calculs Moteur (Power)
    cycles_per_sec = rpm / 60 / 2 # 4 temps
    power_kw = (res['W_total'] * cycles_per_sec) / 1000
    torque_nm = (res['W_total'] * cycles_per_sec * 1000) / (2 * np.pi * (rpm/60)) if rpm > 0 else 0

except Exception as e:
    st.error(f"Erreur de calcul : {e}")
    st.stop()


# =============================================================================
# 4. FRONTEND : VISUALISATION
# =============================================================================

col1, col2 = st.columns([0.7, 0.3])
with col1:
    st.title("Simulateur Moteur Thermique")
with col2:
    # Status badges
    st.markdown(f"""
    <div style='text-align: right; padding-top: 10px;'>
        <span style='background-color: #3730a3; padding: 5px 10px; border-radius: 15px; font-size: 0.8em; margin-right: 5px;'>{cycle_type}</span>
        <span style='background-color: #065f46; padding: 5px 10px; border-radius: 15px; font-size: 0.8em;'>{gas_model}</span>
    </div>
    """, unsafe_allow_html=True)
    if st.session_state['ref_name']:
         st.markdown(f"<div style='text-align: right; font-size: 0.8em; color: gray; margin-top: 5px;'>Versus: {st.session_state['ref_name']}</div>", unsafe_allow_html=True)


tabs = st.tabs(["📊 Labo Virtuel", "📈 Étude Paramétrique", "📋 Données", "🎓 Projet EPL"])

# --- TAB 1: LABO VIRTUEL (MAIN DASHBOARD) ---
# --- TAB 1: LABO VIRTUEL (MAIN DASHBOARD) ---
with tabs[0]:
    # 1. LIGNE DES MÉTRIQUES (Haut)
    st.markdown("###  Performances Temps Réel")
    m1, m2, m3, m4 = st.columns(4)
    
    eta = res['eta_numerique'] * 100
    m1.metric("Rendement (η)", f"{eta:.2f} %", delta=f"{eta-50:.1f} pts" if eta > 50 else None)
    m2.metric("Travail Net (W)", f"{res['W_total']:.0f} J")
    m3.metric("Puissance", f"{power_kw:.1f} kW", f"{rpm} rpm", delta_color="off")
    m4.metric("Couple", f"{torque_nm:.0f} N.m")

    st.markdown("---")

    # 2. GRAPHIQUES CÔTE À CÔTE (Bas)
    col_pv, col_ts = st.columns(2)
    
    with col_pv:
        st.subheader("1. Diagramme de Clapeyron (P, V)")
        
        fig_pv = go.Figure()
        
        # --- Reference Overlay ---
        if st.session_state['ref_curves']:
            for rx, ry in st.session_state['ref_curves']:
                fig_pv.add_trace(go.Scatter(x=np.array(rx)*1000, y=np.array(ry)/1e5, mode='lines', 
                                       line=dict(color='rgba(255,255,255,0.2)', width=2, dash='dash'), hoverinfo='skip', showlegend=False))

        # --- Active Cycle Segments ---
        colors = ['#6366f1', '#f43f5e', '#ec4899', '#10b981'] # Indigo, Rose, Pink, Emerald
        
        # 1. A->B
        vx, vy = cycle_obj.obtenir_courbe_adiabatique('A', 'B')
        fig_pv.add_trace(go.Scatter(x=vx*1000, y=vy/1e5, mode='lines', name='Compression', line=dict(color=colors[0], width=3)))
        
        # 2. B->C
        fig_pv.add_trace(go.Scatter(
            x=[cycle_obj.points['B'][0]*1000, cycle_obj.points['C'][0]*1000],
            y=[cycle_obj.points['B'][1]/1e5, cycle_obj.points['C'][1]/1e5],
            mode='lines', name='Combustion', line=dict(color=colors[1], width=3)
        ))

        # 3. C->D
        vx, vy = cycle_obj.obtenir_courbe_adiabatique('C', 'D')
        fig_pv.add_trace(go.Scatter(x=vx*1000, y=vy/1e5, mode='lines', name='Détente', line=dict(color=colors[2], width=3)))

        # 4. D->A
        fig_pv.add_trace(go.Scatter(
            x=[cycle_obj.points['D'][0]*1000, cycle_obj.points['A'][0]*1000],
            y=[cycle_obj.points['D'][1]/1e5, cycle_obj.points['A'][1]/1e5],
            mode='lines', name='Échappement', line=dict(color=colors[3], width=3)
        ))
        
        # Points Markers
        for p in "ABCD":
            pt = cycle_obj.points[p]
            fig_pv.add_trace(go.Scatter(x=[pt[0]*1000], y=[pt[1]/1e5], mode='markers+text', text=[p], textposition="top right",
                                        marker=dict(size=10, color='white'), showlegend=False))

        fig_pv.update_layout(
            template="plotly_dark", 
            xaxis_title="Volume (L)", 
            yaxis_title="Pression (bar)",
            height=450,
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig_pv, use_container_width=True)

    with col_ts:
        st.subheader("2. Diagramme Entropique (T, S)")
        
        try:
            S_list, T_list, names = cycle_obj.generer_donnees_entropie()
            fig_ts = go.Figure()
            
            # Use same colors as PV diagram for consistency
            cols = ['#6366f1', '#f43f5e', '#ec4899', '#10b981']
            
            for i, (s, t) in enumerate(zip(S_list, T_list)):
                fig_ts.add_trace(go.Scatter(x=s, y=t, mode='lines', name=names[i], line=dict(color=cols[i], width=3), showlegend=False))
            
            # Points Markers for TS (Approximation for visualization)
            # Note: S values are relative in the generator, so we take the start/end of segments
            # A is start of segment 0, B is end of 0/start of 1, etc.
            # This is a bit tricky to map perfectly without stored S points, so we rely on lines.
            
            fig_ts.update_layout(
                template="plotly_dark",
                xaxis_title="Entropie Spécifique ΔS (J/K)", 
                yaxis_title="Température (K)",
                height=450,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig_ts, use_container_width=True)
            
        except Exception as e:
            st.warning(f"Diagramme T-S indisponible: {e}")
            st.info("Vérifiez l'implémentation de `generer_donnees_entropie` dans `cycles.py`.")


# --- TAB 2: ANALYSE PARAMETRIQUE ---
with tabs[1]:
    st.header("📈 Sensibilité au Taux de Compression")
    st.markdown("Influence du taux de compression $\\tau$ sur le rendement $\\eta$.")
    
    # Computation heavy - cache if possible, but here fast enough
    tau_x = np.linspace(4, 30, 40)
    eta_y = []
    
    for tx in tau_x:
        v_min_x = V_MAX / tx
        if cycle_type.startswith("Otto"):
            c = CycleOtto(gaz, v_min_x, V_MAX, T_A, P_A, t_max)
        else:
            c = CycleDiesel(gaz, v_min_x, V_MAX, T_A, P_A, t_max)
        try:
            c.calculer_points_cycle()
            eta_y.append(c.calculer_rendement()['eta_numerique'] * 100)
        except:
            eta_y.append(None)
            
    fig_sens = go.Figure()
    fig_sens.add_trace(go.Scatter(x=tau_x, y=eta_y, mode='lines', name='Courbe Théorique', line=dict(color='#818cf8', width=3)))
    fig_sens.add_trace(go.Scatter(x=[tau], y=[eta], mode='markers', name='Point Actuel', marker=dict(color='#f472b6', size=15, symbol='diamond')))
    
    fig_sens.update_layout(template="plotly_dark", xaxis_title="Taux de Compression", yaxis_title="Rendement (%)", height=500)
    st.plotly_chart(fig_sens, use_container_width=True)


# --- TAB 3: DATA EXPORT ---
with tabs[2]:
    st.header("📋 Données Numériques")
    df_data = [
        {"Point": p, "P (bar)": f"{cycle_obj.points[p][1]/1e5:.3f}", "T (K)": f"{cycle_obj.points[p][2]:.1f}", "V (L)": f"{cycle_obj.points[p][0]*1000:.3f}"}
        for p in "ABCD"
    ]
    st.table(df_data)
    st.download_button("📥 Exporter en JSON", data=str(df_data), file_name=f"cycle_{cycle_type.split()[0].lower()}.json")


# --- TAB 4: CONTEXTE PROJET ---
with tabs[3]:
    st.markdown("""
    ## 🎓 Contexte du Projet Académique
    **École Polytechnique de Lomé (EPL) - Projet Étudiant 2026**
    
    ### Sujet : Étude comparative des cycles Otto et Diesel
    Ce simulateur interactif répond au besoin de modéliser le comportement thermodynamique des moteurs à combustion interne, en intégrant des modèles de gaz parfaits et réels.
    
    ### 🎯 Objectifs Scientifiques
    1.  **Thermodynamique** : Application des lois de conservation et des équations d'état.
    2.  **Numérique** : Résolution d'équations non-linéaires (volume combustion Diesel) et intégration numérique (calcul du travail $W = \oint P dV$).
    3.  **Informatique** : Architecture logicielle modulaire en Python.

    ### 📐 Modèles Mathématiques
    
    **Gaz de Van der Waals :**
    $$ (P + \\frac{n^2 a}{V^2})(V - nb) = nRT $$
    
    **Rendement Thermodynamique :**
    $$ \\eta = \\frac{W_{utile}}{Q_{fournie}} = 1 - \\frac{|Q_{out}|}{|Q_{in}|} $$
    """)

# Footer
st.markdown("---")
st.markdown("<center style='color: #64748b; font-size: 0.8em;'>Développé par OHOUNSOUN Bienvenu </center>", unsafe_allow_html=True)
