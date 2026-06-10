# Notas para a apresentacao

## Cuidado com os resultados baseline

Os resultados gerados sem habilitar `openai`, `ollama` ou `openai_compatible` sao apenas uma validacao do pipeline experimental. Eles nao devem ser apresentados como evidencia de que a abordagem proposta supera ou perde para LLMs reais.

Por padrao, somente `heuristic_baseline` fica habilitado. Isso evita o problema anterior em que `bert_paper_reference` e `mock_llm` apareciam nos graficos como se fossem modelos reais, mas na pratica repetiam a mesma heuristica.

## Como apresentar corretamente

Use a execucao baseline para mostrar:

- o desenho experimental e os arquivos gerados;
- que o pipeline e reproduzivel;
- que o experimento D detecta a lacuna de mudanca posterior de regra de negocio;
- que a metrica de DSL funciona como checagem sintatica.

Use conclusoes comparativas somente depois de rodar pelo menos um modelo real:

- `gpt_current`, via OpenAI;
- algum `ollama_*`, via Ollama local;
- `openrouter_free_model`, via provedor compativel.

## Frase recomendada

"Os graficos baseline nao sao a conclusao do estudo; eles validam o aparato experimental. A conclusao empirica depende da execucao com modelos reais atuais, justamente para corrigir a comparacao possivelmente injusta do artigo com modelos antigos."

## Se muitos valores aparecerem iguais

Valores iguais em todos os modelos geralmente indicam um destes casos:

- somente baseline/mock foi executado;
- o modelo real falhou e o pipeline usou fallback heuristico;
- a metrica observada nao depende da etapa em que o modelo foi usado.

A versao atual reduz esse risco:

- `F_model_comparison` nao aparece mais como experimento duplicado; a comparacao entre modelos fica em `results/model_comparison.csv`.
- Em modelos reais, o F1 passa a considerar termos extraidos da DSL gerada pelo modelo quando essa DSL e valida.
- O experimento de mudanca de regra agora chama o modelo real para tentar atualizar o codigo; se falhar, registra fallback em `notes`.
- O grafico de erros agora mostra falhas medias por `modelo/experimento`, nao apenas soma bruta por experimento.

Ao analisar os CSVs, confira a coluna `notes`: entradas com `fallback_to_heuristic_*` nao devem ser interpretadas como desempenho puro do modelo.
