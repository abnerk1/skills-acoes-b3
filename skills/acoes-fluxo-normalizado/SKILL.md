---
name: "acoes-fluxo-normalizado"
description: "Calcula preço justo, preço-teto, DY esperado e viés de empresas não financeiras da B3 (commodities, indústria, elétricas, petróleo, seguridade) por ROE real normalizado × PL com crescimento. Não use para bancos."
---

# Fluxo normalizado — valuation por ROE normalizado (v1.2)

Microskill de cálculo. Entrega um bloco fixo de números; não escreve relatório (isso é da maestrina).

## Quando usar
- Commodities e cíclicas: VALE3, PETR4, PRIO3, RECV3, KLBN4, SUZB3, UNIP6, SLCE3, FESA4, RANI3.
- Indústria madura: TUPY3, SHUL4, KEPL3, CAMB3.
- Elétricas e concessões: EGIE3, AXIA7, CLSC4 e similares.
- Seguridade e corretagem: BBSE3, CXSE3, WIZC3.
- Não usar para bancos (→ Financeiras), empresas de crescimento (→ Crescimento) nem holdings e ativos reais (→ Ativos).

## Regra (fixa, não alterar)
1. ROE de cada ano = lucro atribuído ao controlador ÷ PL do controlador médio (início e fim do ano). Fonte: DFP consolidada na CVM.
2. ROE nominal = média aritmética dos últimos 10 exercícios completos (média do ciclo).
3. IPCA = média aritmética dos mesmos 10 anos (IBGE).
4. ROE real = (1 + ROE nominal) ÷ (1 + IPCA) − 1.
5. Lucro normalizado = ROE real × PL do controlador mais recente (último ITR), em reais de hoje.
6. Payout = política declarada no RI; sem política, média de 5 anos pela CVM (dividendos + JCP pagos ÷ lucro).
7. Crescimento g = mín((1 − payout) × ROE real; 3%), nunca negativo. Sem payout disponível, g = 0. (Mesma linha da Financeiras v1.1.)
8. Fluxo distribuível = (ROE real − g) × PL atual.
9. Horizonte:
   - perpétuo (padrão): valor = fluxo distribuível ÷ (10% − g), ou seja, P/VP = (ROE real − g) ÷ (10% − g);
   - prazo de N anos (concessão, reservas 2P, contrato): valor = fluxo distribuível × [1 − ((1 + g) ÷ 1,10)^N] ÷ (10% − g), sem valor residual.
10. Preço justo = valor ÷ ações ex-tesouraria × ações por ativo.
11. Preço-teto = preço justo × 0,8 (margem fixa de 20%).
12. Bear / bull = ROE real −3 p.p. / +3 p.p. (g recalculado em cada cenário).
13. DY esperado = payout × (ROE nominal × PL atual) ÷ ações ÷ preço atual.
14. Viés = "Comprar" se preço atual ≤ preço-teto; senão "Aguardar".
15. ROE real ≤ 0 → preço justo zero, com aviso (a empresa não remunerou o capital acima da inflação no ciclo).

Ke de 10% real, margem de 20%, janela de 10 anos e teto de g em 3% são constantes. Checagem de caixa (FCO − capex sobre lucro, 10 anos) só gera aviso; não muda o número.

## Armadilha de dividendo e status da tese (v1.2)
Só avisos: nada aqui muda preço justo, teto ou viés.
- **Armadilha de dividendo:** proventos pagos (dividendos + JCP, DFC) somados nos últimos 3 exercícios acima do lucro do controlador no mesmo período (payout > 100%). Três anos, e não um, para não confundir dividendo extraordinário de capital excedente com distribuição insustentável.
- **Status da tese**, separado do viés, calculado pelo script nesta ordem:
  - **Revisão crítica:** armadilha de dividendo, ou preço justo zerado pela regra.
  - **Monitoramento:** (FCO − capex) dos últimos 3 exercícios abaixo dos proventos pagos no período (v1.2; em holdings e seguradoras os dividendos recebidos de investidas ficam fora do FCO, então conferir antes de concluir); ROE dos últimos 12 meses a mais de 5 p.p. da média de 10 anos; lucro vira pouco caixa: (FCO − capex) < 60% do lucro em 10 anos; menos de 10 anos de dados.
  - **Consolidada:** nenhum dos casos acima.
  O viés diz se o preço está bom; o status diz se a tese está de pé.

## Passos
1. **Identificar** o nome da companhia como aparece na CVM (ex.: "VALE S.A.", "PETROLEO BRASILEIRO", "ENGIE BRASIL", "KLABIN S.A.", "BB SEGURIDADE") e quantas ações compõem o ativo negociado (units: KLBN11 = 5, TAEE11 = 3).
2. **Cotação atual**: uma única fonte, com data. Registrar fonte e data.
3. **Horizonte**: perpétuo, salvo se o negócio depende de algo com prazo. Nesse caso, buscar N no RI da empresa:
   - elétricas: prazo médio remanescente das concessões (ponderado pela receita ou capacidade);
   - petróleo: reservas 2P ÷ produção anual;
   - contratos de distribuição (seguridade/corretagem): anos até o vencimento do contrato principal.
   Nunca tirar N de relatório de casa de análise.
4. **Payout**: política declarada no RI com `--payout`; sem política, omitir e o script calcula pela CVM.
5. **Rodar o cálculo**: salvar o script abaixo como `fluxo.py` e executar:
   `python3 fluxo.py --empresa "ENGIE BRASIL" --preco 31.11 --prazo 17`
   O script baixa as DFPs e ITRs da CVM (dados.cvm.gov.br) e o IPCA do IBGE. Não refazer contas à mão.
6. **Tratar avisos de dados**, nesta ordem: RI → PDF da DFP/ITR na CVM → pedir o PDF ao usuário. Reexecutar com `--manual "ANO=LUCRO;PL_FIM"` (R$ bi), `--pl-atual X --data-pl AAAA-MM-DD` ou `--acoes N`. Dado faltante nunca bloqueia a entrega.
7. **Entregar** o bloco de saída.

## Saída (formato fixo)
```
[TICKER] — Fluxo normalizado v1.2 — cotação de DD/MM/AAAA (fonte)
Preço atual:  R$ X
Preço justo:  R$ X   (bear R$ X | bull R$ X)
Preço-teto:   R$ X
DY esperado:  X%     (payout X%, fonte)
Viés:         Comprar | Aguardar
Status da tese: Consolidada | Monitoramento (motivos) | Revisão crítica (motivos)
Memória de cálculo: ROE nominal médio X% | IPCA médio X% | ROE real X% | g X% | P/VP implícito X | horizonte (perpétuo ou N anos, fonte do N) | conversão em caixa X%
Avisos: (lista do script, se houver)
```
Incluir a tabela anual de ROE impressa pelo script quando o usuário pedir detalhe.

## Regras gerais
- Isolamento: nunca consultar nem citar tese, preço-teto ou premissa de casas de análise (research independente, bancos, corretoras). Só dados primários (CVM, RI, IBGE) e cotação.
- Premissas neutras: não acrescentar folga além dos 20%.
- Não ajustar a regra caso a caso; divergências viram aviso, não exceção.

## Script
```python
#!/usr/bin/env python3
"""Microskill Fluxo normalizado (v1.2): preço justo e preço-teto de empresas não financeiras.

Fontes: CVM dados abertos (DFP/ITR consolidados) e IBGE (IPCA).
Regra v1.1:
  ROE anual          = lucro atribuído ao controlador / PL do controlador médio (início e fim do ano)
  ROE nominal        = média aritmética dos últimos 10 anos completos (média do ciclo)
  IPCA               = média aritmética dos mesmos 10 anos
  ROE real           = (1 + ROE nominal) / (1 + IPCA) - 1
  Lucro normalizado  = ROE real x PL do controlador atual (em reais de hoje)
  Crescimento g      = mín((1 - payout) x ROE real; 3%), nunca negativo (sem payout: g = 0)
  Fluxo distribuível = (ROE real - g) x PL do controlador atual
  Valor (perpétuo)   = Fluxo distribuível / (10% - g)               (P/VP = (ROE real - g) / (10% - g))
  Valor (prazo N)    = Fluxo distribuível x (1 - ((1+g)/1,10)^N) / (10% - g)   (concessão, reservas, contrato)
  Preço justo        = Valor / ações x ações por ativo
  Preço-teto         = Preço justo x 0,8
  Bear / Bull        = ROE real -3 p.p. / +3 p.p.
  DY esperado        = payout x (ROE nominal x PL atual) / ações / preço atual
  Checagem de caixa  = (FCO - capex) acumulado de 10 anos / lucro acumulado (só aviso)
Uso:
  python3 fluxo.py --empresa "VALE S.A." --preco 67.09 [--prazo 17] [--payout 0.45] [--acoes-por-ativo 1]
"""
import argparse, csv, gzip, io, json, os, sys, time, unicodedata, urllib.request, zipfile, datetime

KE = 0.10
MARGEM = 0.20
G_MAX = 0.03
CACHE = os.path.expanduser('~/.cache/cvm')
CVM = 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/{doc}/DADOS/{doc_l}_cia_aberta_{ano}.zip'


def norm(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()


def baixar(doc, ano):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f'{doc.lower()}_{ano}.zip')
    if not os.path.exists(path) or (doc == 'ITR' and ano >= datetime.date.today().year - 1
                                     and time.time() - os.path.getmtime(path) > 86400):  # ITR: renova 1x por dia
        url = CVM.format(doc=doc, doc_l=doc.lower(), ano=ano)
        try:
            urllib.request.urlretrieve(url, path)
        except Exception:
            return None
    return path


def ler(zpath, nome):
    with zipfile.ZipFile(zpath) as z:
        alvo = [n for n in z.namelist() if n.endswith(nome)]
        if not alvo:
            return []
        with z.open(alvo[0]) as fh:
            return list(csv.DictReader(io.TextIOWrapper(fh, encoding='latin1'), delimiter=';'))


def achar_cnpj(empresa, zpath, doc):
    alvo = norm(empresa)
    for r in ler(zpath, f'{doc.lower()}_cia_aberta_{zpath[-8:-4]}.csv'):
        if alvo in norm(r['DENOM_CIA']):
            return r['CNPJ_CIA'], r['DENOM_CIA']
    return None, None


def coletar(cnpj, zpath, doc, ano):
    """Retorna dicts: lucro controlador por período (ini, fim), PL controlador por data, ações ex-tesouraria por data."""
    p = f'{doc.lower()}_cia_aberta_'
    escala = lambda r: 1e3 if r.get('ESCALA_MOEDA', 'MIL').upper() == 'MIL' else 1.0

    def ultima_versao(linhas):
        """Mantém só a versão mais recente de cada documento (DT_REFER)."""
        vmax = {}
        for r in linhas:
            vmax[r['DT_REFER']] = max(vmax.get(r['DT_REFER'], 0), int(r['VERSAO']))
        return [r for r in linhas if int(r['VERSAO']) == vmax[r['DT_REFER']]]

    dre = ultima_versao([r for r in ler(zpath, f'{p}DRE_con_{ano}.csv') if r['CNPJ_CIA'] == cnpj])
    bpp = ultima_versao([r for r in ler(zpath, f'{p}BPP_con_{ano}.csv') if r['CNPJ_CIA'] == cnpj])
    ll_ctrl, ll_cons, ll_nc = {}, {}, {}
    for r in dre:
        d, cd, k = norm(r['DS_CONTA']), r['CD_CONTA'], (r['DT_INI_EXERC'], r['DT_FIM_EXERC'])
        v = float(r['VL_CONTA']) * escala(r)
        if cd.startswith('3.') and cd.count('.') == 2 and 'controladora' in d and 'nao' not in d:
            ll_ctrl[k] = v
        elif cd.startswith('3.') and cd.count('.') == 2 and 'nao controladores' in d:
            ll_nc[k] = v
        elif cd.count('.') == 1 and d.startswith('lucro') and 'consolidado' in d:
            ll_cons[k] = v
    ll = {}
    for k in set(ll_ctrl) | set(ll_cons):
        v = ll_ctrl.get(k, 0.0)
        if v == 0.0 and ll_cons.get(k):  # empresa não preencheu a linha do controlador
            v = ll_cons[k] - ll_nc.get(k, 0.0)
        ll[k] = (int(ano), v)
    pl_c, pl_nc, pl_cons = {}, {}, {}
    for r in bpp:
        d, fim, v = norm(r['DS_CONTA']), r['DT_FIM_EXERC'], float(r['VL_CONTA']) * escala(r)
        if d.startswith('patrimonio liquido atribuido ao controlador'):
            pl_c[fim] = v
        elif d.startswith('patrimonio liquido consolidado'):
            pl_cons[fim] = v
        elif 'nao controladores' in d and r['CD_CONTA'].count('.') == 2:
            pl_nc[fim] = v
    for fim, v in pl_cons.items():
        if not pl_c.get(fim):
            pl_c[fim] = v - pl_nc.get(fim, 0.0)
    # sem consolidado (companhia sem controladas): usar as demonstrações individuais
    if not any(ll.values()) or not any(v[1] for v in ll.values()) or not any(pl_c.values()):
        for r in ultima_versao([r for r in ler(zpath, f'{p}DRE_ind_{ano}.csv') if r['CNPJ_CIA'] == cnpj]):
            d, cd, k = norm(r['DS_CONTA']), r['CD_CONTA'], (r['DT_INI_EXERC'], r['DT_FIM_EXERC'])
            if cd.count('.') == 1 and d.startswith('lucro') and not ll.get(k, (0, 0.0))[1]:
                ll[k] = (int(ano), float(r['VL_CONTA']) * escala(r))
        for r in ultima_versao([r for r in ler(zpath, f'{p}BPP_ind_{ano}.csv') if r['CNPJ_CIA'] == cnpj]):
            if r['CD_CONTA'].count('.') == 1 and norm(r['DS_CONTA']).startswith('patrimonio liquido') and not pl_c.get(r['DT_FIM_EXERC']):
                pl_c[r['DT_FIM_EXERC']] = float(r['VL_CONTA']) * escala(r)
    fco, capex = {}, {}
    for arq in (f'{p}DFC_MI_con_{ano}.csv', f'{p}DFC_MD_con_{ano}.csv'):
        for r in ultima_versao([r for r in ler(zpath, arq) if r['CNPJ_CIA'] == cnpj]):
            d, cd, k = norm(r['DS_CONTA']), r['CD_CONTA'], r['DT_FIM_EXERC']
            if r['DT_INI_EXERC'][5:] != '01-01' or k[5:] != '12-31':
                continue
            v = float(r['VL_CONTA']) * escala(r)
            if cd == '6.01':
                fco[k] = v
            elif cd.startswith('6.02.') and cd.count('.') == 2 and v < 0 and any(t in d for t in ('imobilizado', 'intangivel', 'plantio')):
                capex[k] = capex.get(k, 0.0) - v
    div = {}
    for tipo in ('con', 'ind'):
        for arq in (f'{p}DFC_MI_{tipo}_{ano}.csv', f'{p}DFC_MD_{tipo}_{ano}.csv'):
            for r in ultima_versao([r for r in ler(zpath, arq) if r['CNPJ_CIA'] == cnpj]):
                d = norm(r['DS_CONTA'])
                if r['CD_CONTA'].startswith('6.03') and ('dividend' in d or 'juros sobre' in d or 'provento' in d) and 'nao cont' not in d:
                    k = r['DT_FIM_EXERC']
                    div[k] = div.get(k, 0.0) + abs(float(r['VL_CONTA']) * escala(r))
        if div:
            break
    acoes = {}
    for r in ler(zpath, f'{p}composicao_capital_{ano}.csv'):
        if r['CNPJ_CIA'] == cnpj:
            acoes[r['DT_REFER']] = int(r['QT_ACAO_TOTAL_CAP_INTEGR']) - int(r['QT_ACAO_TOTAL_TESOURO'])
    return ll, pl_c, acoes, div, fco, capex


def ipca_anual(anos):
    per = '|'.join(f'{a}12' for a in anos)
    url = f'https://servicodados.ibge.gov.br/api/v3/agregados/1737/periodos/{per}/variaveis/69?localidades=N1[all]'
    with urllib.request.urlopen(url.replace('[', '%5B').replace(']', '%5D'), timeout=60) as resp:
        raw = resp.read()
    if raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    serie = json.loads(raw)[0]['resultados'][0]['series'][0]['serie']
    return {int(k[:4]): float(v) / 100 for k, v in serie.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--empresa', required=True, help='trecho do nome na CVM, ex.: "VALE S.A.", "ENGIE BRASIL"')
    ap.add_argument('--preco', type=float, required=True, help='cotação atual do ativo negociado')
    ap.add_argument('--payout', type=float, default=None, help='política de payout declarada (0 a 1); sem ela, média de 5 anos pela CVM')
    ap.add_argument('--prazo', type=float, default=None, help='anos restantes de concessão, reservas ou contrato; omitir = perpétuo')
    ap.add_argument('--acoes-por-ativo', type=float, default=1.0, help='2 para units 1 ON + 1 PN, 3 para 1 ON + 2 PN')
    ap.add_argument('--ultimo-ano', type=int, default=None, help='último exercício completo (padrão: mais recente disponível)')
    ap.add_argument('--manual', action='append', default=[], metavar='ANO=LUCRO;PL_FIM',
                    help='completa um exercício ausente na CVM com dados do RI/PDF, em R$ bilhões. Ex.: --manual "2025=0,95;6,40"')
    ap.add_argument('--pl-atual', type=float, default=None, help='PL do controlador mais recente (R$ bi), se a CVM estiver defasada')
    ap.add_argument('--data-pl', default=None, help='data do --pl-atual (AAAA-MM-DD)')
    ap.add_argument('--acoes', type=int, default=None, help='ações em circulação ex-tesouraria (unidades), se a CVM estiver defasada')
    a = ap.parse_args()
    avisos = []

    hoje = datetime.date.today().year
    ll, pl, acoes, cnpj, nome = {}, {}, {}, None, None
    anos_dfp, divs, fcos, capexs = [], {}, {}, {}
    for ano in range(hoje, hoje - 13, -1):
        z = baixar('DFP', ano)
        if not z:
            continue
        if cnpj is None:
            cnpj, nome = achar_cnpj(a.empresa, z, 'DFP')
            if cnpj is None:
                continue
        l, p, ac, dv, fc, cx = coletar(cnpj, z, 'DFP', ano)
        for k, v in dv.items():
            divs.setdefault(k, v)
        for k, v in fc.items():
            fcos.setdefault(k, v)
        for k, v in cx.items():
            capexs.setdefault(k, v)
        if l:
            anos_dfp.append(ano)
        for k, v in l.items():  # versão mais nova prevalece, mas zero nunca apaga valor preenchido
            if k not in ll or (v[1] and (v[0] >= ll[k][0] or not ll[k][1])):
                ll[k] = v
        for k, v in p.items():
            if not pl.get(k):
                pl[k] = v
        acoes.update(ac)
    if cnpj is None:
        sys.exit(f'Empresa "{a.empresa}" não encontrada na CVM.')
    for ano in (hoje, hoje - 1):
        z = baixar('ITR', ano)
        if z:
            l, p, ac, _, _, _ = coletar(cnpj, z, 'ITR', ano)
            for k, v in l.items():
                ll.setdefault(k, v)
            pl.update({k: v for k, v in p.items() if k not in pl})
            acoes.update(ac)

    for m in a.manual:
        ano_m, vals = m.split('=')
        lucro_m, pl_m = (float(x.replace(',', '.')) * 1e9 for x in vals.split(';'))
        ll[(f'{ano_m}-01-01', f'{ano_m}-12-31')] = (9999, lucro_m)
        pl[f'{ano_m}-12-31'] = pl_m
        avisos.append(f'Exercício {ano_m} informado manualmente (RI/PDF), não pela CVM.')
    if a.pl_atual:
        pl[a.data_pl or datetime.date.today().isoformat()] = a.pl_atual * 1e9
    ultimo = a.ultimo_ano or max(int(f[:4]) for (i, f) in ll if i[5:] == '01-01' and f[5:] == '12-31')
    anos = list(range(ultimo - 9, ultimo + 1))
    linhas, roes = [], []
    for ano in anos:
        lucro = ll.get((f'{ano}-01-01', f'{ano}-12-31'), (0, None))[1]
        ini, fim = pl.get(f'{ano - 1}-12-31'), pl.get(f'{ano}-12-31')
        if lucro is None or not ini or not fim or ini <= 0 or fim <= 0:
            linhas.append((ano, lucro, ini, fim, None))
            continue
        roe = lucro / ((ini + fim) / 2)
        roes.append((ano, roe))
        linhas.append((ano, lucro, ini, fim, roe))
    if len(roes) < 5:
        sys.exit('Menos de 5 anos de ROE disponíveis; enviar DFPs manualmente.')
    ipca = ipca_anual([y for y, _ in roes])
    roe_nom = sum(r for _, r in roes) / len(roes)
    ipca_med = sum(ipca[y] for y, _ in roes) / len(roes)
    roe_real = (1 + roe_nom) / (1 + ipca_med) - 1

    if ultimo < hoje - 1:
        avisos.append(f'Último exercício completo na CVM é {ultimo}; faltam {", ".join(str(x) for x in range(ultimo + 1, hoje))}. '
                      'Completar com --manual a partir do RI ou do PDF da DFP.')
    data_pl = max(pl)
    pl_atual = pl[data_pl]
    if (datetime.date.today() - datetime.date.fromisoformat(data_pl)).days > 270:
        avisos.append(f'PL mais recente é de {data_pl} (mais de 9 meses). Informar --pl-atual a partir do último ITR no RI.')
    if a.acoes:
        n_acoes, data_ac = a.acoes, 'informado'
    else:
        data_ac = max(d for d in acoes if d <= data_pl) if any(d <= data_pl for d in acoes) else max(acoes)
        n_acoes = acoes[data_ac]
    vpa = pl_atual / n_acoes
    if vpa > 1000:  # algumas companhias informam a composição do capital em milhares de ações
        n_acoes *= 1000
        vpa = pl_atual / n_acoes
        avisos.append('Quantidade de ações da CVM estava em milhares; multiplicada por 1.000. Conferir no RI.')

    if a.payout is not None:
        payout, fonte_payout = a.payout, 'política declarada'
    else:
        anos_p = [y for y in range(ultimo - 4, ultimo + 1) if f'{y}-12-31' in divs and (f'{y}-01-01', f'{y}-12-31') in ll]
        lucro_p = sum(ll[(f'{y}-01-01', f'{y}-12-31')][1] for y in anos_p)
        if len(anos_p) >= 3 and lucro_p > 0:
            payout = min(sum(divs[f'{y}-12-31'] for y in anos_p) / lucro_p, 1.0)
            fonte_payout = f'média CVM {anos_p[0]}-{anos_p[-1]} (pagos/lucro)'
        else:
            payout, fonte_payout = None, 'indisponível'
            avisos.append('Payout indisponível: DY n/d. Informar --payout a partir do RI.')

    def crescimento(rr):
        return 0.0 if (payout is None or rr <= 0) else min((1 - payout) * rr, G_MAX)

    def pvp(rr):
        """Valor / PL atual: (ROE - g) x fator, com fator perpétuo ou de prazo N."""
        if rr <= 0:
            return 0.0
        g = crescimento(rr)
        fator = (1 - ((1 + g) / (1 + KE)) ** a.prazo) / (KE - g) if a.prazo else 1 / (KE - g)
        return (rr - g) * fator

    def justo(rr):
        return pvp(rr) * pl_atual / n_acoes * a.acoes_por_ativo

    g = crescimento(roe_real)

    pj = justo(roe_real)
    teto = pj * (1 - MARGEM)
    lucro_norm = roe_nom * pl_atual
    dy = payout * lucro_norm / n_acoes * a.acoes_por_ativo / a.preco if payout is not None else None
    vies = 'Comprar' if a.preco <= teto else 'Aguardar'

    anos_c = [y for y in anos if f'{y}-12-31' in fcos and (f'{y}-01-01', f'{y}-12-31') in ll]
    conv = None
    if len(anos_c) >= 5:
        lucro_c = sum(ll[(f'{y}-01-01', f'{y}-12-31')][1] for y in anos_c)
        fcl_c = sum(fcos[f'{y}-12-31'] - capexs.get(f'{y}-12-31', 0.0) for y in anos_c)
        if lucro_c > 0:
            conv = fcl_c / lucro_c
            if conv > 1.5:
                avisos.append(f'Caixa bem acima do lucro: (FCO - capex) foi {conv:.0%} do lucro em {anos_c[0]}-{anos_c[-1]}. '
                              'O lucro pode estar deprimido por baixas contábeis (impairment); conferir no RI.')
            if conv < 0.6:
                avisos.append(f'Lucro vira pouco caixa: (FCO - capex) foi {conv:.0%} do lucro em {anos_c[0]}-{anos_c[-1]}. '
                              'Capex de crescimento ou capital de giro pesado; o lucro normalizado pode estar alto.')
    if not a.prazo:
        avisos.append('Avaliado como perpétuo. Se o negócio depende de concessão, reservas ou contrato com prazo, informar --prazo.')

    # ROE dos últimos 12 meses (para aviso)
    # 12 meses = último ano completo - acumulado do ano anterior até a mesma data + acumulado do ano atual
    roe_ltm = None
    ytd = sorted((f, v[1]) for (i, f), v in ll.items() if i[5:] == '01-01' and f[5:] != '12-31' and int(f[:4]) > ultimo)
    if ytd:
        f_atual, lucro_ytd = ytd[-1]
        f_ant = f'{int(f_atual[:4]) - 1}{f_atual[4:]}'
        anual = ll.get((f'{ultimo}-01-01', f'{ultimo}-12-31'), (0, None))[1]
        ytd_ant = ll.get((f'{ultimo}-01-01', f_ant), (0, None))[1]
        if None not in (anual, ytd_ant) and pl.get(f'{ultimo}-12-31') and pl.get(f_atual):
            roe_ltm = (anual - ytd_ant + lucro_ytd) / ((pl[f'{ultimo}-12-31'] + pl[f_atual]) / 2)

    print(f'Empresa: {nome}  (CNPJ {cnpj})')
    print('\nAno   Lucro ctrl (R$ bi)  PL início  PL fim   ROE    IPCA')
    for ano, lucro, ini, fim, roe in linhas:
        f = lambda x: f'{x / 1e9:9.2f}' if x is not None else '      n/d'
        print(f'{ano}  {f(lucro)}        {f(ini)} {f(fim)}  ' + (f'{roe:6.1%}  {ipca.get(ano, 0):5.2%}' if roe is not None else '   n/d'))
    print(f'\nROE nominal médio ({len(roes)} anos): {roe_nom:.2%}')
    print(f'IPCA médio (mesmos anos):        {ipca_med:.2%}')
    print(f'ROE real:                        {roe_real:.2%}')
    print(f'Payout:                          {payout:.0%} ({fonte_payout})' if payout is not None else 'Payout:                          n/d')
    print(f'Lucro normalizado (ROE real x PL atual): R$ {roe_real * pl_atual / 1e9:.2f} bi')
    print(f'Crescimento g:                   {g:.2%}' + (' (sem payout: g = 0)' if payout is None else f' = mín((1 - {payout:.0%}) x {roe_real:.2%}; 3%)'))
    print(f'Horizonte: {"perpétuo" if not a.prazo else format(a.prazo, "g") + " anos"}')
    print(f'Valor do equity: R$ {pvp(roe_real) * pl_atual / 1e9:.2f} bi | P/VP implícito: {pvp(roe_real):.2f}')
    if conv is not None:
        print(f'Conversão em caixa ({anos_c[0]}-{anos_c[-1]}): (FCO - capex) / lucro = {conv:.0%}')
    print(f'PL controlador em {data_pl}: R$ {pl_atual / 1e9:.2f} bi | ações ex-tesouraria ({data_ac}): {n_acoes:,}')
    print(f'VPA: R$ {vpa:.2f} (x {a.acoes_por_ativo:g} por ativo)')
    print('\n=== RESULTADO ===')
    print(f'Preço atual:   R$ {a.preco:.2f}')
    print(f'Preço justo:   R$ {pj:.2f}   (bear R$ {justo(roe_real - 0.03):.2f} | bull R$ {justo(roe_real + 0.03):.2f})')
    print(f'Preço-teto:    R$ {teto:.2f}')
    if dy is not None:
        print(f'DY esperado:   {dy:.1%}  (payout {payout:.0%}, {fonte_payout}; lucro normalizado R$ {lucro_norm / 1e9:.1f} bi)')
    else:
        print('DY esperado:   n/d (payout indisponível)')
    print(f'Viés:          {vies}')
    if len(roes) < 10:
        avisos.append(f'Só {len(roes)} anos de ROE disponíveis (padrão: 10).')
    if roe_ltm is not None and abs(roe_ltm - roe_nom) > 0.05:
        avisos.append(f'ROE dos últimos 12 meses ({roe_ltm:.1%}) difere em mais de 5 p.p. da média de 10 anos ({roe_nom:.1%}).')
    if roe_real <= 0:
        avisos.append('ROE real médio ≤ 0: preço justo zerado pela regra.')
    # Armadilha de dividendo (v1.2): só aviso, não muda o número
    armadilha = []
    anos_d = [y for y in range(ultimo - 2, ultimo + 1) if f'{y}-12-31' in divs and (f'{y}-01-01', f'{y}-12-31') in ll]
    if len(anos_d) == 3:
        pago_d = sum(divs[f'{y}-12-31'] for y in anos_d)
        lucro_d = sum(ll[(f'{y}-01-01', f'{y}-12-31')][1] for y in anos_d)
        if pago_d > max(lucro_d, 0.0):
            armadilha.append(f'proventos pagos em {anos_d[0]}-{anos_d[-1]} (R$ {pago_d / 1e9:.2f} bi) acima do lucro do período (R$ {lucro_d / 1e9:.2f} bi), payout > 100%')
    caixa_curto = False
    anos_f = [y for y in range(ultimo - 2, ultimo + 1) if f'{y}-12-31' in fcos and f'{y}-12-31' in divs]
    if len(anos_f) == 3:
        fcl_f = sum(fcos[f'{y}-12-31'] - capexs.get(f'{y}-12-31', 0.0) for y in anos_f)
        div_f = sum(divs[f'{y}-12-31'] for y in anos_f)
        if div_f > 0 and fcl_f < div_f:
            caixa_curto = True
            avisos.append(f'Caixa não cobre os proventos: (FCO - capex) de {anos_f[0]}-{anos_f[-1]} (R$ {fcl_f / 1e9:.2f} bi) ficou abaixo dos '
                          f'proventos pagos no período (R$ {div_f / 1e9:.2f} bi). Conferir se a diferença veio de dívida ou venda de ativos '
                          '(em holdings e seguradoras, dividendos recebidos de investidas entram fora do FCO).')
    if armadilha:
        avisos.append('Possível armadilha de dividendo: ' + '; '.join(armadilha) + '. O DY esperado pode não se sustentar.')

    # Status da tese (v1.2): separado do viés. Crítica > Monitoramento > Consolidada
    criticos = (['armadilha de dividendo'] if armadilha else []) + (['preço justo zerado pela regra'] if pj <= 0 else [])
    MONITOR = [('caixa não cobre os proventos', caixa_curto),
               ('ROE dos últimos 12 meses longe da média', roe_ltm is not None and abs(roe_ltm - roe_nom) > 0.05),
               ('lucro vira pouco caixa', conv is not None and conv < 0.6),
               ('menos de 10 anos de dados', len(roes) < 10)]
    monitorar = [m for m, c in MONITOR if c]
    if criticos:
        status = 'Revisão crítica (' + '; '.join(criticos) + ')'
    elif monitorar:
        status = 'Monitoramento (' + '; '.join(monitorar) + ')'
    else:
        status = 'Consolidada'
    print(f'Status da tese: {status}')
    if avisos:
        print('\nAvisos:')
        for x in avisos:
            print(' - ' + x)


if __name__ == '__main__':
    main()
```