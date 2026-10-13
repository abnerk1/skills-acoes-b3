#!/usr/bin/env python3
"""Microskill Ativos (v1): preço justo e preço-teto por valor dos ativos (NAV / soma das partes).

Fontes: CVM dados abertos (DFP/ITR) e, para marcação a mercado, o RI da empresa ou as outras microskills.
Regra v1:
  NAV                = PL do controlador (último ITR/DFP)
                       + soma dos ajustes a mercado (RI: laudo de terras, imóveis etc.), líquidos de 34% de IR
                       + soma das participações: % detido x (preço justo da investida x ações da investida - PL da investida)
                       - despesas G&A anuais da holding / 10%        (só quando há participações)
  Preço justo        = NAV / ações ex-tesouraria x ações por ativo
  Preço-teto         = Preço justo x 0,8
  Bear / Bull        = ativos avaliados (NAV antes das despesas da holding) -10% / +10%
  DY esperado        = proventos pagos, média dos últimos 3 exercícios / ações / preço atual
Uso:
  python3 ativos.py --empresa "EZ TEC" --preco 15.00
  python3 ativos.py --empresa "BRASILAGRO" --preco 24.00 --ajuste "Fazendas (laudo RI)=2.1"
  python3 ativos.py --empresa "ITAUSA" --preco 10.50 --participacao "ITAU UNIBANCO HOLDING=0.372@27.90"
"""
import argparse, csv, gzip, io, json, os, sys, time, unicodedata, urllib.request, zipfile, datetime

KE = 0.10
MARGEM = 0.20
FAIXA = 0.10     # bear/bull: ativos avaliados -10% / +10%
IR = 0.34        # IR + CSLL sobre o ganho de marcação a mercado
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


def carregar(empresa):
    """Dados da companhia na CVM: nome, PL do controlador mais recente, ações ex-tesouraria, proventos, G&A individual."""
    hoje = datetime.date.today().year
    ll, pl, acoes, divs, cnpj, nome, ga = {}, {}, {}, {}, None, None, {}
    for ano in range(hoje, hoje - 6, -1):
        z = baixar('DFP', ano)
        if not z:
            continue
        if cnpj is None:
            cnpj, nome = achar_cnpj(empresa, z, 'DFP')
            if cnpj is None:
                continue
        l, p, ac, dv, _, _, _ = coletar(cnpj, z, 'DFP', ano)
        for k, v in dv.items():
            divs.setdefault(k, v)
        for k, v in l.items():
            if k not in ll or (v[1] and (v[0] >= ll[k][0] or not ll[k][1])):
                ll[k] = v
        for k, v in p.items():
            if not pl.get(k):
                pl[k] = v
        acoes.update(ac)
        # despesas gerais e administrativas da controladora (individual), exercício completo
        for r in ler(z, f'dfp_cia_aberta_DRE_ind_{ano}.csv'):
            if r['CNPJ_CIA'] == cnpj and r['ORDEM_EXERC'] == 'ÚLTIMO' and r['CD_CONTA'] == '3.04.02':
                ga.setdefault(r['DT_FIM_EXERC'], -float(r['VL_CONTA']) * (1e3 if r.get('ESCALA_MOEDA', 'MIL').upper() == 'MIL' else 1.0))
    if cnpj is None:
        return None
    for ano in (hoje, hoje - 1):
        z = baixar('ITR', ano)
        if z:
            l, p, ac, *_ = coletar(cnpj, z, 'ITR', ano)
            pl.update({k: v for k, v in p.items() if k not in pl})
            acoes.update(ac)
    data_pl = max(pl)
    data_ac = max(d for d in acoes if d <= data_pl) if any(d <= data_pl for d in acoes) else max(acoes)
    n_acoes = acoes[data_ac]
    milhares = False
    if pl[data_pl] / n_acoes > 1000:  # composição do capital informada em milhares de ações
        n_acoes *= 1000
        milhares = True
    return dict(cnpj=cnpj, nome=nome, pl=pl[data_pl], data_pl=data_pl, acoes=n_acoes, data_ac=data_ac,
                divs=divs, ga=ga, milhares=milhares)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--empresa', required=True, help='trecho do nome na CVM, ex.: "ITAUSA", "BRASILAGRO", "EZ TEC"')
    ap.add_argument('--preco', type=float, required=True, help='cotação atual do ativo negociado')
    ap.add_argument('--ajuste', action='append', default=[], metavar='NOME=VALOR',
                    help='marcação a mercado de um ativo, em R$ bi (valor de mercado - valor contábil), com fonte no RI')
    ap.add_argument('--participacao', action='append', default=[], metavar='EMPRESA_CVM=PCT@PRECO_JUSTO',
                    help='participação relevante: %% do capital total detido e preço justo por ação calculado pela microskill da investida')
    ap.add_argument('--acoes-por-ativo', type=float, default=1.0, help='2 para units 1 ON + 1 PN, 3 para 1 ON + 2 PN')
    ap.add_argument('--pl-atual', type=float, default=None, help='PL do controlador mais recente (R$ bi), se a CVM estiver defasada')
    ap.add_argument('--acoes', type=int, default=None, help='ações em circulação ex-tesouraria (unidades), se a CVM estiver defasada')
    a = ap.parse_args()
    avisos = []

    d = carregar(a.empresa)
    if d is None:
        sys.exit(f'Empresa "{a.empresa}" não encontrada na CVM.')
    pl_atual = a.pl_atual * 1e9 if a.pl_atual else d['pl']
    n_acoes = a.acoes or d['acoes']
    if d['milhares'] and not a.acoes:
        avisos.append('Quantidade de ações da CVM estava em milhares; multiplicada por 1.000. Conferir no RI.')
    if not a.pl_atual and (datetime.date.today() - datetime.date.fromisoformat(d['data_pl'])).days > 270:
        avisos.append(f'PL mais recente é de {d["data_pl"]} (mais de 9 meses). Informar --pl-atual a partir do último ITR no RI.')

    linhas = [('PL do controlador (' + (d['data_pl'] if not a.pl_atual else 'informado') + ')', pl_atual)]
    for aj in a.ajuste:
        nome, val = aj.split('=')
        bruto = float(val.replace(',', '.')) * 1e9
        liq = bruto * (1 - IR) if bruto > 0 else bruto  # ganho só vira caixa ao acionista depois do imposto
        linhas.append((f'Ajuste a mercado: {nome} (R$ {bruto / 1e9:.2f} bi bruto, líquido de IR {IR:.0%})', liq))
    for pa in a.participacao:
        emp, resto = pa.split('=')
        pct, pj_inv = (float(x.replace(',', '.')) for x in resto.split('@'))
        inv = carregar(emp)
        if inv is None:
            avisos.append(f'Investida "{emp}" não encontrada na CVM; participação mantida a valor contábil.')
            continue
        justo_inv = pj_inv * inv['acoes']
        aj = pct * (justo_inv - inv['pl'])
        linhas.append((f'Participação {inv["nome"][:30]}: {pct:.1%} x (R$ {justo_inv / 1e9:.1f} bi justo - R$ {inv["pl"] / 1e9:.1f} bi PL)', aj))
    ativos = sum(v for _, v in linhas)

    custo_holding = 0.0
    if a.participacao:
        if d['ga']:
            ult = max(d['ga'])
            custo_holding = d['ga'][ult] / KE
            linhas.append((f'Despesas da holding: G&A {ult[:4]} R$ {d["ga"][ult] / 1e6:.0f} mi / 10%', -custo_holding))
        else:
            avisos.append('Despesas G&A da holding não encontradas na CVM; não descontadas. Conferir no RI.')
    nav = ativos - custo_holding

    def justo(fator):
        return max(ativos * fator - custo_holding, 0.0) / n_acoes * a.acoes_por_ativo

    pj = justo(1.0)
    teto = pj * (1 - MARGEM)
    anos_div = sorted(d['divs'])[-3:]
    prov = sum(d['divs'][k] for k in anos_div) / len(anos_div) if anos_div else None
    dy = prov / n_acoes * a.acoes_por_ativo / a.preco if prov is not None else None
    vies = 'Comprar' if a.preco <= teto else 'Aguardar'

    print(f'Empresa: {d["nome"]}  (CNPJ {d["cnpj"]})')
    print('\nComposição do NAV (R$ bi)')
    for nome, v in linhas:
        print(f'  {v / 1e9:9.2f}  {nome}')
    print(f'  {nav / 1e9:9.2f}  = NAV')
    print(f'Ações ex-tesouraria ({d["data_ac"] if not a.acoes else "informado"}): {n_acoes:,} | NAV por ação: R$ {nav / n_acoes:.2f}')
    print(f'P/VP implícito: {nav / pl_atual:.2f}')
    print('\n=== RESULTADO ===')
    print(f'Preço atual:   R$ {a.preco:.2f}')
    print(f'Preço justo:   R$ {pj:.2f}   (bear R$ {justo(1 - FAIXA):.2f} | bull R$ {justo(1 + FAIXA):.2f})')
    print(f'Preço-teto:    R$ {teto:.2f}')
    if dy is not None:
        print(f'DY esperado:   {dy:.1%}  (proventos pagos, média {anos_div[0][:4]}-{anos_div[-1][:4]}: R$ {prov / 1e9:.2f} bi)')
    else:
        print('DY esperado:   n/d (sem proventos pagos na CVM)')
    print(f'Viés:          {vies}')
    if not a.ajuste and not a.participacao:
        avisos.append('Sem ajustes a mercado: NAV = PL contábil (P/VP 1). Se houver ativo relevante a custo (terras, imóveis, participações), informar --ajuste com o valor do RI.')
    if avisos:
        print('\nAvisos:')
        for x in avisos:
            print(' - ' + x)


if __name__ == '__main__':
    main()
