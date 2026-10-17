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
abster-se quando os excertos não sustentarem uma conclusão.
O assistente responde no mesmo idioma da pergunta, incluindo em inglês.

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
