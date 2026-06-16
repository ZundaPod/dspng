# Issue: 拖拽导出命名方案与内联编辑

## 描述
拖拽导出 PNG 文件使用 `{display_name}_{counter:03d}.png` 命名方案。
display_name 可在文件列表中内联编辑，counter 通过 QSpinBox 调整。
导出成功后 counter 自动递增并在列表中实时更新。

## 修复方案
- `models.py` → PsdDocument 添加 display_name, export_counter
- `psd_manager.py` → add_document 设置默认 display_name
- `file_list.py` → QListWidget + per-item 控件（缩略图 | QLineEdit 名称 | QSpinBox 计数器）
- `render_canvas.py` → 命名方案 + drag cancel 检测 + 文件覆盖处理
- `main_window.py` → export_occurred 信号刷新计数器
- `main.py` → 设置 applicationVersion 用于 About 对话框
- 移除了 ↶ 撤销按钮（QSpinBox 已可双向调整）

## 状态
✅ 已修复
