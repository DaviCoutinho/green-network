# train_dqn.py
"""
train_dqn.py
============
Treina o agente DQN (Stable-Baselines3) no GreenNetworkEnv.

Hiperparametros alinhados com a Secao 7.3 do artigo:
  gamma = 0.95, epsilon inicial = 1.0 -> 0.05 (decaimento),
  ~5000 episodios x 200 passos. Aqui expomos via timesteps totais.

Uso:
    python train_dqn.py --cenario baseline --timesteps 300000 --seed 0
    python train_dqn.py --cenario sustentabilidade --timesteps 300000 --seed 0
    python train_dqn.py --cenario desempenho --timesteps 300000 --seed 0

Salva o modelo em agent/models/dqn_<cenario>_seed<seed>.zip
e o log de treino em logs/.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "env"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "env"))

import numpy as np
from green_network_env import GreenNetworkEnv

from stable_baselines3 import DQN
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.callbacks import CheckpointCallback

# Tabela 4 do artigo -- conjuntos de pesos (w1 QoS, w2 Energia, w3 Lat, w4 Perda)
CENARIOS = {
    "sustentabilidade": (0.3, 0.5, 0.1, 0.1),
    "baseline":         (0.4, 0.3, 0.2, 0.1),
    "desempenho":       (0.5, 0.1, 0.2, 0.2),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cenario", choices=list(CENARIOS), default="baseline")
    ap.add_argument("--timesteps", type=int, default=300000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--steps-per-episode", type=int, default=200)
    args = ap.parse_args()

    weights = CENARIOS[args.cenario]
    here = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(here, "models")
    logs_dir = os.path.join(here, "..", "logs")
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)

    def make_env():
        env = GreenNetworkEnv(weights=weights,
                              steps_per_episode=args.steps_per_episode,
                              seed=args.seed)
        return Monitor(env, filename=os.path.join(
            logs_dir, f"monitor_{args.cenario}_seed{args.seed}"))

    env = make_env()

    # DQN com MLP. epsilon: 1.0 -> 0.05 ao longo de ~60% do treino (Sec 7.3).
    model = DQN(
        "MlpPolicy", env,
        learning_rate=1e-3,
        gamma=0.95,                      # Secao 7.3
        exploration_initial_eps=1.0,     # Secao 7.3
        exploration_final_eps=0.05,      # Secao 7.3 (epsilon_min)
        exploration_fraction=0.6,
        buffer_size=50000,               # replay buffer (Sec 7.4)
        learning_starts=1000,
        batch_size=64,
        target_update_interval=500,      # target network (Sec 7.3)
        train_freq=4,
        seed=args.seed,
        verbose=1,
    )

    print(f"Treinando cenario='{args.cenario}' pesos={weights} "
          f"timesteps={args.timesteps} seed={args.seed}")

    # Checkpoint periodico: se o treino travar, nao perde tudo.
    ckpt = CheckpointCallback(
        save_freq=max(args.timesteps // 10, 10000),
        save_path=os.path.join(models_dir, "checkpoints"),
        name_prefix=f"dqn_{args.cenario}_seed{args.seed}")

    model.learn(total_timesteps=args.timesteps, progress_bar=False,
                callback=ckpt)

    path = os.path.join(models_dir, f"dqn_{args.cenario}_seed{args.seed}.zip")
    model.save(path)
    print(f"Modelo salvo em: {path}")

    # Plot da curva de convergencia (retorno medio movel, Secao 7.3).
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from stable_baselines3.common.monitor import load_results
        from stable_baselines3.common.results_plotter import ts2xy

        x, y = ts2xy(load_results(logs_dir), "timesteps")
        if len(y) > 0:
            # media movel de 100 episodios (criterio do artigo)
            w = min(100, len(y))
            y_mov = np.convolve(y, np.ones(w) / w, mode="valid")
            x_mov = x[w - 1:]
            fig, ax = plt.subplots(figsize=(8, 4.5))
            ax.plot(x, y, alpha=0.25, label="retorno por episodio")
            ax.plot(x_mov, y_mov, lw=2, label=f"media movel ({w} ep)")
            ax.set_xlabel("timesteps")
            ax.set_ylabel("retorno do episodio")
            ax.set_title(f"Convergencia DQN - {args.cenario} (seed {args.seed})")
            ax.legend()
            ax.grid(alpha=0.3)
            plt.tight_layout()
            results_dir = os.path.join(here, "..", "results")
            os.makedirs(results_dir, exist_ok=True)
            fig_path = os.path.join(
                results_dir, f"convergencia_{args.cenario}_seed{args.seed}.png")
            plt.savefig(fig_path, dpi=130)
            print(f"Curva de convergencia salva em: {fig_path}")
    except Exception as e:
        print(f"(curva nao gerada: {e})")


if __name__ == "__main__":
    main()
