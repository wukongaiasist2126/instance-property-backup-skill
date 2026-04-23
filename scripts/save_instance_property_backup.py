#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from install_instance_property_backup import WEEKDAY_TEXT, pretty_display_path, render_template, resolve_user_entry_dir, write_rendered_outputs


def normalize_backup_root(text: str) -> str:
    raw = text.strip()
    if len(raw) >= 3 and raw[1] == ':' and raw[2] in ('\\', '/'):
        drive = raw[0].lower()
        rest = raw[2:].replace('\\', '/').lstrip('/')
        return f'/mnt/{drive}/{rest}'
    return raw


def main() -> int:
    parser = argparse.ArgumentParser(description='Save and apply instance property backup settings.')
    parser.add_argument('--config', required=True)
    parser.add_argument('--daily-time', required=True)
    parser.add_argument('--weekly-day', required=True)
    parser.add_argument('--weekly-time', required=True)
    parser.add_argument('--backup-root-display', required=True)
    args = parser.parse_args()

    config_path = Path(args.config)
    cfg = json.loads(config_path.read_text(encoding='utf-8'))
    cfg['daily_time'] = args.daily_time
    cfg['weekly_day'] = args.weekly_day
    cfg['weekly_time'] = args.weekly_time
    cfg['backup_root_display'] = args.backup_root_display
    cfg['backup_root'] = normalize_backup_root(args.backup_root_display)
    cfg['instance_backup_dir'] = cfg['backup_root']
    cfg['instance_backup_dir_display'] = args.backup_root_display
    config_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding='utf-8')

    skill_dir = Path(cfg['save_script']).resolve().parents[1]
    doc_template = (skill_dir / 'references' / 'backup-mechanism-template.md').read_text(encoding='utf-8')
    html_template = (skill_dir / 'references' / 'backup-config-page-template.html').read_text(encoding='utf-8')
    output_doc = Path(cfg['doc_path'])
    output_html = Path(cfg['html_path'])
    user_entry_dir = resolve_user_entry_dir()
    config_page_relative_link = output_html.name if output_html.parent == output_doc.parent else str(output_html)
    values = {
        'instance_name': cfg['instance_name'],
        'instance_label': cfg.get('instance_label', cfg['instance_name']),
        'instance_name_json': json.dumps(cfg['instance_name'], ensure_ascii=False),
        'workspace_path': cfg['workspace'],
        'backup_root': cfg['backup_root'],
        'backup_root_display': cfg['backup_root_display'],
        'instance_backup_dir': cfg['instance_backup_dir'],
        'instance_backup_dir_display': cfg['instance_backup_dir_display'],
        'daily_time': cfg['daily_time'],
        'weekly_day_text': WEEKDAY_TEXT.get(cfg['weekly_day'], cfg['weekly_day']),
        'weekly_time': cfg['weekly_time'],
        'script_path': cfg['script_path'],
        'state_file': cfg['state_file'],
        'config_file': str(config_path),
        'doc_path': cfg['doc_path'],
        'config_page_relative_link': config_page_relative_link,
        'user_entry_dir': str(user_entry_dir),
        'daily_time_json': json.dumps(cfg['daily_time'], ensure_ascii=False),
        'weekly_day_json': json.dumps(cfg['weekly_day'], ensure_ascii=False),
        'weekly_time_json': json.dumps(cfg['weekly_time'], ensure_ascii=False),
        'backup_root_json': json.dumps(cfg['backup_root'], ensure_ascii=False),
        'backup_root_display_json': json.dumps(cfg['backup_root_display'], ensure_ascii=False),
        'config_file_json': json.dumps(str(config_path), ensure_ascii=False),
        'apply_script_json': json.dumps(cfg['apply_script'], ensure_ascii=False),
        'save_script_json': json.dumps(cfg['save_script'], ensure_ascii=False),
        'advanced_path_hint': 'workspace/property-backup/',
    }
    write_rendered_outputs(
        output_doc=output_doc,
        output_html=output_html,
        output_config=config_path,
        user_entry_dir=user_entry_dir,
        values=values,
        config_payload=cfg,
        doc_template=doc_template,
        html_template=html_template,
        instance_name=cfg['instance_name'],
    )

    apply_script = Path(cfg['apply_script'])
    proc = subprocess.run(
        ['python3', str(apply_script), '--config', str(config_path)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or proc.stdout.strip() or 'Save failed')

    print(proc.stdout.strip())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
