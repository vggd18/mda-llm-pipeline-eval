# Desenho experimental

## Objetivo

Testar se um pipeline CIM -> PIM/DSL -> PSM inspirado no artigo generaliza para bases diferentes, mudancas de regra de negocio, ablacoees da DSL e modelos LLM modernos.

O artigo-base e "LLM-Driven MDA Pipeline for Generating UML Class Diagrams and Code" (Babaalla, Jakimi e Oualla, IEEE Access, 2025). O metodo descrito combina NER com Transformers, DSL textual intermediaria, geracao de UML class diagram e codigo Python.

## Hipoteses

H1. A precisao alta reportada pode nao generalizar para bases diferentes ou mais realistas.

H2. O pipeline pode ser sensivel a mudancas de regra de negocio apos modificacoes do usuario.

H3. Transformers podem estar sendo usados apenas para identificacao inicial de tokens.

H4. A etapa de DSL pode ser necessaria ou removivel sem perda significativa.

H5. Comparar com modelos antigos pode favorecer artificialmente a abordagem proposta.

H6. DSLs podem ser usadas em multiplas camadas de abstracao, nao apenas em uma transicao PIM.

## Experimentos

- A: CIM texto -> extracao -> DSL/PIM -> codigo/PSM.
- B: CIM texto -> codigo diretamente.
- C: CIM textual -> DSL de requisitos -> DSL de design -> codigo.
- D: gerar artefato inicial, simular modificacao do usuario, alterar regra e medir consistencia.
- E: testar casos simples, medianos, ambiguos, incompletos e fora do padrao.
- F: comparar GPT atual, modelo alternativo configuravel e baseline heuristico.

## Comparacao justa com LLMs atuais

O paper compara sua abordagem com GPT-3.5 e DeepSeek, mas essa comparacao pode favorecer artificialmente o pipeline proposto porque usa modelos antigos e nao necessariamente avalia modelos recentes com maior capacidade de raciocinio/codigo.

Este projeto inclui uma nova comparacao:

- `heuristic_baseline`: baseline reproduzivel sem IA externa.
- `bert_paper_reference`: referencia simbolica ao modelo usado no paper; no projeto local e um mock, nao um BERT fine-tuned real.
- `gpt_current`: GPT atual via OpenAI API.
- `gpt_current_cost_control`: GPT atual mais barato para avaliar custo/beneficio.
- `ollama_qwen_recent_free`: modelo aberto recente via Ollama.
- `ollama_deepseek_recent_free`: DeepSeek recente/local via Ollama.
- `ollama_llama_recent_free`: Llama recente/local via Ollama.
- `ollama_apertus_free`: modelo aberto/auditavel via Ollama.
- `openrouter_free_model`: slot para provedores gratuitos compativeis com API OpenAI.

Nos experimentos com `provider: openai`, `provider: ollama` ou `provider: openai_compatible`, o modelo passa a gerar efetivamente DSL ou codigo. Se a DSL gerada for invalida, o pipeline registra a falha na coluna `notes` e usa fallback heuristico para manter a execucao reprodutivel.

Essa comparacao permite avaliar:

- se modelos atuais end-to-end superam a arquitetura rigida do artigo;
- se a DSL ainda melhora validade sintatica e rastreabilidade;
- se modelos gratuitos recentes reduzem a diferenca para modelos pagos;
- se a conclusao do paper muda quando a comparacao deixa de usar modelos antigos.

## Variaveis do paper usadas como referencia

- Corpus anotado manualmente: 132 especificacoes, 915 sentencas, 11.460 tokens.
- Esquema IOB enriquecido: classes fonte/alvo, atributos, metodos e tipos de relacionamento UML.
- Tags centrais: `B_CLASS_SOURCE`, `I_CLASS_SOURCE`, `B_CLASS_TARGET`, `I_CLASS_TARGET`, `B_ATTRIBUTE`, `I_ATTRIBUTE`, `B_METHOD`, `I_METHOD`, `B_ASSOCIATION`, `B_COMPOSITION`, `B_AGGREGATION`, `B_INHERITANCE`, `O`.
- Modelos do paper: BERT, RoBERTa, XLNet, SpanBERT, MiniLM e Electra.
- Hiperparametros reportados: 25 epocas, learning rate 2e-5, batch size 16, 512 tokens por sequencia.
- DSL do paper: `Class`, `Attributes`, `Methods`, `Relation`.
- Codigo gerado: esqueleto Python com construtor, inicializacao de atributos e metodos vazios.

## Criterios a validar

- TODO: validar criterio de avaliacao com o professor.
- TODO: decidir se os cenarios aproximados devem ser substituidos por transcricoes manuais das Figuras 6, 7 e 8.
- TODO: decidir se a comparacao com GPT atual deve avaliar UML textual, codigo Python, ou ambos.
- TODO: confirmar quais modelos gratuitos estarao disponiveis no ambiente da apresentacao, porque nomes exatos no Ollama/OpenRouter podem variar.
- TODO: definir rubrica objetiva para "fidelidade semantica" e "qualidade de codigo", pois no paper esses resultados incluem avaliacao qualitativa/por cenario.
