# Suposicoes e lacunas

Este documento deve ser atualizado conforme o PDF/resumo do artigo for analisado.

## Informacoes que voce precisa inserir

1. Titulo: "LLM-Driven MDA Pipeline for Generating UML Class Diagrams and Code".
2. Autores: Zakaria Babaalla, Abdeslam Jakimi e Mohamed Oualla.
3. Publicacao: IEEE Access, 2025. DOI informado no PDF: 10.1109/ACCESS.2025.3615828.
4. Pipeline original: texto em linguagem natural no nivel CIM, extracao semantica via NER/Transformer, DSL textual no nivel PIM, transformacao para diagrama de classes UML no nivel PSM e geracao de codigo Python esqueleto.
5. CIM: especificacoes textuais em linguagem natural, incluindo requisitos funcionais, casos de uso e regras de negocio.
6. DSL/PIM: sintaxe textual hierarquica com `Class`, `Attributes`, `Methods` e `Relation`.
7. PSM/codigo: diagrama de classes UML e codigo Python com classes, `__init__`, atributos e metodos vazios com `pass`.
8. Corpus: 132 especificacoes, 915 sentencas, 11.460 tokens e 10.650 ocorrencias anotadas.
9. Modelos NER avaliados: BERT, RoBERTa, XLNet, SpanBERT, MiniLM e Electra, fine-tuned com HuggingFace Transformers.
10. Comparacao qualitativa adicional: abordagem do paper, GPT-3.5 e DeepSeek.
11. Metricas originais: precision, recall e F1-score por entidade, matching estrito de span e rotulo.
12. Treinamento reportado: split 80/20, cerca de 185 sentencas no teste, 25 epocas, learning rate 2e-5, batch size 16, limite de 512 tokens.

## Suposicoes implementadas nesta replica aproximada

- O CIM e tratado como texto em linguagem natural, conforme o paper.
- O PIM e aproximado pela DSL textual `Class/Attributes/Methods/Relation` descrita no paper.
- O PSM e aproximado por codigo Python sintaticamente verificavel; o paper tambem gera/visualiza UML class diagrams, mas este projeto salva os artefatos textuais e metricas.
- O baseline local extrai termos por heuristica e gera artefatos deterministivos.
- O uso de LLM externo e opcional e depende de `.env`.
- A replica e experimental, nao fiel, porque o codigo e o corpus originais nao foram incorporados.
- Os tres cenarios citados no paper sao: arquitetura de hardware de um computador pessoal, estrutura logica de um documento editorial e biblioteca municipal. Como o texto completo desses cenarios nao aparece de forma recuperavel no PDF, os casos em `data/` sao aproximacoes editaveis.

## Limitacoes

- Os dados de exemplo em `data/` sao templates, nao dados do artigo.
- As taxas de corretude dependem de gold standard preenchido manualmente.
- A avaliacao semantica e aproximada enquanto os criterios formais nao forem definidos.
- O artigo reporta 100% de validade sintatica da DSL em 26 especificacoes de teste, 74% de blocos aceitos sem modificacao, 20% com edicoes menores e 6% com reescrita parcial. Este projeto mede validade sintatica local, mas nao reproduz automaticamente a revisao humana do paper.
- O artigo foca estrutura estatica UML. Experimentos sobre mudanca de regra de negocio e DSL multicamadas sao extensoes criticas propostas para a disciplina, nao etapas originais confirmadas.
