const root = document.querySelector('#referral-time-tree');
const names = ['官方入口', '一级邀请', '二级邀请', '三级邀请', '四级邀请'];
let state = { snapshot: null, selected: null, foldedFrom: null, zoom: 1, drag: null, expandedBins: new Set() };

function formatTime(value) {
  return new Date(value).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' });
}

function formatGeneratedAt(value) {
  return new Date(value).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' });
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[character]);
}

function normalizeSnapshot(payload) {
  if (!payload || !Array.isArray(payload.nodes) || !payload.generatedAt) throw new Error('数据格式无效');
  const ids = new Set();
  const nodes = payload.nodes.map(item => {
    if (!item || typeof item.id !== 'string' || typeof item.submittedAt !== 'string' || !/^(\d{4}|未知)$/.test(item.tail || '')) throw new Error('数据记录无效');
    if (ids.has(item.id)) throw new Error('数据存在重复节点');
    ids.add(item.id);
    const time = new Date(item.submittedAt.replace(' ', 'T')).getTime();
    if (!Number.isFinite(time)) throw new Error('提交时间无效');
    return { id: item.id, submittedAt: item.submittedAt, tail: item.tail, parent: item.parent || null, time };
  });
  const byId = new Map(nodes.map(node => [node.id, node]));
  nodes.forEach(node => { if (node.parent && !byId.has(node.parent)) node.parent = null; });
  const children = new Map(nodes.map(node => [node.id, []]));
  nodes.forEach(node => { if (node.parent) children.get(node.parent).push(node.id); });
  const depthMemo = new Map();
  function depth(id) {
    if (depthMemo.has(id)) return depthMemo.get(id);
    const node = byId.get(id);
    const value = !node?.parent ? 0 : Math.min(4, depth(node.parent) + 1);
    depthMemo.set(id, value);
    return value;
  }
  nodes.forEach(node => { node.depth = depth(node.id); });
  return { generatedAt: payload.generatedAt, nodes, byId, children };
}

function descendants(snapshot, id) {
  const result = new Set();
  const stack = [...(snapshot.children.get(id) || [])];
  while (stack.length) {
    const current = stack.pop();
    if (result.has(current)) continue;
    result.add(current);
    stack.push(...(snapshot.children.get(current) || []));
  }
  return result;
}

function chain(snapshot, id) {
  const result = descendants(snapshot, id);
  result.add(id);
  for (let parent = snapshot.byId.get(id)?.parent; parent; parent = snapshot.byId.get(parent)?.parent) result.add(parent);
  return result;
}

function isHidden(node) {
  return state.foldedFrom !== null && node.depth >= state.foldedFrom;
}

function render() {
  const snapshot = state.snapshot;
  if (!snapshot?.nodes.length) {
    root.innerHTML = '<div class="empty">暂无可展示的招募提交数据。</div>';
    return;
  }
  const visibleCount = snapshot.nodes.filter(node => !isHidden(node)).length;
  root.innerHTML = `<div class="status-line" id="status-line"><span>数据更新于 <strong>${formatGeneratedAt(snapshot.generatedAt)}</strong></span><span>总提交 <strong>${snapshot.nodes.length}</strong></span><span>当前可见 <strong>${visibleCount}</strong></span></div><div class="toolbar"><div class="level-controls" id="level-controls"></div><button class="button reset" type="button" id="reset-view">重置视图</button></div><div class="chart-frame" id="chart-frame"><svg id="chart" role="img" aria-label="二阶段招募裂变时间轴"></svg></div><p class="legend" id="legend">滚轮缩放时间轴，拖动空白处平移；颜色更深、气泡更大表示直接邀请更多。</p><div class="tooltip" id="tooltip" role="tooltip" hidden></div>`;
  renderControls();
  renderChart();
  bindFrame();
}

function renderControls() {
  const controls = root.querySelector('#level-controls');
  controls.innerHTML = names.map((name, index) => {
    const count = state.snapshot.nodes.filter(node => node.depth === index).length;
    const folded = state.foldedFrom !== null && index >= state.foldedFrom;
    return `<button class="button${folded ? ' is-folded' : ''}" type="button" data-level="${index}">${folded ? '展开' : '收起'}${name} · ${count}</button>`;
  }).join('');
  controls.querySelectorAll('[data-level]').forEach(button => button.addEventListener('click', () => {
    const level = Number(button.dataset.level);
    state.foldedFrom = state.foldedFrom === level ? null : level;
    if (state.selected && isHidden(state.snapshot.byId.get(state.selected))) state.selected = null;
    render();
  }));
  root.querySelector('#reset-view').addEventListener('click', () => {
    state.selected = null;
    state.foldedFrom = null;
    state.zoom = 1;
    state.expandedBins.clear();
    render();
  });
}

function renderChart() {
  const snapshot = state.snapshot;
  const frame = root.querySelector('#chart-frame');
  const svg = root.querySelector('#chart');
  const tooltip = root.querySelector('#tooltip');
  const hour = 60 * 60 * 1000;
  const minTime = Math.min(...snapshot.nodes.map(node => node.time));
  const maxTime = Math.max(...snapshot.nodes.map(node => node.time));
  const hourStart = Math.floor(minTime / hour) * hour;
  const hourEnd = Math.ceil(maxTime / hour) * hour;
  const hourCount = Math.max(1, (hourEnd - hourStart) / hour);
  const compact = state.zoom <= .72;
  const height = Math.max(compact ? 960 : 1000, Math.ceil(hourCount * (compact ? 52 : 128 * state.zoom)) + 130);
  const width = Math.max(460, Math.floor(frame.clientWidth));
  const left = 92, right = 30, top = 62, bottom = 32, column = (width - left - right) / 4;
  const x = depth => left + depth * column;
  const y = value => top + (value - hourStart) / Math.max(1, hourEnd - hourStart) * (height - top - bottom);
  const officialBins = new Map();
  snapshot.nodes.filter(node => node.depth === 0 && !snapshot.children.get(node.id).length).forEach(node => {
    const id = `official-${Math.floor(node.time / (15 * 60 * 1000))}`;
    const group = officialBins.get(id) || { id, nodes: [] };
    group.nodes.push(node);
    officialBins.set(id, group);
  });
  const aggregates = [...officialBins.values()].filter(group => !isHidden(group.nodes[0]) && state.zoom < 3 && !state.expandedBins.has(group.id));
  const aggregateIds = new Set(aggregates.flatMap(group => group.nodes.map(node => node.id)));
  const visible = snapshot.nodes.filter(node => !isHidden(node) && !aggregateIds.has(node.id));
  const visibleIds = new Set(visible.map(node => node.id));
  const selectedChain = state.selected ? chain(snapshot, state.selected) : new Set();
  const positions = new Map();
  const radius = node => 4.5 + Math.min(9, Math.sqrt(snapshot.children.get(node.id).length) * 2.3);
  names.forEach((_, depth) => {
    const placed = [];
    const direction = depth === 4 ? -1 : 1;
    const offsets = [0, ...Array.from({ length: 32 }, (_, index) => direction * (index + 1) * 12), ...Array.from({ length: 32 }, (_, index) => -direction * (index + 1) * 12)];
    visible.filter(node => node.depth === depth).sort((a, b) => a.time - b.time).forEach(node => {
      const nodeY = y(node.time);
      const nodeRadius = radius(node);
      const offset = offsets.find(candidate => placed.every(item => Math.hypot(candidate - item.offset, nodeY - item.y) >= nodeRadius + item.radius + 3)) ?? offsets.at(-1);
      positions.set(node.id, { x: x(depth) + offset, y: nodeY });
      placed.push({ offset, y: nodeY, radius: nodeRadius });
    });
  });
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  svg.setAttribute('width', width);
  svg.setAttribute('height', height);
  const allHours = Array.from({ length: hourCount + 1 }, (_, index) => hourStart + index * hour);
  const hourStep = compact ? 2 : 1;
  const grid = allHours.filter((tick, index) => index === 0 || hourStep === 1 || new Date(tick).getHours() % hourStep === 0).map(tick => `<line class="time-grid" x1="${left - 16}" y1="${y(tick)}" x2="${width - right}" y2="${y(tick)}"></line><text class="time-axis" x="8" y="${y(tick) + 4}">${formatTime(tick)}</text>`).join('');
  const days = new Map();
  snapshot.nodes.forEach(node => { const date = new Date(node.time); date.setHours(0, 0, 0, 0); const key = date.getTime(); days.set(key, (days.get(key) || 0) + 1); });
  const dividers = allHours.filter(tick => tick !== hourStart && new Date(tick).getHours() === 0).map(tick => `<line class="day-divider" x1="${left - 16}" y1="${y(tick)}" x2="${width - right}" y2="${y(tick)}"></line><text class="day-label" x="${left - 4}" y="${y(tick) - 8}">${new Date(tick).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })} · 新一天</text>`).join('');
  const summaries = [...days.entries()].sort(([a], [b]) => a - b).map(([day, count]) => `<g class="day-summary"><rect x="${width - right - 118}" y="${y(Math.max(day, hourStart)) + 10}" width="118" height="21" rx="10.5"></rect><text x="${width - right - 59}" y="${y(Math.max(day, hourStart)) + 24}" text-anchor="middle">${new Date(day).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })} · ${count} 人</text></g>`).join('');
  const lanes = names.map((name, depth) => `<text class="time-lane" x="${x(depth)}" y="34" text-anchor="middle">${name}</text><line class="time-grid lane" x1="${x(depth)}" y1="${top - 12}" x2="${x(depth)}" y2="${height - bottom}"></line>`).join('');
  const aggregatesMarkup = aggregates.map(group => { const first = Math.min(...group.nodes.map(node => node.time)); const last = Math.max(...group.nodes.map(node => node.time)); const center = (y(first) + y(last)) / 2; const groupHeight = Math.max(14, y(last) - y(first) + 8); const groupWidth = 20 + Math.min(14, Math.sqrt(group.nodes.length) * 3); const groupLeft = x(0) + 14; return `<g class="aggregate" data-bin="${group.id}"><rect x="${groupLeft}" y="${center - groupHeight / 2}" width="${groupWidth}" height="${groupHeight}" rx="${Math.min(7, groupHeight / 2)}"></rect><text x="${groupLeft + groupWidth / 2}" y="${center + 3.5}" text-anchor="middle">${group.nodes.length}</text></g>`; }).join('');
  const edges = visible.filter(node => node.parent && visibleIds.has(node.parent)).map(node => { const from = positions.get(node.parent); const to = positions.get(node.id); const curve = (to.x - from.x) * .46; const className = state.selected ? (selectedChain.has(node.id) && selectedChain.has(node.parent) ? ' in-chain' : ' outside') : ''; return `<path class="edge${className}" d="M ${from.x} ${from.y} C ${from.x + curve} ${from.y}, ${to.x - curve} ${to.y}, ${to.x} ${to.y}"></path>`; }).join('');
  const nodes = visible.map(node => { const point = positions.get(node.id); const direct = snapshot.children.get(node.id).length; const band = direct === 0 ? 0 : direct < 4 ? 1 : direct < 8 ? 2 : 3; const className = state.selected ? (selectedChain.has(node.id) ? ' in-chain' : ' outside') : ''; return `<circle class="node depth-${node.depth} direct-${band}${className}" data-id="${node.id}" cx="${point.x}" cy="${point.y}" r="${radius(node)}" aria-label="尾号 ${escapeHtml(node.tail)}，${names[node.depth]}，${formatTime(node.time)}"></circle>`; }).join('');
  svg.innerHTML = `${grid}${dividers}${summaries}${lanes}${aggregatesMarkup}${edges}${nodes}`;
  function hideTooltip() { tooltip.hidden = true; }
  function moveTooltip(event) { if (tooltip.hidden) return; const rect = tooltip.getBoundingClientRect(); tooltip.style.left = `${Math.max(8, Math.min(window.innerWidth - rect.width - 8, event.clientX + 14))}px`; tooltip.style.top = `${Math.max(8, Math.min(window.innerHeight - rect.height - 8, event.clientY + 14))}px`; }
  svg.querySelectorAll('.node').forEach(mark => { const node = snapshot.byId.get(mark.dataset.id); mark.addEventListener('click', () => { state.selected = state.selected === node.id ? null : node.id; hideTooltip(); render(); }); mark.addEventListener('pointerenter', event => { const following = [...descendants(snapshot, node.id)].map(id => snapshot.byId.get(id).time).sort((a, b) => a - b); tooltip.innerHTML = [['identity', '尾号', node.tail], ['source', '来源', names[node.depth]], ['time', '提交', formatTime(node.time)], ['direct', '直接邀请', `${snapshot.children.get(node.id).length} 人`], ['range', '后续提交', following.length ? `${formatTime(following[0])} 至 ${formatTime(following.at(-1))}` : '暂无']].map(([tone, label, value]) => `<div class="tooltip-row"><span class="tooltip-key ${tone}">${label}</span><span>${escapeHtml(value)}</span></div>`).join(''); tooltip.hidden = false; moveTooltip(event); }); mark.addEventListener('pointermove', moveTooltip); mark.addEventListener('pointerleave', hideTooltip); });
  svg.querySelectorAll('.aggregate').forEach(mark => mark.addEventListener('click', () => { state.expandedBins.add(mark.dataset.bin); renderChart(); }));
}

function bindFrame() {
  const frame = root.querySelector('#chart-frame');
  frame.addEventListener('wheel', event => { event.preventDefault(); const ratio = frame.scrollTop / Math.max(1, frame.scrollHeight - frame.clientHeight); const next = Math.max(.55, Math.min(12, state.zoom * (event.deltaY > 0 ? .56 : 1.8))); if (next === state.zoom) return; state.zoom = next; renderChart(); frame.scrollTop = ratio * Math.max(0, frame.scrollHeight - frame.clientHeight); }, { passive: false });
  frame.addEventListener('pointerdown', event => { if (event.target.closest('.node,.aggregate,button')) return; state.drag = { x: event.clientX, y: event.clientY, left: frame.scrollLeft, top: frame.scrollTop }; frame.classList.add('dragging'); frame.setPointerCapture(event.pointerId); });
  frame.addEventListener('pointermove', event => { if (!state.drag) return; frame.scrollLeft = state.drag.left - (event.clientX - state.drag.x); frame.scrollTop = state.drag.top - (event.clientY - state.drag.y); });
  ['pointerup', 'pointercancel'].forEach(type => frame.addEventListener(type, () => { state.drag = null; frame.classList.remove('dragging'); }));
}

async function loadSnapshot() {
  try {
    const dataUrl = new URL(window.PH2_REF_DATA_URL, window.location.href);
    dataUrl.searchParams.set('v', String(Math.floor(Date.now() / 300_000)));
    const response = await fetch(dataUrl, { cache: 'no-store' });
    if (!response.ok) throw new Error(`数据请求失败 (${response.status})`);
    state.snapshot = normalizeSnapshot(await response.json());
    render();
  } catch (error) {
    const status = root.querySelector('#status-line');
    if (status) status.classList.add('error');
    if (status) status.insertAdjacentHTML('beforeend', `<span>更新失败：${escapeHtml(error.message)}；保留当前图</span>`);
    else root.innerHTML = `<div class="empty">暂时无法加载数据，请稍后刷新。</div>`;
  }
}

loadSnapshot();
setInterval(loadSnapshot, 300_000);
