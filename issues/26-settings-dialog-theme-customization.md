# Issue: 设置对话框与主题自定义

## 描述
添加设置对话框，左侧边栏标签页，右侧对应设置内容。
首个标签页为「外观」，包含语言选择、主题模式选择和全量颜色自定义。

## 修复方案

### 新增
- `ui/settings_dialog.py` — SettingsDialog + AppearancePage + ColorRow 控件
- 实时预览卡片（标签 + 按钮 + 列表）

### 修改
- `ui/theme_manager.py` — set_custom_colors(), reset_customs(), get() 优先检查自定义颜色
- `ui/settings.py` — 重新设计 settings.json 结构（app / theme 分区）
- `ui/main_window.py` — File 菜单添加 Ctrl+, 快捷键

### 设置结构
```json
{
  "app": { "language": "en" },
  "theme": { "mode": "dark", "custom_colors": {} }
}
```

## 状态
✅ 已修复

### 实现
- `ui/settings_dialog.py` — SettingsDialog + AppearancePage 含实时预览
- `ui/theme_manager.py` — set_custom_colors(), reset_customs()
- `ui/settings.py` — 重新设计的嵌套结构 (app / theme 分区)
- `ui/main_window.py` — File > Settings... (Ctrl+,)
