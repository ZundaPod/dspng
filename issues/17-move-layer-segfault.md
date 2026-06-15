# Issue: 图层上/下移按钮导致 Segmentation fault

## 描述
选中图层后点击上移/下移按钮，程序闪退，终端输出 Segmentation fault。

## 原因分析
`move_item` 中 `_populate_children` 重建 wrapper 后，旧 QModelIndex 的
`internalPointer()` 仍指向旧 wrapper。`layoutChanged` 信号触发视图刷新时，
视图可能访问了已失效的索引，导致空指针解引用。

## 修复方案
用 `beginResetModel` / `endResetModel` 替代 `layoutChanged`，
彻底重置视图状态，避免访问旧索引。

## 状态
✅ 已修复
