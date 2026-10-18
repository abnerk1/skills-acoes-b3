#!/usr/bin/env python3
"""Análise de FIIs (v1): identifica o FII, escolhe o motor e calcula preço-teto, DY esperado, P/VP e viés.

Uso:
  python3 fii.py --ticker HGLG11 --preco 155.76 --liquidez 12500 [--credito 2.5] [--rendimento 1.17,1.17,1.17]
    --preco      cotação atual (R$)
    --liquidez   volume médio diário negociado, em R$ mil
    --credito    só papel: % do PL (marcação atual) em watchlist/inadimplência/reestruturação/repactuação
                 + imóveis retomados, excluído o que já está marcado a zero. Lido no relatório gerencial.
    --rendimento rendimentos por cota dos últimos avisos (mais antigo -> mais recente), se o FundosNet
                 estiver fora do ar e o usuário mandar o aviso/relatório em PDF.

Fontes: CVM dados abertos (informe mensal e trimestral de FII) e FundosNet (avisos de rendimento).
Só biblioteca padrão. Dado faltante vira aviso e nunca bloqueia a entrega.
"""
import argparse, csv, datetime, io, json, os, re, sys, time, unicodedata, urllib.parse, urllib.request, zipfile

VERSAO = 'v1'
# --- regras fixas (metodologia de 14-17/10/2026) ---
YIELD_TETO = {'padrao': 0.0875, 'lajes': 0.10, 'hoteis': 0.10}   # tijolo: teto = rendimento ÷ yield
AGIO_PAPEL = [(5.0, 1.05), (10.0, 1.00), (float('inf'), 0.95)]  # papel: % PL problema -> teto = VP × fator
AGIO_PAPEL_SEM_RG = 1.00                                         # papel sem relatório gerencial
FATOR_FOF = 1.00                                                 # FoF: teto = VP
FATOR_TRANSICAO = 0.80                                           # transição: teto = 0,80 × VP
GATILHO_ALAV = 0.30                                              # passivo total ÷ ativo
GATILHO_YIELD_VP = 0.06                                          # rendimento corrente ÷ VP (tijolo)
ALERTA_RECORRENTE = 0.80                                         # recorrente 12m < 80% da base -> aviso
LIQ_MIN, LIQ_FILTRO = 1e6, 0.2e6                                 # R$/dia: alerta e filtro

# Tabela fixa: prevalece sobre a regra. ticker: (CNPJ, motor, segmento)
TABELA = {
    'PMLL11': ('26.499.833/0001-32', 'tijolo', 'shopping'), 'VISC11': ('17.554.274/0001-25', 'tijolo', 'shopping'),
    'XPML11': ('28.757.546/0001-00', 'tijolo', 'shopping'), 'BTLG11': ('11.839.593/0001-09', 'tijolo', 'logistico'),
    'HGLG11': ('11.728.688/0001-47', 'tijolo', 'logistico'), 'BRCO11': ('20.748.515/0001-81', 'tijolo', 'logistico'),
    'XPLG11': ('26.502.794/0001-85', 'tijolo', 'logistico'), 'GARE11': ('37.295.919/0001-60', 'tijolo', 'hibrido'),
    'HGRU11': ('29.641.226/0001-53', 'tijolo', 'hibrido'), 'KNRI11': ('12.005.956/0001-65', 'tijolo', 'hibrido'),
    'TRXF11': ('28.548.288/0001-52', 'tijolo', 'hibrido'), 'FATN11': ('30.567.216/0001-02', 'tijolo', 'lajes'),
    'PVBI11': ('35.652.102/0001-76', 'tijolo', 'lajes'), 'HTMX11': ('08.706.065/0001-69', 'tijolo', 'hoteis'),
    'MCCI11': ('23.648.935/0001-84', 'papel', 'cri'), 'RECR11': ('28.152.272/0001-26', 'papel', 'cri'),
    'VGIP11': ('34.197.811/0001-46', 'papel', 'cri'), 'MXRF11': ('97.521.225/0001-25', 'papel', 'cri'),
    'KNUQ11': ('42.754.362/0001-18', 'papel', 'cri'), 'RBRY11': ('30.166.700/0001-11', 'papel', 'cri'),
    'VRTA11': ('11.664.201/0001-00', 'papel', 'cri'),
}

CVM = 'https://dados.cvm.gov.br/dados/FII/DOC/{tipo}/DADOS/{arq}_{ano}.zip'
FNET = 'https://fnet.bmfbovespa.com.br/fnet/publico/'
HDR = {'User-Agent': 'Mozilla/5.0', 'X-Requested-With': 'XMLHttpRequest', 'Referer': FNET + 'abrirGerenciadorDocumentosCVM'}
CACHE = os.path.expanduser('~/.cache/fii')
avisos = []


def norm(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()


def num(x):
    try:
        return float(str(x).replace(',', '.'))
    except (TypeError, ValueError):
        return 0.0


# ---------------- CVM ----------------
def baixar(tipo, arq, ano):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f'{arq}_{ano}.zip')
    velho = not os.path.exists(path) or time.time() - os.path.getmtime(path) > 86400
    if velho:
        try:
            urllib.request.urlretrieve(CVM.format(tipo=tipo, arq=arq, ano=ano), path + '.tmp')
            os.replace(path + '.tmp', path)
        except Exception:
            pass
    return path if os.path.exists(path) else None


def ler(tipo, arq, parte, cnpj=None):
    """Linhas do CSV `parte` (ex.: 'complemento') dos dois últimos anos, só do CNPJ (se dado), última versão."""
    hoje = datetime.date.today().year
    linhas = []
    for ano in (hoje - 1, hoje):
        z = baixar(tipo, arq, ano)
        if not z:
            continue
        with zipfile.ZipFile(z) as zz:
            nomes = [n for n in zz.namelist() if n.endswith(f'_{parte}_{ano}.csv')]
            if not nomes:
                continue
            for r in csv.DictReader(io.TextIOWrapper(zz.open(nomes[0]), encoding='latin1'), delimiter=';'):
                if cnpj is None or r['CNPJ_Fundo_Classe'] == cnpj:
                    linhas.append(r)
    ult = {}
    for r in linhas:  # última versão de cada (CNPJ, data)
        k = (r['CNPJ_Fundo_Classe'], r['Data_Referencia'])
        if k not in ult or int(r.get('Versao') or 0) >= int(ult[k].get('Versao') or 0):
            ult[k] = r
    return sorted(ult.values(), key=lambda r: r['Data_Referencia'])


def mensal(arq_parte, cnpj):
    return ler('INF_MENSAL', 'inf_mensal_fii', arq_parte, cnpj)


def trimestral(arq_parte, cnpj):
    return ler('INF_TRIMESTRAL', 'inf_trimestral_fii', arq_parte, cnpj)


def resolver(ticker):
    """Ticker -> (CNPJ, motor, segmento, origem). Tabela fixa; fora dela, ISIN + composição do ativo."""
    if ticker in TABELA:
        c, m, s = TABELA[ticker]
        return c, m, s, 'tabela fixa'
    geral = ler('INF_MENSAL', 'inf_mensal_fii', 'geral')
    cands = {}
    for r in geral:
        if (r.get('Codigo_ISIN') or '')[2:6] == ticker[:4]:
            cands[r['CNPJ_Fundo_Classe']] = r
    if not cands:
        sys.exit(f'{ticker}: não encontrado no informe mensal da CVM (ISIN). Incluir na tabela fixa com o CNPJ.')
    comp = {c: (mensal('complemento', c) or [{}])[-1] for c in cands}
    cnpj = max(cands, key=lambda c: num(comp[c].get('Patrimonio_Liquido')))  # ISIN usado por mais de um fundo: maior PL
    if len(cands) > 1:
        avisos.append(f'ISIN de {ticker} aparece em {len(cands)} CNPJs na CVM; usado o de maior PL ({cnpj}). Conferir e incluir na tabela fixa.')
    g = cands[cnpj]
    ap = (mensal('ativo_passivo', cnpj) or [{}])[-1]
    ativo = num(comp[cnpj].get('Valor_Ativo')) or 1
    cri = (num(ap.get('CRI')) + num(ap.get('CRI_CRA')) + num(ap.get('LCI')) + num(ap.get('LCI_LCA'))) / ativo
    fii = num(ap.get('FII')) / ativo
    imov = num(ap.get('Direitos_Bens_Imoveis')) / ativo
    seg = norm(g.get('Segmento_Atuacao'))
    mand = norm(g.get('Mandato'))
    if 'desenvolvimento' in mand:
        motor = 'transicao'
    elif cri >= 0.5:
        motor = 'papel'
    elif fii >= 0.5:
        motor = 'fof'
    else:
        motor = 'tijolo'
    segmento = 'lajes' if 'laje' in seg or 'escritorio' in seg else 'hoteis' if 'hotel' in seg else seg or 'n/d'
    avisos.append(f'{ticker} fora da tabela fixa: motor "{motor}" pela regra (CRI {cri:.0%}, FII {fii:.0%}, '
                  f'imóveis {imov:.0%} do ativo; segmento CVM "{g.get("Segmento_Atuacao")}"; mandato "{g.get("Mandato")}"). '
                  f'Conferir no relatório gerencial.')
    return cnpj, motor, segmento, 'regra'


# ---------------- FundosNet ----------------
def fnet_get(url, tries=8, timeout=12):
    err = None
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=timeout) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:
            err = e
            time.sleep(1 + k)
    raise RuntimeError(err)


def fnet_rendimentos(cnpj, ticker, n=8, prazo=150):
    """Rendimento por cota dos últimos avisos estruturados (mais antigo -> mais recente)."""
    fim = time.time() + prazo
    q = {'d': 0, 's': 0, 'l': n, 'o[0][dataEntrega]': 'desc', 'tipoFundo': 1, 'idCategoriaDocumento': 14,
         'idTipoDocumento': 41, 'idEspecieDocumento': 0, 'cnpjFundo': re.sub(r'\D', '', cnpj)}
    docs = json.loads(fnet_get(FNET + 'pesquisarGerenciadorDocumentosDados?' + urllib.parse.urlencode(q)))['data']
    cache = os.path.join(CACHE, 'fnet')
    os.makedirs(cache, exist_ok=True)
    por_mes = {}
    for d in docs:
        if d.get('situacaoDocumento') != 'A' or time.time() > fim:
            continue
        f = os.path.join(cache, f"{d['id']}.html")
        if os.path.exists(f) and os.path.getsize(f) > 500:
            t = open(f, encoding='utf-8').read()
        else:
            t = fnet_get(FNET + f"exibirDocumento?id={d['id']}")
            open(f, 'w', encoding='utf-8').write(t)
        for bloco in re.split(r'C[^<]{0,12}digo ISIN', t)[1:]:
            m = re.search(r'negocia[^<]*</span></td>\s*<td[^>]*><span[^>]*>\s*([A-Z0-9]+)\s*<', bloco)
            if not m or m.group(1) != ticker:
                continue
            def linha(rot):
                r = re.search(rot + r'.*?</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>', bloco, re.S)
                return [re.sub(r'<[^>]+>', '', x).strip() for x in r.groups()] if r else ['', '']
            db = linha('Data-base')[0]
            v = linha('Valor do provento')[0]
            try:
                dt = datetime.datetime.strptime(db, '%d/%m/%Y').date()
            except ValueError:
                continue
            k = (dt.year, dt.month)
            val = float(v.replace('.', '').replace(',', '.')) if re.search(r'\d', v) else 0.0
            if k not in por_mes or (d.get('versao') or 0) >= por_mes[k][1]:
                por_mes[k] = (val, d.get('versao') or 0, db)
    meses = sorted(por_mes)
    return [(por_mes[k][2], por_mes[k][0]) for k in meses]


# ---------------- cálculo ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ticker', required=True)
    ap.add_argument('--preco', type=float, required=True)
    ap.add_argument('--liquidez', type=float, default=None, help='R$ mil por dia')
    ap.add_argument('--credito', type=float, default=None, help='papel: %% do PL em problema não provisionado')
    ap.add_argument('--rendimento', default=None, help='rendimentos por cota, separados por vírgula (fallback)')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    t = a.ticker.upper()
    cnpj, motor_base, segmento, origem = resolver(t)

    comp = mensal('complemento', cnpj)
    if not comp:
        sys.exit(f'{t}: CNPJ {cnpj} sem informe mensal na CVM.')
    ult = comp[-1]
    vp, cotas, ativo = num(ult['Valor_Patrimonial_Cotas']), num(ult['Cotas_Emitidas']), num(ult['Valor_Ativo'])
    ref_vp = ult['Data_Referencia'][:7]
    app = mensal('ativo_passivo', cnpj)
    passivo = num(app[-1]['Total_Passivo']) if app else 0.0
    alav = passivo / ativo if ativo else 0.0

    # rendimento corrente: média dos 3 últimos avisos × 12
    fonte_rend, serie = None, []
    if a.rendimento:
        serie = [('informado', num(x)) for x in a.rendimento.split(',') if x.strip()]
        fonte_rend = 'informado pelo usuário (aviso/relatório em PDF)'
    else:
        try:
            serie = fnet_rendimentos(cnpj, t)
            fonte_rend = 'FundosNet, avisos de rendimento'
        except Exception as e:
            avisos.append(f'FundosNet indisponível ({type(e).__name__}); rendimento pela fonte alternativa indicada abaixo.')
    if not serie:
        ult_cvm = [(r['Data_Referencia'][:7], num(r['Percentual_Dividend_Yield_Mes']) * num(r['Valor_Patrimonial_Cotas']))
                   for r in comp[-3:]]
        if len(ult_cvm) == 3 and all(v > 0 for _, v in ult_cvm):  # só os 3 últimos meses, todos preenchidos
            serie = ult_cvm
            fonte_rend = 'CVM, informe mensal (DY do mês × VP)'
            avisos.append('Rendimento pela CVM (DY mensal × VP): aproximação dos avisos de rendimento.')
    ult3 = [v for _, v in serie[-3:]]
    rend = sum(ult3) / len(ult3) * 12 if ult3 else 0.0
    rend12 = sum(v for _, v in serie[-12:]) if len(serie) >= 12 else None

    # recorrente 12m (trimestral, regime de caixa, sem ganho na venda de imóveis e títulos)
    rec, res12 = None, 0.0
    tri = [r for r in trimestral('resultado_contabil_financeiro', cnpj) if r['Data_Referencia'][5:7] in ('03', '06', '09', '12')]
    tri = {r['Data_Referencia'][:7]: r for r in tri}
    qs = sorted(tri)[-4:]
    if len(qs) == 4:
        cot_mes = {r['Data_Referencia'][:7]: num(r['Cotas_Emitidas']) for r in comp}
        rec = res12 = 0.0
        for q in qs:
            r = tri[q]
            k = cot_mes.get(q) or next((cot_mes[m] for m in sorted(cot_mes, reverse=True) if m <= q), cotas)
            ganho = (num(r['Receita_Venda_Investimento_Financeiro']) + num(r['Custo_Investimento_Financeiro'])
                     + num(r['Resultado_Venda_TVM_Financeiro']))
            rec += (num(r['Resultado_Trimestral_Liquido_Financeiro']) - ganho) / k
            res12 += num(r['Resultado_Trimestral_Liquido_Financeiro']) / k
        ref_tri = f'{qs[0]} a {qs[-1]}'
    else:
        ref_tri = 'n/d'

    if not rend and res12:
        rend = res12
        fonte_rend = f'CVM, informe trimestral (resultado de 12m, {ref_tri})'
        avisos.append(f'Sem avisos de rendimento nem DY mensal recente: usado o resultado de 12m do trimestral ({ref_tri}), defasado.')
    if not rend:
        avisos.append('Sem rendimento disponível: DY esperado e teto do tijolo não calculados.')

    # motor
    motor, gatilho = motor_base, None
    yv = rend / vp if vp else 0.0
    if motor_base == 'tijolo':
        if alav > GATILHO_ALAV:
            motor, gatilho = 'transicao', f'alavancagem {alav:.1%} do ativo (> {GATILHO_ALAV:.0%})'
        elif rend and yv < GATILHO_YIELD_VP:
            motor, gatilho = 'transicao', f'rendimento corrente {yv:.1%} do VP (< {GATILHO_YIELD_VP:.0%})'

    if motor_base == 'tijolo' and rec is not None and rend and rec < ALERTA_RECORRENTE * rend:
        avisos.append(f'Resultado recorrente de 12m (R$ {rec:.2f}/cota, {ref_tri}) é {rec / rend:.0%} do rendimento '
                      f'corrente: distribuição apoiada em ganho de capital ou reservas.')

    if motor == 'tijolo':
        y = YIELD_TETO.get(segmento, YIELD_TETO['padrao'])
        teto = rend / y if rend else 0.0
        conta = f'rendimento corrente R$ {rend:.2f}/cota ÷ {y:.2%} = R$ {teto:.2f}'
    elif motor == 'papel':
        if a.credito is None:
            fator = AGIO_PAPEL_SEM_RG
            avisos.append('Relatório gerencial não lido: ágio do papel limitado a 0% (teto = VP).')
        else:
            fator = next(f for lim, f in AGIO_PAPEL if a.credito <= lim)
        teto = vp * fator
        conta = f'VP R$ {vp:.2f} × {fator:.2f}' + (f' (problema de crédito {a.credito:.1f}% do PL)' if a.credito is not None else '') + f' = R$ {teto:.2f}'
    elif motor == 'fof':
        teto = vp * FATOR_FOF
        conta = f'VP R$ {vp:.2f} × {FATOR_FOF:.2f} = R$ {teto:.2f}'
    else:
        teto = vp * FATOR_TRANSICAO
        conta = f'VP R$ {vp:.2f} × {FATOR_TRANSICAO:.2f} = R$ {teto:.2f}' + (f' (gatilho: {gatilho})' if gatilho else ' (desenvolvimento)')

    dy = rend / a.preco if a.preco and rend else 0.0
    pvp = a.preco / vp if vp else 0.0
    vies = 'Comprar' if teto and a.preco <= teto else 'Aguardar'
    liq_status = 'n/d'
    if a.liquidez is not None:
        liq = a.liquidez * 1e3
        if liq < LIQ_FILTRO:
            liq_status = 'filtro'
            vies = 'Aguardar (liquidez)'
        elif liq < LIQ_MIN:
            liq_status = 'alerta'
            avisos.append('Baixa liquidez (< R$ 1 mi/dia): montar posição aos poucos.')
        else:
            liq_status = 'adequada'

    out = dict(ticker=t, cnpj=cnpj, nome=(mensal('geral', cnpj) or [{}])[-1].get('Nome_Fundo_Classe', ''),
               origem=origem, motor=motor, motor_base=motor_base, segmento=segmento, versao=VERSAO,
               preco=a.preco, teto=round(teto, 2), dy_esperado=round(dy, 4), p_vp=round(pvp, 2), vies=vies,
               distancia_teto=round(a.preco / teto - 1, 4) if teto else None, conta=conta,
               vp=round(vp, 2), ref_vp=ref_vp, cotas=cotas, alavancagem=round(alav, 4), rendimento_corrente=round(rend, 4),
               ultimos_rendimentos=serie[-3:], rendimento_12m=round(rend12, 2) if rend12 else None, fonte_rendimento=fonte_rend,
               recorrente_12m=round(rec, 2) if rec is not None else None, ref_trimestral=ref_tri,
               yield_sobre_vp=round(yv, 4), credito=a.credito, liquidez_mil=a.liquidez, liquidez=liq_status, avisos=avisos)
    if a.json:
        print(json.dumps(out, ensure_ascii=False, default=str))
        return
    print(f"{t} | {out['nome']} | CNPJ {cnpj} ({origem})")
    print(f"MOTOR: {motor}{' (base ' + motor_base + ')' if motor != motor_base else ''} | segmento {segmento}")
    print(f"Preço R$ {a.preco:.2f} | Teto R$ {teto:.2f} | DY esperado {dy:.1%} | P/VP {pvp:.2f} | VIÉS: {vies}")
    print(f'Conta: {conta}')
    print(f"VP R$ {vp:.2f} ({ref_vp}) | alavancagem {alav:.1%} | rendimento corrente R$ {rend:.2f}/cota ({fonte_rend}) | "
          f"últimos: {', '.join(f'{d} R$ {v:.3f}' for d, v in serie[-3:])}")
    print(f"Recorrente 12m: {'n/d' if rec is None else f'R$ {rec:.2f}'} ({ref_tri}) | liquidez: {liq_status}")
    for x in avisos:
        print('AVISO:', x)


if __name__ == '__main__':
    main()
