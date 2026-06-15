# Issue: 图层/图层组拖拽重排未实现

## 描述
虽然 tree view 设置了 drag mode，但 `dropMimeData` 未实现，
拖拽后图层顺序不会实际改变。

## 修复方案
1. 在 `LayerTreeModel` 中实现 `dropMimeData()`
2. 解码拖拽的 wrapper 标识，找到源节点和目标位置
3. 从源父节点移除，插入到目标父节点的正确位置
4. 调用 `beginMoveRows` / `endMoveRows` 通知视图
5. 触发 canvas 重渲染和缩略图缓存失效

## 状态
✅ 已修复
