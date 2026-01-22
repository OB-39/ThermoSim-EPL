import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.gas_models import GazParfait, GazVanDerWaals
from src.cycles import CycleOtto, CycleDiesel

# Configuration Initiale
INIT_TAU = 8.0
INIT_TMAX = 2000.0
# Valeurs fixes
V_MAX = 1.0e-3
P_A = 1.013e5
T_A = 300.0
R = 8.314
# Estimation n
n_moles = (P_A * V_MAX) / (R * T_A)

class ThermoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulation Moteur Thermique - Tkinter Modernisé")
        self.geometry("1200x800")
        
        # === Configuration du Style (Look & Feel) ===
        style = ttk.Style()
        style.theme_use('clam')  # Base moderne
        
        # Couleurs et Polices
        bg_color = "#f4f6f9"
        panel_color = "#ffffff"
        accent_color = "#3498db"
        text_color = "#2c3e50"
        font_main = ("Segoe UI", 10)
        font_header = ("Segoe UI", 12, "bold")
        
        self.configure(bg=bg_color)
        style.configure("TFrame", background=bg_color)
        style.configure("Panel.TFrame", background=panel_color)
        style.configure("TLabel", background=panel_color, foreground=text_color, font=font_main)
        style.configure("Header.TLabel", font=font_header, foreground=accent_color)
        style.configure("TRadiobutton", background=panel_color, font=font_main)
        style.configure("TLabelframe", background=panel_color, foreground=text_color)
        style.configure("TLabelframe.Label", font=font_header, background=panel_color, foreground=accent_color)
        style.configure("TButton", font=font_main)
        
        # Configuration Grid principale
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # === 1. Panneau Contrôle (Gauche) ===
        # Un conteneur avec un style "Panel" (fond blanc) et une ombre (simulée par padding/border si besoin, ici simple)
        self.control_panel = ttk.Frame(self, style="Panel.TFrame", padding="20")
        self.control_panel.grid(row=0, column=0, sticky="ns", padx=(0, 2))
        
        # Titre de l'App
        ttk.Label(self.control_panel, text="SimuThermo", font=("Segoe UI", 20, "bold"), background=panel_color).pack(pady=(0, 20))

        # --- Groupe 1 : Choix du Cycle ---
        self.frame_cycle = ttk.LabelFrame(self.control_panel, text="Modèle de Cycle", padding="15")
        self.frame_cycle.pack(fill="x", pady=10)
        
        self.cycle_mode = tk.StringVar(value="Otto_Ideal")
        cycles = [
            ("Otto (Gaz Parfait)", "Otto_Ideal"),
            ("Otto (Van der Waals)", "Otto_VdW"),
            ("Diesel (Gaz Parfait)", "Diesel_Ideal"),
            ("Diesel (Van der Waals)", "Diesel_VdW"),
        ]
        
        for text, val in cycles:
            ttk.Radiobutton(self.frame_cycle, text=text, variable=self.cycle_mode, 
                            value=val, command=self.update_plot).pack(anchor="w", pady=2)

        # --- Groupe 2 : Paramètres ---
        self.frame_params = ttk.LabelFrame(self.control_panel, text="Paramètres Thermodynamiques", padding="15")
        self.frame_params.pack(fill="x", pady=10)

        # Slider Taux de Compression (Tau)
        self.var_tau = tk.DoubleVar(value=INIT_TAU)
        frame_tau = ttk.Frame(self.frame_params, style="Panel.TFrame")
        frame_tau.pack(fill="x", pady=(5, 0))
        ttk.Label(frame_tau, text="Taux Compression (τ)").pack(side="left")
        self.lbl_tau_val = ttk.Label(frame_tau, text=f"{INIT_TAU:.1f}", font=("Segoe UI", 10, "bold"))
        self.lbl_tau_val.pack(side="right")
        
        self.scale_tau = ttk.Scale(self.frame_params, from_=4.0, to=25.0, 
                                   variable=self.var_tau, command=self.on_param_change)
        self.scale_tau.pack(fill="x", pady=(5, 15))

        # Slider T_max
        self.var_tmax = tk.DoubleVar(value=INIT_TMAX)
        frame_tmax = ttk.Frame(self.frame_params, style="Panel.TFrame")
        frame_tmax.pack(fill="x", pady=(5, 0))
        ttk.Label(frame_tmax, text="Température Max (K)").pack(side="left")
        self.lbl_tmax_val = ttk.Label(frame_tmax, text=f"{INIT_TMAX:.0f}", font=("Segoe UI", 10, "bold"))
        self.lbl_tmax_val.pack(side="right")
        
        self.scale_tmax = ttk.Scale(self.frame_params, from_=800.0, to=4000.0, 
                                    variable=self.var_tmax, command=self.on_param_change)
        self.scale_tmax.pack(fill="x", pady=(5, 5))
        
        # --- Groupe 3 : Résultats ---
        self.frame_results = ttk.LabelFrame(self.control_panel, text="Performances", padding="15")
        self.frame_results.pack(fill="x", pady=20)
        
        self.lbl_work = ttk.Label(self.frame_results, text="Travail: --- J", font=("Consolas", 11))
        self.lbl_work.pack(anchor="w", pady=2)
        
        self.lbl_heat = ttk.Label(self.frame_results, text="Chaleur: --- J", font=("Consolas", 11))
        self.lbl_heat.pack(anchor="w", pady=2)
        
        self.lbl_eta = ttk.Label(self.frame_results, text="Rendement: --- %", font=("Consolas", 12, "bold"), foreground="#27ae60")
        self.lbl_eta.pack(anchor="w", pady=8)

        # === 2. Zone Graphique (Droite) ===
        self.plot_frame = ttk.Frame(self, style="TFrame") # Fond gris clair pour détacher le graph
        self.plot_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # Style Matplotlib
        try:
            plt.style.use('bmh') # 'ggplot', 'seaborn-v0_8', ou 'bmh' sont jolis
        except:
            pass # Fallback défaut
            
        # Figure Matplotlib avec couleur de fond adaptée
        self.fig, self.ax = plt.subplots(figsize=(6, 5), dpi=100)
        self.fig.patch.set_facecolor(bg_color) # Fond de la figure correspond à l'app
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Ombre portée simulée autour du canvas (optionnel, simple border ici)
        self.canvas_widget.configure(highlightthickness=1, highlightbackground="#bdc3c7")

        # Premier tracé
        self.update_plot()

    def on_param_change(self, event=None):
        # Mettre à jour les labels de valeur
        self.lbl_tau_val.config(text=f"{self.var_tau.get():.1f}")
        self.lbl_tmax_val.config(text=f"{self.var_tmax.get():.0f}")
        # Mettre à jour le graphique
        self.update_plot()

    def update_plot(self, event=None):
        mode = self.cycle_mode.get()
        tau = self.var_tau.get()
        t_max = self.var_tmax.get()
        
        # Paramètres dérivés
        v_min = V_MAX / tau
        
        cycle = None
        
        if mode == "Otto_Ideal":
            gaz = GazParfait(n=n_moles, gamma=1.4)
            cycle = CycleOtto(gaz, v_min, V_MAX, T_A, P_A, t_max)
            
        elif mode == "Otto_VdW":
             # Constantes pour N2
            a_n2 = 0.14
            b_n2 = 3.9e-5
            gaz = GazVanDerWaals(n=n_moles, gamma=1.4, a=a_n2, b=b_n2)
            cycle = CycleOtto(gaz, v_min, V_MAX, T_A, P_A, t_max)
            
        elif mode == "Diesel_Ideal":
            gaz = GazParfait(n=n_moles, gamma=1.4)
            cycle = CycleDiesel(gaz, v_min, V_MAX, T_A, P_A, t_max)

        elif mode == "Diesel_VdW":
            # Constantes pour N2
            a_n2 = 0.14
            b_n2 = 3.9e-5
            gaz = GazVanDerWaals(n=n_moles, gamma=1.4, a=a_n2, b=b_n2)
            cycle = CycleDiesel(gaz, v_min, V_MAX, T_A, P_A, t_max)
        
        # Calculs
        try:
            cycle.calculer_points_cycle()
            res = cycle.calculer_rendement()
            
            # Mise à jour UI Résultats
            self.lbl_work.config(text=f"Travail:   {res['W_total']:.1f} J")
            self.lbl_heat.config(text=f"Chaleur in:{res['Q_in']:.1f} J")
            self.lbl_eta.config(text=f"Rendement: {res['eta_numerique']*100:.2f} %")
            
            # Tracé
            self.ax.clear()
            cycle.tracer_sur_axe(self.ax)
            
            # Amélioration Cosmesique du Graphique
            self.ax.set_title(f"Cycle {mode.replace('_', ' ')}", fontsize=12, fontweight='bold')
            self.ax.grid(True, linestyle='--', alpha=0.7)
            self.ax.legend(loc='upper right', frameon=True, fancybox=True, framealpha=0.9)
            
            self.canvas.draw()
        except Exception as e:
            print(f"Erreur calcul: {e}")

if __name__ == "__main__":
    app = ThermoApp()
    app.mainloop()
