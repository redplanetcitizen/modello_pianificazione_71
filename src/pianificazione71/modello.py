"""Passo D: modello LP intertemporale a 71 industrie / 71 prodotti ordinari, 2012-2016 (specifica v0.2.1, §3-§8).

Unità: miliardi di dollari 2012; lavoro in migliaia di FTE. Il modello è costruito come matrice sparsa
e risolto con HiGHS (highspy). Ogni blocco di vincoli è attivabile da `Opzioni`, così da ricondurre
un'eventuale non fattibilità al blocco che la causa.

Obiettivi (§8):
  O1  max Σ_t β^(t−2012) γ_t         consumo privato a composizione osservata dell'anno, γ = 1 al livello 2012
  O2  max Σ_t Σ_c w_c f(ρ_{c,t})     programmazione per obiettivi: ρ = consumo / obiettivo, f concava a tratti
  O3  max Σ K_{T+1}                  capitale terminale a valore dello stock (dollari 2012), con γ_t ≥ γ_min;
                                     variante storica: pesi a costo d'uso w (pesi_o3 = "costo_uso", passo D2)
  O4  min distanza L1 normalizzata dai valori osservati (solo diagnostica)
"""
from __future__ import annotations

from dataclasses import dataclass, field

import highspy
import numpy as np
import pandas as pd

from .blocchi import COMPARTI, industrie_comparto
from .dati_modello import TIPI, Parametri

INF = highspy.kHighsInf
TRATTI_O2 = ((0.9, 1.0), (0.1, 0.5), (0.2, 0.1))  # (ampiezza del tratto in ρ, punteggio marginale)


@dataclass
class Opzioni:
    obiettivo: str = "O1"
    capacita: bool = True
    capacita_tipo: str = "lineare"         # "lineare" (H8) oppure "leontief" (un vincolo per tipo)
    deriva: bool = True                    # opzione (a): κ con deriva stimata dove esiste la G.17
    theta_non_g17: float = 0.0             # deriva per le industrie senza dati G.17 (sensibilità: −0,018)
    u_non_g17: float = 1.0                 # utilizzo 2012 delle industrie senza G.17: 1 (H9) o 0,772 (H9b)
    capacita_non_g17: str = "uniforme"     # "uniforme" (u_non_g17, H9/H9b) | "inviluppo" | "inviluppo_tendenza" (H9c, anche per HS)
    sigma_fattore: float = 1.0             # minimo delle scorte come quota del rapporto 2012 (H13: 1; H13b: 0,85)
    accumulazione: bool = True
    terminale: bool = True
    crescita_terminale: float = 0.0        # K_{T+1} ≥ (1+g) K_2012 per tipo
    terminale_scorte: bool = True          # S_{z,T} ≥ S_{z,2011}: nessun esaurimento delle scorte a fine orizzonte
    sigma_max_fattore: float | None = 1.20 # massimo delle scorte come quota del rapporto 2012 (H13c: la banda 0,85-1,20 contiene tutti i rapporti osservati); None = nessun massimo
    scorte: bool = True
    lavoro: bool = True
    lavoro_scala: float = 1.0              # moltiplicatore dell'offerta di lavoro osservata
    estero: bool = True
    bande_import: bool = True
    epsilon: float = 0.10
    import_scala: float = 1.0              # moltiplicatore del tetto alle importazioni totali
    beta: float = 1.0
    gamma_min: float = 1.0                 # per O3
    pesi_o3: str = "valore"                # "valore" (stock a prezzi 2012, decisione 22/09) | "costo_uso" (D2)
    obiettivi_o2: str = "osservato"        # "osservato" | "costante_2012"
    # --- gradualità dell'investimento (passo E; tutte disattivate per default: O1-O4 del passo D restano invariati) ---
    limite_var_inv: float | None = None    # H25a: (1−g)·I_{a,t−1} ≤ I_{a,t} ≤ (1+g)·I_{a,t−1}, per tipo (somma sulle industrie); I_2011 osservato
    penalita_var_inv: float = 0.0          # H25b: penalità per unità di variazione relativa di I_a oltre la soglia (rispetto a I_{a,2011})
    soglia_var_inv: float = 0.05           # H25b: variazione relativa annua non penalizzata
    tempi_costruzione: tuple = ()          # H26: tipi con spesa ripartita su due anni, es. ("S", "R")
    quota_primo_anno: float = 0.5          # H26: quota della spesa di un progetto nell'anno di avvio
    # --- funzione d'investimento stimata (passo E3; disattivata per default) ---
    regola_inv: dict | None = None         # H28: tipo → {"k": c0, "x": c1, "costante": {anno: v}}; obiettivo I_a,t = c0·K_a,t + c1·X_t + v_t
                                           #      X_t = produzione delle industrie private (per R: produzione di HS)
    regola_modo: str = "banda"             # "banda": (1−ε)·obiettivo ≤ I ≤ (1+ε)·obiettivo; "penalita": scarto penalizzato a gradini
    regola_eps: float = 0.10
    regola_tratti: tuple = ((0.05, 0.0), (0.15, 0.1), (float("inf"), 0.5))  # (ampiezza cumulata relativa a I_prec, penalità per unità relativa)
    elastico: bool = False                 # scarti di capacità penalizzati, solo per diagnosi
    penalita_elastico: float = 1e3


class Costruttore:
    def __init__(self):
        self.lb, self.ub, self.costo, self.nomi = [], [], [], []
        self.righe, self.rlo, self.rhi, self.rnomi = [], [], [], []

    def var(self, nome, lb=0.0, ub=INF, costo=0.0) -> int:
        self.lb.append(lb); self.ub.append(ub); self.costo.append(costo); self.nomi.append(nome)
        return len(self.lb) - 1

    def riga(self, coef: dict, lo, hi, nome) -> int:
        self.righe.append({k: v for k, v in coef.items() if v != 0.0}); self.rlo.append(lo); self.rhi.append(hi)
        self.rnomi.append(nome)
        return len(self.righe) - 1

    def risolvi(self, massimizza: bool, opzioni_highs: dict | None = None):
        h = highspy.Highs()
        h.setOptionValue("output_flag", False)
        for k, v in (opzioni_highs or {}).items():
            h.setOptionValue(k, v)
        n = len(self.lb)
        h.addVars(n, np.array(self.lb, float), np.array(self.ub, float))
        h.changeColsCost(n, np.arange(n, dtype=np.int32), np.array(self.costo, float))
        if massimizza:
            h.changeObjectiveSense(highspy.ObjSense.kMaximize)
        starts, idx, val = [], [], []
        for r in self.righe:
            starts.append(len(idx)); idx.extend(r.keys()); val.extend(r.values())
        h.addRows(len(self.righe), np.array(self.rlo, float), np.array(self.rhi, float), len(idx),
                  np.array(starts, np.int32), np.array(idx, np.int32), np.array(val, float))
        h.run()
        return h


@dataclass
class Risultato:
    stato: str
    obiettivo: float | None
    opzioni: Opzioni
    tabelle: dict = field(default_factory=dict)
    grezzi: dict = field(default_factory=dict)
    n_var: int = 0
    n_vincoli: int = 0


def costruisci_e_risolvi(P: Parametri, o: Opzioni) -> Risultato:
    C = Costruttore()
    anni = list(P.anni)
    T = anni[-1]
    J, Cc = P.industrie, P.prodotti
    cap_ind = [j for j in P.kappa.index if j in P.private and j != "HS"]  # industrie private con capitale non residenziale
    tipi_j = {j: [a for a in TIPI if (j, a) in P.K0.index and P.K0[(j, a)] > 0] for j in cap_ind}
    tipi_j["HS"] = ["R"] if ("HS", "R") in P.K0.index else []
    v = {}  # (nome, chiavi...) → indice

    # ---------------------------- variabili ----------------------------
    for t in anni:
        for j in J:
            v[("x", j, t)] = C.var(f"x[{j},{t}]")
        for c in Cc:
            v[("q", c, t)] = C.var(f"q[{c},{t}]")
            v[("m", c, t)] = C.var(f"m[{c},{t}]") if o.estero else None
            v[("r", c, t)] = C.var(f"r[{c},{t}]")
        if o.obiettivo in ("O1", "O3"):
            v[("g", t)] = C.var(f"gamma[{t}]", lb=o.gamma_min if o.obiettivo == "O3" else 0.0)
        else:
            for c in Cc:
                v[("c", c, t)] = C.var(f"cons[{c},{t}]")
        for j in cap_ind + ["HS"]:
            for a in tipi_j.get(j, []):
                v[("I", j, a, t)] = C.var(f"I[{j},{a},{t}]")
        if o.scorte:
            for z in COMPARTI:
                v[("dS", z, t)] = C.var(f"dS[{z},{t}]", lb=-INF)
                v[("S", z, t)] = C.var(f"S[{z},{t}]")
    if o.accumulazione:
        for t in anni[1:] + [T + 1]:
            for j in cap_ind + ["HS"]:
                for a in tipi_j.get(j, []):
                    v[("K", j, a, t)] = C.var(f"K[{j},{a},{t}]")

    def K(j, a, t):  # stock di inizio anno: costante nel 2012, variabile dopo
        if t == anni[0] or not o.accumulazione:
            return None, float(P.K0[(j, a)])
        return v[("K", j, a, t)], 0.0

    # ---------------------------- vincoli ----------------------------
    comp_cons = {t: P.consumo_oss[t] / P.consumo_oss[t].sum() for t in anni}
    liv_2012 = P.consumo_oss[anni[0]].sum()
    for t in anni:
        B, D, phi_R = P.B[t], P.D[t], P.phi_R[t]
        # (1) bilancio materiale per prodotto
        for c in Cc:
            coef = {v[("q", c, t)]: 1.0, v[("r", c, t)]: -1.0}
            if o.estero:
                coef[v[("m", c, t)]] = 1.0
            for j in J:
                if B.at[c, j] != 0.0:
                    coef[v[("x", j, t)]] = coef.get(v[("x", j, t)], 0.0) - B.at[c, j]
            if o.obiettivo in ("O1", "O3"):
                coef[v[("g", t)]] = -comp_cons[t][c] * liv_2012
            else:
                coef[v[("c", c, t)]] = -1.0
            for j in cap_ind:
                for a in tipi_j[j]:
                    f = P.phi[(t, a)].at[c, j]
                    if f:
                        coef[v[("I", j, a, t)]] = -f
            if tipi_j["HS"]:
                coef[v[("I", "HS", "R", t)]] = -float(phi_R.get(c, 0.0))
            if o.scorte and P.psi.get(c, 0.0):
                for z in COMPARTI:
                    coef[v[("dS", z, t)]] = -float(P.psi[c])
            rhs = float(P.pubblica[t][c] + P.esportazioni[t][c] + P.usi_esterni_fissi[t][c])
            if not o.estero:  # senza estero le importazioni restano ai valori osservati
                rhs -= float(P.import_oss[t][c])
            if not o.scorte:
                rhs += float(P.scorte_oss[t][c])
            C.riga(coef, rhs, rhs, f"bilancio[{c},{t}]")
        # (2) quote di mercato
        for j in J:
            coef = {v[("x", j, t)]: 1.0}
            for c in Cc:
                if D.at[j, c]:
                    coef[v[("q", c, t)]] = -D.at[j, c]
            rhs = float(P.x_speciali[t][j])
            C.riga(coef, rhs, rhs, f"quote[{j},{t}]")
        # (3) capacità
        if o.capacita:
            for j in cap_ind + (["HS"] if tipi_j["HS"] else []):
                theta = float(P.theta.get(j, 0.0)) if o.deriva else 0.0
                if o.deriva and j not in P.theta[P.theta != 0].index:
                    theta = o.theta_non_g17
                u_j = o.u_non_g17 if (j not in P.theta[P.theta != 0].index and j != "HS") else 1.0
                if o.capacita_non_g17 != "uniforme" and j not in set(P.g17):
                    cinv = P.capacita_inviluppo.set_index("industria_io")
                    u_j = float(cinv.at[j, f"u_{o.capacita_non_g17}"])
                    theta = float(cinv.at[j, "theta_inviluppo_tendenza"]) if o.capacita_non_g17 == "inviluppo_tendenza" else 0.0
                fattore = (1 + theta) ** (t - anni[0])
                kap = float(P.kappa[j]) * u_j / fattore
                if o.capacita_tipo == "leontief" and j != "HS":
                    for a in tipi_j[j]:
                        ka = float(P.K0[(j, a)])
                        kap_a = kap * ka / sum(float(P.w[(j, b)]) * float(P.K0[(j, b)]) for b in tipi_j[j])
                        idx, cost = K(j, a, t)
                        coef = {v[("x", j, t)]: kap_a}
                        if idx is not None:
                            coef[idx] = -1.0
                        C.riga(coef, -INF, cost, f"capacita[{j},{a},{t}]")
                else:
                    coef, cost = {v[("x", j, t)]: kap}, 0.0
                    for a in tipi_j[j]:
                        w = 1.0 if a == "R" else float(P.w[(j, a)])
                        idx, c0 = K(j, a, t)
                        if idx is not None:
                            coef[idx] = -w
                        cost += w * c0
                    if o.elastico:
                        coef[C.var(f"scarto_cap[{j},{t}]", costo=0.0)] = -1.0
                    C.riga(coef, -INF, cost, f"capacita[{j},{t}]")
        # (6) lavoro
        if o.lavoro:
            coef = {v[("x", j, t)]: float(P.ell[t][j]) for j in J if P.ell[t][j]}
            C.riga(coef, -INF, P.lavoro_tot[t] * o.lavoro_scala, f"lavoro[{t}]")
        # (7) estero
        if o.estero:
            C.riga({v[("m", c, t)]: 1.0 for c in Cc}, -INF, P.import_tot[t] * o.import_scala, f"import_totale[{t}]")
            if o.bande_import:
                for c in Cc:
                    mu = float(P.mu[t][c]) * (1 + o.epsilon)
                    coef = {v[("m", c, t)]: 1.0}
                    for j in J:
                        if B.at[c, j]:
                            coef[v[("x", j, t)]] = coef.get(v[("x", j, t)], 0.0) - mu * B.at[c, j]
                    if o.obiettivo in ("O1", "O3"):
                        coef[v[("g", t)]] = -mu * comp_cons[t][c] * liv_2012
                    else:
                        coef[v[("c", c, t)]] = -mu
                    for j in cap_ind:
                        for a in tipi_j[j]:
                            f = P.phi[(t, a)].at[c, j]
                            if f:
                                coef[v[("I", j, a, t)]] = coef.get(v[("I", j, a, t)], 0.0) - mu * f
                    C.riga(coef, -INF, mu * float(P.pubblica[t][c]), f"banda_import[{c},{t}]")
        # (5) scorte
        if o.scorte:
            for z in COMPARTI:
                coef = {v[("S", z, t)]: 1.0, v[("dS", z, t)]: -1.0}
                rhs = 0.0
                if t == anni[0]:
                    rhs = float(P.S0[z])
                else:
                    coef[v[("S", z, t - 1)]] = -1.0
                C.riga(coef, rhs, rhs, f"scorte[{z},{t}]")
                sg = float(P.sigma.set_index("riga").at[z, "sigma"]) * o.sigma_fattore
                coef = {v[("S", z, t)]: 1.0}
                for j in industrie_comparto(z, P.private):
                    coef[v[("x", j, t)]] = -sg
                C.riga(coef, 0.0, INF, f"scorte_minime[{z},{t}]")
                if o.sigma_max_fattore is not None:
                    sgmax = sg / o.sigma_fattore * o.sigma_max_fattore
                    coefm = {v[("S", z, t)]: 1.0}
                    for j in industrie_comparto(z, P.private):
                        coefm[v[("x", j, t)]] = -sgmax
                    C.riga(coefm, -INF, 0.0, f"scorte_massime[{z},{t}]")
                if o.terminale_scorte and t == T:
                    C.riga({v[("S", z, t)]: 1.0}, float(P.S0[z]), INF, f"terminale_scorte[{z}]")
    # (4) accumulazione
    if o.accumulazione:
        for t in anni:
            for j in cap_ind + ["HS"]:
                for a in tipi_j.get(j, []):
                    d = float(P.delta[(j, a)])
                    coef = {v[("K", j, a, t + 1)]: 1.0, v[("I", j, a, t)]: -1.0}
                    idx, c0 = K(j, a, t)
                    rhs = (1 - d) * c0
                    if idx is not None:
                        coef[idx] = -(1 - d)
                    C.riga(coef, rhs, rhs, f"accumulazione[{j},{a},{t}]")
        # (8) condizione terminale di non depauperamento per tipo
        if o.terminale:
            for a in list(TIPI) + ["R"]:
                membri = [j for j in cap_ind + ["HS"] if a in tipi_j.get(j, [])]
                base = sum(float(P.K0[(j, a)]) for j in membri)
                C.riga({v[("K", j, a, T + 1)]: 1.0 for j in membri}, base * (1 + o.crescita_terminale), INF,
                       f"terminale[{a}]")

    # (9) gradualità dell'investimento (passo E, opzionale)
    massimizza = o.obiettivo != "O4"
    membri_tipo = {a: [j for j in cap_ind + ["HS"] if a in tipi_j.get(j, [])] for a in list(TIPI) + ["R"]}
    base_2011 = {a: sum(float(P.I_prec.get((j, a), 0.0)) for j in membri_tipo[a]) for a in membri_tipo}
    if o.limite_var_inv is not None or o.penalita_var_inv:
        for a, membri in membri_tipo.items():
            if not membri or base_2011[a] <= 0:
                continue
            for t in anni:
                coef = {v[("I", j, a, t)]: 1.0 for j in membri}
                prec = 0.0
                if t == anni[0]:
                    prec = base_2011[a]
                else:
                    for j in membri:
                        coef[v[("I", j, a, t - 1)]] = -1.0
                # coef·I = I_t − I_{t−1} (+ prec per il 2012)
                if o.limite_var_inv is not None:
                    g = o.limite_var_inv
                    cs = {k: (1.0 if val > 0 else -(1 + g)) for k, val in coef.items()}
                    C.riga(cs, -INF, (1 + g) * prec, f"inv_max[{a},{t}]")
                    ci = {k: (1.0 if val > 0 else -(1 - g)) for k, val in coef.items()}
                    C.riga(ci, (1 - g) * prec, INF, f"inv_min[{a},{t}]")
                if o.penalita_var_inv:
                    segno = -1.0 if massimizza else 1.0
                    costo = segno * o.penalita_var_inv / base_2011[a]
                    su1 = C.var(f"dinv_su_libera[{a},{t}]", ub=o.soglia_var_inv * base_2011[a])
                    giu1 = C.var(f"dinv_giu_libera[{a},{t}]", ub=o.soglia_var_inv * base_2011[a])
                    su2 = C.var(f"dinv_su[{a},{t}]", costo=costo)
                    giu2 = C.var(f"dinv_giu[{a},{t}]", costo=costo)
                    cp = dict(coef)
                    cp.update({su1: -1.0, su2: -1.0, giu1: 1.0, giu2: 1.0})
                    C.riga(cp, prec, prec, f"var_inv[{a},{t}]")
    for a in o.tempi_costruzione:
        qa = o.quota_primo_anno
        for j in membri_tipo.get(a, []):
            avvii_prec = float(P.I_prec.get((j, a), 0.0))   # progetti avviati nel 2011: ipotesi di regime (avvii = spesa 2011)
            for t in anni:
                s_t = C.var(f"avvii[{j},{a},{t}]")
                C.riga({v[("I", j, a, t)]: 1.0, s_t: -qa} | ({} if t == anni[0] else {prec_var: -(1 - qa)}),
                       (1 - qa) * avvii_prec if t == anni[0] else 0.0,
                       (1 - qa) * avvii_prec if t == anni[0] else 0.0, f"tempi_costruzione[{j},{a},{t}]")
                prec_var = s_t

    # (10) funzione d'investimento stimata (passo E3, opzionale)
    if o.regola_inv:
        for a, coeff in o.regola_inv.items():
            membri = membri_tipo.get(a, [])
            if not membri:
                continue
            prod = ["HS"] if a == "R" else list(P.private)
            scala = base_2011[a] if base_2011[a] > 0 else 1.0
            for t in anni:
                # obiettivo = c0·ΣK + c1·ΣX + v_t  →  termini variabili (coef_ob) e costante (cost_ob)
                coef_ob, cost_ob = {}, float(coeff.get("costante", {}).get(t, 0.0))
                c0, c1 = float(coeff.get("k", 0.0)), float(coeff.get("x", 0.0))
                for j in membri:
                    idx, c = K(j, a, t)
                    if idx is None:
                        cost_ob += c0 * c
                    elif c0:
                        coef_ob[idx] = coef_ob.get(idx, 0.0) + c0
                if c1:
                    for j in prod:
                        coef_ob[v[("x", j, t)]] = coef_ob.get(v[("x", j, t)], 0.0) + c1
                I_t = {v[("I", j, a, t)]: 1.0 for j in membri}
                if o.regola_modo == "banda":
                    for fatt, nome, lo, hi in ((1 + o.regola_eps, "max", -INF, None), (1 - o.regola_eps, "min", None, INF)):
                        coef = dict(I_t)
                        for k2, val in coef_ob.items():
                            coef[k2] = coef.get(k2, 0.0) - fatt * val
                        rhs = fatt * cost_ob
                        C.riga(coef, rhs if lo is None else lo, rhs if hi is None else hi, f"regola_inv_{nome}[{a},{t}]")
                else:
                    segno = -1.0 if massimizza else 1.0
                    coef = dict(I_t)
                    for k2, val in coef_ob.items():
                        coef[k2] = coef.get(k2, 0.0) - val
                    prec = 0.0
                    for verso, sg in (("su", -1.0), ("giu", 1.0)):
                        prec_amp = 0.0
                        for k3, (amp, pen) in enumerate(o.regola_tratti):
                            ub = INF if amp == float("inf") else (amp - prec_amp) * scala
                            coef[C.var(f"scarto_regola_{verso}{k3}[{a},{t}]", ub=ub, costo=segno * pen / scala)] = sg
                            prec_amp = amp
                    C.riga(coef, cost_ob, cost_ob, f"regola_inv[{a},{t}]")

    # ---------------------------- obiettivo ----------------------------
    if o.obiettivo == "O1":
        for t in anni:
            C.costo[v[("g", t)]] = o.beta ** (t - anni[0])
    elif o.obiettivo == "O2":
        for t in anni:
            obiettivo = P.consumo_oss[t] if o.obiettivi_o2 == "osservato" else P.consumo_oss[anni[0]]
            obiettivo = obiettivo.clip(lower=0)
            peso = obiettivo / obiettivo.sum()
            for c in Cc:
                if obiettivo[c] <= 0:
                    C.ub[v[("c", c, t)]] = 0.0
                    continue
                coef = {v[("c", c, t)]: 1.0}
                for k, (ampiezza, punteggio) in enumerate(TRATTI_O2):
                    rho = C.var(f"rho{k}[{c},{t}]", ub=ampiezza, costo=float(peso[c]) * punteggio)
                    coef[rho] = -float(obiettivo[c])
                C.riga(coef, 0.0, 0.0, f"o2[{c},{t}]")
    elif o.obiettivo == "O3":
        for j in cap_ind + ["HS"]:
            for a in tipi_j.get(j, []):
                usa_w = o.pesi_o3 == "costo_uso" and a != "R"
                C.costo[v[("K", j, a, T + 1)]] = float(P.w[(j, a)]) if usa_w else 1.0
    elif o.obiettivo == "O4":
        blocchi = {"x": (lambda t: P.x_oss[t], J), "c": (lambda t: P.consumo_oss[t].clip(lower=0), Cc)}
        if o.estero:
            blocchi["m"] = (lambda t: P.import_oss[t], Cc)
        for t in anni:
            for nome, (oss, chiavi) in blocchi.items():
                val = oss(t)
                norma = float(val.abs().sum())
                for k in chiavi:
                    dp = C.var(f"dev+[{nome},{k},{t}]", costo=1.0 / norma)
                    dm = C.var(f"dev-[{nome},{k},{t}]", costo=1.0 / norma)
                    C.riga({v[(nome, k, t)]: 1.0, dp: -1.0, dm: 1.0}, float(val[k]), float(val[k]),
                           f"distanza[{nome},{k},{t}]")
            # investimento per tipo, industria per industria (residenziale compreso)
            for a in list(TIPI) + ["R"]:
                oss = P.I_oss[(P.I_oss.anno == t) & (P.I_oss.tipo == a)].set_index("industria_io")["I"]
                norma = float(oss.sum())
                for j in (["HS"] if a == "R" else cap_ind):
                    if a in tipi_j.get(j, []):
                        dp = C.var(f"dev+[I,{j},{a},{t}]", costo=1.0 / norma)
                        dm = C.var(f"dev-[I,{j},{a},{t}]", costo=1.0 / norma)
                        C.riga({v[("I", j, a, t)]: 1.0, dp: -1.0, dm: 1.0}, float(oss.get(j, 0.0)),
                               float(oss.get(j, 0.0)), f"distanza[I,{j},{a},{t}]")
    if o.elastico:
        for i, n in enumerate(C.nomi):
            if n.startswith("scarto_cap"):
                C.costo[i] = -o.penalita_elastico if massimizza else o.penalita_elastico

    h = C.risolvi(massimizza)
    stato = h.modelStatusToString(h.getModelStatus())
    R = Risultato(stato, None, o, n_var=len(C.lb), n_vincoli=len(C.righe))
    if stato != "Optimal":
        return R
    sol = h.getSolution()
    R.obiettivo = h.getInfo().objective_function_value
    xv, dual = np.array(sol.col_value), np.array(sol.row_dual)
    R.tabelle = estrai(P, o, v, C, xv, dual, cap_ind, tipi_j, comp_cons, liv_2012)
    R.grezzi = {"v": v, "valori": xv, "duali": pd.Series(dual, index=C.rnomi)}  # non scritti su disco
    return R


def estrai(P, o, v, C, xv, dual, cap_ind, tipi_j, comp_cons, liv) -> dict:
    anni = list(P.anni)
    val = lambda k: float(xv[v[k]]) if v.get(k) is not None else 0.0
    righe = []
    for t in anni:
        cons = (comp_cons[t] * liv * val(("g", t))) if ("g", t) in v else pd.Series({c: val(("c", c, t)) for c in P.prodotti})
        inv = {a: sum(val(("I", j, a, t)) for j in cap_ind if a in tipi_j[j]) for a in TIPI}
        invR = val(("I", "HS", "R", t)) if tipi_j["HS"] else 0.0
        dS = sum(val(("dS", z, t)) for z in COMPARTI) if o.scorte else float(P.scorte_oss[t].sum())
        m = sum(val(("m", c, t)) for c in P.prodotti) if o.estero else float(P.import_oss[t].sum())
        x = sum(val(("x", j, t)) for j in P.industrie)
        r = sum(val(("r", c, t)) for c in P.prodotti)
        # ammortamento dello stock di inizio anno
        amm = 0.0
        for j in cap_ind + ["HS"]:
            for a in tipi_j.get(j, []):
                k = float(P.K0[(j, a)]) if t == anni[0] or not o.accumulazione else val(("K", j, a, t))
                amm += float(P.delta[(j, a)]) * k
        dom_prodotti = sum(sum(P.phi[(t, a)].sum(axis=0).get(j, 0) * val(("I", j, a, t)) for j in cap_ind if a in tipi_j[j]) for a in TIPI)
        righe.append({
            "anno": t, "produzione_lorda": x, "consumo_privato": float(cons.sum()),
            "consumo_pubblico_e_inv_pubblici": float(P.pubblica[t].sum()),
            "investimento_E": inv["E"], "investimento_S": inv["S"], "investimento_N": inv["N"],
            "investimento_R": invR, "investimento_totale_FA": sum(inv.values()) + invR,
            "domanda_di_prodotti_per_investimento": dom_prodotti + invR * float(P.phi_R[t].sum()),
            "ammortamento": amm, "investimento_netto": sum(inv.values()) + invR - amm,
            "variazione_scorte": dS, "esportazioni": float(P.esportazioni[t].sum()), "importazioni": m,
            "residuo_materiale": r,
            "gamma": val(("g", t)) if ("g", t) in v else float(cons.sum()) / liv,
        })
    agg = pd.DataFrame(righe)
    # prodotto finale e surplus (§7): prodotto netto − consumo privato
    agg["prodotto_finale_lordo"] = (agg["consumo_privato"] + agg["consumo_pubblico_e_inv_pubblici"]
                                    + agg["domanda_di_prodotti_per_investimento"] + agg["variazione_scorte"]
                                    + agg["esportazioni"] - agg["importazioni"] + agg["residuo_materiale"])
    agg["prodotto_netto"] = agg["prodotto_finale_lordo"] - agg["ammortamento"]
    agg["surplus_economico"] = agg["prodotto_netto"] - agg["consumo_privato"]

    ind = pd.DataFrame([{"anno": t, "industria": j, "x": val(("x", j, t)), "x_oss": float(P.x_oss[t][j])}
                        for t in anni for j in P.industrie])
    inv = pd.DataFrame([{"anno": t, "industria": j, "tipo": a, "I": val(("I", j, a, t))}
                        for t in anni for j in cap_ind + ["HS"] for a in tipi_j.get(j, [])])
    duali = pd.DataFrame({"vincolo": C.rnomi, "duale": dual})
    duali["famiglia"] = duali["vincolo"].str.split("[").str[0]
    prezzi_ombra = duali[duali["famiglia"] == "bilancio"].copy()
    attivi = duali[duali["duale"].abs() > 1e-9].groupby("famiglia").size().rename("vincoli_con_duale_non_nullo")
    scarti = {n: float(xv[i]) for i, n in enumerate(C.nomi) if n.startswith("scarto_cap") and xv[i] > 1e-7}
    return {"aggregati": agg, "industrie": ind, "investimento": inv, "prezzi_ombra": prezzi_ombra,
            "vincoli_attivi": attivi.reset_index(), "scarti_capacita": pd.Series(scarti, dtype=float)}
