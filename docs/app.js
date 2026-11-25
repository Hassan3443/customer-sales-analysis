(async function () {
  const $ = s => document.querySelector(s);
  const S = await (await fetch('summary.json')).json();
  const cube = S.cube; // [month, category, country, status, orders, value]
  const M = 0, CAT = 1, CTY = 2, ST = 3, ORD = 4, VAL = 5;
  const fmt = n => Math.round(n).toLocaleString('en-US');
  const money = n => n >= 1e6 ? (n / 1e6).toFixed(2) + 'M' : n >= 1e3 ? (n / 1e3).toFixed(0) + 'K' : n.toFixed(0);
  const years = [...new Set(cube.map(r => r[M].slice(0, 4)))].sort();
  const cats = [...new Set(cube.map(r => r[CAT]))].sort(), ctys = [...new Set(cube.map(r => r[CTY]))].sort();
  const months = [...new Set(cube.map(r => r[M]))].sort();
  const fill = (sel, items) => items.forEach(v => { const o = document.createElement('option'); o.value = v; o.textContent = v; $(sel).appendChild(o); });
  fill('#f-cat', cats); fill('#f-country', ctys); fill('#f-from', years); fill('#f-to', years);
  const def = { from: years[0], to: years[years.length - 1], cat: '', country: '', status: 'all' };
  const f = { ...def };
  $('#f-from').value = f.from; $('#f-to').value = f.to;
  const isLost = s => s === 'Cancelled' || s === 'Returned';

  function pick() {
    return cube.filter(r => r[M].slice(0, 4) >= f.from && r[M].slice(0, 4) <= f.to && (!f.cat || r[CAT] === f.cat) && (!f.country || r[CTY] === f.country) &&
      (f.status === 'all' || (f.status === 'lost') === isLost(r[ST])));
  }
  const sum = (rows, i) => rows.reduce((s, r) => s + r[i], 0);
  const group = (rows, i, j) => { const m = new Map(); rows.forEach(r => m.set(r[i], (m.get(r[i]) || 0) + r[j])); return m; };

  function hbars(el, entries, fmtv) {
    const max = Math.max(1, ...entries.map(e => e[1]));
    el.innerHTML = entries.map(([k, v]) => `<div class="hb"><span title="${k}">${k}</span><div class="tr"><div class="fl" style="width:${v / max * 100}%"></div></div><b>${fmtv(v)}</b></div>`).join('') || '<p class="note">No orders match.</p>';
  }
  function line(el, labels, values, w = 760, h = 230) {
    if (!values.length) { el.innerHTML = '<p class="note">No orders match.</p>'; return; }
    const max = Math.max(...values) * 1.05, min = 0, n = values.length, tip = $('#tip');
    const x = i => 44 + i * (w - 54) / Math.max(1, n - 1), y = v => 10 + (h - 10) * (1 - (v - min) / (max - min));
    let o = `<svg viewBox="0 0 ${w} ${h + 26}" role="img">`;
    [0, .5, 1].forEach(t => { const yy = 10 + (h - 10) * (1 - t); o += `<line x1="40" x2="${w}" y1="${yy}" y2="${yy}" stroke="rgba(255,255,255,.07)"/><text x="36" y="${yy + 4}" text-anchor="end" fill="#8f99b3" font-size="10">${money(max * t)}</text>`; });
    const pts = values.map((v, i) => `${x(i)},${y(v)}`).join(' ');
    o += `<defs><linearGradient id="g" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#34d399" stop-opacity=".35"/><stop offset="1" stop-color="#34d399" stop-opacity="0"/></linearGradient></defs>`;
    o += `<polygon points="${x(0)},${h} ${pts} ${x(n - 1)},${h}" fill="url(#g)"/><polyline points="${pts}" fill="none" stroke="#34d399" stroke-width="2"/>`;
    labels.forEach((l, i) => { if (l.endsWith('-01')) o += `<text x="${x(i)}" y="${h + 18}" text-anchor="middle" fill="#8f99b3" font-size="10">${l.slice(0, 4)}</text>`; });
    values.forEach((v, i) => { o += `<circle cx="${x(i)}" cy="${y(v)}" r="7" fill="transparent" data-t="${labels[i]}: ${money(v)}"/>`; });
    el.innerHTML = o + '</svg>';
    el.querySelectorAll('circle').forEach(c => { c.onmousemove = e => { tip.style.display = 'block'; tip.textContent = c.dataset.t; tip.style.left = e.clientX + 12 + 'px'; tip.style.top = e.clientY + 12 + 'px'; }; c.onmouseleave = () => tip.style.display = 'none'; });
  }

  function render() {
    const rows = pick(), val = sum(rows, VAL), ord = sum(rows, ORD);
    const lost = sum(rows.filter(r => isLost(r[ST])), VAL);
    $('#kpis').innerHTML = [[money(val), 'order value'], [fmt(ord), 'orders'], [ord ? '$' + (val / ord).toFixed(0) : 'n/a', 'average order value'], [val ? (lost / val * 100).toFixed(1) + '%' : 'n/a', 'of value cancelled or returned']]
      .map(([b, s]) => `<div class="kpi"><b>${b}</b><span>${s}</span></div>`).join('');
    const byMonth = group(rows, M, VAL), ml = months.filter(m => byMonth.has(m));
    line($('#c-month'), ml, ml.map(m => byMonth.get(m)));
    const top = (i, j = VAL) => [...group(rows, i, j)].sort((a, b) => b[1] - a[1]);
    hbars($('#c-cat'), top(CAT), money); hbars($('#c-country'), top(CTY), money);
    hbars($('#c-status'), top(ST, ORD).map(([k, v]) => [k, v]), v => (ord ? (v / ord * 100).toFixed(1) + '%' : '0%'));
  }

  // static sections
  hbars($('#c-state'), Object.entries(S.top_states), money);
  const segMax = Math.max(...S.segments.map(s => s.share_of_value));
  $('#c-seg').innerHTML = S.segments.map(s => `<div class="seg-row"><span>${s.segment}</span><div class="tr"><div class="fl" style="width:${s.share_of_value / segMax * 100}%"></div></div><b>${fmt(s.customers)}</b><b>${s.avg_orders}</b></div>`).join('');
  const champ = S.segments.find(s => s.segment === 'Champions'), lostSeg = S.segments.find(s => s.segment === 'Lost');
  $('#seg-note').textContent = `Champions are ${(champ.customers / S.customers * 100).toFixed(0)}% of ${fmt(S.customers)} customers and ${(champ.share_of_value * 100).toFixed(0)}% of order value. ${fmt(lostSeg.customers)} customers are in the Lost segment (last order about ${Math.round(lostSeg.avg_recency_days / 365 * 10) / 10} years before the end of the data). Share of order value is shown as bars; the two right columns are customers and average orders per customer.`;
  const d = S.discounts, dmax = Math.max(...d.map(x => x.avg_order_value));
  $('#c-disc').innerHTML = `<table><thead><tr><th>Discount</th><th>Orders</th><th>Avg quantity</th><th>Avg unit price</th><th>Avg order value</th><th></th></tr></thead><tbody>${d.map(x => `<tr><td>${Math.round(x.discount * 100)}%</td><td>${fmt(x.orders)}</td><td>${x.avg_quantity.toFixed(2)}</td><td>$${x.avg_unit_price.toFixed(0)}</td><td>$${x.avg_order_value.toFixed(0)}</td><td style="width:30%"><div class="seg-row" style="display:block;margin:0"><div class="tr"><div class="fl" style="width:${x.avg_order_value / dmax * 100}%"></div></div></div></td></tr>`).join('')}</tbody></table>`;
  $('#disc-note').textContent = `Average quantity stays at about 3 items at every discount level, so higher discounts did not lead to bigger baskets. Average order value falls from $${d[0].avg_order_value.toFixed(0)} with no discount to $${d[d.length - 1].avg_order_value.toFixed(0)} at 30%. This is an association in this dataset, not proof of cause.`;

  const bind = (sel, key) => $(sel).onchange = e => { f[key] = e.target.value; if (f.from > f.to) { if (key === 'from') { f.to = f.from; $('#f-to').value = f.to; } else { f.from = f.to; $('#f-from').value = f.from; } } render(); };
  bind('#f-from', 'from'); bind('#f-to', 'to'); bind('#f-cat', 'cat'); bind('#f-country', 'country'); bind('#f-status', 'status');
  $('#reset').onclick = () => { Object.assign(f, def); $('#f-from').value = f.from; $('#f-to').value = f.to; $('#f-cat').value = ''; $('#f-country').value = ''; $('#f-status').value = 'all'; render(); };
  render();
})();
