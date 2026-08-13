"""Cross-validate PyiTOL monophyly calls on the LACA tree against ete3/ete4."""
from __future__ import annotations
import csv
from pathlib import Path

import dendropy

TREE = 'benchmarks/data/FigTree_withLACA_CLK_95CI.tree.recover'
TAX = 'benchmarks/data/laca_tree_taxonomy.csv'
PYI = 'benchmarks/data/laca_monophyly_genus_strict.csv'

# Build genus -> member set
groups: dict[str, list[str]] = {}
with open(TAX) as fh:
    for row in csv.DictReader(fh):
        g = row['genus']
        if g:
            groups.setdefault(g, []).append(row['id'])

# Load PyiTOL results
pyi: dict[str, str] = {}
with open(PYI) as fh:
    for row in csv.DictReader(fh):
        pyi[row['group']] = row['status']

# Export to newick for ete
tree = dendropy.Tree.get(path=TREE, schema='nexus', suppress_internal_node_taxa=True)
nwk = tree.as_string(schema='newick')

# --- ete3 ---
from ete3 import Tree as E3Tree
t3 = E3Tree(nwk, format=1)
# --- ete4 ---
import ete4
t4 = ete4.Tree(nwk)

def norm(name: str) -> str:
    # ete3/ete4 convert underscores to spaces and may keep quoting characters
    return name.replace('_', ' ').strip("'\"")


# Normalize leaf names once so member sets match
for n in t3.get_leaves():
    n.name = norm(n.name)
for n in t4.leaves():
    n.name = norm(n.name)


def ete_call(t, members, engine):
    values = {norm(m) for m in members}
    try:
        if engine == 'ete3':
            is_mono, ctype, leaves = t.check_monophyly(values=values, target_attr='name')
            return ctype
        else:
            is_mono, ctype, leaves = t.check_monophyly(values=values, prop='name')
            return ctype
    except Exception as e:
        return f'ERR:{e}'

# Only report non-monophyletic by PyiTOL plus a sample of monophyletic controls
focus = [g for g, s in pyi.items() if s != 'monophyletic']
print(f'Non-monophyletic genera per PyiTOL: {focus}')
print(f'{"Genus":<22}{"PyiTOL":<20}{"ete3":<16}{"ete4":<16}{"members"}')
for g in focus:
    e3 = ete_call(t3, groups[g], 'ete3')
    e4 = ete_call(t4, groups[g], 'ete4')
    print(f'{g:<22}{pyi[g]:<20}{str(e3):<16}{str(e4):<16}{len(groups[g])}')

# Controls: 5 monophyletic genera
mono = [g for g, s in pyi.items() if s == 'monophyletic'][:5]
print('\nMonophyletic controls:')
for g in mono:
    e3 = ete_call(t3, groups[g], 'ete3')
    e4 = ete_call(t4, groups[g], 'ete4')
    print(f'{g:<22}{pyi[g]:<20}{str(e3):<16}{str(e4):<16}{len(groups[g])}')

# Aggregate binary agreement (mono vs non-mono) against ete3 and ete4
stats = {'ete3_all': [0, 0], 'ete3_multi': [0, 0], 'ete4_all': [0, 0]}
disagreements = {'ete3': [], 'ete4': []}
for g, members in groups.items():
    e3 = str(ete_call(t3, members, 'ete3'))
    e4 = str(ete_call(t4, members, 'ete4'))
    py_mono = (pyi[g] == 'monophyletic')
    stats['ete3_all'][1] += 1
    stats['ete4_all'][1] += 1
    if len(members) > 1:
        stats['ete3_multi'][1] += 1
        if py_mono == (e3 == 'monophyletic'):
            stats['ete3_multi'][0] += 1
        else:
            disagreements['ete3'].append((g, len(members), pyi[g], e3))
    if py_mono == (e3 == 'monophyletic'):
        stats['ete3_all'][0] += 1
    else:
        disagreements['ete3'].append((g, len(members), pyi[g], e3)) if False else None
    if py_mono == (e4 == 'monophyletic'):
        stats['ete4_all'][0] += 1
    else:
        disagreements['ete4'].append((g, len(members), pyi[g], e4))
for k, (ok, tot) in stats.items():
    print(f'\nBinary agreement PyiTOL vs {k}: {ok}/{tot} ({100*ok/tot:.1f}%)')
for k, lst in disagreements.items():
    print(f'  {k} discrepancies:', lst)
