import numpy as np
from src.transformations import isotherme, adiabatique, van_der_waals

class ModeleGaz:
    """
    Classe de base pour les modèles de gaz.
    """
    def __init__(self, n=1.0, gamma=1.4):
        self.n = n
        self.gamma = gamma
        self.R = 8.314

    def pression(self, V, T):
        """Renvoie la pression pour un V et T donnés."""
        raise NotImplementedError

    def temperature(self, P, V):
        """Renvoie la température pour un P et V donnés."""
        raise NotImplementedError
    
    def pression_adiabatique(self, V, P0, V0):
        """
        Renvoie la pression après une transformation adiabatique partant de (P0, V0).
        Par défaut: comportement Gaz Parfait, surcharger pour gaz réels.
        """
        return adiabatique(V, P0, V0, self.gamma)

    def variation_entropie(self, T, V, T_ref, V_ref):
        """
        Calcule S(T, V) - S(T_ref, V_ref).
        Formule générale pour GP et VdW (avec b=0 pour GP):
        Delta S = n * Cv * ln(T/T_ref) + n * R * ln((V - nb)/(V_ref - nb))
        """
        # Cv molaire = R / (gamma - 1)
        # Cv total = n * Cv_molaire
        Cv = (self.n * self.R) / (self.gamma - 1)
        
        # Gestion du covolume b (0 pour Gaz Parfait)
        b = getattr(self, 'b', 0) * self.n
        
        term_T = Cv * np.log(T / T_ref)
        
        # Protection contre log(<=0)
        V_eff = np.maximum(1e-10, V - b)
        V_ref_eff = np.maximum(1e-10, V_ref - b)
        
        term_V = self.n * self.R * np.log(V_eff / V_ref_eff)
        
        return term_T + term_V

class GazParfait(ModeleGaz):
    """
    Modèle de Gaz Parfait (PV = nRT).
    """
    def pression(self, V, T):
        return isotherme(V, self.n, T)

    def temperature(self, P, V):
        return (P * V) / (self.n * self.R)

class GazVanDerWaals(ModeleGaz):
    """
    Modèle de Gaz de Van der Waals.
    Paramètres a (attraction) et b (covolume).
    """
    def __init__(self, n=1.0, gamma=1.4, a=0.0, b=0.0):
        super().__init__(n, gamma)
        self.a = a
        self.b = b

    def pression(self, V, T):
        return van_der_waals(V, self.n, T, self.a, self.b)
    
    def temperature(self, P, V):
        # (P + an^2/V^2)(V - nb) = nRT
        term1 = P + (self.a * self.n**2) / V**2
        term2 = V - self.n * self.b
        return (term1 * term2) / (self.n * self.R)
    
    def pression_adiabatique(self, V, P0, V0):
        """
        Adiabatique pour Van der Waals (approx. Cv constant):
        T * (V - nb)^(gamma - 1) = constant
        """
        # 1. Calculer T0 à partir de P0, V0
        T0 = self.temperature(P0, V0)
        
        # 2. Calculer T au nouveau volume V
        # T_new = T0 * ((V0 - nb) / (V - nb))**(gamma - 1)
        
        # Sécurité pour éviter division par zéro ou volume interdit
        if np.any(V <= self.n * self.b):
             # On pourrait lever une erreur, mais pour l'instant on laisse passer
             pass 

        T_new = T0 * ((V0 - self.n * self.b) / (V - self.n * self.b))**(self.gamma - 1)
        
        # 3. Calculer P à partir de T_new et V
        return self.pression(V, T_new)
