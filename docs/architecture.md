# dspng 架构文档

## 概述

dspng 是一个独立的 PSD → PNG 渲染导出工具，无需启动 Photoshop。
用户可以导入 PSD 文件，在内存中调整图层可见性和顺序，实时预览渲染结果，
并通过拖拽或菜单导出 PNG。

## 技术栈

| 组件 | 技术 |
|---|---|
| 语言 | Python 3.14 |
| 包管理 | uv |
| PSD 解析 | psd-tools |
| GUI | PySide6 (Qt for Python) |
| 图像处理 | Pillow (PIL) |
| 打包 | PyInstaller |

## 目录结构

```
src/dspng/
├── __init__.py              # 包标识
├── __main__.py              # python -m dspng 入口
├── main.py                  # QApplication 启动 + CLI 参数
├── models.py                # 数据模型 (LayerNode, LayerGroup, PsdDocument)
├── psd_manager.py           # PSD 加载 + DocumentStore 状态管理
├── renderer.py              # 图像合成 + 缩略图生成 + PNG 导出
└── ui/
    ├── __init__.py
    ├── main_window.py        # 主窗口 (三栏布局 + 菜单 + 信号连接)
    ├── styles.py             # 动态 QSS 样式表生成
    ├── themes.py             # Lettepa 配色 + 主题定义
    ├── settings.py           # 持久化设置 (~/.dspng/settings.json)
    └── panels/
        ├── __init__.py
        ├── file_list.py      # 文件列表面板
        ├── layer_panel.py    # 图层树面板
        └── render_canvas.py  # 渲染画布

scripts/
├── build.py                 # PyInstaller 打包脚本
└── make_icon.py             # 图标生成脚本

docs/                        # 文档
issues/                      # 问题跟踪 (22 个已解决)
icon.ico / icon.png          # 应用图标
```

## 核心模块

### models.py — 数据模型

纯数据容器，不包含任何 GUI 逻辑：

- **`LayerNode`**: 单个图层，持有 PIL 图像、偏移、可见性、透明度、混合模式。
- **`LayerGroup`**: 图层组，递归包含子节点列表。
- **`PsdDocument`**: 一个 PSD 文件的完整内存表示，包含图层树和尺寸。

每个模型都提供 `invalidate_thumbnail()` 方法用于清除缩略图缓存。

### psd_manager.py — PSD 加载

- `load_psd(path)` 用 psd-tools 打开 PSD，递归提取图层树。
- psd-tools 按从下到上顺序遍历图层 (index 0 = 最底层)。
  代码保留此顺序用于渲染合成。
- `DocumentStore` 管理所有已加载文档和当前选中文档。
- `PsdLoadError` 自定义异常，PSD 解析失败时抛出。

### renderer.py — 图像合成

- `composite(doc)` 按从下到上顺序合成所有可见图层，返回 RGBA PIL Image。
- 图层组透明度递归传播：子图层的有效透明度 = 自身透明度 × 所有祖先组透明度。
- `make_thumbnail(image, size)` 生成固定正方形缩略图 (不保持宽高比)。
- `generate_*_thumbnail()` 带缓存，缓存尺寸不匹配时自动重新生成。
- `export_png()` / `composite_to_bytes()` 用于导出。

### UI 层

- **主窗口**: 三栏布局 (渲染画布 | 文件列表 + 图层树)，用 QSplitter 实现可拖拽调整。
  - View 菜单：Light/Dark/System 主题切换，6 种强调色变体。
  - Help 菜单：Keyboard Shortcuts (F1)、About 对话框。
  - 设置持久化到 `~/.dspng/settings.json`。
- **文件列表**: 支持拖放 PSD 文件、点击选择、添加/删除/重新加载。
  S/M/L 三种尺寸预设 (32/64/128px)。
- **图层树**: 树形结构展示，自定义 Delegate 管理可见性复选框。
  显示顺序从上到下 (Photoshop 一致)，底层数据从下到上。
  S/M/L 三种行高预设 (32/64/128px)。上移/下移按钮。
- **渲染画布**: 滚轮缩放、中键/Alt+左键平移、双击适配视口。
  左键拖拽导出 PNG (写入临时文件，系统拖放)。

### 主题系统

- `themes.py`: Lettepa 配色 (传统中国色名)，ThemeMode (Light/Dark/System)，6 种 Accent。
- `styles.py`: `generate_stylesheet(theme)` 动态生成 QSS。
- `settings.py`: 持久化到 `~/.dspng/settings.json`。

## 信号流

```
用户点击可见性 checkbox
  → _VisibilityDelegate.toggled
  → LayerTreeModel.setData (更新 item.visible + 清除祖先缩略图缓存)
  → LayerPanel._on_visibility_toggled
    → regenerate thumbnails
    → emit layer_visibility_changed → RenderCanvas.refresh_composite (保持缩放)
    → emit thumbnail_changed → FileListPanel.refresh_current_thumbnail
```

## 已知限制

- 仅支持 Normal 混合模式，其他模式按 Normal 处理
- 拖拽导出的临时文件未自动清理
- 初始加载大 PSD (100+ 图层) 可能较慢
