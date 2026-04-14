#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
TARGET = 'user:ou_65f872e3769176d5575eec0965746ee8'


def send_text(text: str):
    script = f'''tell application "System Events" to do shell script "python3 - <<'PY'\nprint('noop')\nPY"'''
    # Placeholder wrapper kept minimal; actual send uses OpenClaw message tool through CLI bridge if available.
    subprocess.run(['python3', '-c', 'print("notify placeholder")'], check=False)
    print(text)


def success_message():
    f85 = json.loads((DATA_DIR / 'sbfz85_nav_enriched.json').read_text(encoding='utf-8'))
    f95 = json.loads((DATA_DIR / 'sbfz95_nav_enriched.json').read_text(encoding='utf-8'))
    r85 = f85['rows'][-1]
    r95 = f95['rows'][-1]
    return (
        'DFund 已完成今日更新\n\n'
        f'SBFZ85: {r85["valuation_date"]}，单位净值 {r85["unit_nav"]:.4f}\n'
        f'SBFZ95: {r95["valuation_date"]}，单位净值 {r95["unit_nav"]:.4f}'
    )


def failure_message(err: str):
    return f'DFund 更新失败\n\n错误信息:\n{err[:1200]}'


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'success'
    if mode == 'success':
        send_text(success_message())
    else:
        err = sys.argv[2] if len(sys.argv) > 2 else 'unknown error'
        send_text(failure_message(err))
