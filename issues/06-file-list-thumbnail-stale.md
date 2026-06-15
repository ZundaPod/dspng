# Issue: 文件列表预览图不随图层区信息更新

## 描述
在图层区切换可见性或重排后，文件列表中的缩略图仍然是旧的合成结果。

## 原因分析
`generate_doc_thumbnail` 将结果缓存在 `doc.thumbnail`，但图层区的
任何改动都没有清除这个缓存，也没有刷新文件列表。

## 修复方案
1. `PsdDocument` 添加 `invalidate_thumbnail()` 方法
2. 图层可见性变化或重排后，调用 `doc.invalidate_thumbnail()`
3. 通知 `FileListPanel` 刷新当前选中项的缩略图

## 状态
✅ 已修复
