#!/usr/bin/env python3
import json
import re
import subprocess
import datetime as dt
from pathlib import Path

try:
    import akshare as ak
except Exception:
    ak = None

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
DOCS_DIR = ROOT / 'docs'

FUNDS = {
    'SBFZ85': '【基金净值】SBFZ85(总)_衍盛天璇CTA一号私募证券投资基金',
    'SBFZ95': '【基金净值】SBFZ95(总)_衍盛开阳多策略混合私募证券投资基金',
}
ACCOUNT = 'ivanwuyh@163.com'
INDEX_MAP = {
    'sh000001': '上证指数',
    'sh000300': '沪深300',
    'sh000905': '中证500',
    'sh000852': '中证1000',
}


def fetch_mail_rows(code: str, subject: str):
    script = f'''
    tell application "Mail"
      set targetSubject to "{subject}"
      set targetMailbox to mailbox "INBOX" of account "{ACCOUNT}"
      set oldDelims to AppleScript's text item delimiters
      set AppleScript's text item delimiters to "§§REC§§"
      set outLines to {{}}
      repeat with m in (messages of targetMailbox)
        try
          set s to subject of m as string
          if s contains targetSubject then
            set d to (date received of m) as string
            set c to content of m as string
            set c to my replaceText(return, " ", c)
            set c to my replaceText(linefeed, " ", c)
            set c to my replaceText(tab, " ", c)
            set c to my replaceText("§§REC§§", " ", c)
            set end of outLines to (d & "§§FLD§§" & s & "§§FLD§§" & c)
          end if
        end try
      end repeat
      set resultText to outLines as string
      set AppleScript's text item delimiters to oldDelims
      return resultText
    end tell
    on replaceText(find, repl, txt)
      set oldDelims to AppleScript's text item delimiters
      set AppleScript's text item delimiters to find
      set parts to every text item of txt
      set AppleScript's text item delimiters to repl
      set txt to parts as string
      set AppleScript's text item delimiters to oldDelims
      return txt
    end replaceText
    '''
    res = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(res.stderr)
    records = [r for r in res.stdout.strip().split('§§REC§§') if r.strip()]
    rows = []
    pattern = re.compile(rf'{code}\(总\).*?(\d{{4}}-\d{{2}}-\d{{2}})\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+{code}')
    fallback = re.compile(rf'(\d{{4}}-\d{{2}}-\d{{2}})\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+{code}')
    for rec in records:
        parts = rec.split('§§FLD§§')
        if len(parts) != 3:
            continue
        received_at, sub, content = parts
        content = re.sub(r'\s+', ' ', content)
        m = pattern.search(content) or fallback.search(content)
        if not m:
            continue
        valuation_date, unit_nav, accum_nav, nav_assets, paid_in_capital = m.groups()
        rows.append({
            'received_at': received_at,
            'subject': sub,
            'valuation_date': valuation_date,
            'unit_nav': float(unit_nav),
            'accum_nav': float(accum_nav),
            'nav_assets': float(nav_assets),
            'paid_in_capital': float(paid_in_capital),
        })
    rows.sort(key=lambda x: x['valuation_date'])
    if rows:
        first = rows[0]['unit_nav']
        for r in rows:
            r['cum_return'] = round(r['unit_nav'] / first - 1, 8)
    return rows


def enrich(rows):
    first = rows[0]['unit_nav']
    last = rows[-1]['unit_nav']
    rets = [rows[i]['unit_nav']/rows[i-1]['unit_nav'] - 1 for i in range(1, len(rows))]
    mean = sum(rets)/len(rets)
    var = sum((x-mean)**2 for x in rets)/(len(rets)-1) if len(rets) > 1 else 0
    peak = rows[0]
    max_dd = 0
    start = end = rows[0]
    for r in rows:
        if r['unit_nav'] > peak['unit_nav']:
            peak = r
        dd = (peak['unit_nav'] - r['unit_nav']) / peak['unit_nav']
        if dd > max_dd:
            max_dd = dd
            start, end = peak, r
    return {
        'rows': rows,
        'metrics': {
            'latest_nav': last,
            'latest_date': rows[-1]['valuation_date'],
            'since_inception': last / first - 1,
            'last_5d': rows[-1]['unit_nav'] / rows[-6]['unit_nav'] - 1 if len(rows) > 5 else 0,
            'last_20d': rows[-1]['unit_nav'] / rows[-21]['unit_nav'] - 1 if len(rows) > 20 else 0,
            'last_60d': rows[-1]['unit_nav'] / rows[-61]['unit_nav'] - 1 if len(rows) > 60 else 0,
            'annualized_vol': (var ** 0.5) * (252 ** 0.5),
            'max_nav': max(rows, key=lambda r: r['unit_nav']),
            'min_nav': min(rows, key=lambda r: r['unit_nav']),
            'max_drawdown': {'value': max_dd, 'start': start, 'end': end},
        }
    }


def fetch_benchmarks(start_date: str, end_date: str):
    if ak is None:
        raise RuntimeError('akshare not installed')
    start = dt.date.fromisoformat(start_date)
    end = dt.date.fromisoformat(end_date)
    out = {}
    for symbol, name in INDEX_MAP.items():
        df = ak.stock_zh_index_daily(symbol=symbol)
        df = df[(df['date'] >= start) & (df['date'] <= end)]
        series = {str(d): float(c) for d, c in zip(df['date'], df['close'])}
        base = None
        arr = []
        last_val = None
        for d in sorted(series.keys()):
            pass
        for d in date_range_keys(start_date, end_date):
            if d in series:
                last_val = series[d]
            if last_val is None:
                continue
            if base is None:
                base = last_val
            arr.append({'date': d, 'close': round(last_val, 4), 'norm': round(last_val / base, 8)})
        out[name] = arr
    return out


def date_range_keys(start_date: str, end_date: str):
    cur = dt.date.fromisoformat(start_date)
    end = dt.date.fromisoformat(end_date)
    out = []
    while cur <= end:
        if cur.weekday() < 5:
            out.append(cur.isoformat())
        cur += dt.timedelta(days=1)
    return out


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    all_funds = {}
    min_date = None
    max_date = None
    for code, subject in FUNDS.items():
        rows = fetch_mail_rows(code, subject)
        enriched = enrich(rows)
        (DATA_DIR / f'{code.lower()}_nav_enriched.json').write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding='utf-8')
        all_funds[code] = {'name': subject.split('_')[1], 'code': code, **enriched}
        min_date = rows[0]['valuation_date'] if min_date is None else min(min_date, rows[0]['valuation_date'])
        max_date = rows[-1]['valuation_date'] if max_date is None else max(max_date, rows[-1]['valuation_date'])
    benchmarks = fetch_benchmarks(min_date, max_date)
    (DATA_DIR / 'benchmark_indices.json').write_text(json.dumps(benchmarks, ensure_ascii=False, indent=2), encoding='utf-8')
    print('updated data')

if __name__ == '__main__':
    main()
