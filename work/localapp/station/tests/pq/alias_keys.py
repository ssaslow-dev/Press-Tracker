#!/usr/bin/env python3
"""Prints {name: [base, exact, fold]} as JSON for the names on stdin (one JSON list), using the build script's own key code.
tests/pq/alias_test.mjs compares it with what the page's JS computes."""
import importlib.util, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('bpa', os.path.join(HERE, '..', '..', 'tools', 'build_pq_aliases.py'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
T = json.load(open(os.path.join(HERE, '..', '..', 'data', 'proquest_outlets.json'), encoding='utf-8'))
out = {}
for n in json.load(sys.stdin):
    e, f = m.keys(n, T)
    out[n] = [m.base_key(n, T), e, f, m.clean_name(n, T)]
print(json.dumps(out, ensure_ascii=False))
