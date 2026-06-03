# Green Network — Seleção Sustentável de Enlace 5G/LEO com Aprendizado por Reforço

Ambiente de simulação em **Python/Gymnasium** e agente **Deep Q-Network (DQN)** para
seleção dinâmica e energeticamente eficiente de enlace em redes híbridas
**5G terrestre + satélites LEO** (Low Earth Orbit).

Este repositório contém o código-fonte da campanha experimental que valida a
arquitetura proposta no artigo científico associado. A simulação foi conduzida
em **Kali Linux**, em hardware modesto (sem GPU, PyTorch em variante CPU-only),
demonstrando reprodutibilidade sem necessidade de recursos computacionais
especializados.

> **Integridade científica.** A dinâmica do ambiente é construída a partir de
> parâmetros físicos independentes (consumo de potência por componente, latências
> típicas por enlace). A redução de energia **não é embutida** nas premissas: ela
> **emerge** da política aprendida pelo agente e é medida contra um baseline
> estático ("sempre 5G terrestre nominal"). Os números reportados são, portanto,
> resultados experimentais, não consequências aritméticas das hipóteses.

---

## Sumário

- [Visão geral](#visão-geral)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Instalação](#instalação)
- [Como usar](#como-usar)
- [Resultados](#resultados)
- [Como citar](#como-citar)
- [Licença](#licença)

---

## Visão geral

O agente observa o estado da rede (carga, latência, energia disponível, perda,
satélites visíveis e classe de tráfego dominante) e escolhe, a cada passo, uma
entre cinco ações de seleção de enlace:

| # | Ação | Descrição |
|---|------|-----------|
| 0 | `5G_TERRESTRE`  | gNodeB ativa em operação nominal |
| 1 | `LEO_SATELITAL` | encaminha tráfego ao segmento satelital |
| 2 | `HIBRIDO_SPLIT` | divide a carga entre 5G e LEO |
| 3 | `5G_LOW_POWER`  | 5G com potência reduzida (sleep parcial) |
| 4 | `DORMENCIA`     | célula em dormência; vizinhas absorvem o tráfego residual |

A função de recompensa pondera quatro objetivos (QoS, energia, latência e perda)
através de quatro pesos `(w1, w2, w3, w4)`, permitindo treinar o agente sob
diferentes prioridades operacionais:

| Cenário | w1 (QoS) | w2 (Energia) | w3 (Latência) | w4 (Perda) |
|---------|:--------:|:------------:|:-------------:|:----------:|
| Sustentabilidade | 0,3 | 0,5 | 0,1 | 0,1 |
| Baseline (equilíbrio) | 0,4 | 0,3 | 0,2 | 0,1 |
| Desempenho | 0,5 | 0,1 | 0,2 | 0,2 |

O modelo de energia segue a formulação afim de **Auer et al. (2011)**, com
parâmetros físicos por componente (gNodeB, satélite, gateway NTN, núcleo 5G).

---

## Estrutura do repositório

```
green-network/
├── env/
│   └── green_network_env.py     # Ambiente Gymnasium: MDP, recompensa, modelo de energia
├── agent/
│   ├── train_dqn.py             # Treina o agente DQN (Stable-Baselines3)
│   ├── evaluate.py              # Avalia a política contra os baselines (multi-semente)
│   └── models/                  # Modelos treinados (.zip) — gerados pelo treino
├── results/                     # CSV e gráficos PNG gerados pela avaliação
├── logs/                        # Logs de treino (Monitor)
├── requirements.txt
├── CITATION.cff
├── LICENSE
└── README.md
```

---

## Instalação

> **Importante:** o Python 3.13 do sistema é recente demais para a stack de RL.
> Use **Python 3.11.x** num ambiente isolado para garantir compatibilidade entre
> Stable-Baselines3, Gymnasium e PyTorch.

```bash
# 1. Clone o repositório
git clone https://github.com/<seu-usuario>/green-network.git
cd green-network

# 2. Crie e ative o ambiente virtual (Python 3.11.x)
python3.11 -m venv .venv
source .venv/bin/activate          # Linux / Mac
# .venv\Scripts\activate           # Windows (PowerShell)

# 3. Instale as dependências
pip install --upgrade pip
pip install -r requirements.txt
```

> **Regra de ouro:** o `.venv` **não** fica ativo entre sessões. Sempre que abrir
> um terminal novo, rode `source .venv/bin/activate` antes de qualquer comando.
> Se aparecer `ModuleNotFoundError: No module named 'gymnasium'`, é quase certo
> que o ambiente não está ativo — confira o `(.venv)` no início do prompt.

---

## Como usar

### 1. Teste rápido (só os baselines, leva segundos)

Confirma que tudo está no lugar, sem treinar nada:

```bash
cd agent
python evaluate.py --cenario baseline --seeds 5 --episodes 10
```

### 2. Treinar o agente DQN

```bash
cd agent
python train_dqn.py --cenario baseline         --timesteps 300000 --seed 0
python train_dqn.py --cenario sustentabilidade --timesteps 300000 --seed 0
python train_dqn.py --cenario desempenho       --timesteps 300000 --seed 0
```

Cada execução salva o modelo em `agent/models/dqn_<cenario>_seed<seed>.zip` e
gera a curva de convergência em `results/`.

### 3. Avaliar uma política treinada (multi-semente)

O nome do `--model` deve combinar com o `--cenario`:

```bash
python evaluate.py --cenario sustentabilidade --seeds 10 --episodes 20 \
    --model models/dqn_sustentabilidade_seed0.zip

python evaluate.py --cenario baseline --seeds 10 --episodes 20 \
    --model models/dqn_baseline_seed0.zip

python evaluate.py --cenario desempenho --seeds 10 --episodes 20 \
    --model models/dqn_desempenho_seed0.zip
```

Os resultados (CSV + gráficos PNG) são salvos em `results/`.

---

## Resultados

Médias sobre 10 sementes × 20 episódios, comparando cada política à rede 5G
tradicional (referência = 100% de energia). A redução de energia emerge da
política aprendida.

| Política | Energia (J) | Redução (%) | Latência (ms) | Throughput (Mbps) | Perda |
|----------|:-----------:|:-----------:|:-------------:|:-----------------:|:-----:|
| DQN desempenho       | 20913,4 | −2,2 | 27,6 | 198,7 | 0,000 |
| DQN baseline         | 18480,0 |  9,7 | 36,8 | 198,7 | 0,001 |
| DQN sustentabilidade | 13948,8 | 31,9 | 55,7 | 186,3 | 0,057 |

**Leitura.** Há um trade-off claro e contínuo: priorizar energia (cenário
sustentabilidade) entrega ~32% de redução, ao custo de maior latência; priorizar
desempenho preserva a latência da rede tradicional, sem economia. O agente DQN
domina a heurística simples na curva de Pareto — economiza de forma contextual
(apenas quando seguro), enquanto a regra fixa economiza de forma cega.

---

## Como citar

Se este software for útil à sua pesquisa, por favor cite o artigo e o código.
O arquivo [`CITATION.cff`](CITATION.cff) contém os metadados de citação.

```
Coutinho, D. (2026). Green Network: Seleção sustentável de enlace 5G/LEO com
aprendizado por reforço (DQN) [Software]. https://doi.org/10.5281/zenodo.20520840
```

> Após publicar no Zenodo, substitua `<DOI-do-Zenodo>` pelo DOI gerado, e
> preencha o campo `orcid` em `CITATION.cff`.

---

## Licença

Distribuído sob a licença **MIT**. Veja o arquivo [`LICENSE`](LICENSE) para os
termos completos. Em resumo: você pode usar, copiar, modificar e distribuir o
código, inclusive comercialmente, desde que mantenha o aviso de copyright.
