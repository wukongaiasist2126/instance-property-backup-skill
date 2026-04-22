#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
from pathlib import Path

DEFAULT_FILES = [
    'AGENTS.md',
    'BOOTSTRAP.md',
    'HEARTBEAT.md',
    'IDENTITY.md',
    'MEMORY.md',
    'SOUL.md',
    'TOOLS.md',
    'USER.md',
]
WEEKDAY_TEXT = {
    '0': '周日', '1': '周一', '2': '周二', '3': '周三', '4': '周四', '5': '周五', '6': '周六',
}


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r'[^a-z0-9\u4e00-\u9fff]+', '-', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text or 'instance'


def render_template(template: str, values: dict[str, str]) -> str:
    out = template
    for key, value in values.items():
        out = out.replace('{{' + key + '}}', value)
    return out


def resolve_user_entry_dir() -> Path:
    system = platform.system()
    if system == 'Windows':
        home = Path.home()
        return home / 'Documents' / 'OpenClaw' / 'Property Backup'
    if system == 'Darwin':
        return Path.home() / 'Documents' / 'OpenClaw' / 'Property Backup'

    candidate_windows_docs = [
        Path('/mnt/c/Users/AI/Documents'),
    ]
    userprofile = os.environ.get('USERPROFILE')
    if userprofile:
        candidate_windows_docs.insert(0, Path(userprofile) / 'Documents')
    for doc_dir in candidate_windows_docs:
        if doc_dir.exists() and doc_dir.is_dir():
            return doc_dir / 'OpenClaw' / 'Property Backup'

    return Path.home() / 'Documents' / 'OpenClaw' / 'Property Backup'


def pretty_display_path(path: Path) -> str:
    text = str(path)
    if text.startswith('/mnt/c/'):
        return 'C:\\' + text[7:].replace('/', '\\')
    if text.startswith('/mnt/') and len(text) > 6:
        drive = text[5].upper()
        rest = text[7:].replace('/', '\\')
        return f'{drive}:\\{rest}'
    return text


def mirror_user_entry(output_html: Path, user_entry_dir: Path, instance_name: str) -> Path:
    user_entry_dir.mkdir(parents=True, exist_ok=True)
    final_name = f'{instance_name}_property-file-backup-settings.html'
    legacy_names = [
        'property-file-backup-settings.html',
        '打开这里配置属性文件备份任务.html',
        f"{slugify(instance_name).replace('-', '_')}_property_file_backup_settings.html",
        '属性文件备份设置.html',
    ]
    user_html = user_entry_dir / final_name
    shutil.copy2(output_html, user_html)
    for legacy_name in legacy_names:
        legacy_path = user_entry_dir / legacy_name
        if legacy_path.exists() and legacy_path != user_html:
            legacy_path.unlink()
    return user_html


def main() -> int:
    parser = argparse.ArgumentParser(description='Install instance property backup files.')
    parser.add_argument('--instance-name', required=True)
    parser.add_argument('--workspace', required=True)
    parser.add_argument('--backup-root', required=True)
    parser.add_argument('--daily-time', required=True)
    parser.add_argument('--weekly-day', required=True)
    parser.add_argument('--weekly-time', required=True)
    parser.add_argument('--skill-dir', required=True)
    parser.add_argument('--output-script', required=True)
    parser.add_argument('--output-doc', required=True)
    parser.add_argument('--output-html', required=True)
    parser.add_argument('--output-config', required=True)
    parser.add_argument('--state-file', required=True)
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir)
    backup_script_template = (skill_dir / 'scripts' / 'backup_property_files.py').read_text(encoding='utf-8')
    doc_template = (skill_dir / 'references' / 'backup-mechanism-template.md').read_text(encoding='utf-8')
    html_template = (skill_dir / 'references' / 'backup-config-page-template.html').read_text(encoding='utf-8')

    output_script = Path(args.output_script)
    output_doc = Path(args.output_doc)
    output_html = Path(args.output_html)
    output_config = Path(args.output_config)
    state_file = Path(args.state_file)
    workspace = Path(args.workspace)
    user_entry_dir = resolve_user_entry_dir()
    backup_root = user_entry_dir / args.instance_name
    instance_dir = backup_root

    output_script.parent.mkdir(parents=True, exist_ok=True)
    output_doc.parent.mkdir(parents=True, exist_ok=True)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_config.parent.mkdir(parents=True, exist_ok=True)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    instance_dir.mkdir(parents=True, exist_ok=True)

    output_script.write_text(backup_script_template, encoding='utf-8')

    apply_script = skill_dir / 'scripts' / 'apply_instance_property_backup.py'

    config_payload = {
        'daily_time': args.daily_time,
        'weekly_day': args.weekly_day,
        'weekly_time': args.weekly_time,
        'backup_root': str(backup_root),
        'backup_root_display': pretty_display_path(backup_root),
        'instance_backup_dir': str(instance_dir),
        'instance_backup_dir_display': pretty_display_path(instance_dir),
        'workspace': str(workspace),
        'doc_path': str(output_doc),
        'html_path': str(output_html),
        'script_path': str(output_script),
        'apply_script': str(apply_script),
        'state_file': str(state_file),
        'source_files': DEFAULT_FILES,
    }
    output_config.write_text(json.dumps(config_payload, ensure_ascii=False, indent=2), encoding='utf-8')

    config_page_relative_link = output_html.name if output_html.parent == output_doc.parent else str(output_html)

    values = {
        'instance_name': args.instance_name,
        'workspace_path': str(workspace),
        'backup_root': str(backup_root),
        'backup_root_display': pretty_display_path(backup_root),
        'instance_backup_dir': str(instance_dir),
        'instance_backup_dir_display': pretty_display_path(instance_dir),
        'daily_time': args.daily_time,
        'weekly_day_text': WEEKDAY_TEXT.get(args.weekly_day, args.weekly_day),
        'weekly_time': args.weekly_time,
        'script_path': str(output_script),
        'state_file': str(state_file),
        'config_file': str(output_config),
        'doc_path': str(output_doc),
        'config_page_relative_link': config_page_relative_link,
        'user_entry_dir': str(user_entry_dir),
        'daily_time_json': json.dumps(args.daily_time, ensure_ascii=False),
        'weekly_day_json': json.dumps(args.weekly_day, ensure_ascii=False),
        'weekly_time_json': json.dumps(args.weekly_time, ensure_ascii=False),
        'backup_root_json': json.dumps(str(backup_root), ensure_ascii=False),
        'backup_root_display_json': json.dumps(pretty_display_path(backup_root), ensure_ascii=False),
        'config_file_json': json.dumps(str(output_config), ensure_ascii=False),
        'apply_script_json': json.dumps(str(apply_script), ensure_ascii=False),
        'advanced_path_hint': 'workspace/property-backup/',
    }
    output_doc.write_text(render_template(doc_template, values), encoding='utf-8')
    output_html.write_text(render_template(html_template, values), encoding='utf-8')
    user_html = mirror_user_entry(output_html, user_entry_dir, args.instance_name)
    output_config.write_text(json.dumps({**config_payload, 'user_entry_html': str(user_html)}, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
