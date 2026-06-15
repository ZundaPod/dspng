# Issue: 图层列表预览图未正确缩放至行高大小

## 描述
调整行高后，缩略图尺寸与行高不匹配。stylesheet 方式对行高控制
不可靠。

## 修复方案
1. 使用 `setIconSize()` 配合 `setUniformRowHeights(True)` 来控制行高
2. 缩略图生成时严格匹配 iconSize
3. 行高 slider 同时更新 iconSize

## 状态
✅ 已修复
