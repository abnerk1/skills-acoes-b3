---
name: "acoes-crescimento"
description: "Calcula preço justo, preço-teto, DY esperado e viés de empresas da B3 que reinvestem o lucro para crescer (varejo, agro, locação, bolsa), por P/L justo de dois estágios com ROIIC. Não use para bancos, commodities nem holdings."
---

# Crescimento — valuation por P/L justo com ROIIC (v1)

Microskill de cálculo. Entrega um bloco fixo de números; não escreve relatório (isso é da maestrina).

## Quando usar
- Empresas cujo valor vem de reinvestir o lucro a retorno alto: B3SA3, VAMO3, GMAT3, VIVA3, SOJA3, TTEN3, PNVL3, MLAS3, FIQE3 e similares.
- Não usar para bancos (→ Financeiras), commodities, indústria madura, elétricas e seguridade (→ Fluxo normalizado), nem holdings e ativos reais (→ Ativos).

## Regra (fixa, não alterar)
1. ROE de cada ano = lucro atribuído ao controlador ÷ PL do controlador médio (início e fim do ano). Fonte: DFP consolidada na CVM (individual, se a companhia não tiver consolidado).
2. ROIIC (retorno sobre o capital reinvestido) = ROE real médio dos últimos 10 anos: (1 + ROE nominal médio) ÷ (1 + IPCA médio dos mesmos anos) − 1. Com menos de 10 anos, usa os disponíveis (mínimo 5), com aviso.
3. Lucro base = média do lucro do controlador dos últimos 3 exercícios, corrigido pelo IPCA para reais de hoje.
4. Retenção = 1 − (dividendos + JCP + recompras) ÷ lucro, média de 5 anos pela CVM. A recompra conta como distribuição.
5. Fase 1 (5 anos): g1 = mín(retenção × ROIIC; 10%). Distribui (1 − g1 ÷ ROIIC) do lucro.
6. Perpetuidade: g2 = 2,5% real. Distribui (1 − g2 ÷ ROIIC) do lucro.
7. P/L justo = valor presente, a 10% real, dos proventos das duas fases por R$ 1 de lucro base.
8. Preço justo = P/L justo × lucro base ÷ ações ex-tesouraria × ações por ativo.
9. Preço-teto = preço justo × 0,8 (margem fixa de 20%).
10. Bear / bull = ROIIC −3 p.p. / +3 p.p.
11. Payout (para o DY) = política declarada no RI; sem política, média de 5 anos pela CVM (só dividendos + JCP, sem recompras).
12. DY esperado = payout × lucro base ÷ ações ÷ preço atual.
13. Viés = "Comprar" se preço atual ≤ preço-teto; senão "Aguardar".
14. Lucro base ≤ 0 ou ROIIC ≤ 0 → preço justo zero, com aviso. ROIIC abaixo de 10% → aviso de que crescer destrói valor.

Ke de 10% real, margem de 20%, fase 1 de 5 anos, teto de 10% em g1 e perpetuidade de 2,5% são constantes. Crescimento só existe se houver lucro retido: sem retenção, g1 = 0 (crescimento sem capital não entra no preço).

## Passos
1. **Identificar** o nome da companhia como aparece na CVM (ex.: "B3 S.A.", "VAMOS LOC", "GRUPO MATEUS", "VIVARA", "BOA SAFRA", "TENTOS", "DIMED") e quantas ações compõem o ativo negociado.
2. **Cotação atual**: uma única fonte, com data. Registrar fonte e data.
3. **Payout**: política declarada no RI com `--payout`; sem política, omitir e o script calcula pela CVM.
4. **Rodar o cálculo**: salvar o script abaixo como `crescimento.py` e executar:
   `python3 crescimento.py --empresa "GRUPO MATEUS" --preco 5.70`
   O script baixa as DFPs e ITRs da CVM (dados.cvm.gov.br) e o IPCA do IBGE. Não refazer contas à mão.
5. **Tratar avisos de dados**, nesta ordem: RI → PDF da DFP/ITR na CVM → pedir o PDF ao usuário. Reexecutar com `--manual "ANO=LUCRO;PL_FIM"` (R$ bi), `--pl-atual X --data-pl AAAA-MM-DD` ou `--acoes N`. Dado faltante nunca bloqueia a entrega.
6. **Entregar** o bloco de saída.

## Saída (formato fixo)
```
[TICKER] — Crescimento v1 — cotação de DD/MM/AAAA (fonte)
Preço atual:  R$ X
Preço justo:  R$ X   (bear R$ X | bull R$ X)
Preço-teto:   R$ X
DY esperado:  X%     (payout X%, fonte)
Viés:         Comprar | Aguardar
Memória de cálculo: lucro base R$ X bi | ROIIC X% | retenção X% | g1 X% (5 anos) | g2 2,5% | P/L justo X
Avisos: (lista do script, se houver)
```
Incluir a tabela anual de ROE impressa pelo script quando o usuário pedir detalhe.

## Regras gerais
- Isolamento: nunca consultar nem citar tese, preço-teto ou premissa de casas de análise (research independente, bancos, corretoras). Só dados primários (CVM, RI, IBGE) e cotação.
- Premissas neutras: não projetar lojas, capacidade, margens ou guidance da empresa; o crescimento sai só da retenção e do retorno histórico.
- Não ajustar a regra caso a caso; divergências viram aviso, não exceção.

## Script
```python
#!/usr/bin/env python3
"""Microskill Crescimento (v1): preço justo e preço-teto de empresas que reinvestem para crescer.

Fontes: CVM dados abertos (DFP/ITR; consolidado, ou individual se não houver) e IBGE (IPCA).
Regra v1:
  ROE anual          = lucro atribuído ao controlador / PL do controlador médio (início e fim do ano)
  ROIIC              = ROE real médio dos últimos 10 anos: (1 + ROE nominal médio) / (1 + IPCA médio) - 1
  Lucro base         = média do lucro dos últimos 3 exercícios, corrigido pelo IPCA (reais de hoje)
  Retenção b         = 1 - (dividendos + JCP + recompras) / lucro, média de 5 anos (CVM)
  Fase 1 (5 anos)    = g1 = mín(b x ROIIC; 10%), distribui (1 - g1 / ROIIC) do lucro
  Perpetuidade       = g2 = 2,5%, distribui (1 - g2 / ROIIC) do lucro
  P/L justo          = valor presente dos proventos das duas fases a 10% real, por R$ 1 de lucro base
  Preço justo        = P/L justo x lucro base / ações x ações por ativo
  Preço-teto         = Preço justo x 0,8
  Bear / Bull        = ROIIC -3 p.p. / +3 p.p.
  DY esperado        = payout (só proventos) x lucro base / ações / preço atual
Uso:
  python3 crescimento.py --empresa "GRUPO MATEUS" --preco 6.00 [--payout 0.25] [--acoes-por-ativo 1]
"""
import argparse, csv, gzip, io, json, os, sys, time, unicodedata, urllib.request, zipfile, datetime

KE = 0.10
MARGEM = 0.20
JANELA = 10      # anos de histórico para o ROIIC
N1 = 5           # anos da fase de crescimento
G1_MAX = 0.10    # teto do crescimento real na fase 1
G2 = 0.025       # crescimento real na perpetuidade
ANOS_BASE = 3    # exercícios na média do lucro base
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
            if r['CD_CONTA'] == '2.03' and not pl_c.get(r['DT_FIM_EXERC']):
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
    rec = {}  # recompras de ações (saída de caixa no financiamento)
    for arq in (f'{p}DFC_MI_con_{ano}.csv', f'{p}DFC_MD_con_{ano}.csv'):
        for r in ultima_versao([r for r in ler(zpath, arq) if r['CNPJ_CIA'] == cnpj]):
            d, v = norm(r['DS_CONTA']), float(r['VL_CONTA']) * escala(r)
            if r['CD_CONTA'].startswith('6.03') and v < 0 and ('recompra' in d or ('acoes' in d and ('tesouraria' in d or 'aquisicao' in d))):
                k = r['DT_FIM_EXERC']
                rec[k] = rec.get(k, 0.0) - v
    acoes = {}
    for r in ler(zpath, f'{p}composicao_capital_{ano}.csv'):
        if r['CNPJ_CIA'] == cnpj:
            acoes[r['DT_REFER']] = int(r['QT_ACAO_TOTAL_CAP_INTEGR']) - int(r['QT_ACAO_TOTAL_TESOURO'])
    return ll, pl_c, acoes, div, fco, capex, rec


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
    anos_dfp, divs, fcos, capexs, recs = [], {}, {}, {}, {}
    for ano in range(hoje, hoje - 13, -1):
        z = baixar('DFP', ano)
        if not z:
            continue
        if cnpj is None:
            cnpj, nome = achar_cnpj(a.empresa, z, 'DFP')
            if cnpj is None:
                continue
        l, p, ac, dv, fc, cx, rc = coletar(cnpj, z, 'DFP', ano)
        for k, v in rc.items():
            recs.setdefault(k, v)
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
            l, p, ac, _, _, _, _ = coletar(cnpj, z, 'ITR', ano)
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
    anos = list(range(ultimo - JANELA + 1, ultimo + 1))
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

    # anos com DFC na CVM: dividendo ou recompra ausente conta como zero
    anos_p = [y for y in range(ultimo - 4, ultimo + 1) if f'{y}-12-31' in fcos and (f'{y}-01-01', f'{y}-12-31') in ll]
    lucro_p = sum(ll[(f'{y}-01-01', f'{y}-12-31')][1] for y in anos_p)
    tx_rec = None
    if len(anos_p) >= 3 and lucro_p > 0:
        tx_rec = sum(recs.get(f'{y}-12-31', 0.0) for y in anos_p) / lucro_p
    if a.payout is not None:
        payout, fonte_payout = a.payout, 'política declarada'
    elif tx_rec is not None:
        payout = min(sum(divs.get(f'{y}-12-31', 0.0) for y in anos_p) / lucro_p, 1.0)
        fonte_payout = f'média CVM {anos_p[0]}-{anos_p[-1]} (pagos/lucro)'
    else:
        payout, fonte_payout = None, 'indisponível'
        avisos.append('Payout indisponível: DY n/d e fase 1 sem crescimento. Informar --payout a partir do RI.')
    # distribuição total = dividendos + JCP + recompras (a recompra também devolve capital)
    distrib = min(payout + (tx_rec or 0.0), 1.0) if payout is not None else None

    # ---- Regra Crescimento: DDM em dois estágios com retorno incremental (ROIIC) ----
    roiic = roe_real
    b = (1 - distrib) if distrib is not None else 0.0

    def multiplo(rr, g1=None):
        """P/L justo sobre o lucro normalizado: fase 1 de N1 anos com g1 = b x ROIIC (teto G1_MAX), depois perpetuidade g2."""
        if rr <= 0:
            return 0.0, 0.0, 0.0
        g1 = min(b * rr, G1_MAX) if g1 is None else g1
        g2 = min(G2, rr)  # nunca cresce mais que o retorno do capital
        d1 = 1 - g1 / rr  # fração do lucro distribuída na fase 1
        d2 = 1 - g2 / rr  # fração distribuída na perpetuidade
        v, e = 0.0, 1.0
        for t in range(1, N1 + 1):
            e *= 1 + g1
            v += e * d1 / (1 + KE) ** t
        v += e * (1 + g2) * d2 / (KE - g2) / (1 + KE) ** N1
        return v, g1, g2

    # lucro base: média dos últimos 3 exercícios em reais de hoje
    base = []
    for y in range(ultimo - ANOS_BASE + 1, ultimo + 1):
        l = ll.get((f'{y}-01-01', f'{y}-12-31'), (0, None))[1]
        if l is None:
            continue
        f = 1.0
        for z in range(y + 1, ultimo + 1):
            f *= 1 + ipca.get(z, ipca_med)
        base.append(l * f)
    lucro_base = sum(base) / len(base) if base else 0.0
    if len(base) < ANOS_BASE:
        avisos.append(f'Lucro base com só {len(base)} exercício(s) (padrão: {ANOS_BASE}).')
    if lucro_base <= 0:
        avisos.append('Lucro base ≤ 0: preço justo zerado pela regra.')

    def justo(rr):
        return multiplo(rr)[0] * max(lucro_base, 0.0) / n_acoes * a.acoes_por_ativo

    pl_justo, g1, g2 = multiplo(roiic)
    pj = justo(roiic)
    teto = pj * (1 - MARGEM)
    dy = payout * max(lucro_base, 0.0) / n_acoes * a.acoes_por_ativo / a.preco if payout is not None else None
    vies = 'Comprar' if a.preco <= teto else 'Aguardar'

    # crescimento real histórico do lucro (só informativo)
    cagr = None
    lucros = [(y, ll[(f'{y}-01-01', f'{y}-12-31')][1]) for y in anos if (f'{y}-01-01', f'{y}-12-31') in ll]
    if len(lucros) >= 5:
        (y0, l0), (y1, l1) = lucros[0], lucros[-1]
        if l0 > 0 and l1 > 0:
            infl = 1.0
            for y in range(y0 + 1, y1 + 1):
                infl *= 1 + ipca.get(y, ipca_med)
            cagr = (l1 / l0 / infl) ** (1 / (y1 - y0)) - 1

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
                              'Normal em fase de investimento; se persistir, o lucro não vira provento.')

    # ROE dos últimos 12 meses (para aviso)
    # 12 meses = último ano completo - acumulado do ano anterior até a mesma data + acumulado do ano atual
    roe_ltm = None
    ytd = sorted((f, v[1]) for (i, f), v in ll.items() if i[5:] == '01-01' and f[5:] != '12-31' and int(f[:4]) > ultimo)
    if ytd:
        f_atual, lucro_ytd = ytd[-1]
        f_ant = f'{int(f_atual[:4]) - 1}{f_atual[4:]}'
        anual = ll.get((f'{ultimo}-01-01', f'{ultimo}-12-31'), (0, None))[1]
        ytd_ant = ll.get((f'{ultimo}-01-01', f_ant), (0, None))[1]
        if None not in (anual, ytd_ant) and f'{ultimo}-12-31' in pl and f_atual in pl:
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
    print(f'Lucro base (média {ANOS_BASE} anos, reais de hoje): R$ {lucro_base / 1e9:.2f} bi')
    print(f'ROIIC (= ROE real médio):        {roiic:.2%}')
    if distrib is not None:
        print(f'Distribuição total (proventos + recompras): {distrib:.0%} | retenção {b:.0%}')
    print(f'Fase 1 ({N1} anos): g1 = mín({b:.0%} x {roiic:.2%}; {G1_MAX:.0%}) = {g1:.2%} | distribui {1 - g1 / roiic if roiic > 0 else 0:.0%} do lucro')
    print(f'Perpetuidade: g2 = {g2:.2%} | distribui {1 - g2 / roiic if roiic > 0 else 0:.0%} do lucro')
    print(f'P/L justo: {pl_justo:.1f}x | Valor do equity: R$ {pl_justo * max(lucro_base, 0) / 1e9:.2f} bi')
    if cagr is not None:
        print(f'Crescimento real histórico do lucro ({lucros[0][0]}-{lucros[-1][0]}): {cagr:.1%} a.a. (informativo)')
    if conv is not None:
        print(f'Conversão em caixa ({anos_c[0]}-{anos_c[-1]}): (FCO - capex) / lucro = {conv:.0%}')
    print(f'PL controlador em {data_pl}: R$ {pl_atual / 1e9:.2f} bi | ações ex-tesouraria ({data_ac}): {n_acoes:,}')
    print(f'VPA: R$ {vpa:.2f} (x {a.acoes_por_ativo:g} por ativo)')
    print('\n=== RESULTADO ===')
    print(f'Preço atual:   R$ {a.preco:.2f}')
    print(f'Preço justo:   R$ {pj:.2f}   (bear R$ {justo(roiic - 0.03):.2f} | bull R$ {justo(roiic + 0.03):.2f})')
    print(f'Preço-teto:    R$ {teto:.2f}')
    if dy is not None:
        print(f'DY esperado:   {dy:.1%}  (payout {payout:.0%}, {fonte_payout}; lucro base R$ {lucro_base / 1e9:.2f} bi)')
    else:
        print('DY esperado:   n/d (payout indisponível)')
    print(f'Viés:          {vies}')
    if len(roes) < 10:
        avisos.append(f'Só {len(roes)} anos de ROE disponíveis (padrão: {JANELA}).')
    if roe_ltm is not None and abs(roe_ltm - roe_nom) > 0.05:
        avisos.append(f'ROE dos últimos 12 meses ({roe_ltm:.1%}) difere em mais de 5 p.p. da média de 10 anos ({roe_nom:.1%}).')
    pequenos = [y for y, _ in roes if (pl[f'{y - 1}-12-31'] + pl[f'{y}-12-31']) / 2 < 0.2 * pl_atual]
    if pequenos:
        avisos.append(f'ROIIC inclui anos com patrimônio abaixo de 20% do atual ({", ".join(map(str, pequenos))}); '
                      'o retorno desses anos pode não se repetir na escala de hoje.')
    if roiic <= 0:
        avisos.append('ROIIC ≤ 0: preço justo zerado pela regra.')
    elif roiic < KE:
        avisos.append(f'ROIIC ({roiic:.1%}) abaixo do custo de capital (10%): crescer destrói valor; o P/L justo fica abaixo de 10x.')
    if avisos:
        print('\nAvisos:')
        for x in avisos:
            print(' - ' + x)


if __name__ == '__main__':
    main()
```