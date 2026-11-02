"""Turn the compare.py results into one markdown table per viewport.
    python3 -I report.py --out DIR [--viewports 1440x900,960x1040] > RESULTS.md
Reads DIR/results_<vp>_exception_applied.json (the reference with the recorded exception applied against the PC page: must be all zero), DIR/results_<vp>_raw.json
(the untouched reference against the PC page, only the exception rectangles masked: shows the reflow) and DIR/parity/<vp>_summary.json."""
import argparse
import json
from pathlib import Path


def load(p):
    p = Path(p)
    return json.loads(p.read_text()) if p.is_file() else {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--viewports', default='1440x900,960x1040')
    o = ap.parse_args()
    for vp in o.viewports.split(','):
        ex, raw = load(o.out / f'results_{vp}_exception_applied.json'), load(o.out / f'results_{vp}_raw.json')
        if not ex:
            continue
        print(f'### {vp}\n')
        print('| route / state | page size | differing pixels (exception applied) | % | style differences | font-file differences | differing pixels (raw, exception rectangles masked) |')
        print('|---|---|---|---|---|---|---|')
        tp = ts = tf = tr = 0
        for n, r in sorted(ex.items()):
            if 'pixels' not in r:
                print(f'| {n} | ERROR {r.get("errors")} | | | | | |')
                continue
            p, s, f = r['pixels'], r['styles'], r['faces']
            nstyle = s['elements_diff'] + len(s['only_a']) + len(s['only_b'])
            rr = raw.get(n, {}).get('pixels', {})
            reflow = len(raw.get(n, {}).get('styles', {}).get('reflow', []))
            tp += p['diff_px']
            ts += nstyle
            tf += f['diff']
            tr += rr.get('diff_px', 0)
            size = f"{p['a_size'][0]}x{p['a_size'][1]}" + ('' if p['size_equal'] else f" vs {p['b_size'][0]}x{p['b_size'][1]}")
            print(f"| {n} | {size} | {p['diff_px']:,} of {p['total_px']:,} | {p['pct']:.4f} | {nstyle} of {s['n_a']:,} | {f['diff']} of {f['n_a']:,} | {rr.get('diff_px', '-')}"
                  + (" (masthead spacer and button group resize, see README)" if reflow else '') + ' |')
        print(f'| **total** | | **{tp:,}** | | **{ts}** | **{tf}** | **{tr}** |\n')
        par = load(o.out / 'parity' / f'{vp}_summary.json')
        if par:
            print(f'Function parity at {vp}:\n')
            print('| interaction | steps compared | differences |')
            print('|---|---|---|')
            for k, v in par.items():
                print(f"| {k} | {v['steps']} | {v['diffs']}{' (CRASH ' + v['crash'][:60] + ')' if v.get('crash') else ''} |")
            print()


if __name__ == '__main__':
    main()
