# Issue: 图层区上移/下移按钮

## 描述
图层区新增「上移」「下移」按钮，将当前选中的图层（或整个图层组）
在同级中移动一个位置。

移动规则：
- 选中的项与同级的相邻项交换
- 组及其子图层整体移动（数据模型 `item.children` 同时交换 wrapper）
- 到达同级边界时无操作

## 修复方案
LayerPanel 新增上移/下移按钮，连接到 LayerTreeModel 的新方法
`swap_with_sibling(selected_index, direction)`。
底层数据模型的 `item.children` 中交换两个项，
然后重建 wrapper 列表（保持 top-to-bottom 显示顺序）。

## 状态
✅ 已修复
