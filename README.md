# mda-llm-pipeline-eval

Projeto experimental reproduzível para avaliar e estender criticamente o artigo **"LLM-Driven MDA Pipeline for Generating UML Class Diagrams and Code"**, de Zakaria Babaalla, Abdeslam Jakimi e Mohamed Oualla, publicado na **IEEE Access em 2025**.

O artigo propõe um pipeline baseado em MDA para transformar especificações textuais em artefatos de software:

```text
CIM textual -> extração com Transformer/NER -> DSL/PIM -> UML/PSM -> código Python
```

Este projeto não tenta afirmar uma reprodução fiel do artigo original, porque o código-fonte e o corpus original não foram incorporados. A proposta aqui é construir uma **réplica aproximada e experimental**, adicionando testes que investigam limitações discutidas em sala.

## Objetivo do projeto

O objetivo é melhorar a qualidade da avaliação do pipeline proposto no paper.

O artigo reporta resultados muito altos, mas alguns pontos ficaram abertos:

- a base pode ser favorável ou enviesada;
- os Transformers parecem ser usados principalmente para identificação inicial de tokens;
- o restante do pipeline parece mais algorítmico/determinístico;
- a DSL é tratada como etapa central, mas o artigo não testa sua remoção;
- o artigo compara com modelos antigos, como GPT-3.5 e DeepSeek;
- o artigo não avalia bem o caso em que o usuário modifica o artefato e depois a regra de negócio muda.

Este projeto implementa um ambiente experimental para testar essas hipóteses.

## Informações do paper usadas como referência

Do PDF analisado:

- Título: **LLM-Driven MDA Pipeline for Generating UML Class Diagrams and Code**
- Autores: **Zakaria Babaalla, Abdeslam Jakimi, Mohamed Oualla**
- Publicação: **IEEE Access, 2025**
- DOI informado no artigo: `10.1109/ACCESS.2025.3615828`
- Corpus: **132 especificações textuais**
- Sentenças: **915**
- Tokens: **11.460**
- Ocorrências anotadas: **10.650**
- Split experimental: **80% treino / 20% teste**
- Teste: aproximadamente **185 sentenças**
- Modelos comparados no artigo:
  - BERT
  - RoBERTa
  - XLNet
  - SpanBERT
  - MiniLM
  - Electra
- Modelos generativos citados na comparação:
  - GPT-3.5
  - DeepSeek

O artigo usa um esquema IOB enriquecido para extração de entidades UML:

```text
B_CLASS_SOURCE / I_CLASS_SOURCE
B_CLASS_TARGET / I_CLASS_TARGET
B_ATTRIBUTE / I_ATTRIBUTE
B_METHOD / I_METHOD
B_ASSOCIATION
B_COMPOSITION
B_AGGREGATION
B_INHERITANCE
O
```

## DSL usada

A DSL textual segue o formato descrito no paper:

```text
Class Customer:
Attributes: name, email
Methods: placeOrder
Class Order:
Attributes: id, date
Relation: Customer association Order
```

Tipos de relação aceitos:

```text
association
composition
aggregation
inheritance
```

## O que este projeto adiciona

Além da réplica aproximada do pipeline, o projeto adiciona experimentos críticos.

### Experimento A - Pipeline completo

```text
CIM textual -> extração -> DSL/PIM -> código Python
```

Representa a aproximação principal do artigo.

### Experimento B - Sem DSL

```text
CIM textual -> código Python diretamente
```

Serve para testar se a DSL é realmente necessária.

### Experimento C - DSL em múltiplas camadas

```text
CIM textual -> DSL de requisitos -> DSL de design -> código Python
```

Testa a ideia de que DSLs podem ser usadas em mais de uma camada de abstração, não apenas como PIM.

### Experimento D - Mudança de regra de negócio

Simula um cenário realista:

```text
gera artefato inicial
-> usuário modifica artefato
-> regra de negócio muda depois
-> mede inconsistência
```

Esse caso não é tratado adequadamente no artigo.

### Experimento E - Generalização

Testa o pipeline em casos:

- simples;
- médios;
- ambíguos;
- incompletos;
- fora do padrão;
- com relações implícitas;
- com coreferência.

### Comparação entre modelos

O projeto compara:

- baseline heurístico;
- GitHub Models;
- modelos gratuitos via OpenRouter;
- modelos atuais/gratuitos em vez de apenas GPT-3.5/DeepSeek antigo.

## Estrutura do projeto

```text
config/
  models.yaml
  experiment_config.yaml

data/
  input_cases_template.csv
  gold_standard_template.csv

docs/
  assumptions.md
  experiment_design.md
  reproduction_guide.md
  presentation_notes.md

prompts/
  extraction_prompt.txt
  dsl_generation_prompt.txt
  code_generation_prompt.txt
  direct_code_prompt.txt
  business_rule_change_prompt.txt

src/
  run_experiments.py
  pipelines/
  evaluators/
  metrics/
  utils/

results/
  raw_results.csv
  summary_metrics.csv
  model_comparison.csv
  error_analysis.csv
  ablation_results.csv
  validity_warnings.csv
  figures/
```

## Instalação

No Codespaces ou Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

No Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configurar variáveis de ambiente

### GitHub Models

No Codespaces, verifique se o token existe:

```bash
echo $GITHUB_TOKEN
```

Se estiver vazio, crie um Personal Access Token no GitHub com escopo `models` e rode:

```bash
export GITHUB_TOKEN="seu_token_aqui"
```

### OpenRouter

Crie uma chave no OpenRouter e rode:

```bash
export OPENROUTER_API_KEY="sua_chave_aqui"
```

## Configurar modelos

Edite:

```text
config/models.yaml
```

Configuração recomendada:

```yaml
models:
  - name: heuristic_baseline
    provider: local
    enabled: true
    cost_per_1k_input_tokens_usd: 0.0
    cost_per_1k_output_tokens_usd: 0.0
    notes: "Baseline heuristico local e reproduzivel."

  - name: github_models_gpt4o_mini
    provider: openai_compatible
    enabled: true
    model_id: "openai/gpt-4o-mini"
    base_url: "https://models.github.ai/inference"
    api_key_env: "GITHUB_TOKEN"
    request_delay_seconds: 4
    max_retries: 6
    timeout_seconds: 180
    cost_per_1k_input_tokens_usd: 0.0
    cost_per_1k_output_tokens_usd: 0.0
    notes: "GPT-4o mini via GitHub Models."

  - name: github_models_gpt41
    provider: openai_compatible
    enabled: true
    model_id: "openai/gpt-4.1"
    base_url: "https://models.github.ai/inference"
    api_key_env: "GITHUB_TOKEN"
    request_delay_seconds: 5
    max_retries: 6
    timeout_seconds: 180
    cost_per_1k_input_tokens_usd: 0.0
    cost_per_1k_output_tokens_usd: 0.0
    notes: "GPT-4.1 via GitHub Models."

  - name: openrouter_qwen3_coder_free
    provider: openai_compatible
    enabled: true
    model_id: "qwen/qwen3-coder:free"
    base_url: "https://openrouter.ai/api/v1"
    api_key_env: "OPENROUTER_API_KEY"
    request_delay_seconds: 10
    max_retries: 6
    timeout_seconds: 240
    cost_per_1k_input_tokens_usd: 0.0
    cost_per_1k_output_tokens_usd: 0.0
    notes: "Qwen3 Coder gratuito via OpenRouter."

  - name: openrouter_llama33_70b_free
    provider: openai_compatible
    enabled: true
    model_id: "meta-llama/llama-3.3-70b-instruct:free"
    base_url: "https://openrouter.ai/api/v1"
    api_key_env: "OPENROUTER_API_KEY"
    request_delay_seconds: 10
    max_retries: 6
    timeout_seconds: 240
    cost_per_1k_input_tokens_usd: 0.0
    cost_per_1k_output_tokens_usd: 0.0
    notes: "Llama 3.3 70B gratuito via OpenRouter."

  - name: openrouter_gpt_oss_120b_free
    provider: openai_compatible
    enabled: true
    model_id: "openai/gpt-oss-120b:free"
    base_url: "https://openrouter.ai/api/v1"
    api_key_env: "OPENROUTER_API_KEY"
    request_delay_seconds: 10
    max_retries: 6
    timeout_seconds: 240
    cost_per_1k_input_tokens_usd: 0.0
    cost_per_1k_output_tokens_usd: 0.0
    notes: "GPT-OSS 120B gratuito via OpenRouter."
```

## Rodar o baseline

Para validar o pipeline sem API externa, deixe só o baseline habilitado:

```yaml
heuristic_baseline:
  enabled: true
```

Depois rode:

```bash
python -m src.run_experiments
```

## Rodar com modelos reais/gratuitos

Depois de configurar `GITHUB_TOKEN` e/ou `OPENROUTER_API_KEY`, rode:

```bash
python -m src.run_experiments
```

Se aparecer erro `429 Too Many Requests`, isso é limite de taxa da API gratuita. Não é problema de timeout.

Soluções:

1. Aumentar `request_delay_seconds`.
2. Rodar menos modelos por vez.
3. Rodar um provedor por vez.

Exemplo:

```yaml
request_delay_seconds: 15
max_retries: 8
timeout_seconds: 300
```

## Verificar se deu certo

Depois da execução:

```bash
cat results/model_comparison.csv
grep "fallback\|ERRO\|429\|404" results/raw_results.csv | head -n 30
```

Se aparecer muito `fallback_to_heuristic`, significa que o modelo falhou e o pipeline usou fallback.

Nesse caso, os resultados daquele modelo devem ser tratados com cuidado.

## Arquivos gerados

```text
results/raw_results.csv
```

Uma linha por execução.

```text
results/summary_metrics.csv
```

Médias por modelo e experimento.

```text
results/model_comparison.csv
```

Resumo por modelo.

```text
results/error_analysis.csv
```

Análise dos erros.

```text
results/ablation_results.csv
```

Comparação entre pipeline completo, sem DSL e DSL multicamadas.

```text
results/validity_warnings.csv
```

Avisos metodológicos.

```text
results/figures/
```

Gráficos gerados automaticamente:

```text
f1_by_model.png
end_to_end_success.png
errors_by_stage.png
dsl_ablation.png
business_rule_change_impact.png
```

## Métricas

### `entity_precision`

Proporção de entidades extraídas que estão corretas.

### `entity_recall`

Proporção de entidades esperadas que foram encontradas.

### `entity_f1`

Média harmônica entre precisão e recall.

### `dsl_correct_rate`

Similaridade aproximada entre DSL gerada e DSL esperada.

### `dsl_syntax_validity`

Indica se a DSL respeita a sintaxe esperada.

### `code_correct_rate`

Verifica se fragmentos esperados aparecem no código gerado.

### `syntax_errors`

Número de erros sintáticos no código Python.

### `semantic_errors`

Erros semânticos aproximados com base nas regras esperadas.

### `semantic_rule_coverage`

Cobertura aproximada das regras semânticas esperadas.

### `business_rule_inconsistencies`

Mede inconsistência após mudança posterior de regra de negócio.

### `end_to_end_success`

Indica sucesso do pipeline completo.

### `stage_failure_count`

Número médio de falhas por etapa.

## Como interpretar os resultados

### DSL

Se `B_no_dsl` tiver desempenho inferior a `A_full_pipeline`, isso sugere que a DSL contribui para controle estrutural e rastreabilidade.

### Mudança de regra de negócio

Se `business_rule_inconsistencies` for alto, isso reforça a crítica de que o artigo não trata bem mudanças posteriores após edição do usuário.

### Modelos atuais

Se modelos atuais não superarem muito o baseline, isso pode indicar:

- métrica ainda rígida;
- problema de prompt;
- fallback heurístico;
- dificuldade real da tarefa;
- necessidade de arquitetura híbrida melhor.

### Fallbacks

Resultados com `fallback_to_heuristic_*` não devem ser tratados como desempenho puro do modelo.

## Como usar na apresentação

Mensagem principal:

> Este projeto não apenas replica aproximadamente o artigo. Ele propõe uma avaliação crítica e reproduzível do pipeline, testando pontos que o artigo não avaliou: generalização, remoção da DSL, uso de modelos atuais, DSL em múltiplas camadas e mudança posterior de regra de negócio.

Conclusão sugerida:

> A DSL ajuda na estruturação e rastreabilidade, mas o pipeline continua frágil diante de mudanças posteriores de regra de negócio. A comparação com modelos atuais mostra que a melhoria não depende apenas de trocar o modelo, mas de redesenhar o processo de reconciliação entre texto, DSL, UML e código.

## Limitações

- O código original do artigo não foi usado.
- O corpus original não foi incorporado.
- Os cenários do paper foram aproximados a partir das descrições disponíveis.
- Algumas APIs gratuitas podem falhar por limite de taxa.
- Alguns resultados podem cair em fallback heurístico.
- A avaliação semântica ainda é aproximada.

## Comandos úteis

Rodar tudo:

```bash
python -m src.run_experiments
```

Limpar imagens antigas:

```bash
rm -f results/figures/*.png
```

Limpar cache Python:

```bash
find . -type d -name "__pycache__" -exec rm -rf {} +
```

Ver modelos comparados:

```bash
cat results/model_comparison.csv
```

Ver erros/fallbacks:

```bash
grep "fallback\|ERRO\|429\|404" results/raw_results.csv | head -n 30
```

Ver arquivos gerados:

```bash
ls results
ls results/figures
```