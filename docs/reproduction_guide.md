# Guia de reproducao

## 1. Preparar ambiente

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Preencher dados

Edite:

- `data/input_cases_template.csv`
- `data/gold_standard_template.csv`
- `docs/assumptions.md`
- `config/models.yaml`
- `config/experiment_config.yaml`

Nao remova marcadores `[INSERIR INFORMACAO DO PAPER AQUI]` enquanto a informacao nao tiver sido confirmada.

Os casos `scenario_1_hardware`, `scenario_2_editorial` e `scenario_3_library` correspondem aos temas citados no paper, mas o texto de entrada e o gold standard atuais sao aproximacoes. Para uma replica mais forte, transcreva manualmente o conteudo das Figuras 6, 7 e 8 do PDF e substitua esses registros.

## 3. Executar

```powershell
python -m src.run_experiments
```

## 4. Verificar resultados

Abra os CSVs em `results/` e as imagens em `results/figures/`.

Compare especialmente:

- `dsl_syntax_validity` contra a validade sintatica da DSL reportada no paper.
- `entity_f1` contra as metricas de NER por entidade.
- `code_correct_rate` e `syntax_errors` contra a executabilidade do codigo Python.

## 5. Reproduzir com API

Crie `.env`:

```env
OPENAI_API_KEY=sua_chave_aqui
```

Depois habilite o modelo em `config/models.yaml`.

## 6. Rodar modelos gratuitos recentes

Opcao A: Ollama local, gratuito mas dependente do hardware da maquina.

1. Instale o Ollama.
2. Baixe os modelos desejados, ajustando os nomes conforme a biblioteca local:

```powershell
ollama pull qwen3.5:32b
ollama pull deepseek-r1:32b
ollama pull llama4:scout
```

3. Em `config/models.yaml`, defina `enabled: true` para os modelos `ollama_*`.
4. Rode:

```powershell
python -m src.run_experiments
```

Opcao B: provedor gratuito compativel com OpenAI, como OpenRouter.

1. Defina a chave no `.env`:

```env
OPENROUTER_API_KEY=sua_chave_aqui
```

2. Atualize `model_id` em `openrouter_free_model` com um slug gratuito atual.
3. Defina `enabled: true`.

Use essa opcao para evitar depender do hardware local, mas registre no relatorio que disponibilidade, limites e modelos gratuitos podem mudar.
