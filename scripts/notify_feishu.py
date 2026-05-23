#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
TARGET = 'chat:oc_dfd9a75cca7150babd3a194a323f3470'
OPENCLAW = shutil.which('openclaw') or '/Users/spicyclaw/.npm-global/bin/openclaw'


def send_feishu(text: str):
    env = os.environ.copy()
    env['PATH'] = '/Users/spicyclaw/.npm-global/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:' + env.get('PATH', '')
    candidates = [
        [OPENCLAW, 'message', 'send', '--channel', 'feishu', '--target', TARGET, '--message', text],
        [OPENCLAW, 'message', 'send', '--channel', 'feishu', '-t', TARGET, '-m', text],
    ]

    for cmd in candidates:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                env=env,
            )
            if result.returncode == 0:
                print(f"[OK] sent to {TARGET} via: {' '.join(cmd[:6])} ...")
                return True
            err = (result.stderr or result.stdout or '').strip()
            print(f"[ERR] {' '.join(cmd[:6])} ...: {err}")
        except FileNotFoundError:
            print(f'[ERR] openclaw command not found: {cmd[0]}')
            break
        except Exception as e:
            print(f'[ERR] failed: {e}')

    print(f'[LOG] Would send: {text}')
    return False


def success_message():
    f85 = json.loads((DATA_DIR / 'sbfz85_nav_enriched.json').read_text(encoding='utf-8'))
    f95 = json.loads((DATA_DIR / 'sbfz95_nav_enriched.json').read_text(encoding='utf-8'))
    r85 = f85['rows'][-1]
    r95 = f95['rows'][-1]
    cta_principal = 470000
    cta_value = round(cta_principal * r85['unit_nav'])
    return (
        '📈 DFund 已完成今日更新\n\n'
        f'SBFZ85 (衍盛天璇 CTA 一号): {r85["valuation_date"]}，单位净值 {r85["unit_nav"]:.4f}，47万本金当前约 {cta_value:,} 元\n'
        f'SBFZ95 (衍盛开阳多策略混合): {r95["valuation_date"]}，单位净值 {r95["unit_nav"]:.4f}'
    )


def failure_message(err: str):
    return '🚨 DFund 更新失败\n\n错误信息:\n' + err[:1200]


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'success'
    if mode == 'success':
        ok = send_feishu(success_message())
    else:
        err = sys.argv[2] if len(sys.argv) > 2 else 'unknown error'
        ok = send_feishu(failure_message(err))
    sys.exit(0 if ok else 2)
