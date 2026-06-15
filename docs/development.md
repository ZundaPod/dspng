# 开发指南

## 环境要求

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) 包管理器

## 安装依赖

```bash
uv sync
```

## 运行

```bash
# 启动 GUI
uv run dspng

# 直接打开 PSD 文件
uv run dspng path/to/file.psd

# 或用 python -m
uv run python -m dspng
```

## 项目结构

```
├── pyproject.toml           # 项目配置 + 依赖
├── uv.lock                  # 锁定依赖版本
├── src/dspng/               # 源码
│   ├── models.py            # 数据模型
│   ├── psd_manager.py       # PSD 加载
│   ├── renderer.py          # 图像合成
│   ├── main.py              # 入口
│   └── ui/                  # GUI
├── docs/                    # 文档
├── issues/                  # 问题跟踪
└── SESSION.md               # 已知问题和 TODO
```

## 添加依赖

```bash
uv add <package-name>
```

## 代码规范

- 使用 type hints
- docstring 解释"为什么"而非"做什么"
- 数据模型 (models.py) 不包含 GUI 逻辑
- GUI 信号驱动：面板间不直接耦合，通过信号通信
