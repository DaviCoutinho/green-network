# evaluate.py
"""
evaluate.py
===========
Avalia a politica treinada contra baselines e coleta as metricas da Secao 7.4:
  - Energia total (J) e por bit (mJ/bit)
  - Latencia media e cauda (P95, P99) em ms
  - Throughput medio entregue (Mbps)
  - Taxa de perda de pacotes
  - Reducao de energia (%) vs baseline 5G tradicional

Compara tres politicas:
  1. BASELINE ESTATICO: sempre 5G_TERRESTRE nominal (a "rede 5G tradicional"
     de 100% da Figura 4 do artigo).
  2. HEURISTICA: regra simples (dorme se carga baixa, LEO se sem 5G, etc.).
  3. AGENTE DQN: politica aprendida.

Roda com N sementes (Secao 7.5: >=10) e reporta media/desvio e mediana/IQR.
Salva resultados em results/ (CSV + JSON) e gera os graficos.

Uso:
    python evaluate.py --cenario baseline --seeds 10 --episodes 20
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "env"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "env"))

import numpy as np
import pandas as pd
from green_network_env import (GreenNetworkEnv, ACOES, A_5G_TERRESTRE,
                               A_LEO_SATELITAL, A_5G_LOW_POWER, A_DORMENCIA,
                               A_HIBRIDO_SPLIT, DEMANDA_DORMENCIA_OK, CAP_5G)

CENARIOS = {
    "sustentabilidade": (0.3, 0.5, 0.1, 0.1),
    "baseline":         (0.4, 0.3, 0.2, 0.1),
    "desempenho":       (0.5, 0.1, 0.2, 0.2),
}


def politica_baseline(obs):
    """Sempre 5G terrestre nominal -- a rede tradicional (100%)."""
    return A_5G_TERRESTRE


def politica_heuristica(obs):
    """Regra determinista simples (baseline nao-IA, Secao 7.5).
    obs = [u, lat_norm, energia, perda, sat_norm, oh_eMBB, oh_URLLC, oh_mMTC]
    """
    u = obs[0]
    sat = obs[4]
    if u < 0.25:
        return A_DORMENCIA          # carga muito baixa: dorme
    if u < 0.5:
        return A_5G_LOW_POWER       # carga baixa: reduz potencia
    if sat > 0 and u > 0.8:
        return A_HIBRIDO_SPLIT      # pico com satelite: divide
    return A_5G_TERRESTRE


def rodar_politica(get_action, weights, n_seeds, n_episodes, steps_per_episode,
                   modelo=None):
    """Roda uma politica e coleta metricas agregadas por episodio."""
    registros = []
    for seed in range(n_seeds):
        env = GreenNetworkEnv(weights=weights,
                              steps_per_episode=steps_per_episode,
                              seed=1000 + seed)
        for ep in range(n_episodes):
            obs, _ = env.reset(seed=1000 + seed * 100 + ep)
            energias, lats, perdas, entregues, demandas = [], [], [], [], []
            done = False
            while not done:
                if modelo is not None:
                    action, _ = modelo.predict(obs, deterministic=True)
                    action = int(action)
                else:
                    action = get_action(obs)
                obs, r, term, trunc, info = env.step(action)
                done = term or trunc
                energias.append(info["energia_J"])
                lats.append(info["latencia_ms"])
                perdas.append(info["perda"])
                entregues.append(info["entregue_bps"])
                demandas.append(info["demanda_bps"])
            energia_total = float(np.sum(energias))
            bits = float(np.sum(entregues)) * env.dt  # bits entregues no episodio
            registros.append({
                "seed": seed, "episode": ep,
                "energia_total_J": energia_total,
                "energia_por_bit_mJ": (energia_total / bits * 1e3) if bits > 0 else np.nan,
                "latencia_media_ms": float(np.mean(lats)),
                "latencia_p95_ms": float(np.percentile(lats, 95)),
                "latencia_p99_ms": float(np.percentile(lats, 99)),
                "throughput_medio_Mbps": float(np.mean(entregues)) / 1e6,
                "perda_media": float(np.mean(perdas)),
            })
    return pd.DataFrame(registros)


def resumo(df, nome):
    """Media/desvio e mediana/IQR das metricas (Secao 7.5)."""
    cols = ["energia_total_J", "energia_por_bit_mJ", "latencia_media_ms",
            "latencia_p95_ms", "latencia_p99_ms", "throughput_medio_Mbps",
            "perda_media"]
    r = {"politica": nome}
    for c in cols:
        r[c + "_media"] = float(df[c].mean())
        r[c + "_std"] = float(df[c].std())
        r[c + "_mediana"] = float(df[c].median())
        r[c + "_iqr"] = float(df[c].quantile(0.75) - df[c].quantile(0.25))
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cenario", choices=list(CENARIOS), default="baseline")
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--episodes", type=int, default=20)
    ap.add_argument("--steps-per-episode", type=int, default=200)
    ap.add_argument("--model", default=None,
                    help="caminho do modelo DQN .zip (opcional)")
    args = ap.parse_args()

    weights = CENARIOS[args.cenario]
    here = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(here, "..", "results")
    os.makedirs(results_dir, exist_ok=True)

    print(f"Avaliando cenario='{args.cenario}' pesos={weights} "
          f"seeds={args.seeds} episodes={args.episodes}")

    # Baselines (sempre rodam)
    df_base = rodar_politica(politica_baseline, weights, args.seeds,
                             args.episodes, args.steps_per_episode)
    df_heur = rodar_politica(politica_heuristica, weights, args.seeds,
                             args.episodes, args.steps_per_episode)

    resultados = [resumo(df_base, "5G_tradicional"),
                  resumo(df_heur, "heuristica")]
    dfs = {"5G_tradicional": df_base, "heuristica": df_heur}

    # Agente DQN (se modelo fornecido)
    if args.model and os.path.exists(args.model):
        from stable_baselines3 import DQN
        modelo = DQN.load(args.model)
        df_dqn = rodar_politica(None, weights, args.seeds, args.episodes,
                                args.steps_per_episode, modelo=modelo)
        resultados.append(resumo(df_dqn, "DQN"))
        dfs["DQN"] = df_dqn
    else:
        print("AVISO: nenhum modelo DQN informado (--model). "
              "Avaliando so os baselines.")

    df_resumo = pd.DataFrame(resultados)

    # Reducao de energia vs baseline 5G tradicional (a metrica central)
    e_base = df_resumo.loc[df_resumo.politica == "5G_tradicional",
                           "energia_total_J_media"].values[0]
    df_resumo["reducao_energia_%"] = (1 - df_resumo["energia_total_J_media"]
                                      / e_base) * 100

    # Salvar
    csv_path = os.path.join(results_dir, f"resumo_{args.cenario}.csv")
    df_resumo.to_csv(csv_path, index=False)
    for nome, d in dfs.items():
        d.to_csv(os.path.join(results_dir, f"bruto_{args.cenario}_{nome}.csv"),
                 index=False)

    # Tabela legivel para a Secao 8
    print("\n" + "=" * 78)
    print(f"RESULTADOS - cenario '{args.cenario}' (medias sobre "
          f"{args.seeds} sementes x {args.episodes} episodios)")
    print("=" * 78)
    print(f"{'Politica':<18}{'Energia(J)':>12}{'Reduc%':>9}"
          f"{'Lat(ms)':>10}{'Thr(Mbps)':>11}{'Perda':>8}{'mJ/bit':>9}")
    for _, row in df_resumo.iterrows():
        print(f"{row['politica']:<18}"
              f"{row['energia_total_J_media']:>12.1f}"
              f"{row['reducao_energia_%']:>9.1f}"
              f"{row['latencia_media_ms_media']:>10.1f}"
              f"{row['throughput_medio_Mbps_media']:>11.1f}"
              f"{row['perda_media_media']:>8.3f}"
              f"{row['energia_por_bit_mJ_media']:>9.2f}")
    print("=" * 78)
    print(f"\nResumo salvo em: {csv_path}")

    # Graficos
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
        nomes = df_resumo["politica"].tolist()
        cores = ["#888", "#4a90d9", "#2ca02c"][:len(nomes)]

        axes[0].bar(nomes, df_resumo["energia_total_J_media"], color=cores,
                    yerr=df_resumo["energia_total_J_std"], capsize=4)
        axes[0].set_ylabel("Energia total (J)")
        axes[0].set_title("Consumo energetico por politica")

        axes[1].bar(nomes, df_resumo["latencia_media_ms_media"], color=cores,
                    yerr=df_resumo["latencia_media_ms_std"], capsize=4)
        axes[1].set_ylabel("Latencia media (ms)")
        axes[1].set_title("Latencia por politica")

        axes[2].bar(nomes, df_resumo["throughput_medio_Mbps_media"], color=cores,
                    yerr=df_resumo["throughput_medio_Mbps_std"], capsize=4)
        axes[2].set_ylabel("Throughput medio (Mbps)")
        axes[2].set_title("Throughput por politica")

        for ax in axes:
            ax.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        fig_path = os.path.join(results_dir, f"kpis_{args.cenario}.png")
        plt.savefig(fig_path, dpi=130)
        print(f"Grafico salvo em: {fig_path}")
    except Exception as e:
        print(f"(grafico nao gerado: {e})")


if __name__ == "__main__":
    main()
