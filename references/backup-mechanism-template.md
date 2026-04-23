# {{instance_name}} 属性文件备份机制说明

**配置页入口：** [点击打开属性文件备份配置页]({{config_page_relative_link}})

如果你想修改每日备份时间、每周备份时间、备份目录，请先点击上面的链接打开配置页。

**用户入口目录：** `{{user_entry_dir}}`

## 一、机制目标

这套机制用于为 {{instance_name}} 实例的属性文件建立稳定、可追溯、便于查看的备份体系。

目标有两个：

1. **保留全部修改历史**，便于回滚、排查、恢复。
2. **始终提供一份最新可直接查看的版本**，方便用户只看当前生效内容。

其中：
- 用户日常主要查看 `latest` 目录。
- `snapshots` 和 `weekly` 主要用于历史追踪与问题恢复。

## 二、备份对象

默认纳入备份的属性文件如下：

- `AGENTS.md`
- `BOOTSTRAP.md`
- `HEARTBEAT.md`
- `IDENTITY.md`
- `MEMORY.md`
- `SOUL.md`
- `TOOLS.md`
- `USER.md`

默认源目录为：

```text
{{workspace_path}}
```

## 三、备份目录

当前备份根目录为：

```text
{{backup_root}}
```

当前实例备份目录为：

```text
{{instance_backup_dir}}
```

目录结构如下：

```text
{{instance_name}}/
  latest/
  snapshots/
    YYYY-MM-DD/
  weekly/
    YYYY-Wxx/
```

## 四、运行规则

### 1. 每日夜间检查备份

执行时间：**每天 {{daily_time}}**

规则：
- 检查属性文件是否相较上次备份发生变化。
- 若有变化：
  - 更新 `latest/`
  - 写入当天 `snapshots/` 历史快照
- 若无变化：
  - 仍刷新 `latest/` 为当前文件版本
  - 不新增历史快照

### 2. 每周基线备份

执行时间：**每周 {{weekly_day_text}} {{weekly_time}}**

规则：
- 对属性文件执行一次全量基线备份
- 写入对应周目录 `weekly/YYYY-Wxx/`
- 同时更新 `latest/`
- 若检测到相对上次状态有变化，也会补充写入当天 `snapshots/`

## 五、普通用户可修改项

普通用户建议只修改以下三项：

1. 每日备份时间
2. 每周备份时间
3. 备份目录

其余内容默认采用标准化设置，不建议手动修改。

## 六、高级修改

如果你是懂技术的用户，需要修改更多内容，可查看或编辑以下文件：

- 备份脚本：

```text
{{script_path}}
```

- 状态文件：

```text
{{state_file}}
```

- 配置文件：

```text
{{config_file}}
```

## 七、说明

- `latest/` 用于日常直接查看。
- `snapshots/` 用于保留历史变更。
- `weekly/` 用于保留每周基线版本。
- 默认情况下，即使不做任何自定义，也可以直接按默认时间与默认路径正常工作。
