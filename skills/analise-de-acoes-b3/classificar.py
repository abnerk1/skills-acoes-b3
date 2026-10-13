#!/usr/bin/env python3
"""Análise de Ações da B3 (v1): identifica a ação na CVM e escolhe a microskill de valuation.

Uso:
  python3 classificar.py --ticker ITSA4 [--preco 15.97] [--liquidez 50] [--empresa "NOME CVM"]
Saída: empresa na CVM (nome para --empresa), ações por ativo (units), setor, testes de balanço,
microskill escolhida (tabela fixa; regra para tickers fora da tabela), valor de mercado e porte.
"""
import argparse, csv, io, os, re, sys, time, unicodedata, urllib.request, zipfile, datetime

SMALL_CAP = 10e9        # valor de mercado abaixo de R$ 10 bi = small cap
LIQ_MIN = 1e6           # liquidez média diária abaixo de R$ 1 mi = alerta de liquidez
LIQ_FILTRO = 0.2e6      # abaixo de R$ 200 mil = filtro: viés fica "Aguardar (liquidez)"
FCA = 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_{ano}.zip'
CAD = 'https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv'

# Tabela fixa (desenho do projeto, a partir das 39 teses). Ticker fora dela -> regra.
TABELA = {
    'Financeiras': 'BBAS3 BBAS3 SANB11 SANB3 SANB4 ITUB3 ITUB4 BBDC3 BBDC4 ABCB4 BRBI11 BPAC11 BRSR6',
    'Fluxo normalizado': 'VALE3 PETR3 PETR4 PRIO3 RECV3 KLBN3 KLBN4 KLBN11 SUZB3 UNIP3 UNIP6 SLCE3 FESA4 RANI3 TUPY3 '
                         'SHUL4 KEPL3 CAMB3 EGIE3 AXIA3 AXIA6 AXIA7 CLSC3 CLSC4 BBSE3 CXSE3 WIZC3 TAEE11 TIMS3 BRKM5',
    'Crescimento': 'B3SA3 VAMO3 GMAT3 VIVA3 SOJA3 TTEN3 PNVL3 MLAS3 FIQE3 SEER3 PLPL3',
    'Ativos': 'AGRO3 EZTC3 G2DI33 SIMH3 ITSA3 ITSA4',
}
SETOR_FLUXO = ('extracao mineral', 'petroleo', 'papel', 'celulose', 'metalurgia', 'siderurgia', 'petroquim',
               'energia eletrica', 'saneamento', 'seguradora', 'previdencia', 'embalagens', 'telecomunica')

CVM = 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/{doc}/DADOS/{doc_l}_cia_aberta_{ano}.zip'
CACHE = os.path.expanduser('~/.cache/cvm')


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
        ult = {}  # última linha de lucro do nível 1 (lucro líquido do período, depois de participações)
        for r in ultima_versao([r for r in ler(zpath, f'{p}DRE_ind_{ano}.csv') if r['CNPJ_CIA'] == cnpj]):
            d, cd, k = norm(r['DS_CONTA']), r['CD_CONTA'], (r['DT_INI_EXERC'], r['DT_FIM_EXERC'])
            if cd.count('.') == 1 and d.startswith('lucro') and 'por acao' not in d and cd > ult.get(k, ('', 0))[0]:
                ult[k] = (cd, float(r['VL_CONTA']) * escala(r))
        for k, (_, v) in ult.items():
            if not ll.get(k, (0, 0.0))[1]:
                ll[k] = (int(ano), v)
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


def baixar_url(url, nome, horas=24):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, nome)
    if not os.path.exists(path) or time.time() - os.path.getmtime(path) > horas * 3600:
        try:
            urllib.request.urlretrieve(url, path)
        except Exception:
            return path if os.path.exists(path) else None
    return path


def resolver(ticker, empresa=None):
    """Ticker -> (CNPJ, nome CVM, ações por ativo). Procura o código no FCA; sem ele, a raiz do ticker ou o nome."""
    hoje = datetime.date.today().year
    linhas = []
    for ano in (hoje, hoje - 1):
        z = baixar_url(FCA.format(ano=ano), f'fca_{ano}.zip')
        if z:
            with zipfile.ZipFile(z) as zz:
                nome = [n for n in zz.namelist() if 'valor_mobiliario' in n][0]
                linhas += list(csv.DictReader(io.TextIOWrapper(zz.open(nome), encoding='latin1'), delimiter=';'))
    t = ticker.upper()
    achou = [r for r in linhas if r['Codigo_Negociacao'].strip().upper() == t]
    if not achou:
        achou = [r for r in linhas if r['Codigo_Negociacao'].strip().upper()[:4] == t[:4]]
    if not achou and empresa:
        achou = [r for r in linhas if norm(empresa) in norm(r['Nome_Empresarial'])]
    if not achou:
        return None, None, 1
    r = achou[0]
    comp = next((x['Composicao_BDR_Unit'] for x in linhas if x['Codigo_Negociacao'].strip().upper() == t and x['Composicao_BDR_Unit']), '')
    por_ativo = sum(int(n) for n in re.findall(r'(\d+)\s*(?:ON|PN|[A-Z]{4}\d)', comp.upper())) or 1
    return r['CNPJ_Companhia'], r['Nome_Empresarial'], por_ativo


def setor(cnpj):
    path = baixar_url(CAD, 'cad_cia_aberta.csv')
    with open(path, encoding='latin1') as fh:
        for r in csv.DictReader(fh, delimiter=';'):
            if r['CNPJ_CIA'] == cnpj and r['SIT'] == 'ATIVO':
                return r['SETOR_ATIV']
    return ''


def balanco(cnpj):
    """Último BP consolidado da DFP: PL, investimentos em coligadas, propriedades para investimento, imóveis/estoques."""
    hoje = datetime.date.today().year
    for ano in range(hoje, hoje - 3, -1):
        z = baixar('DFP', ano)
        if not z:
            continue
        out = {}
        for tipo in ('con', 'ind'):
            rows = [r for r in ler(z, f'dfp_cia_aberta_BPA_{tipo}_{ano}.csv') if r['CNPJ_CIA'] == cnpj and r['ORDEM_EXERC'] == 'ÚLTIMO']
            rows += [r for r in ler(z, f'dfp_cia_aberta_BPP_{tipo}_{ano}.csv') if r['CNPJ_CIA'] == cnpj and r['ORDEM_EXERC'] == 'ÚLTIMO']
            if not rows or not any(float(r['VL_CONTA']) for r in rows):
                continue
            esc = lambda r: float(r['VL_CONTA']) * (1e3 if r.get('ESCALA_MOEDA', 'MIL').upper() == 'MIL' else 1.0)
            for r in rows:
                cd, d = r['CD_CONTA'], norm(r['DS_CONTA'])
                if cd == '1':
                    out['ativo'] = esc(r)
                elif cd == '1.02.02':
                    out['investimentos'] = esc(r)
                elif cd.count('.') == 1 and d.startswith('patrimonio liquido'):
                    out['pl'] = esc(r)
                elif 'propriedade' in d and 'investimento' in d and cd.startswith('1.02'):
                    out['prop_invest'] = out.get('prop_invest', 0.0) + esc(r)
                elif cd.startswith(('1.01.04', '1.02.01')) and ('imove' in d or (cd == '1.01.04')):
                    out['imoveis'] = out.get('imoveis', 0.0) + esc(r)
                elif d.startswith('patrimonio liquido atribuido ao controlador'):
                    out['pl_ctrl'] = esc(r)
            out['tipo'], out['ano'] = tipo, ano
            return out
    return {}


def retencao(cnpj):
    """1 - (dividendos + JCP + recompras) / lucro, média dos últimos 5 exercícios (CVM)."""
    hoje = datetime.date.today().year
    ll, divs, recs = {}, {}, {}
    for ano in range(hoje, hoje - 6, -1):
        z = baixar('DFP', ano)
        if not z:
            continue
        l, _, _, dv, _, _, rc = coletar(cnpj, z, 'DFP', ano)
        for (i, f), v in l.items():
            if i[5:] == '01-01' and f[5:] == '12-31' and v[1]:
                ll.setdefault(f, v[1])
        for k, v in dv.items():
            divs.setdefault(k, v)
        for k, v in rc.items():
            recs.setdefault(k, v)
    anos = sorted(ll)[-5:]
    lucro = sum(ll[k] for k in anos)
    if len(anos) < 3 or lucro <= 0:
        return None
    return 1 - min((sum(divs.get(k, 0.0) + recs.get(k, 0.0) for k in anos)) / lucro, 1.0)


def acoes_total(cnpj):
    hoje = datetime.date.today().year
    for ano in (hoje, hoje - 1):
        z = baixar('ITR', ano)
        if not z:
            continue
        rows = [r for r in ler(z, f'itr_cia_aberta_composicao_capital_{ano}.csv') if r['CNPJ_CIA'] == cnpj]
        if rows:
            r = max(rows, key=lambda r: r['DT_REFER'])
            return int(r['QT_ACAO_TOTAL_CAP_INTEGR']) - int(r['QT_ACAO_TOTAL_TESOURO'])
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ticker', required=True)
    ap.add_argument('--preco', type=float, default=None, help='cotação atual (para valor de mercado)')
    ap.add_argument('--liquidez', type=float, default=None, help='volume médio diário negociado, em R$ mil')
    ap.add_argument('--empresa', default=None, help='nome na CVM, se o ticker não for encontrado no FCA (ex.: BDR)')
    a = ap.parse_args()
    t = a.ticker.upper()
    cnpj, nome, por_ativo = resolver(t, a.empresa)
    if cnpj is None:
        sys.exit(f'Ticker {t} não encontrado no FCA da CVM. Informar --empresa com o nome da companhia.')
    st = setor(cnpj)
    b = balanco(cnpj)
    ret = retencao(cnpj)
    pl = b.get('pl_ctrl') or b.get('pl') or 0.0
    r_inv = b.get('investimentos', 0.0) / pl if pl > 0 else 0.0
    r_prop = b.get('prop_invest', 0.0) / pl if pl > 0 else 0.0
    r_imov = b.get('imoveis', 0.0) / pl if pl > 0 else 0.0
    sn = norm(st)

    # regra (para tickers fora da tabela)
    if 'banco' in sn:
        regra, motivo = 'Financeiras', f'setor CVM "{st}"'
    elif r_inv >= 0.5:
        regra, motivo = 'Ativos', f'investimentos em coligadas = {r_inv:.0%} do PL'
    elif r_prop >= 0.5:
        regra, motivo = 'Ativos', f'propriedades para investimento = {r_prop:.0%} do PL'
    elif 'const' in sn and r_imov >= 0.5:
        regra, motivo = 'Ativos', f'imóveis a comercializar = {r_imov:.0%} do PL'
    elif any(x in sn for x in SETOR_FLUXO):
        regra, motivo = 'Fluxo normalizado', f'setor CVM "{st}"'
    elif ret is not None and ret >= 0.5:
        regra, motivo = 'Crescimento', f'retém {ret:.0%} do lucro (proventos + recompras, 5 anos)'
    else:
        regra, motivo = 'Fluxo normalizado', 'retém menos de 50% do lucro' if ret is not None else 'retenção n/d'
    tabela = next((k for k, v in TABELA.items() if t in v.split()), None)
    escolha = tabela or regra

    print(f'Ticker: {t} | Empresa CVM: {nome} (CNPJ {cnpj})')
    print(f'Ações por ativo: {por_ativo}' + (' (unit)' if por_ativo > 1 else ''))
    if t.endswith('11') and por_ativo == 1:
        print('  AVISO: ticker final 11 sem composição no FCA; conferir no RI quantas ações compõem a unit.')
    print(f'Setor CVM: {st or "n/d"}')
    print(f'Testes de balanço ({b.get("tipo", "?")} {b.get("ano", "?")}): investimentos/PL {r_inv:.0%} | '
          f'propriedades p/ investimento/PL {r_prop:.0%} | imóveis e estoques/PL {r_imov:.0%} | '
          f'retenção {"n/d" if ret is None else format(ret, ".0%")}')
    print(f'Regra: {regra} ({motivo})')
    print(f'Tabela: {tabela or "fora da tabela"}')
    print(f'MICROSKILL: {escolha}')
    if tabela and tabela != regra:
        print(f'  (tabela prevalece sobre a regra; divergência registrada)')
    n = acoes_total(cnpj)
    if n and pl / n > 1000:  # composição do capital informada em milhares de ações
        n *= 1000
    if a.preco and n:
        vm = a.preco / por_ativo * n
        print(f'Valor de mercado: R$ {vm / 1e9:.2f} bi -> ' + ('SMALL CAP' if vm < SMALL_CAP else 'large/mid cap'))
    if a.liquidez is not None:
        liq = a.liquidez * 1e3
        if liq < LIQ_FILTRO:
            print(f'Liquidez: R$ {a.liquidez:,.0f} mil/dia -> FILTRO: viés limitado a "Aguardar (liquidez)"')
        elif liq < LIQ_MIN:
            print(f'Liquidez: R$ {a.liquidez:,.0f} mil/dia -> ALERTA: baixa liquidez, montar posição aos poucos')
        else:
            print(f'Liquidez: R$ {a.liquidez:,.0f} mil/dia -> adequada')


if __name__ == '__main__':
    main()
