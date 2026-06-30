"""Create a self-contained executive HTML report."""

from __future__ import annotations

import html
import sqlite3
from pathlib import Path


def _bar(label: str, value: float, maximum: float, color: str) -> str:
    width = 0 if maximum == 0 else 100 * value / maximum
    return f'<div class="bar-row"><span>{html.escape(label)}</span><div class="track"><div class="bar" style="width:{width:.1f}%;background:{color}"></div></div><b>{value:.2f}%</b></div>'


def create_report(db_path: Path, result: dict, output: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        summary = conn.execute("SELECT * FROM experiment_summary ORDER BY variant").fetchall()
        segments = conn.execute("SELECT * FROM segment_results").fetchall()
        funnel = conn.execute("SELECT * FROM funnel_summary ORDER BY variant").fetchall()
        daily = conn.execute("SELECT * FROM daily_experiment_results").fetchall()
    segment_bars = "".join(_bar(f"{d} · {v}", pct, 25, "#9FE870" if v == "treatment" else "#5B8DEF") for d, v, _, _, pct, _ in segments)
    summary_rows = "".join(f"<tr><td>{v.title()}</td><td>{u:,}</td><td>{p:,}</td><td>{cr:.2%}</td><td>${rev:,.0f}</td><td>${rpu:.2f}</td><td>${aov:.2f}</td></tr>" for v, u, p, cr, rev, rpu, aov in summary)
    funnel_rows = "".join(f"<tr><td>{v.title()}</td><td>{s:,}</td><td>{views:,}</td><td>{carts:,}</td><td>{purchases:,}</td><td>{v2c:.1f}%</td><td>{c2p:.1f}%</td></tr>" for v, s, views, carts, purchases, _, v2c, c2p in funnel)
    daily_rows = "".join(f"<tr><td>{date}</td><td>{variant.title()}</td><td>{users:,}</td><td>{purchasers:,}</td><td>{conversion:.2f}%</td><td>${rpu:.2f}</td></tr>" for date, variant, users, purchasers, conversion, rpu in daily)
    decision_class = "ship" if result["recommendation"].startswith("Ship") else "hold"
    srm = result["sample_ratio_mismatch"]
    check_class = "ship" if srm["passed"] and result["adequately_powered"] else "hold"
    document = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Checkout Experiment</title>
<style>body{{margin:0;background:#0b1020;color:#eef2ff;font:16px system-ui}}main{{max-width:1080px;margin:auto;padding:42px 24px}}h1{{font-size:42px;margin-bottom:8px}}.sub{{color:#aab4cf}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:16px;margin:28px 0}}.card,section{{background:#141b2d;border:1px solid #28324a;border-radius:16px;padding:22px}}.metric{{font-size:32px;font-weight:800}}.label{{color:#aab4cf;font-size:13px;text-transform:uppercase}}section{{margin:18px 0}}table{{width:100%;border-collapse:collapse}}th,td{{padding:12px;text-align:right;border-bottom:1px solid #28324a}}th:first-child,td:first-child{{text-align:left}}.decision{{padding:18px;border-radius:12px;font-weight:700}}.ship{{background:#153927;color:#9FE870}}.hold{{background:#46232b;color:#ff9b9b}}.bar-row{{display:grid;grid-template-columns:170px 1fr 70px;gap:12px;align-items:center;margin:12px 0}}.track{{height:12px;background:#28324a;border-radius:8px;overflow:hidden}}.bar{{height:100%;border-radius:8px}}code{{color:#9FE870}}@media(max-width:700px){{table{{font-size:12px}}.bar-row{{grid-template-columns:110px 1fr 55px}}}}</style></head>
<body><main><p class="sub">PRODUCT ANALYTICS · CHECKOUT PROGRESS EXPERIMENT</p><h1>Did the new checkout experience work?</h1><p class="sub">A reproducible A/B test using event-level behavioral data, SQL funnel models, segmentation, and a two-proportion significance test.</p>
<div class="grid"><div class="card"><div class="label">Control conversion</div><div class="metric">{result['control_rate']:.2%}</div></div><div class="card"><div class="label">Treatment conversion</div><div class="metric">{result['treatment_rate']:.2%}</div></div><div class="card"><div class="label">Relative lift</div><div class="metric">{result['relative_lift']:.1%}</div></div><div class="card"><div class="label">P-value</div><div class="metric">{result['p_value']:.4f}</div></div></div>
<div class="decision {decision_class}">{result['recommendation']} · 95% CI for absolute lift: {result['ci_low']:.2%} to {result['ci_high']:.2%}</div>
<section><h2>Experiment health</h2><div class="decision {check_class}">Sample-ratio check: {'PASS' if srm['passed'] else 'FAIL'} (p={srm['p_value']:.3f}) · Power check: {'PASS' if result['adequately_powered'] else 'FAIL'} · Required users per variant: {result['required_users_per_variant']:,}</div><p class="sub">The shipping decision is blocked if assignment balance or planned statistical power fails.</p></section>
<section><h2>Experiment scorecard</h2><table><tr><th>Variant</th><th>Users</th><th>Purchasers</th><th>Conversion</th><th>Revenue</th><th>RPU</th><th>AOV</th></tr>{summary_rows}</table></section>
<section><h2>Conversion by device</h2><p class="sub">Guardrail against shipping an aggregate win that harms an important segment.</p>{segment_bars}</section>
<section><h2>Checkout funnel</h2><table><tr><th>Variant</th><th>Sessions</th><th>Views</th><th>Carts</th><th>Purchases</th><th>View→Cart</th><th>Cart→Purchase</th></tr>{funnel_rows}</table></section>
<section><h2>Daily stability</h2><p class="sub">Daily results reveal instrumentation failures, novelty effects, or a win driven by one unusual day.</p><div style="overflow:auto;max-height:390px"><table><tr><th>Date</th><th>Variant</th><th>Users</th><th>Purchasers</th><th>Conversion</th><th>RPU</th></tr>{daily_rows}</table></div></section>
<section><h2>Decision framework</h2><p>The treatment ships only when the two-sided test reaches <code>p &lt; 0.05</code> and the observed lift is positive. Segment results are diagnostic and are not treated as independently powered experiments.</p></section>
</main></body></html>"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")
