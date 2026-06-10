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

