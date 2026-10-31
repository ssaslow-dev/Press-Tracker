"""VIEWER-v1: build the shareable viewer copy of the tracker from a built index.html.

Usage: python3 -I code/make_viewer.py <built index.html> <out dir>      (two positional arguments, no flags)
  <built index.html>  a built tracker page: work/build_last/pipe_index.html (bash build/build.sh; OUT=<dir> to build elsewhere)
                      or the handoff kit's publish/index.html (the page as shipped)
  <out dir>           new or empty folder; written: index.html, data/data.json, data/rows.json

- moves the inline `data` and `rows` JSON blocks into <out>/data/data.json and
  <out>/data/rows.json (the sharing review rejects a 10 MB page) and loads them back
  with a synchronous XHR before the app script runs;
- titles the page "AJG Press Coverage Tracker (Shared)";
- hides controls that need connectors or downloads (Update, Refresh, Save to sheet,
  spreadsheet / CSV downloads), since the viewer copy is published with capabilities {}.

Publish <out dir>/index.html with capabilities {} (the viewer declares no mcp or db), plus
data/data.json and data/rows.json from disk. Every other file (articles/, img/, pdf/,
data/sheet.json, data/release_texts.json) is copied server side from the tracker at publish
time: Artifact `files` entries {"<path>": {"artifact": "<tracker URL>", "path": "<path>"}},
in batches under 64 MB / 255 files, the page last. On a NEW account the source must be the
NEW tracker (the old account's tracker cannot be opened there). HANDOFF 4.4a has the steps.
"""
import os, re, sys

LOADER = ("<script>/* VIEWER-LOAD */(function(){[['data','data/data.json'],['rows','data/rows.json']]"
          ".forEach(function(p){try{var x=new XMLHttpRequest();x.open('GET',p[1],false);x.send(null);"
          "if(x.status>=200&&x.status<300){document.getElementById(p[0]).textContent=x.responseText;}}"
          "catch(e){console.error('load '+p[1],e);}});})();</script>")
HIDE = ("<style>/* VIEWER-HIDE */#runFind,#runRefresh,#raStrip,[data-runfind],#updGo,#updRefresh,#updSave,"
        "#updAdd,#updCopy,#updAgain,[data-dl],#bkCsv{display:none!important}</style>")
TITLE = "AJG Press Coverage Tracker (Shared)"


def main(src, out):
    s = open(src, encoding="utf-8").read()
    os.makedirs(os.path.join(out, "data"), exist_ok=True)
    for bid in ("data", "rows"):
        m = re.search(r'(<script id="%s" type="application/json">)(.*?)(</script>)' % bid, s, re.S)
        if not m:
            sys.exit("block %s not found" % bid)
        if m.group(2).strip():
            open(os.path.join(out, "data", bid + ".json"), "w", encoding="utf-8").write(m.group(2))
        s = s[:m.start()] + m.group(1) + m.group(3) + s[m.end():]
    if "VIEWER-LOAD" not in s:
        m = re.search(r'<script id="rows" type="application/json"></script>', s)
        s = s[:m.end()] + LOADER + s[m.end():]
    if "VIEWER-HIDE" not in s:
        s = s.replace("</head>", HIDE + "</head>", 1)
    s = re.sub(r"<title>.*?</title>", "<title>%s</title>" % TITLE, s, count=1, flags=re.S)
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(s)
    print("viewer written:", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
