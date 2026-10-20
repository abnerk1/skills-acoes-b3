---
name: "acoes-financeiras"
description: "Calcula preço justo, preço-teto, DY esperado e viés de bancos listados na B3 (BBAS3, ITUB4, SANB11, BBDC4, ABCB4, BRBI11, BPAC11) pela regra fixa P/VP = (ROE real − g) ÷ (10% − g). Use para valuation de banco; não para seguradoras, corretoras ou holdings."
---

# Financeiras — valuation de bancos (v1.2)

Microskill de cálculo. Entrega um bloco fixo de números; não escreve relatório (isso é da maestrina).

## Quando usar
- Bancos: ROE × patrimônio descreve o negócio (BBAS3, ITUB4, SANB11, BBDC4, ABCB4, BRBI11, BPAC11, BRSR6 etc.).
- Não usar para seguradoras (BBSE3, CXSE3, PSSA3 → Seguradoras), corretoras (WIZC3 → Fluxo normalizado) nem holdings (ITSA4 → Ativos, chamando esta skill só para a parte do banco).

## Regra (fixa, não alterar)
1. ROE de cada ano = lucro atribuído ao controlador ÷ PL do controlador médio (início e fim do ano). Fonte: DFP consolidada na CVM.
2. ROE nominal = média aritmética dos últimos 10 exercícios completos.
3. IPCA = média aritmética dos mesmos 10 anos (IBGE).
4. ROE real = (1 + ROE nominal) ÷ (1 + IPCA) − 1.
5. Payout = política declarada no RI; sem política, média de 5 anos calculada pela CVM (dividendos + JCP pagos ao controlador ÷ lucro do controlador).
6. g = (1 − payout) × ROE real, limitado a 3% real e nunca negativo (v1.1). O teto de 3% evita que a fórmula exploda quando g se aproxima de 10%.
7. P/VP justo = (ROE real − g) ÷ (10% − g).
8. VPA = PL do controlador mais recente (último ITR) ÷ ações ex-tesouraria.
9. Preço justo = P/VP justo × VPA × ações por ativo (units: SANB11 = 2, BRBI11 = 3).
10. Preço-teto = preço justo × 0,8 (margem fixa de 20%).
11. Bear / bull = ROE real −3 p.p. / +3 p.p.
12. DY esperado = payout × (ROE nominal × PL atual) ÷ ações ÷ preço atual.
13. Viés = "Comprar" se preço atual ≤ preço-teto; senão "Aguardar".

Ke de 10% real, margem de 20%, janela de 10 anos e g máximo de 3% são constantes. Não usar o ROE "ajustado" ou "recorrente" divulgado pelo banco: a conta usa sempre o consolidado da CVM, igual para todos os bancos.

## Armadilha de dividendo e status da tese (v1.2)
Só avisos: nada aqui muda preço justo, teto ou viés.
- **Armadilha de dividendo:** proventos pagos (dividendos + JCP, DFC) somados nos últimos 3 exercícios acima do lucro do controlador no mesmo período (payout > 100%). Três anos, e não um, para não confundir dividendo extraordinário de capital excedente com distribuição insustentável.
- **Status da tese**, separado do viés, calculado pelo script nesta ordem:
  - **Revisão crítica:** armadilha de dividendo, ou preço justo zerado pela regra.
  - **Monitoramento:** ROE dos últimos 12 meses a mais de 5 p.p. da média de 10 anos; ROE médio dos últimos 3 anos a mais de 3 p.p. da média de 10 anos (v1.2; acima = preço justo pode estar conservador, ver o bull; abaixo = pode estar otimista, ver o bear); menos de 10 anos de dados.
  - **Consolidada:** nenhum dos casos acima.
  O viés diz se o preço está bom; o status diz se a tese está de pé.
- Em bancos não se usa a checagem de caixa: FCO de banco mistura depósitos e crédito e não mede capacidade de pagar proventos.

## Passos
1. **Identificar** o nome da companhia como aparece na CVM (ex.: "BCO BRASIL S.A", "ITAU UNIBANCO HOLDING", "BCO SANTANDER (BRASIL)", "BCO BRADESCO", "BCO ABC BRASIL") e quantas ações compõem o ativo negociado.
2. **Cotação atual**: uma única fonte, com data. Registrar fonte e data.
3. **Payout**: se o banco tiver política declarada no RI, passar com `--payout`. Sem política, rodar sem `--payout`: o script calcula a média de 5 anos pela CVM. Se nem isso existir, g = 0 e DY "n/d", com aviso.
4. **Rodar o cálculo**: salvar o script abaixo como `financeiras.py` e executar:
   `python3 financeiras.py --empresa "BCO BRASIL S.A" --preco 24.64 --payout 0.30 --acoes-por-ativo 1`
   O script baixa as DFPs e ITRs da CVM (dados.cvm.gov.br) e o IPCA do IBGE. Não refazer contas à mão.
5. **Tratar avisos de dados**, nesta ordem: RI do banco → PDF da DFP/ITR na CVM → pedir o PDF ao usuário. Reexecutar com:
   - `--manual "ANO=LUCRO;PL_FIM"` (R$ bi) para cada exercício ausente;
   - `--pl-atual X --data-pl AAAA-MM-DD` se o PL mais recente tiver mais de 9 meses;
   - `--acoes N` se a quantidade de ações estiver errada.
   Se mesmo assim faltar dado, entregar o resultado com o aviso. Dado faltante nunca bloqueia a entrega.
6. **Entregar** o bloco de saída.

## Saída (formato fixo)
```
[TICKER] — Financeiras v1.2 — cotação de DD/MM/AAAA (fonte)
Preço atual:  R$ X
Preço justo:  R$ X   (bear R$ X | bull R$ X)
Preço-teto:   R$ X
DY esperado:  X%     (payout X%, fonte)
Viés:         Comprar | Aguardar
Status da tese: Consolidada | Monitoramento (motivos) | Revisão crítica (motivos)
Memória de cálculo: ROE nominal médio X% | IPCA médio X% | ROE real X% | payout X% | g X% | P/VP justo X | VPA R$ X (data)
Avisos: (lista do script, se houver)
```
Incluir a tabela anual de ROE impressa pelo script quando o usuário pedir detalhe.

## Regras gerais
- Isolamento: nunca consultar nem citar tese ou preço-teto de casas de análise (research independente, bancos, corretoras). Só dados primários (CVM, RI, IBGE) e cotação.
- Premissas neutras: não acrescentar folga além dos 20%.
- Não ajustar a regra caso a caso; divergências viram aviso, não exceção.

## Script
```python
#!/usr/bin/env python3
"""Microskill Financeiras (v1.2): preço justo e preço-teto de bancos.

Fontes: CVM dados abertos (DFP/ITR consolidados) e IBGE (IPCA).
Regra v1.1:
  ROE anual        = lucro atribuído ao controlador / PL do controlador médio (início e fim do ano)
  ROE nominal      = média aritmética dos últimos 10 anos completos
  IPCA             = média aritmética dos mesmos 10 anos
  ROE real         = (1 + ROE nominal) / (1 + IPCA) - 1
  Payout           = política declarada (--payout) ou média de 5 anos da CVM (dividendos+JCP pagos / lucro)
  g (v1.1)         = min((1 - payout) x ROE real; 3%), nunca negativo
  P/VP justo       = (ROE real - g) / (10% - g)
  Preço justo      = P/VP justo x VPA x ações por ativo
  Preço-teto       = Preço justo x 0,8
  Bear / Bull      = ROE real -3 p.p. / +3 p.p.
  DY esperado      = payout x (ROE nominal x PL atual) / ações / preço atual
Uso:
  python3 financeiras.py --empresa "BCO BRASIL" --preco 24.64 --payout 0.30 [--acoes-por-ativo 1]
"""
import argparse, csv, gzip, io, json, os, sys, time, unicodedata, urllib.request, zipfile, datetime

KE = 0.10
MARGEM = 0.20
G_MAX = 0.03  # crescimento real máximo na perpetuidade
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
    return ll, pl_c, acoes, div


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
    ap.add_argument('--empresa', required=True, help='trecho do nome na CVM, ex.: "BCO BRASIL", "ITAU UNIBANCO HOLDING"')
    ap.add_argument('--preco', type=float, required=True, help='cotação atual do ativo negociado')
    ap.add_argument('--payout', type=float, default=None, help='política de payout declarada (0 a 1); sem ela, informar a média de 5 anos do RI')
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
    anos_dfp, divs = [], {}
    for ano in range(hoje, hoje - 13, -1):
        z = baixar('DFP', ano)
        if not z:
            continue
        if cnpj is None:
            cnpj, nome = achar_cnpj(a.empresa, z, 'DFP')
            if cnpj is None:
                continue
        l, p, ac, dv = coletar(cnpj, z, 'DFP', ano)
        for k, v in dv.items():
            divs.setdefault(k, v)
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
            l, p, ac, _ = coletar(cnpj, z, 'ITR', ano)
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
        if lucro is None or ini is None or fim is None:
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
            avisos.append('Payout indisponível: g = 0 e DY n/d. Informar --payout a partir do RI.')

    def crescimento(rr):
        if payout is None or rr <= 0:
            return 0.0
        return min((1 - payout) * rr, G_MAX)

    def pvp(rr):
        if rr <= 0:
            return 0.0
        g = crescimento(rr)
        return (rr - g) / (KE - g)

    def justo(rr):
        return pvp(rr) * vpa * a.acoes_por_ativo

    pj = justo(roe_real)
    teto = pj * (1 - MARGEM)
    lucro_norm = roe_nom * pl_atual
    dy = payout * lucro_norm / n_acoes * a.acoes_por_ativo / a.preco if payout is not None else None
    vies = 'Comprar' if a.preco <= teto else 'Aguardar'

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
    print(f'g = min((1 - payout) x ROE real; {G_MAX:.0%}): {crescimento(roe_real):.2%}')
    print(f'P/VP justo = (ROE real - g) / ({KE:.0%} - g): {pvp(roe_real):.2f}')
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
    roe_3a = sum(r for _, r in roes[-3:]) / len(roes[-3:])
    if roe_3a - roe_nom > 0.03:
        avisos.append(f'ROE médio dos últimos 3 anos ({roe_3a:.1%}) acima da média de 10 anos ({roe_nom:.1%}): '
                      'o preço justo pode estar conservador se o novo patamar se mantiver; ver o cenário bull.')
    elif roe_nom - roe_3a > 0.03:
        avisos.append(f'ROE médio dos últimos 3 anos ({roe_3a:.1%}) abaixo da média de 10 anos ({roe_nom:.1%}): '
                      'o preço justo pode estar otimista se o novo patamar se mantiver; ver o cenário bear.')
    # Armadilha de dividendo (v1.2): só aviso, não muda o número
    armadilha = []
    anos_d = [y for y in range(ultimo - 2, ultimo + 1) if f'{y}-12-31' in divs and (f'{y}-01-01', f'{y}-12-31') in ll]
    if len(anos_d) == 3:
        pago_d = sum(divs[f'{y}-12-31'] for y in anos_d)
        lucro_d = sum(ll[(f'{y}-01-01', f'{y}-12-31')][1] for y in anos_d)
        if pago_d > max(lucro_d, 0.0):
            armadilha.append(f'proventos pagos em {anos_d[0]}-{anos_d[-1]} (R$ {pago_d / 1e9:.2f} bi) acima do lucro do período (R$ {lucro_d / 1e9:.2f} bi), payout > 100%')
    if armadilha:
        avisos.append('Possível armadilha de dividendo: ' + '; '.join(armadilha) + '. O DY esperado pode não se sustentar.')

    # Status da tese (v1.2): separado do viés. Crítica > Monitoramento > Consolidada
    criticos = (['armadilha de dividendo'] if armadilha else []) + (['preço justo zerado pela regra'] if pj <= 0 else [])
    MONITOR = [('ROE dos últimos 12 meses longe da média', roe_ltm is not None and abs(roe_ltm - roe_nom) > 0.05),
               ('ROE dos últimos 3 anos longe da média', abs(roe_3a - roe_nom) > 0.03),
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