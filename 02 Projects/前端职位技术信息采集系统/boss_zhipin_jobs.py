#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOSS直聘 职位采集（前端 · 深圳）
=================================

思路：用 Playwright 启动一个**你自己的**真实浏览器，登录一次后复用会话，
在页面内调用站内搜索接口 /wapi/zpgeek/search/joblist.json 拿结构化 JSON。

为什么这样做：
  1. 列表页是 Vue SPA，HTML 里没有职位数据；
  2. /wapi/ 接口只认浏览器会话里的 cookie（含 __zp_stoken__），requests 直连拿不到；
  3. 页面上的工资被 @font-face 私有区字符混淆（U+E000~U+F8FF），
     只有接口返回的 salaryDesc 是真实可读的 "18-22K"。

依赖：
    pip install playwright
    # 用本机已装的 Chrome/Edge 即可，不需要 playwright install chromium

用法：
    # 1) 首次登录（打开浏览器，手机扫码，登录完回终端按 Enter）
    python boss_zhipin_jobs.py --login

    # 2) 采集
    python boss_zhipin_jobs.py --keywords 前端,前端开发,web前端 --pages 10

    # 3) 带职位详情（JD 正文），只抓前 30 个，避免请求过多
    python boss_zhipin_jobs.py --detail --detail-limit 30

输出（默认 ./data/）：
    jobs_YYYYmmdd_HHMM.jsonl   逐条完整 JSON
    jobs_YYYYmmdd_HHMM.csv     Excel 可直接打开（UTF-8 BOM）

注意：
    * 只用于个人求职分析，控制频率（默认每页 2~4 秒随机间隔），不要并发；
    * 搜索接口单关键词通常最多返回前 10 页左右，想覆盖更多岗位请换关键词/筛选条件；
    * 遇到 code != 0 或跳转到安全验证，说明触发风控：停 30 分钟以上、换关键词再试，
      必要时重新 --login。
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

# 引擎选择：优先 patchright（Playwright 的反检测补丁版，API 完全一致），
# BOSS 会检测 Playwright 的 CDP 特征（Runtime.enable 泄漏 / --enable-automation /
# navigator.webdriver），自动化浏览器打开 1~2 秒会被重定向到 about:blank（白屏）。
try:  # pip install patchright
    from patchright.sync_api import sync_playwright  # type: ignore

    ENGINE = "patchright"
except ImportError:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore

        ENGINE = "playwright"
    except ImportError:  # pragma: no cover
        sys.exit("缺少 playwright，请先执行：pip install playwright\n"
                 "（强烈建议改用 patchright：pip install patchright）")

HOME = "https://www.zhipin.com/web/geek/job"
SEARCH_API = "/wapi/zpgeek/search/joblist.json"
DETAIL_API = "/wapi/zpgeek/job/detail.json"

# 城市 code 来自 https://www.zhipin.com/wapi/zpgeek/common/data/city/site.json
CITY_CODES = {
    "全国": "100010000",
    "北京": "101010100",
    "上海": "101020100",
    "广州": "101280100",
    "深圳": "101280600",
    "杭州": "101210100",
    "成都": "101270100",
    "南京": "101190100",
    "武汉": "101200100",
    "东莞": "101281600",
    "佛山": "101280800",
    "珠海": "101280700",
    "苏州": "101190400",
    "西安": "101110100",
    "长沙": "101250100",
    "厦门": "101230200",
}

CSV_FIELDS = [
    "query", "job_name", "salary", "salary_min_k", "salary_max_k",
    "company", "industry", "company_scale", "company_stage",
    "city", "district", "business_area",
    "experience", "degree", "skills", "labels", "welfare",
    "boss_name", "boss_title", "boss_online",
    "job_id", "security_id", "url", "crawled_at",
]


# ---------------------------------------------------------------- 浏览器

def launch_browser(p, profile_dir: str, headless: bool):
    """优先用本机 Chrome，其次 Edge，最后内置 chromium。"""
    last_err = None
    for channel in ("chrome", "msedge", None):
        kwargs = dict(
            user_data_dir=profile_dir,
            headless=headless,
            locale="zh-CN",
            viewport={"width": 1440, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        if channel:
            kwargs["channel"] = channel
        try:
            ctx = p.chromium.launch_persistent_context(**kwargs)
            print(f"[browser] 启动成功：{channel or '内置 chromium'}"
                  f"（引擎={ENGINE}，{'无头' if headless else '有界面'}，profile={profile_dir}）")
            if ENGINE == "playwright":
                print("[browser] ⚠️  当前是原版 Playwright，BOSS 大概率会检测到并白屏；"
                      "建议 pip install patchright 后重试。")
            return ctx
        except Exception as exc:  # noqa: BLE001
            last_err = exc
    sys.exit(f"[browser] 启动失败：{last_err}")


def open_page(ctx, timeout=60_000):
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.set_default_timeout(timeout)
    return page


def goto_home(page):
    """进入职位搜索页，建立会话（这一步决定后续 fetch 能不能带上 cookie）。"""
    page.goto(HOME, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(2500)
    # SPA 建立会话需要一点时间；若被重定向到 about:blank 说明触发了风控
    if page.url.startswith("about:"):
        raise RuntimeError("页面被重定向到 about:blank，疑似触发风控，请稍后再试或重新登录")


# ---------------------------------------------------------------- 接口调用

def api_get(page, path: str) -> dict:
    """在页面上下文里发 fetch，自动带上登录 cookie。"""
    res = page.evaluate(
        """async ({u}) => {
            try {
                const r = await fetch(u, {
                    credentials: 'include',
                    headers: { 'Accept': 'application/json' },
                });
                return { status: r.status, body: await r.text() };
            } catch (e) {
                return { status: -1, body: String(e) };
            }
        }""",
        {"u": path},
    )
    return res


def search_path(query: str, city_code: str, page_no: int, page_size: int) -> str:
    qs = urlencode(
        {"scene": 1, "query": query, "city": city_code,
         "page": page_no, "pageSize": page_size},
        encoding="utf-8",
    )
    return f"{SEARCH_API}?{qs}"


def parse_salary(text: str) -> tuple[int | None, int | None]:
    """'18-22K' -> (18,22); '15-20K·13薪' -> (15,20); '面议' -> (None,None)"""
    if not text:
        return None, None
    t = text.replace("·", "·")
    m = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*K", t, re.I)
    if m:
        return int(float(m.group(1))), int(float(m.group(2)))
    m = re.search(r"(\d+(?:\.\d+)?)\s*K\s*以上", t, re.I)
    if m:
        return int(float(m.group(1))), None
    return None, None


def normalize(raw: dict, query: str, city_name: str) -> dict:
    lo, hi = parse_salary(raw.get("salaryDesc", ""))
    job_id = raw.get("encryptJobId") or ""
    return {
        "query": query,
        "job_name": raw.get("jobName") or "",
        "salary": raw.get("salaryDesc") or "",
        "salary_min_k": lo,
        "salary_max_k": hi,
        "company": raw.get("brandName") or "",
        "industry": raw.get("brandIndustry") or "",
        "company_scale": raw.get("brandScaleName") or "",
        "company_stage": raw.get("brandStageName") or "",
        "city": raw.get("cityName") or city_name,
        "district": raw.get("areaDistrict") or "",
        "business_area": raw.get("businessDistrict") or "",
        "experience": raw.get("jobExperience") or "",
        "degree": raw.get("jobDegree") or "",
        "skills": " / ".join(raw.get("skills") or []),
        "labels": " / ".join(raw.get("jobLabels") or []),
        "welfare": " / ".join(raw.get("welfareList") or []),
        "boss_name": raw.get("bossName") or "",
        "boss_title": raw.get("bossTitle") or "",
        "boss_online": bool(raw.get("bossOnline")),
        "job_id": job_id,
        "security_id": raw.get("securityId") or "",
        "url": f"https://www.zhipin.com/job_detail/{job_id}.html" if job_id else "",
        "crawled_at": datetime.now().isoformat(timespec="seconds"),
    }


def fetch_job_detail(page, security_id: str) -> dict:
    """职位详情（JD 正文、地址、公司信息）。"""
    if not security_id:
        return {}
    res = api_get(page, f"{DETAIL_API}?{urlencode({'securityId': security_id})}")
    if res["status"] != 200:
        return {}
    try:
        data = json.loads(res["body"])
    except json.JSONDecodeError:
        return {}
    if data.get("code") != 0:
        return {}
    zp = data.get("zpData") or {}
    job = zp.get("jobInfo") or {}
    boss = zp.get("bossInfo") or {}
    brand = zp.get("brandComInfo") or {}
    return {
        "description": re.sub(r"<[^>]+>", "\n", job.get("postDescription") or "").strip(),
        "address": job.get("address") or "",
        "location": job.get("locationName") or "",
        "skills_detail": " / ".join(job.get("showSkills") or []),
        "company_name": brand.get("brandName") or "",
        "company_industry": brand.get("industryName") or "",
        "company_scale": brand.get("scaleName") or "",
        "company_stage": brand.get("stageName") or "",
        "boss_name": boss.get("name") or "",
        "boss_title": boss.get("title") or "",
    }


def collect_keyword(page, keyword: str, city_code: str, city_name: str,
                    pages: int, page_size: int, delay: tuple[float, float]) -> list[dict]:
    rows: list[dict] = []
    for page_no in range(1, pages + 1):
        path = search_path(keyword, city_code, page_no, page_size)
        res = api_get(page, path)
        if res["status"] != 200:
            print(f"  ! HTTP {res['status']}：{str(res['body'])[:120]}")
            break
        try:
            data = json.loads(res["body"])
        except json.JSONDecodeError:
            print(f"  ! 返回不是 JSON：{str(res['body'])[:120]}")
            break

        code = data.get("code")
        if code != 0:
            print(f"  ! 接口 code={code} message={data.get('message') or data.get('msg') or ''}")
            print("    触发安全校验的常见处理：停 30 分钟以上；换关键词；重新 --login。")
            break

        zp = data.get("zpData") or {}
        jobs = zp.get("jobList") or []
        print(f"  第 {page_no} 页：{len(jobs)} 条  hasMore={zp.get('hasMore')}")
        if not jobs:
            break
        rows.extend(normalize(j, keyword, city_name) for j in jobs)
        if zp.get("hasMore") is False:
            break
        if page_no < pages:
            time.sleep(random.uniform(*delay))
    return rows


# ---------------------------------------------------------------- 输出

def save(rows: list[dict], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    jsonl = out_dir / f"jobs_{stamp}.jsonl"
    csv_path = out_dir / f"jobs_{stamp}.csv"

    with jsonl.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    fields = list(rows[0].keys()) if rows else CSV_FIELDS
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return csv_path, jsonl


def summarize(rows: list[dict]):
    if not rows:
        print("没有采到数据。")
        return
    print(f"\n共 {len(rows)} 条，公司 {len({r['company'] for r in rows})} 家")
    lows = [r["salary_min_k"] for r in rows if r.get("salary_min_k")]
    highs = [r["salary_max_k"] for r in rows if r.get("salary_max_k")]
    if lows and highs:
        print(f"薪资区间（K/月）：最低中位 {sorted(lows)[len(lows)//2]}，"
              f"最高中位 {sorted(highs)[len(highs)//2]}")
    top = {}
    for r in rows:
        top[r["company"]] = top.get(r["company"], 0) + 1
    print("招聘最多的公司：", "，".join(f"{k}({v})" for k, v in
                                  sorted(top.items(), key=lambda kv: -kv[1])[:5]))


# ---------------------------------------------------------------- 主流程

def cmd_login(args):
    with sync_playwright() as p:
        ctx = launch_browser(p, args.profile, headless=False)
        page = open_page(ctx)
        page.goto(HOME, wait_until="domcontentloaded", timeout=60_000)
        print("\n浏览器已打开：请用手机 App 扫码登录 BOSS 直聘，登录成功后回到这里。")
        input("登录完成后按 Enter 继续... ")
        ok, msg = probe(page, args.keywords.split(",")[0], CITY_CODES.get(args.city, args.city))
        print(("✅ 接口可用：" if ok else "⚠️  接口仍不可用：") + msg)
        ctx.close()


def probe(page, keyword: str, city_code: str) -> tuple[bool, str]:
    res = api_get(page, search_path(keyword, city_code, 1, 15))
    if res["status"] != 200:
        return False, f"HTTP {res['status']}"
    try:
        data = json.loads(res["body"])
    except json.JSONDecodeError:
        return False, "返回不是 JSON（可能需要登录或触发验证）"
    if data.get("code") != 0:
        return False, f"code={data.get('code')} {data.get('message') or ''}"
    jobs = (data.get("zpData") or {}).get("jobList") or []
    return True, f"第 1 页取到 {len(jobs)} 条职位"


def cmd_collect(args):
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    city_code = CITY_CODES.get(args.city, args.city)
    delay = (args.delay_min, args.delay_max)

    with sync_playwright() as p:
        ctx = launch_browser(p, args.profile, headless=args.headless)
        try:
            page = open_page(ctx)
            goto_home(page)
            ok, msg = probe(page, keywords[0], city_code)
            if not ok:
                print(f"⚠️  预检失败：{msg}")
                print("   请先运行：python boss_zhipin_jobs.py --login")
                return
            print(f"✅ 预检通过：{msg}\n")

            all_rows: list[dict] = []
            seen: set[str] = set()
            for kw in keywords:
                print(f"[{kw}] 城市={args.city}({city_code}) 最多 {args.pages} 页")
                rows = collect_keyword(page, kw, city_code, args.city,
                                       args.pages, args.page_size, delay)
                for row in rows:
                    key = row["job_id"] or f"{row['company']}|{row['job_name']}|{row['salary']}"
                    if key in seen:
                        continue
                    seen.add(key)
                    all_rows.append(row)
                time.sleep(random.uniform(*delay))

            if args.detail and all_rows:
                print(f"\n抓取职位详情（前 {args.detail_limit} 条）...")
                for i, row in enumerate(all_rows[: args.detail_limit], 1):
                    detail = fetch_job_detail(page, row.get("security_id", ""))
                    row.update(detail)
                    print(f"  {i}/{min(len(all_rows), args.detail_limit)} {row['job_name']}")
                    time.sleep(random.uniform(*delay))

            csv_path, jsonl_path = save(all_rows, Path(args.out))
            summarize(all_rows)
            print(f"\nCSV : {csv_path}")
            print(f"JSONL: {jsonl_path}")
        finally:
            ctx.close()


def main():
    ap = argparse.ArgumentParser(
        description="BOSS直聘 职位采集（复用本机登录态，调用站内搜索接口）")
    ap.add_argument("--login", action="store_true", help="首次登录：打开浏览器扫码，保存会话")
    ap.add_argument("--keywords", default="前端",
                    help="关键词，逗号分隔，如 前端,前端开发,web前端,React")
    ap.add_argument("--city", default="深圳", help="城市名（见脚本内 CITY_CODES）或直接给 code")
    ap.add_argument("--pages", type=int, default=10, help="每个关键词最多翻几页（默认 10）")
    ap.add_argument("--page-size", type=int, default=30, help="每页条数（默认 30）")
    ap.add_argument("--detail", action="store_true", help="额外抓取 JD 正文等详情")
    ap.add_argument("--detail-limit", type=int, default=30, help="详情最多抓多少条")
    ap.add_argument("--delay-min", type=float, default=2.0)
    ap.add_argument("--delay-max", type=float, default=4.0)
    ap.add_argument("--out", default="data", help="输出目录（默认 ./data）")
    ap.add_argument("--profile", default=".browser_profile", help="浏览器用户目录（保存登录态）")
    ap.add_argument("--headless", action="store_true",
                    help="无头模式（更快但更容易被识别，建议不加）")
    args = ap.parse_args()

    if args.login:
        cmd_login(args)
    else:
        cmd_collect(args)


if __name__ == "__main__":
    main()
