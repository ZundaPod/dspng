# Issue: 图层拖拽排序容易误操作为"放入组中"

## 描述
拖拽图层 `a` 到 `b` 上方时，`a above b` 很容易变为 `a joins b as a sublayer`。
原因是 tree view 的 drop indicator 有三个区域 (above / onto / below)，
"onto" 区域太大导致误操作。

## 修复方案
将 drag drop mode 改为 `InternalMoveDrop`，使 drop indicator 只显示
"between" 位置，不显示 "onto" 位置。同时确保 `dropMimeData` 正确处理
所有 drop 场景。

## 状态
✅ 已修复
