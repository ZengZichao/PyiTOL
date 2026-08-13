"""Extract taxonomy from embedded tip labels of the LACA clock tree (NEXUS).

Tip labels follow the pattern:
  <accession>_d__<domain>_superphylum__<sp>_p__<phylum>_c__<class>_o__<order>_f__<family>_g__<genus>

Outputs a CSV compatible with `pyitol taxonomy monophyly` (id column uses the
tree tip labels exactly as PyiTOL reports them (underscores preserved).
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

import dendropy

RANK_ORDER = ['domain', 'phylum', 'class', 'order', 'family', 'genus']
MARKER = re.compile(r'_(superphylum|d|p|c|o|f|g)__')


def parse_label(label: str) -> dict[str, str]:
    """Parse one embedded-taxonomy tip label into a rank dict."""
    result = {rank: '' for rank in RANK_ORDER}
    result['superphylum'] = ''
    parts = MARKER.split(label)
    # parts: [accession, marker1, value1, marker2, value2, ...]
    for i in range(1, len(parts) - 1, 2):
        marker, value = parts[i], parts[i + 1]
        if marker == 'superphylum':
            result['superphylum'] = '' if value == 'none' else value
        elif marker in ('d', 'p', 'c', 'o', 'f', 'g'):
            rank = {'d': 'domain', 'p': 'phylum', 'c': 'class',
                    'o': 'order', 'f': 'family', 'g': 'genus'}[marker]
            result[rank] = '' if value == 'none' else value.replace('_', ' ')
    return result


def main() -> None:
    tree_path = Path('benchmarks/data/FigTree_withLACA_CLK_95CI.tree.recover')
    out_path = Path('benchmarks/data/laca_tree_taxonomy.csv')
    tree = dendropy.Tree.get(path=str(tree_path), schema='nexus',
                             suppress_internal_node_taxa=True)
    tip_labels = [n.taxon.label for n in tree.leaf_node_iter()]
    rows = []
    for tip in tip_labels:
        original = tip.replace(' ', '_')
        parsed = parse_label(original)
        row = {'id': original}
        row.update({rank: parsed[rank] for rank in RANK_ORDER})
        rows.append(row)
    with out_path.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=['id'] + RANK_ORDER)
        writer.writeheader()
        writer.writerows(rows)
    print(f'wrote {len(rows)} rows -> {out_path}')
    genera = {r['genus'] for r in rows if r['genus']}
    print(f'non-empty genera: {len(genera)}')


if __name__ == '__main__':
    main()
