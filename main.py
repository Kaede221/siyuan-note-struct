import requests
from typing import Optional
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.tree import Tree
from rich import box

load_dotenv()

console = Console()

API_BASE_URL = ""
API_TOKEN = ""
OUTPUT_NAME = ""


def select_notebooks_interactive(notebooks: list) -> list:
    """交互式选择要导出的笔记本。"""
    # 过滤掉已关闭的笔记本
    available_notebooks = [nb for nb in notebooks if not nb.get("closed", False)]

    if not available_notebooks:
        console.print(
            Panel("没有找到任何可用的笔记本（所有笔记本都已关闭）", style="yellow")
        )
        return []

    table = Table(
        title="可用的笔记本",
        box=box.ROUNDED,
        title_style="bold cyan",
        header_style="bold magenta",
    )
    table.add_column("序号", justify="center", style="dim", width=6)
    table.add_column("笔记本名称", style="green")

    for i, notebook in enumerate(available_notebooks, 1):
        table.add_row(str(i), notebook["name"])

    console.print()
    console.print(table)
    console.print()

    console.print(
        Panel(
            "[bold]输入格式:[/bold] 1,2,3 或 1-3 或直接按 Enter 选择全部\n"
            "[dim]例如: 1,3 表示选择第1和第3个笔记本[/dim]",
            title="选择要导出的笔记本",
            title_align="left",
            border_style="blue",
        )
    )

    user_input = Prompt.ask("[bold cyan]请输入[/bold cyan]", default="").strip()

    # 默认全选
    if not user_input:
        console.print("[green]已选择全部笔记本[/green]")
        return available_notebooks

    selected_indices = set()

    try:
        # 处理逗号分隔的输入
        parts = user_input.split(",")
        for part in parts:
            part = part.strip()
            # 处理范围输入 (如 1-3)
            if "-" in part:
                start, end = part.split("-")
                start, end = int(start.strip()), int(end.strip())
                selected_indices.update(range(start, end + 1))
            else:
                selected_indices.add(int(part))

        # 验证索引范围
        selected_indices = {
            i for i in selected_indices if 1 <= i <= len(available_notebooks)
        }

        if not selected_indices:
            console.print("[yellow]输入无效，已选择全部笔记本[/yellow]")
            return available_notebooks

        selected = [available_notebooks[i - 1] for i in sorted(selected_indices)]
        names = ", ".join(f"[green]{nb['name']}[/green]" for nb in selected)
        console.print(
            f"\n[bold]已选择 [cyan]{len(selected)}[/cyan] 个笔记本:[/bold] {names}\n"
        )
        return selected

    except (ValueError, IndexError):
        console.print("[yellow]输入格式错误，已选择全部笔记本[/yellow]\n")
        return available_notebooks


def set_api_token(token: str):
    """设置用于身份验证的 API token。"""
    global API_TOKEN
    API_TOKEN = token


def set_api_baseurl(base_url: str, port: str):
    """设置思源笔记的请求地址"""
    global API_BASE_URL
    API_BASE_URL = f"{base_url}:{port}"


def set_output_name(name: str):
    """设置生成的文件名"""
    global OUTPUT_NAME
    OUTPUT_NAME = name


def make_request(endpoint: str, data: Optional[dict] = None) -> dict:
    """向思源 API 发送请求。"""
    headers = {
        "Authorization": f"Token {API_TOKEN}",
        "Content-Type": "application/json",
    }

    url = f"{API_BASE_URL}{endpoint}"
    response = requests.post(url, headers=headers, json=data or {})
    response.raise_for_status()
    return response.json()


def get_notebooks() -> list:
    """获取所有笔记本。"""
    result = make_request("/api/notebook/lsNotebooks")
    if result["code"] != 0:
        raise Exception(f"获取笔记本失败: {result['msg']}")
    return result["data"]["notebooks"]


def get_doc_tree(notebook_id: str, path: str = "/", depth: int = 0) -> list:
    """递归获取笔记本的所有文档树。"""
    result = make_request(
        "/api/filetree/listDocsByPath", {"notebook": notebook_id, "path": path}
    )

    if result["code"] != 0:
        raise Exception(f"查询文档失败: {result['msg']}")

    files = result["data"].get("files", [])
    docs = []

    for file in files:
        doc_info = {
            "name": file["name"],
            "path": file["path"],
            "id": file["id"],
            "depth": depth,
            "subFileCount": file.get("subFileCount", 0),
        }
        docs.append(doc_info)

        # 如果有子文档，递归获取
        if file.get("subFileCount", 0) > 0:
            sub_docs = get_doc_tree(notebook_id, file["path"], depth + 1)
            docs.extend(sub_docs)

    return docs


def build_nested_markdown_tree(docs: list) -> str:
    """构建嵌套的 Markdown 树形结构。"""
    if not docs:
        return "- （空）"

    md_lines = []

    for doc in docs:
        depth = doc.get("depth", 0)
        name = doc.get("name", "未命名")
        indent = "  " * depth
        md_lines.append(f"{indent}- {name}")

    return "\n".join(md_lines)


def generate_markdown_page(notebooks: list) -> str:
    """生成完整的 Markdown 文档。"""
    md = "# 📚 笔记结构\n\n"

    for notebook in notebooks:
        notebook_id = notebook["id"]
        notebook_name = notebook["name"]

        docs = get_doc_tree(notebook_id)

        md += f"## {notebook_name}\n\n"

        if docs:
            tree = build_nested_markdown_tree(docs)
            md += f"{tree}\n\n"
        else:
            md += "- （空）\n\n"

    return md


def display_notebook_structure():
    """显示所有笔记本的结构，生成 Markdown 文件。"""
    try:
        with console.status("[bold cyan]正在获取笔记本列表...[/bold cyan]"):
            all_notebooks = get_notebooks()

        # 交互式选择笔记本
        selected_notebooks = select_notebooks_interactive(all_notebooks)

        if not selected_notebooks:
            console.print(Panel("未选择任何笔记本，已退出", style="yellow"))
            return

        console.print()
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            task = progress.add_task("正在导出笔记本结构...", total=len(selected_notebooks))
            notebook_docs = {}
            for notebook in selected_notebooks:
                notebook_name = notebook["name"]
                progress.update(task, description=f"正在获取: [green]{notebook_name}[/green]")
                docs = get_doc_tree(notebook["id"])
                notebook_docs[notebook["id"]] = docs
                progress.advance(task)

        # 用 Tree 展示获取结果
        console.print()
        result_tree = Tree("[bold cyan]获取结果[/bold cyan]")
        for notebook in selected_notebooks:
            docs = notebook_docs[notebook["id"]]
            result_tree.add(
                f"[green]{notebook['name']}[/green] [dim]({len(docs)} 个文档)[/dim]"
            )
        console.print(result_tree)
        console.print()

        md_content = generate_markdown_page(selected_notebooks)

        os.makedirs("dist", exist_ok=True)
        with open(f"dist/{OUTPUT_NAME}.md", "w", encoding="utf-8") as f:
            f.write(md_content)

        console.print(
            Panel(
                f"[bold green]已生成[/bold green] [cyan]dist/{OUTPUT_NAME}.md[/cyan]\n"
                f"[dim]请用 Markdown 编辑器打开该文件查看[/dim]",
                title="导出完成",
                title_align="left",
                border_style="green",
            )
        )

    except Exception as e:
        console.print_exception()
        console.print(Panel(f"[bold red]错误:[/bold red] {e}", border_style="red"))


if __name__ == "__main__":
    console.print(
        Panel(
            "[bold]思源笔记结构导出工具[/bold]",
            subtitle="SiYuan Note Struct",
            style="cyan",
            box=box.DOUBLE,
        )
    )

    env_vars = {
        "API_TOKEN": os.getenv("API_TOKEN"),
        "BASE_URL": os.getenv("BASE_URL"),
        "PORT": os.getenv("PORT"),
        "OUTPUT_NAME": os.getenv("OUTPUT_NAME"),
    }

    missing = [k for k, v in env_vars.items() if not v]
    if missing:
        console.print(
            Panel(
                "[bold red]以下环境变量未在 .env 文件中设置:[/bold red]\n"
                + "\n".join(f"  [yellow]{k}[/yellow]" for k in missing),
                title="配置错误",
                border_style="red",
            )
        )
        raise SystemExit(1)

    # missing check above guarantees these are str, assert for type checker
    assert env_vars["API_TOKEN"] is not None
    assert env_vars["BASE_URL"] is not None
    assert env_vars["PORT"] is not None
    assert env_vars["OUTPUT_NAME"] is not None

    set_api_token(env_vars["API_TOKEN"])
    set_api_baseurl(env_vars["BASE_URL"], env_vars["PORT"])
    set_output_name(env_vars["OUTPUT_NAME"])
    display_notebook_structure()
