// ==UserScript==
// @name         BOSS直聘 职位采集（前端/深圳）
// @namespace    dsh.local.boss
// @version      1.0.0
// @description  在你自己已登录的浏览器里调用站内搜索接口采集职位，导出 CSV/JSON。全程不启动任何自动化框架，不会触发 Playwright/CDP 检测。
// @match        https://www.zhipin.com/*
// @run-at       document-idle
// @grant        none
// @noframes
// ==/UserScript==

/*
 * 为什么用用户脚本而不是 Playwright：
 *   BOSS 会检测 CDP 特征（navigator.webdriver、Runtime.enable 泄漏、--enable-automation 等），
 *   自动化浏览器打开 1~2 秒后会被重定向到 about:blank（白屏）。
 *   用户脚本跑在你平时用的 Chrome 里，没有 CDP、没有 webdriver 标志，
 *   fetch 也走页面自己的 origin，风控视角下和正常翻页没有区别。
 *
 * 用法：
 *   1. 装 Tampermonkey，新建脚本，粘贴本文件保存；
 *   2. 打开 https://www.zhipin.com/web/geek/job?query=前端&city=101280600 并确认已登录；
 *   3. 右下角面板里点「开始采集」，完成后点「导出 CSV」。
 */

(function () {
  'use strict';

  const API_PATH = '/wapi/zpgeek/search/joblist.json';
  const SKEY = 'bzp_settings_v1';
  const DEFAULT_CFG = {
    query: '前端',
    city: '101280600', // 深圳
    pages: 10,
    pageSize: 30,
    delayMin: 2500,
    delayMax: 4500,
  };

  const CITY_HINT = {
    '101010100': '北京', '101020100': '上海', '101280100': '广州',
    '101280600': '深圳', '101210100': '杭州', '101270100': '成都',
    '101190100': '南京', '101200100': '武汉', '101281600': '东莞',
  };

  const state = { rows: [], seen: new Set(), running: false, stop: false };

  // ---------- UI ----------
  const host = document.createElement('div');
  host.id = 'bzp-panel-host';
  document.documentElement.appendChild(host);
  const root = host.attachShadow({ mode: 'open' });

  root.innerHTML = `
    <style>
      :host { all: initial; }
      .panel {
        position: fixed; right: 16px; bottom: 16px; z-index: 2147483647;
        width: 296px; font: 13px/1.5 -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
        background: #fff; color: #222; border: 1px solid #e3e6eb; border-radius: 10px;
        box-shadow: 0 8px 28px rgba(0,0,0,.14); overflow: hidden;
      }
      .hd { display: flex; align-items: center; justify-content: space-between;
            padding: 9px 12px; background: #00bebd; color: #fff; cursor: pointer; user-select: none; }
      .hd b { font-size: 13px; font-weight: 600; }
      .hd span { font-size: 11px; opacity: .85; }
      .body { padding: 10px 12px 12px; }
      .body.hide { display: none; }
      .row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
      .row label { width: 52px; flex: none; color: #555; font-size: 12px; }
      .row input { flex: 1; min-width: 0; height: 28px; padding: 0 8px; font-size: 13px;
                   border: 1px solid #dcdfe6; border-radius: 6px; outline: none; background: #fff; color: #222; }
      .row input:focus { border-color: #00bebd; }
      .hint { font-size: 11px; color: #999; flex: none; width: 46px; }
      .btns { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin: 10px 0 8px; }
      button { height: 30px; font-size: 12px; border-radius: 6px; border: 1px solid #dcdfe6;
               background: #fff; color: #333; cursor: pointer; }
      button:hover:not(:disabled) { border-color: #00bebd; color: #00a3a2; }
      button.primary { background: #00bebd; border-color: #00bebd; color: #fff; }
      button.primary:hover:not(:disabled) { background: #00a3a2; color: #fff; }
      button:disabled { opacity: .45; cursor: not-allowed; }
      .log { height: 132px; overflow-y: auto; padding: 6px 8px; font-size: 11px; line-height: 1.6;
             background: #f7f8fa; border-radius: 6px; color: #555; }
      .log .line { white-space: pre-wrap; word-break: break-all; }
      .log .err { color: #d93025; }
      .log .ok { color: #0b8043; }
      .log .warn { color: #b06000; }
      .foot { margin-top: 6px; font-size: 11px; color: #aaa; display: flex; justify-content: space-between; }
    </style>
    <div class="panel">
      <div class="hd" id="hd"><b>BOSS 职位采集</b><span id="stat">就绪</span></div>
      <div class="body" id="body">
        <div class="row"><label>关键词</label><input id="kw" placeholder="前端"></div>
        <div class="row"><label>城市码</label><input id="city" placeholder="101280600"><span class="hint" id="cityhint">深圳</span></div>
        <div class="row"><label>页数</label><input id="pages" type="number" min="1" max="30" step="1"></div>
        <div class="row"><label>每页</label><input id="size" type="number" min="10" max="50" step="10"></div>
        <div class="btns">
          <button class="primary" id="start">开始采集</button>
          <button id="stop" disabled>停止</button>
          <button id="csv" disabled>导出 CSV</button>
          <button id="json" disabled>导出 JSON</button>
        </div>
        <div class="log" id="log"></div>
        <div class="foot"><span>每页间隔 2.5~4.5 秒</span><span id="count">0 条</span></div>
      </div>
    </div>
  `;

  const $ = (id) => root.getElementById(id);
  const el = {
    hd: $('hd'), body: $('body'), kw: $('kw'), city: $('city'), cityhint: $('cityhint'),
    pages: $('pages'), size: $('size'), start: $('start'), stop: $('stop'),
    csv: $('csv'), json: $('json'), log: $('log'), stat: $('stat'), count: $('count'),
  };

  // ---------- 配置 ----------
  function loadCfg() {
    let saved = {};
    try { saved = JSON.parse(localStorage.getItem(SKEY) || '{}'); } catch (e) { /* ignore */ }
    const qs = new URLSearchParams(location.search);
    return Object.assign({}, DEFAULT_CFG, saved, {
      query: saved.query || qs.get('query') || DEFAULT_CFG.query,
      city: saved.city || qs.get('city') || DEFAULT_CFG.city,
    });
  }

  function applyCfg(cfg) {
    el.kw.value = cfg.query;
    el.city.value = cfg.city;
    el.pages.value = cfg.pages;
    el.size.value = cfg.pageSize;
    updateCityHint();
  }

  function readCfg() {
    const cfg = {
      query: (el.kw.value || '').trim() || DEFAULT_CFG.query,
      city: (el.city.value || '').trim() || DEFAULT_CFG.city,
      pages: Math.min(Math.max(parseInt(el.pages.value, 10) || 10, 1), 30),
      pageSize: Math.min(Math.max(parseInt(el.size.value, 10) || 30, 10), 50),
      delayMin: DEFAULT_CFG.delayMin,
      delayMax: DEFAULT_CFG.delayMax,
    };
    try { localStorage.setItem(SKEY, JSON.stringify(cfg)); } catch (e) { /* ignore */ }
    return cfg;
  }

  function updateCityHint() {
    const code = (el.city.value || '').trim();
    el.cityhint.textContent = CITY_HINT[code] || '自定义';
  }

  // ---------- 工具 ----------
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const rand = (a, b) => Math.floor(a + Math.random() * (b - a));

  function log(msg, cls) {
    const line = document.createElement('div');
    line.className = 'line' + (cls ? ' ' + cls : '');
    const t = new Date().toLocaleTimeString('zh-CN', { hour12: false });
    line.textContent = '[' + t + '] ' + msg;
    el.log.appendChild(line);
    el.log.scrollTop = el.log.scrollHeight;
  }

  function updateCount() {
    const companies = new Set(state.rows.map((r) => r.company)).size;
    el.count.textContent = state.rows.length + ' 条 / ' + companies + ' 家';
    el.stat.textContent = state.rows.length ? '已采 ' + state.rows.length : '就绪';
  }

  function parseSalary(text) {
    if (!text) return [null, null];
    let m = /(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*K/i.exec(text);
    if (m) return [Math.round(+m[1]), Math.round(+m[2])];
    m = /(\d+(?:\.\d+)?)\s*K\s*以上/i.exec(text);
    if (m) return [Math.round(+m[1]), null];
    return [null, null];
  }

  function normalize(j, query) {
    const [lo, hi] = parseSalary(j.salaryDesc);
    const id = j.encryptJobId || '';
    return {
      query: query,
      job_name: j.jobName || '',
      salary: j.salaryDesc || '',
      salary_min_k: lo == null ? '' : lo,
      salary_max_k: hi == null ? '' : hi,
      company: j.brandName || '',
      industry: j.brandIndustry || '',
      company_scale: j.brandScaleName || '',
      company_stage: j.brandStageName || '',
      city: j.cityName || '',
      district: j.areaDistrict || '',
      business_area: j.businessDistrict || '',
      experience: j.jobExperience || '',
      degree: j.jobDegree || '',
      skills: (j.skills || []).join(' / '),
      labels: (j.jobLabels || []).join(' / '),
      welfare: (j.welfareList || []).join(' / '),
      boss_name: j.bossName || '',
      boss_title: j.bossTitle || '',
      boss_online: j.bossOnline ? '在线' : '',
      job_id: id,
      security_id: j.securityId || '',
      url: id ? 'https://www.zhipin.com/job_detail/' + id + '.html' : '',
      crawled_at: new Date().toLocaleString('zh-CN', { hour12: false }),
    };
  }

  // ---------- 接口 ----------
  async function fetchPage(cfg, pageNo) {
    const qs = new URLSearchParams({
      scene: '1', query: cfg.query, city: cfg.city,
      page: String(pageNo), pageSize: String(cfg.pageSize),
    });
    const resp = await fetch(API_PATH + '?' + qs.toString(), {
      credentials: 'include',
      headers: { Accept: 'application/json' },
    });
    const text = await resp.text();
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    let data;
    try { data = JSON.parse(text); }
    catch (e) { throw new Error('返回不是 JSON（可能未登录或触发安全验证）'); }
    if (data.code !== 0) throw new Error('code=' + data.code + ' ' + (data.message || data.msg || ''));
    const zp = data.zpData || {};
    return { jobs: zp.jobList || [], hasMore: zp.hasMore !== false };
  }

  // ---------- 主流程 ----------
  async function run() {
    if (state.running) return;
    const cfg = readCfg();
    state.running = true;
    state.stop = false;
    state.rows = [];
    state.seen = new Set();
    el.start.disabled = true;
    el.stop.disabled = false;
    el.csv.disabled = true;
    el.json.disabled = true;
    updateCount();

    log('开始：关键词「' + cfg.query + '」城市 ' + cfg.city + '，最多 ' + cfg.pages + ' 页', 'ok');
    if (!location.pathname.startsWith('/web/geek')) {
      log('提示：当前不在职位搜索页，建议先打开 /web/geek/job 并确认已登录', 'warn');
    }

    try {
      for (let p = 1; p <= cfg.pages; p++) {
        if (state.stop) { log('已手动停止', 'warn'); break; }
        const { jobs, hasMore } = await fetchPage(cfg, p);
        log('第 ' + p + ' 页：' + jobs.length + ' 条');
        if (!jobs.length) { log('空页，结束', 'warn'); break; }
        let added = 0;
        for (const j of jobs) {
          const key = j.encryptJobId || (j.brandName + '|' + j.jobName + '|' + j.salaryDesc);
          if (state.seen.has(key)) continue;
          state.seen.add(key);
          state.rows.push(normalize(j, cfg.query));
          added++;
        }
        updateCount();
        log('累计 ' + state.rows.length + ' 条（本页新增 ' + added + '）');
        if (!hasMore) { log('没有更多页了', 'ok'); break; }
        if (p < cfg.pages) await sleep(rand(cfg.delayMin, cfg.delayMax));
      }
      log('完成：' + state.rows.length + ' 条', 'ok');
    } catch (err) {
      log('出错：' + err.message, 'err');
      log('若是 code!=0 / 非 JSON：停 30 分钟以上，或刷新页面重新登录后再试', 'warn');
    } finally {
      state.running = false;
      el.start.disabled = false;
      el.stop.disabled = true;
      el.csv.disabled = !state.rows.length;
      el.json.disabled = !state.rows.length;
      el.stat.textContent = state.rows.length ? '已采 ' + state.rows.length : '失败';
    }
  }

  // ---------- 导出 ----------
  function download(filename, content, mime) {
    const blob = new Blob([content], { type: mime + ';charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 3000);
  }

  function stamp() {
    const d = new Date();
    const p = (n) => String(n).padStart(2, '0');
    return d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate()) + '_' + p(d.getHours()) + p(d.getMinutes());
  }

  function exportCSV() {
    if (!state.rows.length) return;
    const cols = Object.keys(state.rows[0]);
    const esc = (v) => {
      const s = v == null ? '' : String(v);
      return /[",\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
    };
    const lines = [cols.join(',')].concat(state.rows.map((r) => cols.map((c) => esc(r[c])).join(',')));
    download('boss_zhipin_' + stamp() + '.csv', '\uFEFF' + lines.join('\r\n'), 'text/csv');
    log('已导出 CSV（' + state.rows.length + ' 条）', 'ok');
  }

  function exportJSON() {
    if (!state.rows.length) return;
    download('boss_zhipin_' + stamp() + '.json',
      JSON.stringify({ count: state.rows.length, jobs: state.rows }, null, 2), 'application/json');
    log('已导出 JSON（' + state.rows.length + ' 条）', 'ok');
  }

  // ---------- 事件 ----------
  el.hd.addEventListener('click', () => el.body.classList.toggle('hide'));
  el.city.addEventListener('input', updateCityHint);
  el.start.addEventListener('click', run);
  el.stop.addEventListener('click', () => { state.stop = true; });
  el.csv.addEventListener('click', exportCSV);
  el.json.addEventListener('click', exportJSON);

  applyCfg(loadCfg());
  updateCount();
  log('就绪。确认已登录后点「开始采集」', 'ok');
})();
