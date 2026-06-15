# Issue: 文件列表行宽改为固定三种尺寸

## 描述
文件列表行宽应提供三种固定预设：32px、64px、128px，对应缩略图正方形尺寸。
提供 S / M / L 三个 toggle 按钮切换。

## 修复方案
- `FileListModel` 新增 `set_icon_size()` 方法
- `FileListPanel` 底部添加 S/M/L 三个 toggle 按钮
- 切换时 invalidate 所有文档缩略图，重新生成

## 状态
✅ 已修复
