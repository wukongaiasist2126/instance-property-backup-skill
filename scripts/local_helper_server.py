#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from install_instance_property_backup import render_template

from save_instance_property_backup import main as save_main  # type: ignore


def choose_folder(initial: str) -> str:
    windows_initial = initial.replace('\\', '\\\\')
    ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms | Out-Null
$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$dialog.Description = '请选择备份目录'
$dialog.UseDescriptionForTitle = $true
if ('{windows_initial}') {{ $dialog.SelectedPath = '{windows_initial}' }}
if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {{
  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
  Write-Output $dialog.SelectedPath
}}
""".strip()
    proc = subprocess.run(
        ['powershell.exe', '-NoProfile', '-STA', '-Command', ps_script],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or 'folder picker failed')
    return (proc.stdout or '').strip()


class Handler(BaseHTTPRequestHandler):
    config_path: Path = Path('.')
    ui_template_path: Path = Path('.')

    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in ('/', '/ui'):
            cfg = json.loads(self.config_path.read_text(encoding='utf-8'))
            values = {
                'instance_name': cfg['instance_name'],
                'daily_time': cfg['daily_time'],
                'weekly_time': cfg['weekly_time'],
                'weekly_day_json': json.dumps(cfg['weekly_day'], ensure_ascii=False),
                'daily_time_json': json.dumps(cfg['daily_time'], ensure_ascii=False),
                'weekly_time_json': json.dumps(cfg['weekly_time'], ensure_ascii=False),
                'backup_root_display_json': json.dumps(cfg['backup_root_display'], ensure_ascii=False),
                'backup_root_display': cfg['backup_root_display'],
            }
            html = render_template(self.ui_template_path.read_text(encoding='utf-8'), values)
            body = html.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == '/config':
            cfg = json.loads(self.config_path.read_text(encoding='utf-8'))
            self._json({'ok': True, 'config': cfg})
            return
        if parsed.path == '/choose-folder':
            cfg = json.loads(self.config_path.read_text(encoding='utf-8'))
            qs = parse_qs(parsed.query)
            initial = qs.get('initial', [cfg.get('backup_root_display', '')])[0]
            chosen = choose_folder(initial)
            self._json({'ok': bool(chosen), 'path': chosen})
            return
        self._json({'ok': False, 'error': 'not found'}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != '/save':
            self._json({'ok': False, 'error': 'not found'}, status=404)
            return
        length = int(self.headers.get('Content-Length', '0'))
        payload = json.loads(self.rfile.read(length).decode('utf-8') or '{}')
        argv = [
            'save_instance_property_backup.py',
            '--config', str(self.config_path),
            '--daily-time', payload['daily_time'],
            '--weekly-day', str(payload['weekly_day']),
            '--weekly-time', payload['weekly_time'],
            '--backup-root-display', payload['backup_root_display'],
        ]
        old_argv = sys.argv[:]
        try:
            sys.argv = argv
            save_main()
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else 1
            if code == 0:
                cfg = json.loads(self.config_path.read_text(encoding='utf-8'))
                self._json({'ok': True, 'config': cfg})
            else:
                self._json({'ok': False, 'error': str(exc)}, status=500)
        except Exception as exc:  # noqa: BLE001
            self._json({'ok': False, 'error': str(exc)}, status=500)
        finally:
            sys.argv = old_argv


def main() -> int:
    parser = argparse.ArgumentParser(description='Local helper server for instance property backup settings.')
    parser.add_argument('--config', required=True)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--open-browser', action='store_true')
    parser.add_argument('--ui-template', required=True)
    args = parser.parse_args()

    Handler.config_path = Path(args.config)
    Handler.ui_template_path = Path(args.ui_template)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    if args.open_browser:
        webbrowser.open(f'http://{args.host}:{args.port}/ui')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
