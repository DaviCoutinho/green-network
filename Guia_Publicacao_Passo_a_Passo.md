# Guia de Publicação — Passo a Passo

Objetivo: **registrar autoria** do artigo e do código, com identificadores
permanentes (DOI) e indexação no Google Acadêmico. Tudo gratuito e legítimo.

Ordem recomendada:

1. Criar ORCID (5 min)
2. Subir o código no GitHub (10 min)
3. Gerar o DOI do código no Zenodo (10 min)
4. Inserir o DOI no artigo (2 min)
5. Submeter o PDF ao SciELO Preprints (20 min)

---

## Passo 1 — Criar o ORCID

O ORCID é um identificador único de autor, exigido pelo SciELO Preprints.

1. Acesse **https://orcid.org/register**
2. Preencha nome, e-mail e senha.
3. Confirme o e-mail. Pronto — você terá um ID no formato
   `0000-0000-0000-0000`.
4. **Anote esse número.** Ele será pedido na submissão do preprint, e você
   vai colá-lo no arquivo `CITATION.cff` do repositório (campo `orcid`).

---

## Passo 2 — Subir o código no GitHub

Você já tem conta. O repositório pronto está no `.zip` que acompanha este guia
(`green-network-repo.zip`). Descompacte-o; a pasta `green-network/` contém tudo.

### Opção A — pela interface web (mais simples)

1. Em **https://github.com/new**, crie um repositório **público** chamado
   `green-network`. **Não** marque "Add a README" (já temos um).
2. Na página do repositório vazio, clique em **"uploading an existing file"**.
3. Arraste **todo o conteúdo de dentro** da pasta `green-network/` (o README,
   LICENSE, as pastas `env/`, `agent/`, etc.) — não a pasta em si, mas o que
   está dentro dela.
4. Escreva uma mensagem de commit (ex.: "Versão inicial do laboratório") e
   clique em **Commit changes**.

### Opção B — pela linha de comando (no Kali)

```bash
cd ~/green-network        # a pasta real do seu laboratório
git init
git add README.md LICENSE requirements.txt CITATION.cff .gitignore env agent results logs
git commit -m "Versão inicial do laboratório Green Network"
git branch -M main
git remote add origin https://github.com/<seu-usuario>/green-network.git
git push -u origin main
```

> **Atenção aos modelos `.zip`:** se quiser que os modelos treinados
> (`agent/models/dqn_*.zip`) fiquem no repositório, adicione-os com
> `git add agent/models/*.zip`. Se forem grandes (>50 MB cada), prefira
> deixá-los de fora (o `.gitignore` já tem a linha pronta para descomentar) e
> disponibilizá-los no próprio Zenodo no Passo 3.

---

## Passo 3 — Gerar o DOI do código no Zenodo

O Zenodo (mantido pelo CERN) transforma um repositório do GitHub num artefato
citável com DOI.

1. Acesse **https://zenodo.org** e clique em **Log in → with GitHub**
   (autorize a conexão).
2. Vá em **https://zenodo.org/account/settings/github/**. Aparecerá a lista dos
   seus repositórios. Ligue a chave (toggle) ao lado de **`green-network`**.
3. Volte ao GitHub, na página do repositório, e crie uma **Release**:
   **Releases → Create a new release**. Defina a tag `v1.0.0`, título
   "Green Network v1.0.0" e publique.
4. O Zenodo detecta a release automaticamente e gera um **DOI**. Encontre-o em
   **https://zenodo.org/account/settings/github/** (ou na sua página de
   uploads). Será algo como `10.5281/zenodo.XXXXXXX`.
5. **Anote o DOI.**

Depois disso:
- Edite o `CITATION.cff` e preencha o DOI e seu ORCID.
- No README, substitua `<DOI-do-Zenodo>` pelo DOI real.
- Faça um novo commit (e, se quiser, uma nova release `v1.0.1`).

---

## Passo 4 — Inserir o DOI do código no artigo

No artigo (Seção 7.5 ou no Apêndice C), adicione uma frase como:

> "O código-fonte completo da simulação está disponível publicamente em
> https://github.com/<seu-usuario>/green-network e arquivado de forma citável
> em https://doi.org/10.5281/zenodo.XXXXXXX, sob licença MIT."

Gere o **PDF final** do artigo com essa informação — é esse PDF que vai ao
SciELO Preprints.

---

## Passo 5 — Submeter o PDF ao SciELO Preprints

1. Cadastre-se em **https://preprints.scielo.org/index.php/scielo/user/register**
   (ou faça login se já tiver conta).
2. Tenha em mãos: o **PDF final** do artigo e seu **número ORCID**.
3. Inicie uma nova submissão. Você vai:
   - escolher a área/seção do conhecimento (Ciências Exatas / Engenharias —
     Ciência da Computação / Telecomunicações);
   - colar título, resumo, abstract e palavras-chave
     (use o arquivo `metadados_scielo.md` que acompanha este guia);
   - fazer o upload do PDF;
   - aceitar as declarações de conformidade (ver abaixo).
4. Após uma checagem editorial básica, o preprint é publicado e recebe um
   **DOI próprio**, ficando indexado no Google Acadêmico e na rede SciELO.

### Declarações que você vai aceitar (esteja ciente)

- Que o manuscrito **não foi publicado** em periódico nem depositado em outro
  servidor de preprints.
- Que **você é o responsável** pelo conteúdo.
- Que, uma vez postado, o preprint **só pode ser retirado** mediante pedido à
  Secretaria Editorial (que afixa um aviso de retratação). Por isso, suba a
  versão **final e revisada**.
- Que o preprint será disponibilizado sob licença **Creative Commons CC-BY**
  (atribuição) — qualquer pessoa pode compartilhar, desde que cite você.

> **Versionamento:** o SciELO Preprints permite enviar novas versões sem limite.
> Quando você concluir a fase ns-3 + Hypatia (trabalho futuro), pode atualizar.

---

## Avisos importantes

- **Fuja de revistas/"congressos" predatórios** — aqueles que mandam e-mail
  prometendo publicação rápida mediante pagamento. Eles predam autores
  iniciantes e prejudicam o currículo. SciELO, Zenodo e arXiv são gratuitos e
  idôneos.
- **arXiv (opcional, mais tarde):** desde janeiro de 2026, novos autores
  precisam de "endorsement" (endosso) de um autor já estabelecido na categoria
  (ex.: cs.NI). Um bom caminho é pedir ao seu professor orientador, se ele
  publicar na área. Deixe para depois do SciELO.
- **Coautoria/afiliação:** você optou por publicar só como Davi Coutinho. Se a
  Estácio exigir menção institucional ou coautoria do orientador, ajuste antes
  de submeter (depois é mais difícil corrigir).
