"""Write PIPELINE.sha256 for a pipeline folder: one "<sha256>  <posix path>" line per file, sorted, excluding docs/, __pycache__/ and
the list itself. The adapter ships this file with the pipeline; saver.py refuses a run when any listed file is missing or differs.
Usage: python3 -I pipeline_sha.py PIPELINE_DIR"""
import hashlib
import sys
from pathlib import Path

EXCLUDE_DIRS = {'docs', '__pycache__'}


def build(folder) -> str:
    folder = Path(folder)
    lines = []
    for p in sorted(folder.rglob('*')):
        rel = p.relative_to(folder)
        if not p.is_file() or rel.parts[0] in EXCLUDE_DIRS or '__pycache__' in rel.parts or p.name == 'PIPELINE.sha256' or p.suffix == '.pyc':
            continue
        lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {rel.as_posix()}")
    return '\n'.join(lines) + '\n'


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 4
    folder = Path(argv[1])
    (folder / 'PIPELINE.sha256').write_text(build(folder), encoding='utf-8', newline='\n')
    print(f'wrote {folder / "PIPELINE.sha256"}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
