# Issue: 配置临时文件目录

## 描述
在设置对话框中添加标签页，允许用户配置拖拽导出 PNG 时使用的临时文件目录。
默认路径为 `<TEMP>/dspng`。

## 修复方案
- `settings.json` → `app.temp_dir` 配置项
- `settings_dialog.py` → 添加 FilesPage（路径输入 + 浏览按钮）
- `render_canvas.py` → 使用配置的临时目录替代硬编码的 tempfile
- `settings.py` → get/set_temp_dir 辅助函数

## 状态
⏳ 待实现
