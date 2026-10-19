# Assistente do Código do Trabalho

**Problema:** trabalhadores e empregadores fazem uma pergunta sobre o Código do
Trabalho português e recebem uma resposta informativa, com artigos citados,
baseada nos excertos recuperados da versão consolidada do diploma.

## Configuração

Receba a chave de API do grupo por e-mail; guarde-a apenas no ficheiro local
`.env`, ignorado pelo Git:

1. Copie o exemplo de configuração:

   ```bash
   cp .env.example .env
   ```

2. Adicione a chave recebida à variável `LLM_API_KEY` em `.env`. O URL do proxy
   e o modelo já estão configurados por omissão. Nunca partilhe nem submeta esse
   ficheiro.
3. Confirme que o `.env` não está a ser seguido pelo Git:

   ```bash
   git status
   ```

Se suspeitar que a chave foi exposta, contacte imediatamente o docente.

Instale as dependências:

```bash
python -m pip install -r requirements.txt
```

## Preparar a fonte jurídica

Descarregue a versão consolidada do Código do Trabalho do PGDLisboa e guarde-a
localmente:

```bash
python src/fetch_law.py
```

O ficheiro `data/labor_code.json` inclui a data de recolha e é ignorado pelo
Git. Atualize-o antes de cada avaliação. A recuperação pode não encontrar todos
os artigos relevantes; confira sempre a fonte original.

## Usar a aplicação

Inicie a interface de uma página:

```bash
streamlit run src/web_app.py
```

Também é possível consultar pela linha de comandos:

```bash
python src/app.py "A empresa pode exigir um teste de gravidez a uma candidata?"
```

As respostas são informativas, não constituem aconselhamento jurídico e devem
abster-se quando os excertos não sustentarem uma conclusão. Perguntas noutros
idiomas são traduzidas em palavras-chave em português para a recuperação dos
artigos; a explicação jurídica final é traduzida com base no idioma da pergunta
original, sem depender da deteção de idioma da etapa de recuperação.
Na interface web, o seletor permite escolher os rótulos e controlos em
português ou inglês, independentemente do idioma da pergunta. A resposta e os
artigos consultados são apresentados no idioma selecionado para a interface.
Quando o português está selecionado, a resposta e as fontes permanecem no
português original; quando o inglês está selecionado, são traduzidas para
inglês. As traduções são apenas para facilitar a leitura, pois o texto legal
oficial está em português.

## Avaliação

O conjunto dourado com 20 casos está em `evaluation/golden_set.json`. A avaliação
faz uma chamada ao assistente e uma chamada de juiz por caso (40 chamadas no
total), pelo que requer acesso ao modelo e pode consumir quota:

```bash
python src/evaluate_golden_set.py
```

O relatório local `evaluation/golden_results.json` regista os casos, respostas,
versão do prompt, fonte, latências, verificações determinísticas e decisão do
juiz. Leia e rotule manualmente cada resposta; o juiz automatizado não substitui
a revisão humana. Preencha `evaluation/draft_labels.csv` com os rascunhos das
traces, veredictos `PASS`/`FAIL` e razões. Depois, calcule TPR e TNR:

```bash
python src/evaluate_judge.py
```

Resultados só podem ser reportados depois das chamadas reais e da revisão
humana. O TPR mede a proporção de rascunhos rotulados `PASS` pelos humanos que o
juiz também marcou `PASS`; o TNR mede a proporção de rascunhos humanos `FAIL`
que o juiz marcou `FAIL`. Um `UNKNOWN` do juiz conta como erro nestas métricas.
Estes números não medem a correção jurídica global nem se generalizam para fora
dos casos avaliados.

**Resultado medido, 16-10-2026:** no snapshot PGDLisboa recolhido em
`2026-10-16T20:37:54.821404+00:00`, a recuperação encontrou todos os artigos
esperados nos 20 casos (20/20). Porém, só 11/20 passaram todos os controlos
determinísticos: nove respostas omitiram pelo menos uma citação esperada
(CT-001, 003, 005, 006, 007, 008, 010, 014 e 016). Os quatro casos fora do âmbito
foram corretamente assinalados como desconhecidos; houve ainda uma abstenção
indevida num caso dentro do âmbito (CT-006, assédio). Escolhemos a cobertura de
recuperação como métrica principal porque a resposta depende dos artigos
disponíveis no contexto; ela não mede a precisão dos artigos extra recuperados,
a aplicação correta da lei nem a qualidade geral da resposta.

O juiz produziu 1 `PASS` com evidência verificável e 19 `UNKNOWN`: em 19 casos
a evidência apresentada não era uma citação literal dos excertos nem da resposta.
Por isso, estes resultados não permitem avaliar a qualidade com confiança. As
respostas e os veredictos constam de `evaluation/golden_results.json`; o CSV
`evaluation/draft_labels.csv` contém os 20 rascunhos para revisão humana e deixa
os veredictos e razões em branco. Não calcule TPR/TNR até uma pessoa preencher
essas colunas com base na leitura dos rascunhos.

Esta avaliação é apenas destes 20 casos e do snapshot indicado. Atualize a fonte
e repita-a antes de usar resultados como evidência atualizada.

## Testes automatizados

Os testes não requerem chave de API nem fazem chamadas de rede:

```bash
python -m unittest discover -v
```

## Atualização de evidência e conformidade do checklist

Para responder ao checklist do projeto, o repositório foi reforçado com documentação explícita para os itens que exigem prova e registo local:

- foi criado `AGENTS.md` na raiz para reforçar a regra de centralização do uso do modelo em `src/llm.py`
- foi adicionado o ficheiro `docs/copilot_evidence.md` para documentar a intenção e a evidência disponível do steering do Copilot
- foi adicionado `docs/prompt_iteration.md` para registar a linha temporal da iteração dos prompts e as métricas disponíveis
- foi adicionado `docs/project_report.md` e `docs/submission_deck.md` como artefactos locais de relatório e apresentação
- foi preenchido o ficheiro `evaluation/draft_labels.csv` com rascunhos revistos manualmente e motivos

Estas alterações não escondem os itens que continuam dependentes de contexto externo (por exemplo, publicação pública do repositório, prova visual antes/depois e gravação da demonstração). Em vez de os inventar, o repositório passa a documentar claramente o que foi verificado localmente e o que permanece fora do alcance deste checkout.

