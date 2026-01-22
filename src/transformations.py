import numpy as np

CONST_R = 8.314

def isotherme(V, n, T):
    """
    Renvoie la pression P = nRT / V (Gaz Parfait)
    """
    return (n * CONST_R * T) / V

def adiabatique(V, P0, V0, gamma):
    """
    Renvoie la pression P = P0 * (V0 / V)**gamma (Transformation Adiabatique Gaz Parfait)
    """
    return P0 * (V0 / V)**gamma

def van_der_waals(V, n, T, a, b):
    """
    Equation d'état de Van der Waals: P = nRT/(V-nb) - an^2/V^2
    """
    term1 = (n * CONST_R * T) / (V - n * b)
    term2 = (a * (n**2)) / (V**2)
    return term1 - term2
