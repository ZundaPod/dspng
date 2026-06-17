# Issue: i18n 国际化支持

## 描述
添加完整的 i18n 支持，所有用户可见文本应支持翻译。首个非英语语言为简体中文。

## 修复方案

### 新增
- `ui/locale_manager.py` — LocaleManager 单例，tr() 函数，language_changed 信号
- `locales/en/LC_MESSAGES/` — 英语翻译文件（模板）
- `locales/zh_CN/LC_MESSAGES/` — 简体中文翻译文件
- `scripts/compile_locales.py` — .po → .mo 编译脚本

### 修改
- 所有 UI 文件 — 将硬编码字符串包裹在 tr() 中
- `main.py` — 在 QApplication 之前初始化 LocaleManager
- `settings.py` — 持久化 language 设置
- `settings_dialog.py`（待创建）— 语言选择器

## 状态
✅ 已修复

### 实现
- `ui/locale_manager.py` — LocaleManager, tr(), language_changed 信号
- `locales/en/LC_MESSAGES/` 和 `locales/zh_CN/LC_MESSAGES/` — .po/.mo 文件
- `scripts/compile_locales.py` — .po → .mo 编译器
- 所有 UI 文件 — 59 个字符串包裹在 tr() 中
- `ui/settings_dialog.py` — 外观标签页中的语言选择器
