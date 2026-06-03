# Metadados para submissão — SciELO Preprints

Copie e cole cada campo no formulário de submissão. **Importante:** o resumo e o
abstract abaixo foram **atualizados para refletir os resultados obtidos** (faixa
medida de ~10% a ~32%), em coerência com o corpo do artigo já revisado — e não a
projeção de "até 42%" da versão antiga. Confira se o PDF que você vai enviar
também usa o resumo atualizado (recomendo alinhar os dois).

---

## Título (português)

Modelo sustentável de integração 5G–LEO com plano de controle por aprendizado por reforço para eficiência energética em redes não-terrestres

## Title (English)

A sustainable 5G–LEO integration model with a reinforcement-learning control plane for energy efficiency in non-terrestrial networks

---

## Autor

- Nome: Davi Coutinho
- ORCID: 0000-0000-0000-0000   ← substitua pelo seu ORCID real
- Afiliação: (preencha conforme combinar com a faculdade — ex.: Estácio)

---

## Área / Seção

Ciências Exatas e da Terra / Engenharias — Ciência da Computação / Redes e
Telecomunicações.

---

## Resumo (português)

A expansão das redes 5G aliada à proliferação das constelações de satélites em
órbita baixa (LEO), como Starlink, OneWeb e Kuiper, inaugura uma nova era de
conectividade global, capaz de alcançar áreas rurais, marítimas e aéreas antes
desassistidas. Todavia, essa expansão eleva expressivamente o consumo energético
do setor de tecnologia da informação e comunicação (TIC), que já responde por
mais de 3% das emissões globais de CO₂. Este artigo propõe um modelo sustentável
de integração entre redes 5G terrestres e satélites LEO, no qual um plano de
controle baseado em inteligência artificial (IA) decide dinamicamente o enlace de
comunicação mais eficiente em função do tráfego, da latência, da qualidade de
serviço (QoS) e, sobretudo, do consumo energético. A arquitetura proposta segue
as diretrizes do 3GPP para redes não-terrestres (5G-NTN), formaliza o problema
como um Processo de Decisão de Markov e emprega aprendizado por reforço
(Deep Q-Network) como mecanismo de decisão. A metodologia inclui revisão
bibliográfica, posicionamento frente ao estado da arte, modelagem matemática do
consumo energético, implementação de um ambiente de simulação em Python/Gymnasium
e análise estatística com múltiplas sementes. Os resultados obtidos demonstram
que a redução de consumo energético emerge da política aprendida e varia conforme
a prioridade operacional adotada: de aproximadamente 10% no ponto de equilíbrio a
cerca de 32% no ponto de máxima sustentabilidade, este último ao custo de maior
latência. Os achados evidenciam um trade-off explícito entre energia e qualidade
de serviço e contribuem para o avanço das chamadas Green Networks.

## Palavras-chave

Redes 5G; Satélites LEO; Inteligência Artificial; Eficiência Energética; Redes Não-Terrestres; Green Networks; Aprendizado por Reforço.

---

## Abstract (English)

The expansion of 5G networks combined with the rise of Low Earth Orbit (LEO)
satellite constellations such as Starlink, OneWeb, and Kuiper inaugurates a new
era of global connectivity capable of reaching rural, maritime, and aerial areas
that were previously underserved. However, this expansion significantly increases
the energy consumption of the Information and Communication Technology (ICT)
sector, which already accounts for more than 3% of global CO₂ emissions. This
article proposes a sustainable model for integrating terrestrial 5G networks with
LEO satellites, in which an artificial intelligence (AI) based control plane
dynamically decides the most efficient communication link as a function of
traffic, latency, quality of service (QoS) and, above all, energy consumption.
The proposed architecture follows the 3GPP guidelines for non-terrestrial
networks (5G-NTN), formalizes the problem as a Markov Decision Process and employs
reinforcement learning (Deep Q-Network) as the decision mechanism. The methodology
includes a literature review, positioning against the state of the art,
mathematical modeling of energy consumption, the implementation of a
Python/Gymnasium simulation environment, and statistical analysis with multiple
seeds. The results obtained show that the reduction in energy consumption emerges
from the learned policy and varies according to the operational priority adopted:
from approximately 10% at the equilibrium point to about 32% at the maximum
sustainability point, the latter at the cost of higher latency. The findings
highlight an explicit trade-off between energy and quality of service and
contribute to the advancement of so-called Green Networks.

## Keywords

5G Networks; LEO Satellites; Artificial Intelligence; Energy Efficiency; Non-Terrestrial Networks; Green Networks; Reinforcement Learning.

---

## Declaração de disponibilidade de dados/código (sugestão)

O código-fonte completo da simulação está disponível publicamente em
https://github.com/<seu-usuario>/green-network e arquivado de forma citável em
https://doi.org/10.5281/zenodo.XXXXXXX, sob licença MIT.
