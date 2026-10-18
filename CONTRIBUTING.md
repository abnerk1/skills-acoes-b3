# Como contribuir

Obrigado por querer melhorar o método. Algumas regras mantêm o projeto coerente.

## O que é sagrado

1. **O `SKILL.md` é a fonte da verdade.** O script `.py` de cada skill é cópia do bloco `## Script` do `SKILL.md`. Edite o `SKILL.md` e depois rode:
   ```bash
   python3 tools/sync_scripts.py --write
   ```
   O CI reprova o PR se os dois divergirem.
2. **Isolamento de fontes.** Só dados primários (CVM, IBGE, RI da empresa, FundosNet e relatório gerencial do FII) e cotação. Não envie PR que use tese, preço-alvo ou premissa de casa de análise, nem dado de assinatura paga.
3. **Premissas neutras.** O método não projeta o que a empresa promete. Mudança que adicione projeção precisa justificar o porquê.
4. **Dado faltante vira aviso**, nunca erro que bloqueia a entrega.

## Como propor uma mudança na regra

A regra de cada microskill é fixa para que os resultados sejam comparáveis entre empresas. Por isso, mudança de método entra como **nova versão**, não como ajuste silencioso:

- Abra uma issue descrevendo o problema, com 2 ou 3 tickers em que a regra atual erra e o que você esperava.
- No PR, atualize a versão no título do `SKILL.md` (ex.: v1.1 → v1.2) e explique o efeito nos números com antes e depois.
- Não ajuste a regra para um caso isolado. Se um caso foge do método, o certo é um aviso.

## Outras contribuições bem-vindas

- **Casos de teste**: ticker, data da cotação, comando rodado e saída esperada.
- **Correções de leitura da CVM** (contas que mudam de nome, empresas sem consolidado, ações informadas em milhares).
- **Novas microskills** (seguradoras, saneamento) e **novos FIIs na tabela fixa** da `analise-de-fiis` (ticker, CNPJ e motor). Siga o formato das existentes: quando usar, regra fixa, passos, saída em formato fixo, script.
- Melhorias no relatório da `analise-de-acoes-b3`, mantendo o formato fixo.

## Checklist do PR

- [ ] `python3 tools/sync_scripts.py` passa
- [ ] O script roda de ponta a ponta em pelo menos um ticker real (informe qual e a data)
- [ ] Nenhuma fonte fora de CVM, IBGE, RI, FundosNet e cotação
- [ ] Nenhum dado pessoal, chave de API ou credencial no diff
