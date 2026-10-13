#!/usr/bin/env python3
"""Mantém o script .py de cada skill idêntico ao bloco ```python do SKILL.md.

O SKILL.md é a fonte da verdade (é o que o Claude lê). O .py ao lado existe para
rodar, testar e revisar o código com ferramentas normais.

Uso:
  python3 tools/sync_scripts.py            # só confere; sai com erro se houver divergência
  python3 tools/sync_scripts.py --write    # regrava os .py a partir dos SKILL.md
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent / 'skills'
SCRIPTS = {
    'analise-de-acoes-b3': 'classificar.py',
    'acoes-financeiras': 'financeiras.py',
    'acoes-fluxo-normalizado': 'fluxo.py',
    'acoes-crescimento': 'crescimento.py',
    'acoes-ativos': 'ativos.py',
}
BLOCO = re.compile(r'^## Script\s*\n```python\n(.*?)\n```\s*$', re.S | re.M)


def extrair(skill_md: Path) -> str:
    m = BLOCO.search(skill_md.read_text(encoding='utf-8'))
    if not m:
        sys.exit(f'{skill_md}: bloco "## Script" com ```python não encontrado.')
    return m.group(1) + '\n'


def main() -> int:
    escrever = '--write' in sys.argv
    divergentes = []
    for skill, nome in SCRIPTS.items():
        codigo = extrair(RAIZ / skill / 'SKILL.md')
        destino = RAIZ / skill / nome
        if escrever:
            destino.write_text(codigo, encoding='utf-8')
            print(f'gravado  {destino.relative_to(RAIZ.parent)}')
        elif not destino.exists() or destino.read_text(encoding='utf-8') != codigo:
            divergentes.append(destino.relative_to(RAIZ.parent))
    if divergentes:
        print('Divergência entre SKILL.md e o script:')
        for d in divergentes:
            print(f'  - {d}')
        print('Edite o SKILL.md e rode: python3 tools/sync_scripts.py --write')
        return 1
    if not escrever:
        print('OK: scripts idênticos aos blocos dos SKILL.md.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
