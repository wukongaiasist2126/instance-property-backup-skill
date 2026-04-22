# instance-property-backup-skill

An OpenClaw skill for backing up instance property files with a simple user-facing settings page.

## What This Skill Does

This skill creates a reusable backup mechanism for OpenClaw instance property files and provides a simple HTML settings page for non-technical users.

## User Entry File

Windows: Open the fixed user entry file at `C:\Users\<YourUserName>\Documents\OpenClaw\Property Backup\<InstanceName>_property-file-backup-settings.html`  
macOS: Open the fixed user entry file at `/Users/<YourUserName>/Documents/OpenClaw/Property Backup/<InstanceName>_property-file-backup-settings.html`

## Included in This Repository

- `instance-property-backup/` — the source skill folder
- `instance-property-backup.skill` — the packaged distributable skill file

## Notes

- The fixed user entry file is generated automatically after the skill is installed.
- The settings page is designed to let users change only the most important backup options.
- The packaged `.skill` file is suitable for direct sharing, while the source folder is better for GitHub version control and future maintenance.
```
