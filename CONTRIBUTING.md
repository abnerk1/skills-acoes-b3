# Contributing

Thanks for wanting to improve the method. A few rules keep the project consistent.

## Non-negotiables

1. **`SKILL.md` is the source of truth.** Each skill's `.py` script is a copy of the `## Script` block in its `SKILL.md`. Edit the `SKILL.md`, then run:
   ```bash
   python3 tools/sync_scripts.py --write
   ```
   CI fails the pull request if the two diverge.
2. **Source isolation.** Only primary data (CVM, IBGE, company investor relations, FundosNet and the FII manager's report) and the share price. Do not open a pull request that relies on a third-party thesis, price target or assumption, or on paywalled data.
3. **Neutral assumptions.** The method does not project what the company promises. A change that adds a projection has to justify why.
4. **Missing data becomes a warning**, never an error that blocks the report.

## Proposing a rule change

Each micro-skill's rule is fixed so results stay comparable across companies. That is why a method change ships as a **new version**, not a quiet tweak:

- Open an issue describing the problem, with two or three tickers where the current rule gets it wrong and the result you expected.
- In the pull request, bump the version in the `SKILL.md` title (for example, v1.1 → v1.2) and show the before/after numbers.
- Do not bend a rule for a single case. If a case falls outside the method, the right answer is a warning.

## Other welcome contributions

- **Test cases**: ticker, price date, the command you ran and the expected output.
- **Fixes to CVM parsing** (accounts that get renamed, companies without consolidated statements, share counts reported in thousands).
- **New micro-skills** (insurers, sanitation) and **new FIIs in the fixed table** of `analise-de-fiis` (ticker, CNPJ and engine). Follow the format of the existing ones: when to use, fixed rule, steps, fixed-format output, script.
- Improvements to the `analise-de-acoes-b3` report that keep the fixed format.

## Pull request checklist

- [ ] `python3 tools/sync_scripts.py` passes
- [ ] The script runs end to end on at least one real ticker (say which one and the date)
- [ ] No source other than CVM, IBGE, investor relations, FundosNet and the share price
- [ ] No personal data, API keys or credentials in the diff
