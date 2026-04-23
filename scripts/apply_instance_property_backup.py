#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
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


def pretty_display_path(path: str) -> str:
    if path.startswith('/mnt/c/'):
        return 'C:\\' + path[7:].replace('/', '\\')
    if path.startswith('/mnt/') and len(path) > 6:
        drive = path[5].upper()
        rest = path[7:].replace('/', '\\')
        return f'{drive}:\\{rest}'
    return path


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


def build_commands(cfg: dict) -> dict:
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
    daily_cmd = base_cmd + ' nightly'
    weekly_cmd = base_cmd + ' weekly'
    return {
        'dailyCronExpr': f'{daily_minute} {daily_hour} * * *',
        'weeklyCronExpr': f'{weekly_minute} {weekly_hour} * * {weekly_day}',
        'dailyCommand': daily_cmd,
        'weeklyCommand': weekly_cmd,
    }


def apply_crontab(cfg: dict) -> dict:
    meta = build_commands(cfg)
    block = '\n'.join([
        MARK_BEGIN,
        f"{meta['dailyCronExpr']} {meta['dailyCommand']}",
        f"{meta['weeklyCronExpr']} {meta['weeklyCommand']}",
        MARK_END,
    ])
    existing = read_current_crontab()
    new_crontab = replace_managed_block(existing, block)
    write_crontab(new_crontab)
    return {
        'ok': True,
        **meta,
        'backupRoot': cfg['backup_root'],
        'backupRootDisplay': cfg.get('backup_root_display') or pretty_display_path(cfg['backup_root']),
        'managedBlockStart': MARK_BEGIN,
        'managedBlockEnd': MARK_END,
    }


def export_portable(cfg: dict, output: Path) -> dict:
    portable = {
        'instance_name': cfg.get('instance_name', ''),
        'daily_time': cfg['daily_time'],
        'weekly_day': cfg['weekly_day'],
        'weekly_time': cfg['weekly_time'],
        'backup_root': cfg['backup_root'],
        'backup_root_display': cfg.get('backup_root_display') or pretty_display_path(cfg['backup_root']),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(portable, ensure_ascii=False, indent=2), encoding='utf-8')
    meta = build_commands(cfg)
    return {
        'ok': True,
        'portableConfig': str(output),
        'backupRootDisplay': portable['backup_root_display'],
        **meta,
        'note': 'Portable config exported. Apply it on the target machine with the generated command or by importing values manually.',
    }


def import_portable(cfg: dict, portable_path: Path) -> dict:
    portable = json.loads(portable_path.read_text(encoding='utf-8'))
    cfg['daily_time'] = portable['daily_time']
    cfg['weekly_day'] = portable['weekly_day']
    cfg['weekly_time'] = portable['weekly_time']
    cfg['backup_root'] = portable['backup_root']
    cfg['backup_root_display'] = portable.get('backup_root_display') or pretty_display_path(portable['backup_root'])
    cfg['instance_backup_dir'] = portable['backup_root']
    cfg['instance_backup_dir_display'] = cfg['backup_root_display']
    return cfg


def main() -> int:
    parser = argparse.ArgumentParser(description='Apply or export instance property backup config.')
    parser.add_argument('--config', required=True)
    parser.add_argument('--export-portable', required=False)
    parser.add_argument('--import-portable', required=False)
    args = parser.parse_args()

    config_path = Path(args.config)
    cfg = json.loads(config_path.read_text(encoding='utf-8'))

    if args.import_portable:
        cfg = import_portable(cfg, Path(args.import_portable))
        config_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding='utf-8')

    if args.export_portable:
        result = export_portable(cfg, Path(args.export_portable))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    result = apply_crontab(cfg)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
