"""Algoritmo genético de agrupamiento.

Cromosoma: K centroides en el espacio de entrada (después del escalado y PCA).
Aptitud: silueta sobre una submuestra fija de entrenamiento. Si algún grupo queda por debajo del 12 % de
la submuestra la partición es inviable y pierde contra cualquier viable. El mínimo prometido en la Entrega 2 es 10 %;
el 2 % extra cubre la variación de medir el tamaño sobre solo 1,000 clientes.
Operadores: torneo, cruce uniforme de centroides previamente emparejados, mutación gaussiana
decreciente con reubicación ocasional, elitismo.
"""
import time

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from sklearn.cluster import kmeans_plusplus

from src.models.evaluacion import asignar, silueta_con_distancias


class AGClustering:
    def __init__(self, k=4, poblacion=40, generaciones=60, torneo=3, p_cruce=0.9, p_mutacion=0.2,
                 p_reubicacion=0.02, sigma_inicial=0.5, sigma_final=0.05, elitismo=2,
                 tamano_minimo=0.12, muestra=1000, init="aleatorio", semilla=42):
        self.k, self.poblacion, self.generaciones, self.torneo = k, poblacion, generaciones, torneo
        self.p_cruce, self.p_mutacion, self.p_reubicacion = p_cruce, p_mutacion, p_reubicacion
        self.sigma_inicial, self.sigma_final, self.elitismo = sigma_inicial, sigma_final, elitismo
        self.tamano_minimo, self.muestra = tamano_minimo, muestra
        self.init, self.semilla = init, semilla
        self.centroides_ = None
        self.historial_ = None
        self.tiempo_entrenamiento_ = None

    def parametros(self):
        return {"k": self.k, "poblacion": self.poblacion, "generaciones": self.generaciones, "torneo": self.torneo,
                "p_cruce": self.p_cruce, "p_mutacion": self.p_mutacion, "p_reubicacion": self.p_reubicacion,
                "sigma_inicial": self.sigma_inicial, "sigma_final": self.sigma_final, "elitismo": self.elitismo,
                "tamano_minimo": self.tamano_minimo, "muestra": self.muestra, "init": self.init, "semilla": self.semilla}

    # ------------------------------------------------------------ aptitud
    def _aptitud(self, centroides):
        etiquetas = cdist(self._S, centroides).argmin(axis=1)
        s, frac = silueta_con_distancias(self._D, etiquetas, self.k)
        if s == -1.0:
            return -1.0
        deficit = max(0.0, self.tamano_minimo - frac)
        if deficit > 0:
            # Regla de Deb: una partición que incumple el tamaño mínimo siempre pierde contra una que lo cumple
            # (la silueta de las viables es >= -1) y entre inviables gana la que menos incumple. Sin esto, el
            # algoritmo aprendió a aislar unos pocos valores atípicos en un grupo diminuto para inflar la silueta.
            return -1.0 - deficit
        return s

    # ------------------------------------------------------------ operadores
    def _inicial(self, rng):
        if self.init == "kmeans++":
            return kmeans_plusplus(self._S, self.k, random_state=int(rng.integers(1 << 30)))[0]
        idx = rng.choice(len(self._S), self.k, replace=False)
        return self._S[idx] + rng.normal(0, 0.05, (self.k, self._S.shape[1])) * self._escala

    def _torneo(self, rng, aptitudes):
        candidatos = rng.choice(len(aptitudes), self.torneo, replace=False)
        return candidatos[np.argmax(aptitudes[candidatos])]

    def _cruce(self, rng, a, b):
        # Se empareja cada centroide de b con el más cercano de a para no mezclar grupos distintos.
        fila, col = linear_sum_assignment(cdist(a, b))
        b = b[col[np.argsort(fila)]]
        toma_a = rng.random(self.k) < 0.5
        return np.where(toma_a[:, None], a, b)

    def _mutar(self, rng, c, sigma):
        hijo = c.copy()
        for j in range(self.k):
            if rng.random() < self.p_reubicacion:
                hijo[j] = self._S[rng.integers(len(self._S))]
            elif rng.random() < self.p_mutacion:
                hijo[j] += rng.normal(0, sigma, hijo.shape[1]) * self._escala
        return hijo

    # ------------------------------------------------------------ entrenamiento
    def fit(self, Z):
        inicio = time.perf_counter()
        rng = np.random.default_rng(self.semilla)
        n = len(Z)
        idx = rng.choice(n, min(self.muestra, n), replace=False)
        self._S = np.asarray(Z)[idx]
        self._D = cdist(self._S, self._S)
        self._escala = self._S.std(axis=0)

        pob = [self._inicial(rng) for _ in range(self.poblacion)]
        apt = np.array([self._aptitud(c) for c in pob])
        historial = [(0, apt.max(), apt.mean(), apt.min())]
        for g in range(1, self.generaciones + 1):
            sigma = self.sigma_final + (self.sigma_inicial - self.sigma_final) * (1 - g / self.generaciones)
            orden = np.argsort(apt)[::-1]
            nueva = [pob[i].copy() for i in orden[: self.elitismo]]
            while len(nueva) < self.poblacion:
                a, b = pob[self._torneo(rng, apt)], pob[self._torneo(rng, apt)]
                hijo = self._cruce(rng, a, b) if rng.random() < self.p_cruce else a.copy()
                nueva.append(self._mutar(rng, hijo, sigma))
            pob = nueva
            apt = np.array([self._aptitud(c) for c in pob])
            historial.append((g, apt.max(), apt.mean(), apt.min()))
        mejor = int(np.argmax(apt))
        self.centroides_ = pob[mejor]
        self.aptitud_final_ = float(apt[mejor])
        self.historial_ = pd.DataFrame(historial, columns=["generacion", "mejor", "media", "peor"])
        self.tiempo_entrenamiento_ = time.perf_counter() - inicio
        del self._S, self._D
        return self

    def predict(self, Z):
        return asignar(Z, self.centroides_)
