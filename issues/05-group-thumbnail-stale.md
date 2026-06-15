# Issue: 图层组预览图不随子图层可见性更新

## 描述
切换图层组内某个图层的可见性后，图层组的缩略图仍然是旧的合成结果。

## 原因分析
`generate_group_thumbnail` 将结果缓存在 `group.thumbnail`，但切换
子图层可见性时没有清除这个缓存。

## 修复方案
1. `LayerGroup` 添加 `invalidate_thumbnail()` 方法，递归清除自身及所有祖先的缓存
2. 图层可见性变化时，向上遍历并调用 `invalidate_thumbnail()`
3. 刷新图层列表的装饰（DecorationRole）

## 状态
✅ 已修复
