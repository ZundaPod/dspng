# Issue: 图层可见性只能取消，无法重新开启

## 描述
点击图层可见性复选框可以取消勾选（隐藏图层），但再次点击无法重新勾选（显示图层）。

## 原因分析
PySide6 的 `QAbstractItemModel.setData` 在处理 `CheckStateRole` 时，标准的
`flags + setData + data` 流程可能存在兼容性问题。使用自定义 Delegate
直接管理复选框的状态读写可以绕开此问题。

## 修复方案
为可见性列（column 1）实现 `QStyledItemDelegate`，在 Delegate 中直接
创建 `QCheckBox` 控件、读写模型数据。
