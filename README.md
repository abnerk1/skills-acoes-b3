# Skills de Ações da B3

Um conjunto de *skills* que emula o trabalho de um analista de ações: identifica o tipo de empresa, aplica o método de valuation certo e entrega **preço justo**, **preço-teto com margem de segurança**, **DY esperado**, **viés** e um relatório em formato fixo.

Tudo é regra quantitativa fixa, calculada a partir de dados públicos (CVM e IBGE). Sem achismo e sem copiar tese de casa de análise.

> Santos Dumont publicou os planos do Demoiselle para que qualquer um pudesse construir e melhorar o avião. Este repositório segue o mesmo espírito: o método está aberto para ser usado, questionado e aprimorado.

## O que tem aqui

| Skill | Para quem | Método | Versão |
|---|---|---|---|
| [`analise-de-acoes-b3`](skills/analise-de-acoes-b3/SKILL.md) | Ponto de entrada (maestrina) | Classifica o ticker, escolhe a microskill, aplica filtro de liquidez e escreve o relatório | v1 |
| [`acoes-financeiras`](skills/acoes-financeiras/SKILL.md) | Bancos | P/VP = (ROE real − g) ÷ (10% − g) | v1.1 |
| [`acoes-fluxo-normalizado`](skills/acoes-fluxo-normalizado/SKILL.md) | Commodities, indústria, elétricas, petróleo, seguros, telecom | ROE real normalizado (10 anos) × PL, com crescimento e horizonte opcional | v1.1 |
| [`acoes-crescimento`](skills/acoes-crescimento/SKILL.md) | Empresas que reinvestem o lucro (varejo, agro, locação, bolsa) | P/L justo em dois estágios com ROIIC | v1 |
| [`acoes-ativos`](skills/acoes-ativos/SKILL.md) | Holdings, incorporadoras, terras, venture capital | NAV / soma das partes | v1 |

A maestrina não calcula nada: toda conta vem do script de uma microskill.

## Regras comuns

- Custo de capital (Ke) de **10% real**.
- **Margem de segurança fixa de 20%**: preço-teto = preço justo × 0,8.
- Premissas neutras. Nada de projetar lojas, capacidade ou *guidance*.
- Dado faltante vira aviso e nunca bloqueia a entrega.
- **Isolamento de fontes**: só CVM, IBGE, RI da empresa e cotação. Teses, preços-alvo e premissas de casas de análise ficam de fora.
- A regra é fixa. Divergências viram aviso, não exceção caso a caso.

## Como usar

**Como skills.** Cada pasta em `skills/` é uma skill no formato `SKILL.md`. Carregue-as no seu cliente de IA compatível; comece pela `analise-de-acoes-b3`.

**Direto no terminal.** Cada skill traz o script `.py` ao lado do `SKILL.md`. Só usam a biblioteca padrão do Python 3, sem dependências. Eles baixam as DFPs e ITRs da [CVM](https://dados.cvm.gov.br) e o IPCA do [IBGE](https://servicodados.ibge.gov.br), com cache em `~/.cache/cvm`.

```bash
# 1. Classificar o ticker (liquidez em R$ mil por dia)
python3 skills/analise-de-acoes-b3/classificar.py --ticker ITSA4 --preco 15.97 --liquidez 525625

# 2. Rodar a microskill indicada (exemplo: banco)
python3 skills/acoes-financeiras/financeiras.py --empresa "BCO BRASIL S.A" --preco 24.64 --payout 0.30
```

Os preços acima são ilustrativos. Use a cotação do dia, de uma única fonte, com a data registrada.

## Limitações conhecidas

- O método usa o ROE contábil consolidado da CVM, igual para todos. Ele não enxerga lucro recorrente ajustado, ciclos fora da janela de 10 anos nem projeções da empresa.
- A tabela fixa de tickers do `classificar.py` reflete o desenho original do projeto. Ticker fora dela cai na regra automática.
- Os scripts dependem do formato dos dados abertos da CVM. Mudança de layout pode quebrar a leitura.
- Cotação e liquidez são informadas à mão (padrão: Status Invest).

## Contribuindo

Veja o [CONTRIBUTING.md](CONTRIBUTING.md). Ideias bem-vindas: novas microskills (FIIs, seguradoras, saneamento), casos de teste, correções de leitura da CVM e melhorias no relatório.

## Aviso

Este projeto é educacional. O resultado de cada relatório é gerado por regra quantitativa fixa a partir de dados públicos e **não é recomendação individual de investimento**. Rentabilidade passada, alocação de carteira, renda fixa e preço de entrada estão fora do escopo. Decisões de investimento são de responsabilidade de quem investe.

## Licença

[MIT](LICENSE).
