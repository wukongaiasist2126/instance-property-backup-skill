#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

WEEKDAY_TO_CRON = {
    '周日': '0', '周一': '1', '周二': '2', '周三': '3', '周四': '4', '周五': '5', '周六': '6',
    '0': '0', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6',
}

MARK_BEGIN = '# >>> instance-property-backup >>>'
MARK_END = '# <<< instance-property-backup <<<'


def hhmm_to_cron(text: str) -> tuple[str, str]:
    hour, minute = text.strip().split(':')
    return minute, hour


def sh_quote(text: str) -> str:
    return "'" + text.replace("'", "'\"'\"'") + "'"


def read_current_crontab() -> str:
    proc = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
    if proc.returncode == 0:
        return proc.stdout.rstrip() + ('\n' if proc.stdout and not proc.stdout.endswith('\n') else '')
    stderr = (proc.stderr or '').lower()
    if 'no crontab' in stderr:
        return ''
    raise RuntimeError(proc.stderr.strip() or 'failed to read crontab')


def write_crontab(content: str) -> None:
    subprocess.run(['crontab', '-'], input=content, text=True, check=True)


def replace_managed_block(existing: str, new_block: str) -> str:
    lines = existing.splitlines()
    kept: list[str] = []
    inside = False
    for line in lines:
        if line.strip() == MARK_BEGIN:
            inside = True
            continue
        if line.strip() == MARK_END:
            inside = False
            continue
        if not inside:
            kept.append(line)
    while kept and not kept[-1].strip():
        kept.pop()
    body = '\n'.join(kept)
    if body:
        body += '\n\n'
    return body + new_block + '\n'


def build_block(cfg: dict) -> tuple[str, dict]:
    daily_minute, daily_hour = hhmm_to_cron(cfg['daily_time'])
    weekly_minute, weekly_hour = hhmm_to_cron(cfg['weekly_time'])
    weekly_day = WEEKDAY_TO_CRON.get(str(cfg['weekly_day']), str(cfg['weekly_day']))

    script_path = Path(cfg['script_path'])
    workspace = cfg['workspace']
    backup_root = cfg['backup_root']
    state_file = cfg['state_file']

    base_cmd = (
        f"cd {sh_quote(workspace)} && "
        f"python3 {sh_quote(str(script_path))} "
        f"--workspace {sh_quote(workspace)} "
        f"--backup-root {sh_quote(backup_root)} "
        f"--state-file {sh_quote(state_file)}"
    )
    daily_cmd = base_cmd + ' --mode nightly'
    weekly_cmd = base_cmd + ' --mode weekly'

    block = '\n'.join([
        MARK_BEGIN,
        f"{daily_minute} {daily_hour} * * * {daily_cmd}",
        f"{weekly_minute} {weekly_hour} * * {weekly_day} {weekly_cmd}",
        MARK_END,
    ])
    return block, {
        'dailyCronExpr': f'{daily_minute} {daily_hour} * * *',
        'weeklyCronExpr': f'{weekly_minute} {weekly_hour} * * {weekly_day}',
        'dailyCommand': daily_cmd,
        'weeklyCommand': weekly_cmd,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Apply updated instance property backup config.')
    parser.add_argument('--config', required=True)
    args = parser.parse_args()

    config_path = Path(args.config)
    cfg = json.loads(config_path.read_text(encoding='utf-8'))

    existing = read_current_crontab()
    block, meta = build_block(cfg)
    new_crontab = replace_managed_block(existing, block)
    write_crontab(new_crontab)

    result = {
        'ok': True,
        **meta,
        'backupRoot': cfg['backup_root'],
        'managedBlockStart': MARK_BEGIN,
        'managedBlockEnd': MARK_END,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
