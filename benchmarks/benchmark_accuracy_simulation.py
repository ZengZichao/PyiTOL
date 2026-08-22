"""Simulation-based accuracy benchmark for three-way monophyly classification.

Ground truth is constructed *by topology construction* (non-circular).  Two
tree regimes are evaluated:

1. **Balanced regime** — deterministic fully balanced binary trees (2,048 and
   8,192 leaves; 5 seeds each).  Six engineered categories:

   - ``monophyletic``: members form a complete clade;
   - ``paraphyletic``: a complete clade minus one whole subclade nested one
     level inside a sibling (exactly one mixed child of the LCA — note that on
     strictly binary trees every paraphyletic group has at least one mixed
     child; the zero-mixed-child case arises only with polytomies and is
     covered by the sandbox tests of main-text Table 2);
   - ``paraphyletic_nested``: same shape with the removed subclade nested two
     levels deep (robustness of the one-mixed-child path to nesting depth);
   - ``polyphyletic``: members interleaved across two sibling clades (two
     mixed children);
   - ``incomplete_sampling``: a complete clade plus phantom members absent
     from the tree;
   - ``data_insufficient``: paraphyletic shape whose extra tips carry *no*
     taxonomy row at all (unmapped extras must trigger ``data_insufficient``).

2. **Random regime** — seeded random-bifurcating (Yule-like, unbalanced)
   binary trees (2,048 and 4,096 leaves; 3 seeds each) with the same six
   categories constructed on disjoint clades of 16-64 leaves.

In the balanced regime every leaf carries a group assignment except the
deliberately unmapped extras of the ``data_insufficient`` category; in the
random regime all non-category leaves receive a background filler group so
that unmapped extras occur only by construction.  Each replicate is evaluated
end-to-end through the ``pyitol taxonomy monophyly`` CLI (strict polytomy
mode) and scored against the engineered labels.
"""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from _bench_utils import bench_provenance

OUT_DIR = Path(__file__).parent / 'accuracy_results'
OUT_DIR.mkdir(exist_ok=True)

CLASSES = ['monophyletic', 'paraphyletic', 'polyphyletic',
           'incomplete_sampling', 'data_insufficient']


# ---------------------------------------------------------------------------
# Tree builders
# ---------------------------------------------------------------------------

def build_balanced_newick(n: int) -> str:
    """Deterministic fully balanced binary tree with leaf labels t0..t{n-1}."""
    labels = [f't{i}' for i in range(n)]

    def rec(items: list[str]) -> str:
        if len(items) == 1:
            return items[0]
        mid = len(items) // 2
        return f'({rec(items[:mid])},{rec(items[mid:])}):1.0'

    return rec(labels) + ';'


def build_tree_dict(n: int) -> dict:
    """Mirror of build_balanced_newick as a nested dict for leaf enumeration."""
    labels = [f't{i}' for i in range(n)]

    def rec(items: list[str]) -> dict:
        if len(items) == 1:
            return {'children': [], 'leaves': items}
        mid = len(items) // 2
        left, right = rec(items[:mid]), rec(items[mid:])
        return {'children': [left, right], 'leaves': left['leaves'] + right['leaves']}

    return rec(labels)


def subtree_leaves(root: dict, depth: int) -> list[dict]:
    """Collect all subtree-root nodes at a given depth of the balanced tree."""
    level = [root]
    for _ in range(depth):
        level = [c for node in level for c in node['children']]
    return level


def build_random_tree(n: int, rng) -> tuple[str, dict]:
    """Seeded random-bifurcating (Yule-like) tree; returns (newick, dict)."""
    clusters = [{'children': [], 'leaves': [f't{i}']} for i in range(n)]
    while len(clusters) > 1:
        i = rng.randrange(len(clusters))
        j = rng.randrange(len(clusters) - 1)
        if j >= i:
            j += 1
        a, b = clusters[i], clusters[j]
        merged = {'children': [a, b], 'leaves': a['leaves'] + b['leaves']}
        for idx in sorted((i, j), reverse=True):
            clusters.pop(idx)
        clusters.append(merged)
    root = clusters[0]

    def to_nwk(node: dict) -> str:
        if not node['children']:
            return node['leaves'][0]
        return f'({to_nwk(node["children"][0])},{to_nwk(node["children"][1])}):1.0'

    return to_nwk(root) + ';', root


def find_disjoint_units(root: dict, min_sz: int = 16, max_sz: int = 64) -> list[dict]:
    """Greedy collection of disjoint clades with both children internal and
    size within [min_sz, max_sz] (for the random regime).  Candidates are
    processed smallest-first so that nested candidates never overlap."""
    candidates: list[dict] = []

    def rec(node: dict) -> None:
        if not node['children']:
            return
        for c in node['children']:
            rec(c)
        size = len(node['leaves'])
        a, b = node['children']
        if min_sz <= size <= max_sz and a['children'] and b['children']:
            candidates.append(node)

    rec(root)
    candidates.sort(key=lambda nd: len(nd['leaves']))
    units: list[dict] = []
    used: set[str] = set()
    for node in candidates:
        leaves = set(node['leaves'])
        if not (leaves & used):
            units.append(node)
            used.update(leaves)
    return units


# ---------------------------------------------------------------------------
# Category constructors (operate on a sibling pair a, b of subtrees)
# ---------------------------------------------------------------------------

def assign_category(cat: str, a: dict, b: dict, gid: int,
                    assignment: dict[str, str], expected: dict[str, str],
                    subgroup_expect: dict[str, int]) -> None:
    """Engineer one target group G{gid} (+ private filler where needed)."""
    group = f'G{gid:04d}'
    filler = f'F{gid:04d}'
    leaves_a, leaves_b = a['leaves'], b['leaves']

    if cat == 'monophyletic':
        for leaf in leaves_a:
            assignment[leaf] = group
        for leaf in leaves_b:
            assignment[leaf] = filler
        expected[group] = 'monophyletic'
    elif cat == 'paraphyletic':
        # Remove one whole child subclade of B (one mixed child of the LCA).
        removed = set(b['children'][0]['leaves'])
        for leaf in leaves_a:
            assignment[leaf] = group
        for leaf in leaves_b:
            assignment[leaf] = filler if leaf in removed else group
        expected[group] = 'paraphyletic'
    elif cat == 'paraphyletic_nested':
        # Remove a subclade nested two levels inside B (still one mixed
        # child, but extras sit deeper); requires B's first child internal.
        bc0 = b['children'][0]
        removed = set(bc0['children'][0]['leaves'])
        for leaf in leaves_a:
            assignment[leaf] = group
        for leaf in leaves_b:
            assignment[leaf] = filler if leaf in removed else group
        expected[group] = 'paraphyletic_nested'
    elif cat == 'polyphyletic':
        # Interleave: half of A + half of B in the target group (balanced
        # regime only, where list halves coincide with whole child clades).
        half_a = len(leaves_a) // 2
        half_b = len(leaves_b) // 2
        for leaf in leaves_a[:half_a] + leaves_b[:half_b]:
            assignment[leaf] = group
        for leaf in leaves_a[half_a:] + leaves_b[half_b:]:
            assignment[leaf] = filler
        expected[group] = 'polyphyletic'
        subgroup_expect[group] = 2
    elif cat == 'polyphyletic_clade':
        # Clade-based interleaving for unbalanced trees: one whole subclade
        # of A plus one whole subclade of B -> exactly two maximal subgroups.
        for leaf in a['children'][0]['leaves'] + b['children'][0]['leaves']:
            assignment[leaf] = group
        for leaf in a['children'][1]['leaves'] + b['children'][1]['leaves']:
            assignment[leaf] = filler
        expected[group] = 'polyphyletic'
        subgroup_expect[group] = 2
    elif cat == 'incomplete_sampling':
        for leaf in leaves_a:
            assignment[leaf] = group
        for leaf in leaves_b:
            assignment[leaf] = filler
        assignment[f'phantom_{gid}_a'] = group
        assignment[f'phantom_{gid}_b'] = group
        expected[group] = 'incomplete_sampling'
    elif cat == 'data_insufficient':
        # Paraphyletic shape, but the extra subclade carries NO taxonomy row.
        removed = set(b['children'][0]['leaves'])
        for leaf in leaves_a:
            assignment[leaf] = group
        for leaf in leaves_b:
            if leaf not in removed:
                assignment[leaf] = group
        expected[group] = 'data_insufficient'
    else:  # pragma: no cover
        raise ValueError(cat)


# ---------------------------------------------------------------------------
# Replicates
# ---------------------------------------------------------------------------

def run_cli(tree_path: Path, tax_path: Path, out_path: Path) -> float:
    pyitol_bin = shutil.which('pyitol')
    cmd_head = [pyitol_bin] if pyitol_bin else [sys.executable, '-m', 'pyitol']
    start = time.perf_counter()
    proc = subprocess.run(
        cmd_head + ['taxonomy', 'monophyly',
                    '--tree', str(tree_path), '--taxonomy', str(tax_path),
                    '--rank', 'genus', '--polytomy-mode', 'strict',
                    '-o', str(out_path)],
        capture_output=True, text=True, cwd=str(Path(__file__).parent.parent))
    wall = time.perf_counter() - start
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-2000:])
    return wall


def score(out_path: Path, expected: dict[str, str],
          subgroup_expect: dict[str, int]) -> tuple[dict, list[int]]:
    # paraphyletic_nested is a construction variant of paraphyletic (the
    # three-way label is identical); it is kept as an engineering category
    # but scored under the paraphyletic class.
    scored_expected = {g: ('paraphyletic' if e == 'paraphyletic_nested' else e)
                       for g, e in expected.items()}
    observed: dict[str, tuple[str, int]] = {}
    with out_path.open() as fh:
        for row in csv.DictReader(fh):
            sub_count = 0
            if row.get('subgroups'):
                sub_count = len([s for s in row['subgroups'].split(';') if s.strip()])
            observed[row['group']] = (row['status'], sub_count)

    confusion = {c: {o: 0 for o in CLASSES + ['other']} for c in CLASSES}
    subgroup_ok = [0, 0]
    for group, exp in scored_expected.items():
        if not group.startswith('G') or group not in observed:
            continue
        obs, sub_count = observed[group]
        bucket = obs if obs in CLASSES else 'other'
        confusion[exp][bucket] += 1
        if group in subgroup_expect:
            subgroup_ok[1] += 1
            if sub_count == subgroup_expect[group]:
                subgroup_ok[0] += 1
    return confusion, subgroup_ok


def run_balanced_replicate(n_leaves: int, seed: int, per_class: int = 30) -> dict:
    import random

    rng = random.Random(seed)
    tree_dict = build_tree_dict(n_leaves)
    # 16-leaf units: each feeds either one deep pair (categories needing a
    # nested B child) or two quarter pairs (the four shallow categories).
    depth = (n_leaves // 16).bit_length() - 1
    units = subtree_leaves(tree_dict, depth)
    rng.shuffle(units)

    deep_need = 2 * per_class          # paraphyletic_nested + data_insufficient
    shallow_need = 4 * per_class       # mono, para, poly, inc (quarter pairs)
    if len(units) < deep_need + (shallow_need + 1) // 2 + 1:
        raise RuntimeError(f'not enough units: {len(units)}')

    assignment: dict[str, str] = {}
    expected: dict[str, str] = {}
    subgroup_expect: dict[str, int] = {}
    gid = 0

    # Deep categories on whole 16-leaf units (8-leaf sibling pairs).
    deep_cats = ['paraphyletic_nested'] * per_class + ['data_insufficient'] * per_class
    for unit, cat in zip(units[:deep_need], deep_cats):
        gid += 1
        assign_category(cat, unit['children'][0], unit['children'][1], gid,
                        assignment, expected, subgroup_expect)

    # Shallow categories on 4-leaf quarter pairs of the next units.
    shallow_cats = (['monophyletic'] * per_class + ['paraphyletic'] * per_class +
                    ['polyphyletic'] * per_class + ['incomplete_sampling'] * per_class)
    quarter_pairs = []
    for unit in units[deep_need:deep_need + (shallow_need + 1) // 2]:
        for half in unit['children']:
            quarter_pairs.append((half['children'][0], half['children'][1]))
    for (a, b), cat in zip(quarter_pairs[:shallow_need], shallow_cats):
        gid += 1
        assign_category(cat, a, b, gid, assignment, expected, subgroup_expect)

    # Remaining units: monophyletic filler groups spanning the whole unit.
    for unit in units[deep_need + (shallow_need + 1) // 2:]:
        gid += 1
        group = f'G{gid:04d}'
        for leaf in unit['leaves']:
            assignment[leaf] = group
        expected[group] = 'monophyletic'

    work = OUT_DIR / f'balanced_n{n_leaves}_seed{seed}'
    work.mkdir(exist_ok=True)
    tree_path = work / 'tree.nwk'
    tax_path = work / 'taxonomy.csv'
    out_path = work / 'result.csv'
    tree_path.write_text(build_balanced_newick(n_leaves))
    with tax_path.open('w', newline='') as fh:
        writer = csv.writer(fh)
        writer.writerow(['id', 'genus'])
        for tid, g in assignment.items():
            writer.writerow([tid, g])

    wall = run_cli(tree_path, tax_path, out_path)
    confusion, subgroup_ok = score(out_path, expected, subgroup_expect)
    return {'tree_kind': 'balanced', 'n_leaves': n_leaves, 'seed': seed,
            'wall_time_s': round(wall, 3), 'confusion': confusion,
            'subgroup_count_correct': subgroup_ok}


def run_random_replicate(n_leaves: int, seed: int) -> dict:
    import random

    rng = random.Random(10_000 + seed)
    newick, root = build_random_tree(n_leaves, rng)
    units = find_disjoint_units(root, 16, 64)
    rng2 = random.Random(seed)
    rng2.shuffle(units)
    if len(units) < 6:
        raise RuntimeError(f'not enough random units: {len(units)}')

    # Background filler covers every leaf not claimed by a category unit so
    # that unmapped extras occur only by construction.
    assignment: dict[str, str] = {leaf: 'F_bg' for leaf in root['leaves']}
    expected: dict[str, str] = {}
    subgroup_expect: dict[str, int] = {}

    cats = ['monophyletic', 'paraphyletic', 'paraphyletic_nested',
            'polyphyletic_clade', 'incomplete_sampling', 'data_insufficient']
    gid = 0
    for unit, cat in zip(units, [cats[i % 6] for i in range(len(units))]):
        a, b = unit['children']
        if cat == 'paraphyletic_nested' and not b['children'][0]['children']:
            cat = 'paraphyletic'  # fall back if B's first child is a cherry
        if cat == 'polyphyletic_clade' and (
                not a['children'] or not b['children'] or
                not a['children'][1]['leaves'] or not b['children'][1]['leaves']):
            cat = 'monophyletic'
        gid += 1
        assign_category(cat, a, b, gid, assignment, expected, subgroup_expect)
        if cat == 'data_insufficient':
            # Extras must stay UNMAPPED: drop the background assignment that
            # the random-regime background filler gave them.
            for leaf in b['children'][0]['leaves']:
                assignment.pop(leaf, None)

    work = OUT_DIR / f'random_n{n_leaves}_seed{seed}'
    work.mkdir(exist_ok=True)
    tree_path = work / 'tree.nwk'
    tax_path = work / 'taxonomy.csv'
    out_path = work / 'result.csv'
    tree_path.write_text(newick)
    with tax_path.open('w', newline='') as fh:
        writer = csv.writer(fh)
        writer.writerow(['id', 'genus'])
        for tid, g in assignment.items():
            writer.writerow([tid, g])

    wall = run_cli(tree_path, tax_path, out_path)
    confusion, subgroup_ok = score(out_path, expected, subgroup_expect)
    return {'tree_kind': 'random', 'n_leaves': n_leaves, 'seed': seed,
            'wall_time_s': round(wall, 3), 'confusion': confusion,
            'subgroup_count_correct': subgroup_ok}


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def summarize(results: list[dict]) -> dict:
    merged = {c: {o: 0 for o in CLASSES + ['other']} for c in CLASSES}
    per_kind = {k: {c: {o: 0 for o in CLASSES + ['other']} for c in CLASSES}
                for k in ('balanced', 'random')}
    sub_ok = [0, 0]
    for r in results:
        for c in CLASSES:
            for o, v in r['confusion'][c].items():
                merged[c][o] += v
                per_kind[r['tree_kind']][c][o] += v
        sub_ok[0] += r['subgroup_count_correct'][0]
        sub_ok[1] += r['subgroup_count_correct'][1]

    def metrics(matrix: dict) -> dict:
        per_class = {}
        for c in CLASSES:
            tp = matrix[c][c]
            fn = sum(v for o, v in matrix[c].items() if o != c)
            fp = sum(matrix[o][c] for o in CLASSES if o != c) + matrix.get('other', {}).get(c, 0)
            precision = tp / (tp + fp) if tp + fp else float('nan')
            recall = tp / (tp + fn) if tp + fn else float('nan')
            per_class[c] = {'tp': tp, 'fp': fp, 'fn': fn,
                            'precision': round(precision, 4), 'recall': round(recall, 4)}
        total = sum(sum(v.values()) for v in matrix.values())
        correct = sum(matrix[c][c] for c in CLASSES)
        return {'confusion_matrix': matrix, 'per_class': per_class,
                'overall_accuracy': round(correct / total, 4) if total else None,
                'groups_scored': total}

    out = metrics(merged)
    out['per_tree_kind'] = {k: metrics(m) for k, m in per_kind.items()}
    out['subgroup_count_accuracy'] = round(sub_ok[0] / sub_ok[1], 4) if sub_ok[1] else None
    out['subgroup_count_checked'] = sub_ok[1]
    return out


def main() -> None:
    results = []
    for n_leaves in (2048, 8192):
        for seed in range(5):
            r = run_balanced_replicate(n_leaves, seed)
            results.append(r)
            print(f"balanced n={n_leaves} seed={seed} wall={r['wall_time_s']}s")
    for n_leaves in (2048, 4096):
        for seed in range(3):
            r = run_random_replicate(n_leaves, seed)
            results.append(r)
            print(f"random   n={n_leaves} seed={seed} wall={r['wall_time_s']}s")
    summary = summarize(results)
    out = OUT_DIR / 'accuracy_summary.json'
    out.write_text(json.dumps(
        {'replicates': results, 'summary': summary, '_provenance': bench_provenance()},
        indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
