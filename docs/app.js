/* globals Plotly, d3 */
(async function () {
  const resultsUrl = './data/monte_carlo_results.csv';
  const regUrl = './data/regression_analysis.csv';

  const results = await d3.csv(resultsUrl, d3.autoType);
  const reg = await d3.csv(regUrl, d3.autoType);

  const factorVars = Object.keys(results[0]).filter(k => /^N(25|26|27|28|29|30)_/.test(k));

  const ui = {
    mode: document.getElementById('mode'),
    x: document.getElementById('xSelect'),
    y: document.getElementById('ySelect'),
    yControl: document.getElementById('yControl'),
    yMinControl: document.getElementById('yMinControl'),
    yMaxControl: document.getElementById('yMaxControl'),
    roicMin: document.getElementById('roicMin'),
    roicMax: document.getElementById('roicMax'),
    xMin: document.getElementById('xMin'),
    xMax: document.getElementById('xMax'),
    yMin: document.getElementById('yMin'),
    yMax: document.getElementById('yMax'),
    resetBtn: document.getElementById('resetBtn'),
  };

  function optionsFor(select, vars) {
    select.innerHTML = vars.map(v => `<option value="${v}">${v}</option>`).join('');
  }
  optionsFor(ui.x, factorVars);
  optionsFor(ui.y, factorVars);
  ui.x.value = factorVars.find(v => /N29_/.test(v)) || factorVars[0];
  ui.y.value = factorVars.find(v => /N26_/.test(v)) || factorVars[1];

  // Precompute stats
  function stats(arr) {
    const a = arr.filter(Number.isFinite).sort((x, y) => x - y);
    if (!a.length) return { min: NaN, max: NaN, mean: NaN, std: NaN, p5: NaN, p95: NaN, median: NaN };
    const mean = a.reduce((s, x) => s + x, 0) / a.length;
    const std = Math.sqrt(a.reduce((s, x) => s + (x - mean) ** 2, 0) / (a.length - 1));
    const q = p => a[Math.floor((a.length - 1) * p)];
    return { min: a[0], max: a[a.length - 1], mean, std, p5: q(0.05), p95: q(0.95), median: q(0.5) };
  }

  const baseStats = {
    ROIC: stats(results.map(r => r.ROIC)),
  };
  for (const v of factorVars) baseStats[v] = stats(results.map(r => r[v]));

  function renderStats(filtered) {
    const el = document.getElementById('stats');
    const s = {
      ROIC: stats(filtered.map(r => r.ROIC)),
      X: stats(filtered.map(r => r[ui.x.value])),
      Y: ui.mode.value === '3d' ? stats(filtered.map(r => r[ui.y.value])) : null,
    };
    const fmt = n => Number.isFinite(n) ? n.toFixed(4) : '-';
    el.innerHTML = `
      <h3>Statystyki (po filtrach)</h3>
      <table class="table">
        <thead><tr><th>Wskaźnik</th><th>Min</th><th>Max</th><th>Średnia</th><th>Std</th><th>P5</th><th>P95</th></tr></thead>
        <tbody>
          <tr><td>ROIC</td><td>${fmt(s.ROIC.min)}</td><td>${fmt(s.ROIC.max)}</td><td>${fmt(s.ROIC.mean)}</td><td>${fmt(s.ROIC.std)}</td><td>${fmt(s.ROIC.p5)}</td><td>${fmt(s.ROIC.p95)}</td></tr>
          <tr><td>${ui.x.value}</td><td>${fmt(s.X.min)}</td><td>${fmt(s.X.max)}</td><td>${fmt(s.X.mean)}</td><td>${fmt(s.X.std)}</td><td>${fmt(s.X.p5)}</td><td>${fmt(s.X.p95)}</td></tr>
          ${ui.mode.value === '3d' ? `<tr><td>${ui.y.value}</td><td>${fmt(s.Y.min)}</td><td>${fmt(s.Y.max)}</td><td>${fmt(s.Y.mean)}</td><td>${fmt(s.Y.std)}</td><td>${fmt(s.Y.p5)}</td><td>${fmt(s.Y.p95)}</td></tr>` : ''}
        </tbody>
      </table>
    `;
  }

  function filterData() {
    const xKey = ui.x.value;
    const yKey = ui.y.value;
    const { value: roicMinStr } = ui.roicMin;
    const { value: roicMaxStr } = ui.roicMax;
    const { value: xMinStr } = ui.xMin;
    const { value: xMaxStr } = ui.xMax;
    const { value: yMinStr } = ui.yMin;
    const { value: yMaxStr } = ui.yMax;

    const roicMin = roicMinStr === '' ? -Infinity : Number(roicMinStr);
    const roicMax = roicMaxStr === '' ? +Infinity : Number(roicMaxStr);
    const xMin = xMinStr === '' ? -Infinity : Number(xMinStr);
    const xMax = xMaxStr === '' ? +Infinity : Number(xMaxStr);
    const yMin = yMinStr === '' ? -Infinity : Number(yMinStr);
    const yMax = yMaxStr === '' ? +Infinity : Number(yMaxStr);

    return results.filter(r => {
      const withinRoic = r.ROIC >= roicMin && r.ROIC <= roicMax;
      const withinX = r[xKey] >= xMin && r[xKey] <= xMax;
      const withinY = ui.mode.value === '3d' ? (r[yKey] >= yMin && r[yKey] <= yMax) : true;
      return withinRoic && withinX && withinY;
    });
  }

  function regress2D(data, xKey) {
    const X = data.map(d => d[xKey]);
    const Y = data.map(d => d.ROIC);
    const n = X.length;
    if (n < 2) return null;
    const mean = a => a.reduce((s, v) => s + v, 0) / a.length;
    const xBar = mean(X), yBar = mean(Y);
    const sxx = X.reduce((s, x) => s + (x - xBar) ** 2, 0);
    const sxy = X.reduce((s, x, i) => s + (x - xBar) * (Y[i] - yBar), 0);
    const b1 = sxx === 0 ? 0 : sxy / sxx;
    const b0 = yBar - b1 * xBar;
    return { b0, b1, xBar, yBar, xMin: d3.min(X), xMax: d3.max(X) };
  }

  function regress3D(data, xKey, yKey) {
    // OLS for plane: z = a + b*x + c*y
    const X = data.map(d => [1, d[xKey], d[yKey]]);
    const Z = data.map(d => d.ROIC);
    const XT = mathTranspose(X);
    const XTX = mathMatMul(XT, X);
    const XTZ = mathVecMul(XT, Z);
    const inv = mathInv3(XTX);
    if (!inv) return null;
    const coeff = mathMatVecMul(inv, XTZ); // [a,b,c]
    return { a: coeff[0], b: coeff[1], c: coeff[2] };
  }

  function mathTranspose(M){
    const r = M.length, c = M[0].length; const T = Array.from({length:c}, () => Array(r));
    for (let i=0;i<r;i++) for (let j=0;j<c;j++) T[j][i]=M[i][j];
    return T;
  }
  function mathMatMul(A,B){
    const r=A.length, c=B[0].length, n=B.length; const R=Array.from({length:r},()=>Array(c).fill(0));
    for(let i=0;i<r;i++) for(let j=0;j<c;j++) for(let k=0;k<n;k++) R[i][j]+=A[i][k]*B[k][j];
    return R;
  }
  function mathVecMul(A, v){
    const r=A.length, c=A[0].length; const res=Array(c).fill(0);
    for(let i=0;i<r;i++) for(let j=0;j<c;j++) res[j]+=A[i][j]*v[i];
    return res;
  }
  function mathDet3(M){
    const [[a,b,c],[d,e,f],[g,h,i]] = M; return a*(e*i-f*h)-b*(d*i-f*g)+c*(d*h-e*g);
  }
  function mathInv3(M){
    if (M.length!==3||M[0].length!==3) return null; const det=mathDet3(M); if(Math.abs(det)<1e-12) return null;
    const [[a,b,c],[d,e,f],[g,h,i]] = M;
    const adj = [
      [ (e*i - f*h), -(b*i - c*h),  (b*f - c*e) ],
      [-(d*i - f*g),  (a*i - c*g), -(a*f - c*d) ],
      [ (d*h - e*g), -(a*h - b*g),  (a*e - b*d) ],
    ];
    const inv = adj.map(row => row.map(x => x / det));
    return inv;
  }
  function mathMatVecMul(M, v){
    return M.map(row => row.reduce((s, x, i) => s + x * v[i], 0));
  }

  function render() {
    const filtered = filterData();
    const xKey = ui.x.value;
    const yKey = ui.y.value;

    // Scatter and regression
    if (ui.mode.value === '2d') {
      const line = regress2D(filtered, xKey);
      const xs = filtered.map(r => r[xKey]);
      const ys = filtered.map(r => r.ROIC);
      const traces = [
        { x: xs, y: ys, type: 'scatter', mode: 'markers', name: 'Scenariusze', marker: { size: 4, color: '#6ea8fe', opacity: 0.65 } },
      ];
      if (line) {
        const xLine = [line.xMin, line.xMax];
        const yLine = xLine.map(x => line.b0 + line.b1 * x);
        traces.push({ x: xLine, y: yLine, mode: 'lines', name: 'Regresja (OLS)', line: { color: '#f59e0b', width: 3 } });
      }
      Plotly.newPlot('scatter', traces, {
        title: `ROIC vs ${xKey}`,
        xaxis: { title: xKey }, yaxis: { title: 'ROIC' }, margin: { t: 40, r: 10, b: 50, l: 50 },
      }, { responsive: true, displayModeBar: true });
    } else {
      const xs = filtered.map(r => r[xKey]);
      const ys = filtered.map(r => r[yKey]);
      const zs = filtered.map(r => r.ROIC);
      const plane = regress3D(filtered, xKey, yKey);

      const traces = [
        { x: xs, y: ys, z: zs, type: 'scatter3d', mode: 'markers', name: 'Scenariusze', marker: { size: 2, color: zs, colorscale: 'Blues' } },
      ];
      if (plane) {
        // Build a grid for the plane
        const xMin = d3.min(xs), xMax = d3.max(xs);
        const yMin = d3.min(ys), yMax = d3.max(ys);
        const nx = 15, ny = 15;
        const xGrid = d3.range(nx).map(i => xMin + (xMax - xMin) * i / (nx - 1));
        const yGrid = d3.range(ny).map(j => yMin + (yMax - yMin) * j / (ny - 1));
        const zGrid = yGrid.map(y => xGrid.map(x => plane.a + plane.b * x + plane.c * y));
        traces.push({ x: xGrid, y: yGrid, z: zGrid, type: 'surface', name: 'Płaszczyzna (OLS)', showscale: false, opacity: 0.6, colorscale: 'YlOrBr' });
      }
      Plotly.newPlot('scatter', traces, {
        title: `ROIC vs ${xKey}, ${yKey}`,
        scene: { xaxis: { title: xKey }, yaxis: { title: yKey }, zaxis: { title: 'ROIC' } }, margin: { t: 40, r: 10, b: 10, l: 10 },
      }, { responsive: true, displayModeBar: true });
    }

    // Histogram ROIC
    Plotly.newPlot('hist', [{ x: filtered.map(r => r.ROIC), type: 'histogram', nbinsx: 50, marker: { color: '#8b5cf6' } }],
      { title: 'Rozkład ROIC (po filtrach)', xaxis: { title: 'ROIC' }, yaxis: { title: 'Liczność' }, margin: { t: 40, r: 10, b: 50, l: 50 } },
      { responsive: true, displayModeBar: false });

    // Betas bar (z CSV regresji)
    const sorted = reg.slice().sort((a,b) => Math.abs(b.Standardized_Beta) - Math.abs(a.Standardized_Beta));
    Plotly.newPlot('betas', [{
      x: sorted.map(r => r.Variable), y: sorted.map(r => r.Standardized_Beta), type: 'bar',
      marker: { color: sorted.map(r => (r.Standardized_Beta >= 0 ? '#16a34a' : '#dc2626')) }
    }], { title: 'Wpływ czynników (standaryzowane beta)', xaxis: { automargin: true }, yaxis: { zeroline: true } },
    { responsive: true, displayModeBar: false });

    renderStats(filtered);
  }

  function toggleMode() {
    const is3d = ui.mode.value === '3d';
    ui.yControl.style.display = is3d ? '' : 'none';
    ui.yMinControl.style.display = is3d ? '' : 'none';
    ui.yMaxControl.style.display = is3d ? '' : 'none';
  }

  ui.mode.addEventListener('change', () => { toggleMode(); render(); });
  ui.x.addEventListener('change', render);
  ui.y.addEventListener('change', render);
  ui.roicMin.addEventListener('input', render);
  ui.roicMax.addEventListener('input', render);
  ui.xMin.addEventListener('input', render);
  ui.xMax.addEventListener('input', render);
  ui.yMin.addEventListener('input', render);
  ui.yMax.addEventListener('input', render);
  ui.resetBtn.addEventListener('click', () => {
    ui.roicMin.value = '';
    ui.roicMax.value = '';
    ui.xMin.value = '';
    ui.xMax.value = '';
    ui.yMin.value = '';
    ui.yMax.value = '';
    render();
  });

  toggleMode();
  render();
})();


