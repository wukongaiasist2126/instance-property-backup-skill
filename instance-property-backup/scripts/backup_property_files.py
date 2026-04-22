#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

DEFAULT_SOURCE_FILES = [
    'AGENTS.md',
    'BOOTSTRAP.md',
    'HEARTBEAT.md',
    'IDENTITY.md',
    'MEMORY.md',
    'SOUL.md',
    'TOOLS.md',
    'USER.md',
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def load_state(state_file: Path) -> dict:
    if state_file.exists():
        return json.loads(state_file.read_text(encoding='utf-8'))
    return {'files': {}, 'lastRun': None, 'lastMode': None}


def save_state(state_file: Path, state: dict) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')


def run(mode: str, workspace: Path, backup_root: Path, source_files: list[str], state_file: Path) -> dict:
    if mode not in {'nightly', 'weekly'}:
        raise ValueError('mode must be nightly or weekly')

    latest_dir = backup_root / 'latest'
    snapshots_dir = backup_root / 'snapshots'
    weekly_dir = backup_root / 'weekly'
    for p in (backup_root, latest_dir, snapshots_dir, weekly_dir, state_file.parent):
        p.mkdir(parents=True, exist_ok=True)

    state = load_state(state_file)
    now = datetime.now()
    timestamp = now.strftime('%Y-%m-%d_%H%M%S')
    day_dir = snapshots_dir / now.strftime('%Y-%m-%d')
    week_dir = weekly_dir / f"{now.strftime('%G')}-W{now.strftime('%V')}"

    changed: list[str] = []
    unchanged: list[str] = []
    missing: list[str] = []

    for name in source_files:
        src = workspace / name
        if not src.exists():
            missing.append(name)
            continue

        current_hash = sha256_file(src)
        previous_hash = state['files'].get(name, {}).get('sha256')
        is_changed = current_hash != previous_hash

        copy_file(src, latest_dir / name)

        if mode == 'weekly':
            copy_file(src, week_dir / name)
            if is_changed:
                copy_file(src, day_dir / f'{timestamp}_{name}')
                changed.append(name)
            else:
                unchanged.append(name)
        else:
            if is_changed:
                copy_file(src, day_dir / f'{timestamp}_{name}')
                changed.append(name)
            else:
                unchanged.append(name)

        state['files'][name] = {
            'sha256': current_hash,
            'lastBackupAt': now.isoformat(timespec='seconds'),
            'latestPath': str(latest_dir / name),
        }

    report = {
        'mode': mode,
        'runAt': now.isoformat(timespec='seconds'),
        'workspace': str(workspace),
        'backupRoot': str(backup_root),
        'changed': changed,
        'unchanged': unchanged,
        'missing': missing,
        'sourceFiles': source_files,
    }

    report_name = f'{mode}-{timestamp}.json'
    report_path = (week_dir if mode == 'weekly' else day_dir) / report_name
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

    state['lastRun'] = report['runAt']
    state['lastMode'] = mode
    save_state(state_file, state)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description='Backup OpenClaw property files for one instance.')
    parser.add_argument('mode', choices=['nightly', 'weekly'])
    parser.add_argument('--workspace', required=True)
    parser.add_argument('--backup-root', required=True)
    parser.add_argument('--state-file', required=True)
    parser.add_argument('--files', nargs='*', default=DEFAULT_SOURCE_FILES)
    args = parser.parse_args()

    report = run(
        mode=args.mode,
        workspace=Path(args.workspace),
        backup_root=Path(args.backup_root),
        source_files=args.files,
        state_file=Path(args.state_file),
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
