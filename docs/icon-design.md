# Icon 设计说明

## 命名灵感

`dspng` = `psd` 反转 (`dsp`) + `png`，共用字母 `P`。

- PSD：Photoshop 的分层图格式
- PNG：扁平的最终输出格式
- 共用的 `P` 连接了两种格式，也暗示了转换过程

## 设计概念

图标以层叠的 `P` 为核心元素：

```
┌──────────────┐
│  ░░░░░░░░░░  │  ← 青色层 (Shilü #57c3c2)  — PSD 底层
│   ░░░░░░░░   │
├──────────────┤
│  ▒▒▒▒▒▒▒▒▒▒  │  ← 蓝色层 (Jianshilan #66a9c9) — PSD 中间层
│   ▒▒▒▒▒▒▒▒   │
├──────────────┤
│  ████████████ │  ← 白色层 (Hanbaiyu #f8f4ed)  — 最终 PNG
│     █P████    │
│  ████████████ │
└──────────────┘
  深色背景 (Anlan #101f30)
```

- **三层叠**：代表 PSD 的图层结构（可见性、层叠关系）
- **每层有微小偏移**：暗示图层可以拖拽重排
- **底层半透明、顶层不透明**：从原始图层到最终合成的渐进过程
- **白色层上的 `P`**：既是 PSD 的首字母，也是 PNG 的首字母
- **深色背景**：与 dspng 的深色主题一致（Lettepa Anlan 色）

## 配色来源

所有颜色取自 [Lettepa](https://github.com/lettepa/lettepa) 调色板
（中国传统色名，灵感来自 Solarized 和 Gruvbox）。

## 生成方式

```bash
uv run python scripts/make_icon.py
```

输出：
- `icon.ico` — Windows 图标（含 16/24/32/48/64/128/256 多尺寸）
- `icon.png` — 256px PNG 预览

PyInstaller 打包时自动嵌入 `icon.ico`。
