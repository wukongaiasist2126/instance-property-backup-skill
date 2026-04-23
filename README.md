# instance-property-backup-skill

An OpenClaw skill for creating and maintaining a reusable backup workflow for instance property files.

## What This Skill Does

This skill helps an OpenClaw instance set up a stable backup mechanism for its property files.

After installation, it can:

- back up core property files from the workspace
- create a user-facing configuration entry under the user's Documents folder
- generate launcher files for Windows and macOS
- create or refresh the backup script, config file, and instruction files
- apply scheduled backup settings for daily and weekly backups

## Repository Structure

This repository contains the source files of the skill:

- `SKILL.md` — skill instructions
- `references/` — template files used to generate user-facing documents and pages
- `scripts/` — installer, save/apply logic, and backup-related scripts

## Generated User Entry Files

After the skill is installed for a specific instance, the user-facing entry files are generated under:

- **Windows:** `C:\Users\<YourUserName>\Documents\OpenClaw\Property Backup\<InstanceName>\`
- **macOS:** `~/Documents/OpenClaw/Property Backup/<InstanceName>/`

Typical generated files include:

- `<InstanceName>_property-file-backup-settings.html`
- `<InstanceLabel>_属性备份.cmd`
- `<InstanceLabel>_属性备份.command`

## How Users Configure It

After installation:

- **Windows users** usually launch the generated `.cmd` file
- **macOS users** usually launch the generated `.command` file
- the setup flow runs as a command-window Q&A process
- users can adjust:
  - daily backup time
  - weekly backup day/time
  - backup directory

The generated HTML file is provided as a user-facing entry page and usage guide.

## Notes

- This repository is the **source skill repository**.
- A packaged `.skill` file is **not required** for the GitHub repository to be usable.
- User-facing launcher files and config files are generated only **after** running the installer for a target instance.
- Different instances are stored in separate subfolders under `Documents/OpenClaw/Property Backup/`, so reinstalling one instance should not remove another instance’s entry files.

