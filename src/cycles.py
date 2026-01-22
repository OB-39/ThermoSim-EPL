import numpy as np
from scipy.integrate import simpson
import matplotlib.pyplot as plt

class CycleOtto:
    """
    Classe représentant le cycle de Beau de Rochas (Otto).
    """
    def __init__(self, modele_gaz, V_min, V_max, T_A, P_A, T_C_max):
        self.gaz = modele_gaz
        self.V_min = V_min
        self.V_max = V_max
        self.V_A = V_max
        self.T_A = T_A
        self.P_A = P_A
        self.T_C = T_C_max
        self.points = {}
        # Taux de compression
        self.tau = V_max / V_min

    def calculer_points_cycle(self):
        """
        Calcule les points caractéristiques A, B, C, D du cycle.
        """
        # Point A (Admission/Début compression)
        V_A = self.V_max
        P_A = self.P_A
        T_A = self.T_A
        
        # A -> B Compression Adiabatique
        V_B = self.V_min
        # Pression obtenue via transformation adiabatique du modèle de gaz
        P_B = self.gaz.pression_adiabatique(V_B, P_A, V_A)
        T_B = self.gaz.temperature(P_B, V_B)

        # B -> C Échauffement Isochore (Explosion)
        V_C = V_B
        T_C = self.T_C # Température max imposée
        P_C = self.gaz.pression(V_C, T_C)

        # C -> D Détente Adiabatique
        V_D = V_A # Retour au volume max
        P_D = self.gaz.pression_adiabatique(V_D, P_C, V_C)
        T_D = self.gaz.temperature(P_D, V_D)

        self.points = {
            'A': (V_A, P_A, T_A),
            'B': (V_B, P_B, T_B),
            'C': (V_C, P_C, T_C),
            'D': (V_D, P_D, T_D)
        }

    def obtenir_courbe_adiabatique(self, point_depart, point_fin, n_points=100):
        """Génère les tableaux (V, P) pour tracer l'adiabatique entre deux points."""
        V_start, P_start, _ = self.points[point_depart]
        V_end, _, _ = self.points[point_fin]
        
        V_values = np.linspace(V_start, V_end, n_points)
        P_values = self.gaz.pression_adiabatique(V_values, P_start, V_start)
        return V_values, P_values

    def calculer_rendement(self):
        """
        Calcule le travail total et le rendement thermique.
        """
        # Travail A->B (Compression)
        V_ab, P_ab = self.obtenir_courbe_adiabatique('A', 'B')
        W_ab = -simpson(P_ab, x=V_ab) # dV < 0 => W > 0 (reçu)

        # Travail C->D (Détente)
        V_cd, P_cd = self.obtenir_courbe_adiabatique('C', 'D')
        W_cd = -simpson(P_cd, x=V_cd) # dV > 0 => W < 0 (fourni)

        # Travail Total (Cycle)
        W_total = W_ab + W_cd
        
        # Chaleur Reçue (Q_chaud) durant B->C (Isochore)
        # Q = n * Cv * (Tc - Tb)
        # Cv = R / (gamma - 1)
        V_B, P_B, T_B = self.points['B']
        V_C, P_C, T_C = self.points['C']
        
        Cv = self.gaz.R / (self.gaz.gamma - 1)
        Q_in = self.gaz.n * Cv * (T_C - T_B)

        eta_simpson = abs(W_total) / Q_in
        
        # Rendement Théorique (seulement valide pour Gaz Parfait idéal)
        # eta = 1 - 1 / (tau^(gamma-1))
        eta_th = 1 - 1 / (self.tau**(self.gaz.gamma - 1))

        return {
            'W_total': W_total,
            'Q_in': Q_in,
            'eta_numerique': eta_simpson,
            'eta_theorique': eta_th
        }

    def tracer_sur_axe(self, ax):
        """
        Trace le cycle sur un objet Axes matplotlib donné.
        """
        if not self.points:
            self.calculer_points_cycle()
            
        # Courbes Adiabatiques
        Va, Pa = self.obtenir_courbe_adiabatique('A', 'B')
        ax.plot(Va, Pa, label='Compression Adiabatique (A->B)', color='blue')
        
        Vc, Pc = self.obtenir_courbe_adiabatique('C', 'D')
        ax.plot(Vc, Pc, label='Détente Adiabatique (C->D)', color='red')
        
        # Courbes Isochores (Lignes verticales)
        # B->C
        ax.plot([self.points['B'][0], self.points['C'][0]], 
                 [self.points['B'][1], self.points['C'][1]], 
                 label='Combustion Isochore (B->C)', color='orange')
        
        # D->A
        ax.plot([self.points['D'][0], self.points['A'][0]], 
                 [self.points['D'][1], self.points['A'][1]], 
                 label='Refroidissement Isochore (D->A)', color='green')

        # Annotations
        for point, (V, P, T) in self.points.items():
            ax.plot(V, P, 'ko')
            # Annotation légère pour ne pas surcharger
            ax.text(V, P, f' {point}', verticalalignment='bottom', fontweight='bold')

        ax.set_xlabel('Volume ($m^3$)')
        ax.set_ylabel('Pression (Pa)')
        ax.set_title(f'Cycle Otto (Tau={self.tau:.1f}) | {type(self.gaz).__name__}')
        ax.legend()
        ax.grid(True, alpha=0.3)

    def _tracer_courbes(self):
        """Méthode interne pour tracer les courbes. Renvoie l'objet Figure."""
        fig, ax = plt.subplots(figsize=(10, 6))
        self.tracer_sur_axe(ax)
        return fig

    def tracer_cycle(self, save_filename=None):
        fig = self._tracer_courbes()
        
        if save_filename:
            fig.savefig(save_filename)
            plt.close(fig)
            print(f"Graphique sauvegardé : {save_filename}")
        else:
            plt.show()
        return fig

    def generer_donnees_entropie(self, n_points=50):
        """
        Génère les tableaux (S, T) pour tracer le diagramme Entropique.
        Reference S=0 au point A.
        """
        if not self.points:
            self.calculer_points_cycle()
            
        S_data = []
        T_data = []
        labels = []
        
        # Ordre: A->B, B->C, C->D, D->A
        segments = [('A', 'B'), ('B', 'C'), ('C', 'D'), ('D', 'A')]
        
        # Récupération état Ref (A)
        try:
           V_ref, _, T_ref = self.points['A']
        except KeyError:
           return [], [], []

        for p_start, p_end in segments:
            V_start, P_start, T_start = self.points[p_start]
            V_end, P_end, T_end = self.points[p_end]
            
            is_isochoric = abs(V_end - V_start) < 1e-9
            
            if (p_start == 'A' and p_end == 'B') or (p_start == 'C' and p_end == 'D'):
                 V_space = np.linspace(V_start, V_end, n_points)
                 P_space = self.gaz.pression_adiabatique(V_space, P_start, V_start)
                 T_space = self.gaz.temperature(P_space, V_space)
            else:
                is_diesel_combustion = isinstance(self, CycleDiesel) and p_start == 'B'
                
                if is_diesel_combustion:
                    V_space = np.linspace(V_start, V_end, n_points)
                    P_space = np.full(n_points, P_start)
                    T_space = self.gaz.temperature(P_space, V_space)
                elif is_isochoric:
                    V_space = np.full(n_points, V_start)
                    T_space = np.linspace(T_start, T_end, n_points)
                else:
                    V_space = np.linspace(V_start, V_end, n_points)
                    T_space = np.linspace(T_start, T_end, n_points)

            S_space = []
            for v, t in zip(V_space, T_space):
                ds = self.gaz.variation_entropie(t, v, T_ref, V_ref)
                S_space.append(ds)
            
            S_data.append(np.array(S_space))
            T_data.append(np.array(T_space))
            
            label_seg = f"{p_start}->{p_end}"
            labels.append(label_seg)
            
        return S_data, T_data, labels

class CycleDiesel(CycleOtto):
    """
    Classe représentant le cycle Diesel (Combustion Isobare).
    """
    def calculer_points_cycle(self):
        # Point A (Admission)
        V_A = self.V_max
        P_A = self.P_A
        T_A = self.T_A
        
        # A -> B Compression Adiabatique
        V_B = self.V_min
        P_B = self.gaz.pression_adiabatique(V_B, P_A, V_A)
        T_B = self.gaz.temperature(P_B, V_B)

        # B -> C Échauffement Isobare (Combustion)
        T_C = self.T_C
        P_C = P_B # Pression constante
        
        # On doit trouver V_C tel que P(V_C, T_C) approxime P_C ou satisfasse l'équation d'état.
        from scipy.optimize import fsolve
        
        def func_p(v):
            return self.gaz.pression(v, T_C) - P_C
            
        V_C_guess = V_B * (T_C/T_B)
        # Résolution numérique pour trouver V_C
        V_C = fsolve(func_p, V_C_guess)[0]

        # C -> D Détente Adiabatique
        V_D = V_A # V_max
        P_D = self.gaz.pression_adiabatique(V_D, P_C, V_C)
        T_D = self.gaz.temperature(P_D, V_D)

        self.points = {
            'A': (V_A, P_A, T_A),
            'B': (V_B, P_B, T_B),
            'C': (V_C, P_C, T_C),
            'D': (V_D, P_D, T_D)
        }

    def calculer_rendement(self):
        # Travail A->B (Compression)
        V_ab, P_ab = self.obtenir_courbe_adiabatique('A', 'B')
        W_ab = -simpson(P_ab, x=V_ab)

        # Travail B->C (Isobare) = -P * DeltaV
        V_B = self.points['B'][0]
        V_C = self.points['C'][0]
        P_B = self.points['B'][1]
        W_bc = -P_B * (V_C - V_B) 

        # Travail C->D (Détente)
        V_cd, P_cd = self.obtenir_courbe_adiabatique('C', 'D')
        W_cd = -simpson(P_cd, x=V_cd)

        W_total = W_ab + W_bc + W_cd
        
        # Chaleur Reçue (Isobare) -> Cp
        T_B = self.points['B'][2]
        T_C = self.points['C'][2]
        
        Cp = (self.gaz.gamma * self.gaz.R) / (self.gaz.gamma - 1)
        Q_in = self.gaz.n * Cp * (T_C - T_B)
        
        eta = abs(W_total) / Q_in
        
        return {
            'W_total': W_total,
            'Q_in': Q_in,
            'eta_numerique': eta,
            'eta_theorique': float('nan')
        }
    
    def tracer_sur_axe(self, ax):
        super().tracer_sur_axe(ax)
        # Correction du titre et de la légende pour Diesel
        # On suppose que l'ordre de création des plots est Adiabatique1, Adiabatique2, B->C (orange), D->A (green)
        # B->C est la 3ème courbe (index 2 dans ax.lines qui contient aussi les points)
        # Attention: ax.lines contient les segments ET les points 'ko'.
        # L'ordre d'ajout dans tracer_sur_axe:
        # 1. Plot A->B (Line2D)
        # 2. Plot C->D (Line2D)
        # 3. Plot B->C (Line2D) -> C'est celle-ci qu'on veut renommer
        # 4. Plot D->A (Line2D)
        # 5. Points (Line2D sans ligne)
        
        # On cherche la ligne orange par sécurité
        for line in ax.get_lines():
            if line.get_color() == 'orange':
                line.set_label('Combustion Isobare (B->C)')
                break
                
        ax.set_title(f'Cycle Diesel (Tau={self.tau:.1f}) | {type(self.gaz).__name__}')
        ax.legend()

    def _tracer_courbes(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        self.tracer_sur_axe(ax)
        return fig
    
    def tracer_cycle(self, save_filename=None):
        fig = self._tracer_courbes()
        
        if save_filename:
            fig.savefig(save_filename)
            plt.close(fig)
            print(f"Graphique sauvegardé : {save_filename}")
        else:
            plt.show()
        return fig
