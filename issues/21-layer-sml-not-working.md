# Issue: 图层区 S/M/L 按钮没有起到作用

## 描述
点击图层区的 S/M/L 按钮后，行高和缩略图大小没有变化。

## 原因
`_apply_icon_size` 只设置了 `iconSize`，但 QTreeView 的行高还需要
配合 stylesheet 的 `height` / `min-height` 才能生效。

## 修复方案
`_apply_icon_size` 中同时设置 iconSize 和 stylesheet。

## 状态
✅ 已修复
