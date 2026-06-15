# Issue: 双击渲染区自动缩放至合适大小

## 描述
在渲染区双击左键时，应将图像缩放至正好铺满视口（fit to view）。

## 修复方案
RenderCanvas 添加 `mouseDoubleClickEvent`，调用 `fitInView`。

## 状态
✅ 已修复
