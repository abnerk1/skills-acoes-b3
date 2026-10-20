# Brazilian Stock and REIT Valuation Skills (B3)

A set of AI *skills* that does an equity analyst's job: it identifies the type of asset, applies the right valuation method and delivers a **price ceiling with a margin of safety**, an **expected dividend yield**, a **Buy/Hold call** and a fixed-format report. For stocks, it also delivers a **fair price**.

Everything is a fixed quantitative rule computed from public data (CVM, FundosNet and IBGE). No guesswork, and no copying of third-party research.

> Santos Dumont published the plans for his Demoiselle airplane so anyone could build and improve it. This repository follows the same spirit: the method is open to be used, challenged and improved.

## What's inside

The skills, reports and command-line flags are in Portuguese because they analyze Brazilian assets with Brazilian data sources. This README and the contributing guide are in English.

### Stocks

| Skill | Covers | Method | Version |
|---|---|---|---|
| [`analise-de-acoes-b3`](skills/analise-de-acoes-b3/SKILL.md) | Entry point (orchestrator) | Classifies the ticker, picks the micro-skill, applies the liquidity filter and writes the report | v1.1 |
| [`acoes-financeiras`](skills/acoes-financeiras/SKILL.md) | Banks | P/B = (real ROE − g) ÷ (10% − g) | v1.2 |
| [`acoes-fluxo-normalizado`](skills/acoes-fluxo-normalizado/SKILL.md) | Commodities, industrials, utilities, oil, insurance, telecom | Normalized 10-year real ROE × book value, with growth and an optional finite horizon | v1.2 |
| [`acoes-crescimento`](skills/acoes-crescimento/SKILL.md) | Companies that reinvest their earnings (retail, agribusiness, leasing, exchanges) | Two-stage fair P/E based on ROIIC | v1.1 |
| [`acoes-ativos`](skills/acoes-ativos/SKILL.md) | Holding companies, homebuilders, farmland, venture capital | NAV / sum of the parts | v1.1 |

The orchestrator computes nothing itself: every number comes from a micro-skill's script.

### Real estate investment funds (FIIs, Brazil's REITs)

| Skill | Covers | Method | Version |
|---|---|---|---|
| [`analise-de-fiis`](skills/analise-de-fiis/SKILL.md) | Any FII, infrastructure debenture fund (FI-Infra) or agribusiness fund (Fiagro) listed on B3 | One skill with six engines; the output is a price ceiling only, with no fair price | v1.1 |

| Engine | Covers | Price ceiling |
|---|---|---|
| Brick-and-mortar | offices, logistics, shopping malls, urban retail, hybrids, hotels | current distribution ÷ 8.75% (÷ 10% for corporate offices and hotels), capped at 1.05 × book value |
| Paper | FIIs that hold real estate receivables (CRIs) | book value × 1.05 / 1.00 / 0.95, based on the credit problems in the manager's report (≤ 5%, 5–10%, > 10% of NAV) |
| Fund of funds | FIIs that hold units of other FIIs | book value × 1.00 |
| Transition | brick-and-mortar funds with leverage > 30% of assets or a distribution < 6% of book value; development funds | book value × 0.80 |
| FI-Infra | funds of tax-exempt infrastructure debentures (e.g. JURO11) | book value × the paper-fund factor |
| Fiagro (credit) | agribusiness funds holding mostly CRAs and agricultural credit (e.g. KNCA11, SNAG11) | book value × the paper-fund factor |
| Fiagro (farmland) | agribusiness funds holding mostly farmland | same as brick-and-mortar |

The current distribution is the average of the last three distribution notices × 12. On the calibration set (21 FIIs, prices as of 10/14/2026), the Buy call matched a professional reference portfolio in 21 of 21 cases. The v1.1 cap at 1.05 × book value binds on five brick-and-mortar funds in that set and changes none of the 21 calls.

## Common rules (stocks)

- Cost of equity of **10% real**.
- **Fixed 20% margin of safety**: price ceiling = fair price × 0.8.
- Neutral assumptions. No projections of new stores, capacity or company guidance.
- Missing data becomes a warning and never blocks the report.
- **Source isolation**: only CVM, IBGE, company investor relations and the share price. Third-party theses, price targets and assumptions stay out.
- The rule is fixed. Exceptions become warnings, never case-by-case adjustments.
- **Dividend-trap warning** (v1.1+): dividends paid over the last three years above net income for the same period (payout > 100%). For non-financials, a separate warning flags free cash flow (operating cash flow − capex) that did not cover the dividends paid.
- **Thesis status**, separate from the Buy/Hold call: *Consolidada* (no quality warnings), *Monitoramento* (a quality warning to watch, such as recent ROE far from the 10-year average) or *Revisão crítica* (dividend trap or zero fair price). The call says whether the price is attractive; the status says whether the thesis still holds.

## Common rules (FIIs)

- No fair price: the margin of safety is built into each engine's price ceiling.
- "Buy" when the price is at or below the ceiling; below R$ 200 thousand of daily liquidity, the call becomes "Hold (liquidity)".
- **Source isolation**: only CVM, FundosNet (the fund's own filings), the fund manager's report and the share price.
- For paper funds, FI-Infra and credit Fiagros, the only figure read by hand is the credit problem from the manager's report (% of NAV), with the page number recorded.
- **Dividend-trap warning**: recurring income over the last 12 months below 80% of the current distribution.
- **Thesis status**: *Revisão crítica* for a dividend trap, a downgrade to the transition engine or credit problems above 10% of NAV; *Monitoramento* for a ceiling capped at book value, an unread manager's report, overdue Fiagro receivables ≥ 5% of NAV and similar flags; *Consolidada* otherwise.

## How to use

**As skills.** Each folder in `skills/` is a skill in the `SKILL.md` format. Load them into a compatible AI client and start with `analise-de-acoes-b3`.

**From the terminal.** Each skill ships its `.py` script next to the `SKILL.md`. The scripts use only the Python 3 standard library, with no dependencies. The stock scripts download annual (DFP) and quarterly (ITR) filings from [CVM](https://dados.cvm.gov.br) and the IPCA inflation index from [IBGE](https://servicodados.ibge.gov.br), with a cache in `~/.cache/cvm`. The FII script downloads CVM's monthly and quarterly FII reports and the distribution notices from [FundosNet](https://fnet.bmfbovespa.com.br), with a cache in `~/.cache/fii`.

```bash
# 1. Classify the ticker (liquidity in R$ thousands per day)
python3 skills/analise-de-acoes-b3/classificar.py --ticker ITSA4 --preco 15.97 --liquidez 525625

# 2. Run the recommended micro-skill (example: a bank)
python3 skills/acoes-financeiras/financeiras.py --empresa "BCO BRASIL S.A" --preco 24.64 --payout 0.30

# FIIs: brick-and-mortar
python3 skills/analise-de-fiis/fii.py --ticker HGLG11 --preco 156.42 --liquidez 22339

# FIIs: paper, with the credit problem (% of NAV) read from the manager's report
python3 skills/analise-de-fiis/fii.py --ticker MXRF11 --preco 9.35 --liquidez 15000 --credito 1.8
```

The prices above are illustrative. Use the day's price from a single source, and record the date.

## Known limitations

- The method uses CVM's consolidated accounting ROE, the same for every company. It does not see adjusted recurring earnings, cycles outside the 10-year window or company projections. For banks whose ROE has moved to a new level, this makes the fair price conservative or optimistic; the micro-skill flags it when the last three years sit more than 3 points away from the 10-year average.
- The fixed ticker table in `classificar.py` reflects the project's original design. Tickers outside it fall back to the automatic rule.
- The scripts depend on the layout of CVM's open data. A layout change can break the parsing.
- Price and liquidity are entered by hand (default source: Status Invest).
- FIIs: the current distribution assumes today's level holds. FundosNet sometimes does not respond; the script falls back to CVM's monthly yield or quarterly results and says so.
- FIIs: manager reports change layout from one asset manager to the next, so the credit problem for paper funds is read by hand.
- FI-Infra funds do not publish structured distribution notices on FundosNet, so their distributions are entered by hand; the price ceiling does not depend on them.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Welcome ideas: new micro-skills (insurers, sanitation), new FIIs in the fixed table, test cases, fixes to CVM parsing and improvements to the report.

## Related projects

- [global-equity-valuation](https://github.com/abnerk1/global-equity-valuation): the same rules-based approach for US stocks and ADRs.
- [anchor-and-tilt](https://github.com/abnerk1/anchor-and-tilt): a deterministic ETF allocation rubric.

## Disclaimer

This project is educational. Each report is generated by fixed quantitative rules from public data and **is not personalized investment advice**. Past returns, portfolio allocation, fixed income and entry prices are out of scope. Investment decisions are the investor's responsibility.

## License

[MIT](LICENSE).
