---
name: instance-property-backup
description: Go to the instance entry folder under Documents/OpenClaw/Property Backup/<实例名> (for example, Windows: C:\Users\XXXXXX\Documents\OpenClaw\Property Backup\<实例名>, macOS: ~/Documents/OpenClaw/Property Backup/<实例名>) to open the backup configuration file. The HTML page works in a normal browser, exports a portable config file, and shows the apply command needed to update the backup rules for the instance property files.
---

# Instance Property Backup

Create or update a reusable backup mechanism for an OpenClaw instance's property files.

## What this skill sets up

For one target instance, this skill should:

1. Confirm the instance name, workspace path, backup root path, daily backup time, and weekly backup schedule.
2. Create an instance-specific backup folder under the chosen backup root.
3. Install a Python backup script from `scripts/backup_property_files.py` with the target parameters filled in.
4. Create or update a human-readable Chinese instruction file from `references/backup-mechanism-template.md`.
5. Configure two cron jobs:
   - nightly change check + latest refresh
   - weekly full baseline backup
6. Optionally run one initial backup after installation.

## Required parameters

Before execution, collect or confirm only the values that should stay user-facing:

- `workspace_path` — target workspace directory
- `backup_root` — root folder that will contain the instance subfolder
- `daily_time` — local time in `HH:MM`
- `weekly_day` — weekday name or number
- `weekly_time` — local time in `HH:MM`
- `initialize_now` — whether to run an initial backup immediately

Keep the rest standardized. Do not expose instance-name edits, script paths, state-file paths, or other internal paths as normal user-facing settings.

## Default file set

Unless the user explicitly changes it, back up exactly these files from the workspace root:

- `AGENTS.md`
- `BOOTSTRAP.md`
- `HEARTBEAT.md`
- `IDENTITY.md`
- `MEMORY.md`
- `SOUL.md`
- `TOOLS.md`
- `USER.md`

## Execution rules

- Prefer updating an existing installation over creating duplicates.
- Reuse stable cron job names derived from the instance slug.
- Keep user-facing instruction files in Chinese.
- Keep the generated backup script deterministic and self-contained.
- When re-running for the same instance, update paths/times safely instead of stacking extra cron jobs.
- After writing the skill outputs, verify that the script file, HTML entry file, and launcher files exist in the expected locations.
- Explicitly distinguish these two steps in agent output: copying/installing the skill directory into `skills/` does **not** generate user-facing `.cmd` / `.command` files; those files appear only after running `scripts/install_instance_property_backup.py` for a target instance.
- Put the main HTML entry file and launchers in the standardized user entry directory under an instance subfolder (`Documents/OpenClaw/Property Backup/<实例名>/`) while keeping generated config/script/state files under the target instance workspace.
- Never delete launchers or HTML files belonging to other instances when reinstalling one instance.
- Respect the user-provided backup root. Do not silently replace it with the entry-file directory.
- Show only three simple editable items in the HTML config page: daily backup time, weekly backup time, backup directory.
- Keep the HTML page browser-safe. Do not depend on require(), child_process, Electron, or OpenClaw-only local runtime APIs.
- Generate a user-facing command-window configuration launcher for Windows and macOS.
- On macOS, mark the generated `.command` launcher executable and document that first launch may require right-click → Open because of Gatekeeper.
- Ask the user one question at a time for daily backup time, weekly day, weekly time, and backup path.
- Show defaults clearly, allow Enter to keep the default, validate inputs, and require a final Y confirmation before saving.
- Use `scripts/save_instance_property_backup.py` as the deterministic save/apply entrypoint that updates config, refreshes the rendered files, and then calls the apply script.
- Treat all other fields as advanced/internal and keep them out of the simple edit surface.

## Resources

- Installer script: `scripts/install_instance_property_backup.py`
- Backup script template: `scripts/backup_property_files.py`
- Reference template: `references/backup-mechanism-template.md`

## Install/use note

When another instance installs this skill, tell it clearly:

1. Copying this skill folder into that instance's `skills/` directory only makes the skill available.
2. To generate the actual per-instance files (`.cmd`, `.command`, HTML entry page, config, script, cron setup), it must then run `scripts/install_instance_property_backup.py` with the target instance parameters.
3. After installation, verify that the generated user-facing files are inside `Documents/OpenClaw/Property Backup/<实例名>/` and that other instances still keep their own separate subfolders.

## Packaging intent

This skill is meant to be reusable across instances and shareable as a packaged `.skill` artifact after validation/testing.
