#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

from save_instance_property_backup import main as save_main

WEEKDAY_MAP = {
    '0': '周日', '1': '周一', '2': '周二', '3': '周三', '4': '周四', '5': '周五', '6': '周六'
}
WEEKDAY_ALIASES = {
    '0': '0', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6',
    '周日': '0', '周天': '0', 'sunday': '0',
    '周一': '1', 'monday': '1',
    '周二': '2', 'tuesday': '2',
    '周三': '3', 'wednesday': '3',
    '周四': '4', 'thursday': '4',
    '周五': '5', 'friday': '5',
    '周六': '6', 'saturday': '6',
}
TIME_RE = re.compile(r'^(?:[01]\d|2[0-3]):[0-5]\d$')

TEXT = {
    'zh': {
        'lang_prompt': 'C-中文，E-English\n请输入：',
        'lang_invalid': '输入无效，请输入 C 或 E。',
        'title': '{instance_name} 属性文件备份设置 / Property File Backup Setup',
        'intro': '请按提示逐项配置，最后统一确认保存。',
        'confirm': '你输入的是：{value_label}{value}。确认请输入 Y，重新输入请按其他键：',
        'ask_time': '{question}（默认为 {default}，24 小时制）。格式例如 01:00。直接回车表示使用默认值。\n请输入：',
        'time_invalid': '输入格式不对，请按 24 小时制 HH:MM 重新输入。',
        'ask_weekday': '请给出你希望的每周备份星期（默认为 {default_label}，可输入 0-6 或 周一/周二 等）。直接回车表示使用默认值。\n请输入：',
        'weekday_invalid': '星期输入无效，请重新输入。',
        'ask_path': '请给出你希望的备份路径。\n默认备份路径：{default}\n你可以直接输入或粘贴新路径；在 Windows 命令窗口里，通常可用右键粘贴，部分环境可用 Ctrl+Shift+V。\n直接回车表示使用默认值。\n请输入：',
        'ask_weekly_time': '请给出你希望的每周备份时间（当前星期为 {weekday}）',
        'summary_title': '请确认以下设置：',
        'summary_daily': '- 每日备份时间：{daily_time}',
        'summary_weekly': '- 每周备份：{weekday} {weekly_time}',
        'summary_path': '- 备份路径：{backup_root_display}',
        'final_confirm': '确认保存并立即生效吗？请输入 Y 确认，其他任意键取消：',
        'cancelled': '已取消，本次没有保存任何修改。',
        'path_changed': '你本次修改了备份路径。\n原路径：{old_path}\n现在是否删除原路径下的备份文件及文件夹？输入 Y 删除，输入 N 保留：',
        'deleted_old': '原路径下的备份文件及文件夹已删除。',
        'delete_failed': '删除原路径失败：{error}',
        'kept_old': '已保留原路径下的备份文件及文件夹。',
        'saved': '保存成功，新的时间和路径已经生效。',
        'exit_action': '请输入 Y 退出并关闭窗口，或输入 A 重新开始设置程序：',
        'exit_invalid': '输入无效，请输入 Y 或 A。',
    },
    'en': {
        'lang_prompt': 'C-中文，E-English\nPlease enter: ',
        'lang_invalid': 'Invalid input. Please enter C or E.',
        'title': '{instance_name} Property File Backup Setup / 属性文件备份设置',
        'intro': 'Follow the prompts to configure settings, then confirm once at the end.',
        'confirm': 'You entered: {value_label}{value}. Enter Y to confirm, or any other key to re-enter: ',
        'ask_time': '{question} (default: {default}, 24-hour format). Example: 01:00. Press Enter to keep the default.\nPlease enter: ',
        'time_invalid': 'Invalid time format. Please use HH:MM in 24-hour format.',
        'ask_weekday': 'Choose the weekly backup day (default: {default_label}; enter 0-6 or Monday/Tuesday etc.). Press Enter to keep the default.\nPlease enter: ',
        'weekday_invalid': 'Invalid weekday. Please try again.',
        'ask_path': 'Choose the backup path.\nDefault backup path: {default}\nYou can type or paste a new path. In Windows cmd, right-click paste usually works; some environments also support Ctrl+Shift+V.\nPress Enter to keep the default.\nPlease enter: ',
        'ask_weekly_time': 'Choose the weekly backup time (current day: {weekday})',
        'summary_title': 'Please confirm these settings:',
        'summary_daily': '- Daily backup time: {daily_time}',
        'summary_weekly': '- Weekly backup: {weekday} {weekly_time}',
        'summary_path': '- Backup path: {backup_root_display}',
        'final_confirm': 'Save now and apply immediately? Enter Y to confirm, or any other key to cancel: ',
        'cancelled': 'Cancelled. No changes were saved.',
        'path_changed': 'You changed the backup path this time.\nOld path: {old_path}\nDelete the old backup files and folders there now? Enter Y to delete, or N to keep them: ',
        'deleted_old': 'Old backup files and folders were deleted.',
        'delete_failed': 'Failed to delete old path: {error}',
        'kept_old': 'Old backup files and folders were kept.',
        'saved': 'Saved successfully. The new time and path are now active.',
        'exit_action': 'Enter Y to exit and close the window, or A to restart the setup: ',
        'exit_invalid': 'Invalid input. Please enter Y or A.',
    },
}

WEEKDAY_MAP_EN = {
    '0': 'Sunday', '1': 'Monday', '2': 'Tuesday', '3': 'Wednesday', '4': 'Thursday', '5': 'Friday', '6': 'Saturday'
}


def ask(prompt: str) -> str:
    return input(prompt).strip()


def print_blank() -> None:
    print('')


def tr(lang: str, key: str, **kwargs) -> str:
    return TEXT[lang][key].format(**kwargs)


def pick_language() -> str:
    while True:
        answer = ask(TEXT['zh']['lang_prompt']).lower()
        print_blank()
        if answer == 'c':
            return 'zh'
        if answer == 'e':
            return 'en'
        print(TEXT['zh']['lang_invalid'])
        print_blank()


def weekday_label(lang: str, weekday: str) -> str:
    return WEEKDAY_MAP[weekday] if lang == 'zh' else WEEKDAY_MAP_EN[weekday]


def confirm_once(lang: str, value_label: str, value: str) -> bool:
    answer = ask(tr(lang, 'confirm', value_label=value_label, value=value))
    print_blank()
    return answer.lower() == 'y'


def ask_time(lang: str, question: str, default: str) -> str:
    while True:
        value = ask(tr(lang, 'ask_time', question=question, default=default)) or default
        if not TIME_RE.match(value):
            print(tr(lang, 'time_invalid'))
            print_blank()
            continue
        if confirm_once(lang, '', value):
            return value


def ask_weekday(lang: str, default: str) -> str:
    default_label = weekday_label(lang, default)
    while True:
        value = ask(tr(lang, 'ask_weekday', default_label=default_label)) or default
        normalized = value.strip().lower()
        chosen = WEEKDAY_ALIASES.get(normalized)
        if chosen is None:
            print(tr(lang, 'weekday_invalid'))
            print_blank()
            continue
        if confirm_once(lang, '', weekday_label(lang, chosen)):
            return chosen


def ask_path(lang: str, default: str) -> str:
    while True:
        value = ask(tr(lang, 'ask_path', default=default)) or default
        if confirm_once(lang, '', value):
            return value


def remove_old_backup_dir(path_text: str) -> None:
    raw = path_text.strip()
    if len(raw) >= 3 and raw[1] == ':' and raw[2] in ('\\', '/'):
        drive = raw[0].lower()
        rest = raw[2:].replace('\\', '/').lstrip('/')
        target = Path(f'/mnt/{drive}/{rest}')
    else:
        target = Path(raw)
    if target.exists():
        shutil.rmtree(target)


def ask_exit_action() -> str:
    while True:
        answer = ask(EXIT_ACTION_PROMPT).lower()
        print_blank()
        if answer in {'y', 'a'}:
            return answer
        print(EXIT_ACTION_INVALID)
        print_blank()


EXIT_ACTION_PROMPT = ''
EXIT_ACTION_INVALID = ''


def run_once() -> tuple[bool, str]:
    config_path = Path(__file__).resolve().parents[3] / 'property-backup' / 'config.json'
    cfg = json.loads(config_path.read_text(encoding='utf-8'))
    lang = pick_language()

    print('========================================')
    print(tr(lang, 'title', instance_name=cfg['instance_name']))
    print(tr(lang, 'intro'))
    print('========================================')
    print_blank()

    old_backup_root_display = cfg['backup_root_display']
    daily_question = '请给出你希望的每日备份时间' if lang == 'zh' else 'Choose the daily backup time'
    daily_time = ask_time(lang, daily_question, cfg['daily_time'])
    weekly_day = ask_weekday(lang, cfg['weekly_day'])
    weekly_time = ask_time(lang, tr(lang, 'ask_weekly_time', weekday=weekday_label(lang, weekly_day)), cfg['weekly_time'])
    backup_root_display = ask_path(lang, cfg['backup_root_display'])

    print(tr(lang, 'summary_title'))
    print(tr(lang, 'summary_daily', daily_time=daily_time))
    print(tr(lang, 'summary_weekly', weekday=weekday_label(lang, weekly_day), weekly_time=weekly_time))
    print(tr(lang, 'summary_path', backup_root_display=backup_root_display))
    print_blank()

    final_confirm = ask(tr(lang, 'final_confirm'))
    print_blank()
    if final_confirm.lower() != 'y':
        print(tr(lang, 'cancelled'))
        print_blank()
        return False, lang

    old_argv = sys.argv[:]
    try:
        sys.argv = [
            'save_instance_property_backup.py',
            '--config', str(config_path),
            '--daily-time', daily_time,
            '--weekly-day', weekly_day,
            '--weekly-time', weekly_time,
            '--backup-root-display', backup_root_display,
        ]
        save_main()
    finally:
        sys.argv = old_argv

    if backup_root_display != old_backup_root_display:
        delete_old = ask(
            tr(lang, 'path_changed', old_path=old_backup_root_display)
        ).lower()
        print_blank()
        if delete_old == 'y':
            try:
                remove_old_backup_dir(old_backup_root_display)
                print(tr(lang, 'deleted_old'))
            except Exception as exc:  # noqa: BLE001
                print(tr(lang, 'delete_failed', error=exc))
            print_blank()
        else:
            print(tr(lang, 'kept_old'))
            print_blank()

    print(tr(lang, 'saved'))
    print_blank()
    return True, lang


def main() -> int:
    global EXIT_ACTION_PROMPT, EXIT_ACTION_INVALID
    while True:
        _, lang = run_once()
        EXIT_ACTION_PROMPT = TEXT[lang]['exit_action']
        EXIT_ACTION_INVALID = TEXT[lang]['exit_invalid']
        action = ask_exit_action()
        if action == 'y':
            return 0


if __name__ == '__main__':
    raise SystemExit(main())
