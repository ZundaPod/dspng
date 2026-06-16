# Issue: Material Design 3 主题系统迁移

## 描述
将现有的 Lettepa 调色板主题系统替换为基于 Material Design 3 设计令牌
的主题引擎，并修复所有布局规则违规。

## 修复方案

### 新增
- `ui/theme_tokens.py` — M3 间距、圆角、浅色/深色调色板、平台字体检测
- `ui/theme_manager.py` — 单例 ThemeManager，集中编译 Qt 样式表，
  支持 light/dark/system 模式切换

### 删除
- `ui/themes.py` — Lettepa 调色板、Theme 数据类、Accent 枚举
- `ui/styles.py` — `generate_stylesheet()` 合并入 ThemeManager

### 修改
- `main_window.py` — 移除 Accent 系统，使用 ThemeManager，简化 View 菜单
- `layer_panel.py` — 移除内联 setStyleSheet（→ 集中样式表），
  移除 setFixedWidth（→ setSizePolicy），动态属性替代内联行高样式，
  添加显式 SizePolicy，间距使用 SPACING_NONE 令牌
- `file_list.py` — 同上，移除 setFixedWidth，添加显式 SizePolicy，
  间距使用令牌
- `render_canvas.py` — 添加 Expanding/Expanding SizePolicy
- `settings.py` — 移除 Accent 导入和 get_accent()

### 布局规则合规
- Rule 1 (绝对定位): ERROR → ✅ 移除 setFixedWidth
- Rule 4 (SizePolicy): ERROR → ✅ 所有控件显式设置
- Rule 5 (间距): WARNING → ✅ 所有 setContentsMargins/setSpacing 使用令牌
- Rule 7 (内联样式): ERROR → ✅ 所有 setStyleSheet 移至集中样式表
- Rule 2, 3: ✅ 已合规
- Rule 6 (嵌套深度): ⚠️ 约 5 层，留待后续优化

## 状态
✅ 已修复
