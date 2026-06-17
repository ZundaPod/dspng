# Issue: 字体自定义

## 描述
在设置对话框的外观标签页中添加字体自定义选项，允许用户选择字体家族和基础字号。

## 修复方案
- `settings.json` → `theme.custom_fonts: { family, size }`
- `ThemeManager` → `set_custom_fonts()`, `font_family()`, `font_size()`
- `build_stylesheet()` 使用自定义字体
- `AppearancePage` → 添加字体选择区域（QFontComboBox + 字号选择）
- 实时应用到主窗口

## 状态
✅ 已修复
