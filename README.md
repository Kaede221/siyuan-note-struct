# 📚 思源笔记结构导出工具

一个简洁高效的 Python 工具，用于从思源笔记（SiYuan）中自动导出笔记本结构，生成美观的 Markdown 文档。

## ✨ 功能特性

- 🔄 **自动递归获取** - 自动遍历所有笔记本及其子文档
- 📄 **生成 Markdown** - 将笔记结构导出为格式化的 Markdown 文件
- 🎯 **树形展示** - 清晰的缩进层级展示文档结构
- 🔐 **安全认证** - 支持 API Token 认证，保护你的数据
- ⚡ **轻量级** - 最小化依赖，快速运行

## 🚀 快速开始

### 前置要求

- Python 3.8+
- 思源笔记应用正在运行（默认监听 `127.0.0.1:6806`）
- 思源笔记 API Token

### 安装

1. **克隆或下载项目**

```bash
git clone <repository-url>
cd siyuan-note-struct
```

2. **安装依赖**

使用 `uv` 包管理器（推荐）：

```bash
uv sync
```

### 配置

1. **获取 API Token**
   - 打开思源笔记
   - 进入 设置 → 关于 → API Token
   - 复制你的 Token

2. **创建 `.env` 文件**

在项目根目录创建 `.env` 文件，添加你的 API Token：

```env
API_TOKEN=your_api_token_here
```

### 使用

运行脚本导出笔记结构：

```bash
python main.py
```

脚本会：
1. 连接到思源笔记 API
2. 获取所有笔记本
3. 递归遍历每个笔记本的文档树
4. 生成 `笔记结构.md` 文件

## 📖 输出示例

生成的 `笔记结构.md` 文件格式如下：

```markdown
# 📚 笔记结构

## 前端学习

- 前端基础
  - 语言知识
    - TypeScript 快速上手
    - 作用域和闭包
  - 进阶技巧
    - 如何实现函数防抖

## 后端学习

- 数据库
  - MySQL
    - MySQL 基础教程
```

## 🔧 API 配置

默认配置：
- **API 地址**: `http://127.0.0.1:6806`
- **认证方式**: Token 认证

如需修改 API 地址，编辑 `main.py` 中的 `API_BASE_URL` 变量。

## 📦 项目结构

```
siyuan-note-struct/
├── main.py              # 主程序
├── pyproject.toml       # 项目配置
├── .env                 # 环境变量（需自行创建）
├── .gitignore           # Git 忽略文件
└── README.md            # 本文件
```

## 🛠️ 主要函数

| 函数 | 说明 |
|------|------|
| `set_api_token(token)` | 设置 API 认证 Token |
| `make_request(endpoint, data)` | 向思源 API 发送请求 |
| `get_notebooks()` | 获取所有笔记本 |
| `get_doc_tree(notebook_id, path, depth)` | 递归获取文档树 |
| `build_nested_markdown_tree(docs)` | 构建 Markdown 树形结构 |
| `generate_markdown_page(notebooks)` | 生成完整 Markdown 文档 |

## ⚠️ 常见问题

**Q: 连接被拒绝？**
- 确保思源笔记应用正在运行
- 检查 API 地址是否正确

**Q: API Token 无效？**
- 重新获取 API Token
- 确保 `.env` 文件中的 Token 正确无误

**Q: 生成的文件为空？**
- 检查笔记本是否包含文档
- 查看控制台错误信息

## 📝 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**提示**: 定期运行此脚本可以保持笔记结构文档的最新状态。
