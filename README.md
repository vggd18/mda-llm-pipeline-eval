# Projeto TAES: Replica experimental aproximada CIM -> DSL/PIM -> UML/PSM -> Python

Este projeto implementa uma replica aproximada e reproduzivel de um pipeline inspirado no artigo "LLM-Driven MDA Pipeline for Generating UML Class Diagrams and Code" (Babaalla, Jakimi e Oualla, IEEE Access, 2025).

Importante: este repositorio nao afirma reproduzir fielmente o artigo original. Como o codigo-fonte original nao esta disponivel, todos os pontos dependentes do paper estao marcados como:

- `[INSERIR INFORMACAO DO PAPER AQUI]`
- `[CONFIRMAR COM BASE NO PAPER]`
- `TODO: preencher com informacao do artigo`

O PDF permitiu preencher os principais pontos metodologicos: corpus IOB enriquecido, modelos NER comparados, DSL textual, geracao de UML e codigo Python esqueleto. Ainda permanecem editaveis os dados exatos dos cenarios/figuras e a rubrica fina de fidelidade semantica.

## Onde inserir informacoes do artigo

Preencha primeiro estes arquivos:

1. `docs/assumptions.md`: escopo, lacunas e suposicoes.
2. `docs/experiment_design.md`: detalhes do metodo descrito no paper.
3. `data/input_cases_template.csv`: casos CIM e categorias de dificuldade.
4. `data/gold_standard_template.csv`: entidades esperadas, DSL esperada, codigo esperado e regras.
5. `config/models.yaml`: modelos GPT/LLM que serao testados.
6. `config/experiment_config.yaml`: seeds, experimentos ativos e criterio de avaliacao.
7. `prompts/*.txt`: prompts usados em cada etapa LLM.

## Instalar

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Crie um arquivo `.env` se for usar API:

```env
OPENAI_API_KEY=sua_chave_aqui
```

Sem `.env`, o projeto roda com modelos locais `mock` e `heuristic_baseline`.

## Rodar todos os experimentos

```powershell
python -m src.run_experiments
```

Se o Windows responder que `python` nao foi encontrado, use um Python instalado localmente ou, neste ambiente Codex, o runtime embutido:

```powershell
& "C:\Users\Vitor\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m src.run_experiments
```

## Comparar GPT atual e modelos gratuitos recentes

Edite [config/models.yaml](C:/Users/Vitor/OneDrive/Documentos/Projeto%20TAES/config/models.yaml) e habilite os modelos desejados.

Opcoes ja preparadas:

- `gpt_current`: OpenAI GPT atual via API.
- `gpt_current_cost_control`: OpenAI mais barato para custo/beneficio.
- `github_models_gpt4o_mini`: GitHub Models gratuito/experimental no Codespaces.
- `github_models_gpt41`: GitHub Models mais forte, se disponivel na sua conta.
- `ollama_qwen_recent_free`: Qwen recente local via Ollama.
- `ollama_deepseek_recent_free`: DeepSeek recente local via Ollama.
- `ollama_llama_recent_free`: Llama recente local via Ollama.
- `ollama_apertus_free`: modelo aberto/auditavel local via Ollama.
- `openrouter_free_model`: slot para modelo gratuito hospedado compativel com OpenAI API.

Para Ollama:

```powershell
ollama pull qwen3.5:32b
ollama pull deepseek-r1:32b
python -m src.run_experiments
```

Os nomes exatos dos modelos locais podem variar; ajuste o campo `model_id` conforme o que estiver instalado.

Para GitHub Models no Codespaces:

```bash
echo $GITHUB_TOKEN
python -m src.run_experiments
```

Antes de rodar, habilite `github_models_gpt4o_mini` ou `github_models_gpt41` em `config/models.yaml`. Se `$GITHUB_TOKEN` estiver vazio, crie um PAT com escopo `models` e rode `export GITHUB_TOKEN="..."`.

Importante: a execucao padrao com `heuristic_baseline` serve para validar o pipeline e gerar arquivos de exemplo. Nao use esses numeros como conclusao empirica da comparacao com o paper. Para conclusoes, habilite pelo menos um provider real (`openai`, `ollama` ou `openai_compatible`).

Saidas geradas:

- `results/raw_results.csv`
- `results/summary_metrics.csv`
- `results/error_analysis.csv`
- `results/ablation_results.csv`
- `results/model_comparison.csv`
- `results/figures/f1_by_model.png`
- `results/figures/end_to_end_success.png`
- `results/figures/errors_by_stage.png`
- `results/figures/dsl_ablation.png`
- `results/figures/business_rule_change_impact.png`

## Experimentos implementados

- A: pipeline completo aproximado: CIM -> extracao -> DSL/PIM -> codigo/PSM.
- B: pipeline sem DSL: CIM -> codigo diretamente.
- C: DSL em multiplas camadas: CIM -> DSL de requisitos -> DSL de design -> codigo.
- D: mudanca de regra de negocio e avaliacao de consistencia.
- E: generalizacao em casos simples, medianos, ambiguos, incompletos e fora do padrao.
- F: comparacao entre modelos configurados, incluindo baseline heuristico.

## Sintaxe DSL adotada do paper

```text
Class Customer:
Attributes: name, email
Methods: placeOrder
Class Order:
Attributes: id, date
Relation: Customer association Order
```

Relacoes permitidas: `association`, `composition`, `aggregation` e `inheritance`.

## Limites

As metricas sao objetivas quando existe gold standard preenchido. Se campos esperados estiverem vazios, o avaliador registra observacoes e evita inventar resultados. Os cenarios do paper incluidos em `data/` sao aproximacoes textuais editaveis, nao transcricoes oficiais das figuras.
