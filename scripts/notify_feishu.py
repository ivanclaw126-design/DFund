#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
TARGET = 'chat:oc_dfd9a75cca7150babd3a194a323f3470'


def send_feishu(text: str):
    try:
        # 使用 openclaw message send 命令
        result = subprocess.run(
            ['openclaw', 'message', 'send', '--channel', 'feishu', '--target', TARGET, '--message', text],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f'[OK] sent to {TARGET}')
            return True
        else:
            print(f'[ERR] openclaw message: {result.stderr}')
    except FileNotFoundError:
        print('[ERR] openclaw command not found')
    except Exception as e:
        print(f'[ERR] failed: {e}')
    print(f'[LOG] Would send: {text[:100]}')
    return False


def success_message():
    f85 = json.loads((DATA_DIR / 'sbfz85_nav_enriched.json').read_text(encoding='utf-8'))
    f95 = json.loads((DATA_DIR / 'sbfz95_nav_enriched.json').read_text(encoding='utf-8'))
    r85 = f85['rows'][-1]
    r95 = f95['rows'][-1]
    return (
        '📈 DFund 已完成今日更新\n\n'
        f'SBFZ85 (衍盛天璇 CTA 一号): {r85["valuation_date"]}，单位净值 {r85["unit_nav"]:.4f}\n'
        f'SBFZ95 (衍盛开阳多策略混合): {r95["valuation_date"]}，单位净值 {r95["unit_nav"]:.4f}'
    )


def failure_message(err: str):
    return '🚨 DFund 更新失败\n\n错误信息:\n' + err[:1200]


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'success'
    if mode == 'success':
        send_feishu(success_message())
    else:
        err = sys.argv[2] if len(sys.argv) > 2 else 'unknown error'
        send_feishu(failure_message(err))
