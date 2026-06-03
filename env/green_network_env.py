# green_network_env.py
"""
green_network_env.py
====================
Ambiente Gymnasium para o projeto Green Network (Davi Novaes Coutinho).

Modela uma celula de rede hibrida 5G + LEO ao longo de um dia simulado.
A cada passo (Delta_t = 100 ms simulados, acelerado), o agente observa o
estado da rede e escolhe uma das 5 acoes (Tabela 3 do artigo). A fisica de
energia segue o modelo afim de Auer et al. (2011) parametrizado pela
Tabela 5; a recompensa segue a Secao 6.2.3.

IMPORTANTE (integridade cientifica): a dinamica e construida a partir de
parametros FISICOS INDEPENDENTES (Tabela 5). A reducao de energia NAO e
embutida -- ela EMERGE da politica que o agente aprende, medida contra um
baseline estatico "sempre 5G_TERRESTRE nominal". O numero final (seja 42%,
35% ou outro) e resultado experimental, nao premissa.

Premissas de modelagem (declarar na Secao 7 / 9.1 do artigo):
- Trafego: curva diurna senoidal + ruido de Poisson (Secao 7.3).
- Satelites visiveis: aleatorio 0-5 por passo (simplificacao; ver Secao 9.1).
  Substituivel futuramente por trajetorias TLE/Hypatia.
- Classe de trafego dominante sorteada por passo, com pesos que variam ao
  longo do dia (URLLC mais frequente em pico).
"""

import numpy as np
import gymnasium as gym
from gymnasium import spaces


# ---------------------------------------------------------------------------
# Parametros fisicos -- Tabela 5 do artigo (valores adotados nas simulacoes)
# ---------------------------------------------------------------------------
P0_GNB = 130.0        # W   - potencia ociosa macro-gNodeB (Auer et al. 2011)
DELTA_P = 4.7         # -   - coeficiente de carga (Auer et al. 2011)
PMAX_GNB = 40.0       # W   - potencia max transmissao (46 dBm ~ 40 W; Piro 2021)
PSLEEP_GNB = 18.0     # W   - potencia dormencia (Lopez-Perez et al. 2022)
PSAT = 1200.0         # W   - potencia satelite payload (Kassing et al. 2020)
PGW0 = 3500.0         # W   - potencia fixa gateway NTN (estimativa operacional)
PCORE = 800.0         # W   - potencia 5G Core por UPF (ITU-T L.1310)
BETA_GW = 2e-9        # J/bit - eficiencia energetica gateway (ITU-T L.1310, ~2 nJ/bit)

# Fracao da capacidade do satelite atribuivel ao nosso trafego (eta na Sec 6.4.3).
# O segmento LEO compartilha capacidade com outros usuarios; so uma fracao do
# consumo do satelite e imputavel ao sistema hibrido.
ETA_SAT = 0.05
POVERHEAD_SAT = 50.0  # W - overhead de controle/telemetria imputado por satelite ativo

# Rateio do gateway NTN: um gateway serve MUITAS celulas simultaneamente
# (Secao 6.4.3 -- capacidade compartilhada). Atribuir P_GW inteiro a uma unica
# celula superestima o consumo LEO por ordem de grandeza. Imputamos a parcela
# correspondente as celulas servidas. Valor conservador: gateway moderno serve
# ~100 celulas; usamos 100 como divisor de rateio.
N_CELULAS_POR_GW = 100.0

# ---------------------------------------------------------------------------
# Parametros de rede / trafego
# ---------------------------------------------------------------------------
THROUGHPUT_ALVO = 310e6   # bps - alvo para normalizar R_QoS (Secao 8: 310 Mbps)
CAP_5G = 400e6            # bps - capacidade nominal do enlace 5G terrestre
CAP_LEO = 220e6          # bps - capacidade tipica por enlace LEO
LAT_5G_BASE = 12.0       # ms  - latencia base 5G terrestre
LAT_LEO_BASE = 35.0      # ms  - latencia base LEO (faixa 20-50 ms, Secao 2.2)
LAT_ALVO = {             # ms  - latencia alvo por classe (normaliza R_L)
    "eMBB": 50.0,
    "URLLC": 20.0,
    "mMTC": 100.0,
}
PERDA_LIMIAR = 0.05      # limiar de violacao de SLA para R_loss (Secao 6.2.3)

# Demanda que celulas vizinhas conseguem absorver quando a celula entra em
# dormencia (Secao 6.4.2). Acima disso, dormir gera perda. Calibrado para
# ~25% da capacidade 5G: a vizinha tem folga para cobrir vales de demanda,
# mas nao um pico. E isto que o agente precisa aprender a respeitar.
DEMANDA_DORMENCIA_OK = 0.25 * CAP_5G

CLASSES = ["eMBB", "URLLC", "mMTC"]

# Acoes -- Tabela 3
A_5G_TERRESTRE = 0
A_LEO_SATELITAL = 1
A_HIBRIDO_SPLIT = 2
A_5G_LOW_POWER = 3
A_DORMENCIA = 4
ACOES = ["5G_TERRESTRE", "LEO_SATELITAL", "HIBRIDO_SPLIT", "5G_LOW_POWER", "DORMENCIA"]


class GreenNetworkEnv(gym.Env):
    """Ambiente de selecao sustentavel de enlace 5G/LEO."""

    metadata = {"render_modes": []}

    def __init__(self, weights=None, steps_per_episode=200, seconds_per_step=0.1,
                 seed=None):
        super().__init__()

        # Pesos da recompensa -- Tabela 4 (default: baseline equilibrio).
        # w1=QoS, w2=Energia, w3=Latencia, w4=Perda
        if weights is None:
            weights = (0.4, 0.3, 0.2, 0.1)
        self.w1, self.w2, self.w3, self.w4 = weights

        self.steps_per_episode = steps_per_episode
        self.dt = seconds_per_step  # duracao do passo em segundos (Delta_t)

        # Observation space: Box continuo de 8 dimensoes (vetor s_t do artigo).
        # [u, lat_norm, energia_disp, perda, sat_norm, onehot_eMBB, onehot_URLLC, onehot_mMTC]
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(8,),
                                            dtype=np.float32)
        # Action space: 5 acoes discretas (Tabela 3).
        self.action_space = spaces.Discrete(5)

        # Referencia de energia para normalizar R_E: consumo de uma gNodeB
        # em carga maxima + core, num passo. Usado so para escalar a recompensa
        # em [0,1] aprox; NAO afeta a medicao absoluta de energia (em joules).
        self.E_ref = (P0_GNB + DELTA_P * 1.0 * PMAX_GNB + PCORE) * self.dt

        self._rng = np.random.default_rng(seed)
        self.t = 0

    # ----------------------------------------------------------------------
    def _demanda_trafego(self, t):
        """Curva diurna senoidal + ruido de Poisson. Retorna demanda em bps.

        t e o indice do passo dentro do episodio; mapeamos o episodio inteiro
        para um ciclo de 24h. Pico ~15h, vale ~3h.
        """
        frac_dia = (t / self.steps_per_episode)  # 0..1 -> 0h..24h
        hora = frac_dia * 24.0
        # senoide com pico em 15h: deslocamento de fase.
        base = 0.5 + 0.45 * np.sin(2 * np.pi * (hora - 9) / 24.0)
        base = np.clip(base, 0.05, 1.0)
        # ruido de Poisson em torno da base (escala lambda alta -> aproxima normal)
        lam = base * 100.0
        ruido = self._rng.poisson(lam) / 100.0
        demanda_norm = np.clip(ruido, 0.02, 1.0)
        return demanda_norm * CAP_5G, demanda_norm, hora

    def _classe_dominante(self, hora):
        """Sorteia a classe dominante; URLLC mais provavel em horario de pico."""
        if 8 <= hora <= 20:
            pesos = [0.5, 0.35, 0.15]   # dia: eMBB e URLLC
        else:
            pesos = [0.4, 0.1, 0.5]     # noite: mMTC (sensores) dominante
        idx = self._rng.choice(3, p=pesos)
        return CLASSES[idx]

    def _satelites_visiveis(self):
        """Aleatorio 0-5 por passo (simplificacao; ver Secao 9.1)."""
        return int(self._rng.integers(0, 6))

    # ----------------------------------------------------------------------
    def _montar_observacao(self, u, lat, energia, perda, sats, classe):
        onehot = [0.0, 0.0, 0.0]
        onehot[CLASSES.index(classe)] = 1.0
        obs = np.array([
            np.clip(u, 0, 1),
            np.clip(lat / 100.0, 0, 1),     # normaliza por 100 ms
            np.clip(energia, 0, 1),
            np.clip(perda, 0, 1),
            np.clip(sats / 5.0, 0, 1),
            *onehot,
        ], dtype=np.float32)
        return obs

    # ----------------------------------------------------------------------
    def _fisica(self, action, demanda_bps, demanda_norm, sats, classe):
        """Calcula energia (J), latencia (ms), perda e throughput entregue (bps)
        para a acao escolhida, dado o estado de trafego/satelites.

        Retorna dict com as grandezas medidas. Tudo deriva da Tabela 5 e dos
        parametros de rede -- nenhuma reducao e pre-programada.
        """
        rho = demanda_norm  # carga normalizada [0,1]

        # Defaults
        p_gnb = 0.0
        p_leo = 0.0
        p_gw = 0.0
        p_core = PCORE          # core sempre ligado, exceto consolidacao em dormencia
        entregue = 0.0
        lat = LAT_5G_BASE
        capacidade = 0.0

        if action == A_5G_TERRESTRE:
            # gNodeB ativa em operacao nominal.
            p_gnb = P0_GNB + DELTA_P * rho * PMAX_GNB
            capacidade = CAP_5G
            lat = LAT_5G_BASE + 30.0 * rho   # congestiona com carga
            entregue = min(demanda_bps, capacidade)

        elif action == A_LEO_SATELITAL:
            if sats > 0:
                # so o trafego imputa potencia incremental; core + gateway ligam.
                p_leo = sats * (ETA_SAT * PSAT + POVERHEAD_SAT)
                capacidade = CAP_LEO * min(sats, 3) / 1.0  # mais sats -> mais capacidade
                # gateway rateado entre as celulas que serve (Sec 6.4.3)
                p_gw = (PGW0 + BETA_GW * min(demanda_bps, capacidade)) / N_CELULAS_POR_GW
                lat = LAT_LEO_BASE + 10.0 * rho
                entregue = min(demanda_bps, capacidade)
            else:
                # sem satelite visivel: enlace indisponivel -> perda total.
                capacidade = 0.0
                lat = 100.0
                entregue = 0.0

        elif action == A_HIBRIDO_SPLIT:
            # divide carga entre 5G e LEO (se houver satelite).
            p_gnb = P0_GNB + DELTA_P * (rho * 0.5) * PMAX_GNB
            cap_terr = CAP_5G * 0.6
            if sats > 0:
                p_leo = sats * (ETA_SAT * PSAT + POVERHEAD_SAT) * 0.5
                cap_sat = CAP_LEO * min(sats, 3)
                p_gw = (PGW0 + BETA_GW * (demanda_bps * 0.4)) / N_CELULAS_POR_GW * 0.5
            else:
                cap_sat = 0.0
            capacidade = cap_terr + cap_sat
            lat = 0.6 * (LAT_5G_BASE + 20.0 * rho) + 0.4 * (LAT_LEO_BASE + 10.0 * rho)
            entregue = min(demanda_bps, capacidade)

        elif action == A_5G_LOW_POWER:
            # 5G com potencia reduzida (sleep parcial): menor P_max efetiva,
            # menor capacidade, maior latencia.
            pmax_eff = PMAX_GNB * 0.5
            p_gnb = P0_GNB * 0.8 + DELTA_P * rho * pmax_eff
            capacidade = CAP_5G * 0.5
            lat = LAT_5G_BASE + 50.0 * rho
            entregue = min(demanda_bps, capacidade)

        elif action == A_DORMENCIA:
            # celula em dormencia: consumo residual; core consolidado.
            # Celulas vizinhas absorvem o trafego residual quando a demanda e
            # baixa (Secao 6.4.2: "dormencia de celulas ociosas proximas").
            # So ha perda se a demanda exceder o que a vizinha comporta.
            p_gnb = PSLEEP_GNB
            p_core = PCORE * 0.3   # consolidacao parcial de UPF
            capacidade = DEMANDA_DORMENCIA_OK  # vizinha cobre ate este nivel
            lat = 80.0
            entregue = min(demanda_bps, capacidade)

        # Potencia total instantanea (Secao 6.4.1) e energia no passo.
        p_total = p_gnb + p_leo + p_gw + p_core
        energia_J = p_total * self.dt

        # Perda: fracao da demanda nao atendida pela capacidade.
        if demanda_bps > 0:
            perda = np.clip((demanda_bps - entregue) / demanda_bps, 0.0, 1.0)
        else:
            perda = 0.0

        return {
            "energia_J": energia_J,
            "p_total": p_total,
            "latencia_ms": lat,
            "perda": perda,
            "entregue_bps": entregue,
            "demanda_bps": demanda_bps,
        }

    # ----------------------------------------------------------------------
    def _recompensa(self, fis, classe):
        """r = w1*R_QoS - w2*R_E - w3*R_L - w4*R_loss (Secao 6.2.3).

        R_QoS: fracao da DEMANDA do passo que foi entregue, em [0,1]. Usar a
        demanda instantanea (e nao um alvo fixo) como referencia torna o termo
        comparavel em escala aos demais e mede diretamente "atendi o que foi
        pedido?". R_E normalizado pela referencia operacional E_ref.
        """
        # R_QoS: throughput entregue / demanda do passo, em [0,1].
        demanda = max(fis["demanda_bps"], 1.0)
        r_qos = np.clip(fis["entregue_bps"] / demanda, 0.0, 1.0)
        # R_E: energia consumida normalizada por referencia operacional.
        r_e = fis["energia_J"] / self.E_ref
        # R_L: latencia observada normalizada pela latencia alvo da classe.
        r_l = np.clip(fis["latencia_ms"] / LAT_ALVO[classe], 0.0, 2.0)
        # R_loss: penalidade discreta se perda excede limiar (violacao SLA).
        r_loss = 1.0 if fis["perda"] > PERDA_LIMIAR else 0.0

        r = self.w1 * r_qos - self.w2 * r_e - self.w3 * r_l - self.w4 * r_loss
        return r, dict(r_qos=r_qos, r_e=r_e, r_l=r_l, r_loss=r_loss)

    # ----------------------------------------------------------------------
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            self._rng = np.random.default_rng(seed)
        self.t = 0
        self.energia_disp = 1.0  # orcamento energetico da celula (drena ao longo do dia)

        demanda_bps, demanda_norm, hora = self._demanda_trafego(self.t)
        sats = self._satelites_visiveis()
        classe = self._classe_dominante(hora)
        obs = self._montar_observacao(demanda_norm, LAT_5G_BASE, self.energia_disp,
                                      0.0, sats, classe)
        self._pendente = (demanda_bps, demanda_norm, sats, classe)
        return obs, {}

    def step(self, action):
        demanda_bps, demanda_norm, sats, classe = self._pendente

        fis = self._fisica(action, demanda_bps, demanda_norm, sats, classe)
        r, comp = self._recompensa(fis, classe)

        # Atualiza orcamento energetico (drena proporcional ao consumo).
        self.energia_disp = float(np.clip(
            self.energia_disp - fis["energia_J"] / (self.E_ref * 50.0), 0.0, 1.0))

        self.t += 1
        terminated = False
        truncated = self.t >= self.steps_per_episode

        # Proximo estado
        demanda_bps2, demanda_norm2, hora2 = self._demanda_trafego(self.t)
        sats2 = self._satelites_visiveis()
        classe2 = self._classe_dominante(hora2)
        obs = self._montar_observacao(demanda_norm2, fis["latencia_ms"],
                                      self.energia_disp, fis["perda"], sats2, classe2)
        self._pendente = (demanda_bps2, demanda_norm2, sats2, classe2)

        info = {
            "energia_J": fis["energia_J"],
            "p_total": fis["p_total"],
            "latencia_ms": fis["latencia_ms"],
            "perda": fis["perda"],
            "entregue_bps": fis["entregue_bps"],
            "demanda_bps": fis["demanda_bps"],
            "acao": ACOES[action],
            "classe": classe,
            "sats": sats,
            **{f"comp_{k}": v for k, v in comp.items()},
        }
        return obs, float(r), terminated, truncated, info
