"""Build report/index.html from template + results + content.py texts."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from analyze import main as summarize, key_of

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SHORT = {
    "A_biped": "A — двуногий",
    "B1_tail_narrow@10cm": "B1 — 1 колесо, ЦМ −10 см",
    "B2_tail_wide@10cm": "B2 — 2 колеса, ЦМ −10 см",
    "B1_tail_narrow@15cm": "B1 — 1 колесо, ЦМ −15 см",
    "B2_tail_wide@15cm": "B2 — 2 колеса, ЦМ −15 см",
}
JOINTS_RU = ["бедро вбок", "бедро вперёд", "колено", "голеностоп вперёд", "голеностоп вбок"]


def torque_table(R, keys):
    out = {}
    for k in keys:
        rows = [c for c in R if c["exp"] == "torque" and key_of(c) == k and c["x"] == 1.0
                and c["pname"] == "push" and not c["fell"]]
        if not rows:
            continue
        c = min(rows, key=lambda c: sum(c["rms_tau"]))
        out[k] = dict(peak=c["peak_tau"][:5], rms=c["rms_tau"][:5], w=c["peak_w"][:5])
    return out


def build(content):
    from analyze import load
    cwd = os.getcwd(); os.chdir(ROOT)
    S = summarize(None, "results/summary.json")
    R = load()
    os.chdir(cwd)
    keys = S["keys"]
    lat_axis = sorted({x for k in keys for p in S["latency"][k].values() for x, _ in p})
    data = dict(keys=keys, short=SHORT, lat_axis=lat_axis, latency=S["latency"],
                push_lats=["5", "40"], push_max=S["push_max"], push_xmax=60,
                joints=JOINTS_RU, torque=torque_table(R, keys))
    tpl = open(os.path.join(HERE, "template.html")).read()
    diagrams = open(os.path.join(HERE, "diagrams.html")).read()
    rep = dict(content)
    rep["DIAGRAMS"] = diagrams
    rep["DATA"] = json.dumps(data, ensure_ascii=False, default=float).replace("</", "<\\/")
    for k, v in rep.items():
        tpl = tpl.replace("{{" + k + "}}", v)
    import re
    missing = re.findall(r"\{\{[A-Z_]+\}\}", tpl)
    out = os.path.join(HERE, "index.html")
    open(out, "w").write(tpl)
    return out, S, data, missing


if __name__ == "__main__":
    from content import CONTENT
    out, S, data, missing = build(CONTENT)
    print(out, "unfilled placeholders:" if missing else "", missing)
