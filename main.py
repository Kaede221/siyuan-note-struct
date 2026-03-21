import requests
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = ""
API_TOKEN = ""
OUTPUT_NAME = ""


def select_notebooks_interactive(notebooks: list) -> list:
    """交互式选择要导出的笔记本。"""
    # 过滤掉已关闭的笔记本
    available_notebooks = [nb for nb in notebooks if not nb.get("closed", False)]

    if not available_notebooks:
        print("没有找到任何可用的笔记本（所有笔记本都已关闭）")
        return []

    print("\n📚 可用的笔记本：\n")
    for i, notebook in enumerate(available_notebooks, 1):
        print(f"  {i}. {notebook['name']}")

    print("\n请选择要导出的笔记本 (默认全选，按 Enter 确认):")
    print("输入格式: 1,2,3 或 1-3 或直接按 Enter 选择全部")
    print("例如: 1,3 表示选择第1和第3个笔记本\n")

    user_input = input("请输入: ").strip()

    # 默认全选
    if not user_input:
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
            print("❌ 输入无效，已选择全部笔记本")
            return available_notebooks

        selected = [available_notebooks[i - 1] for i in sorted(selected_indices)]
        print(
            f"\n✓ 已选择 {len(selected)} 个笔记本: {', '.join(nb['name'] for nb in selected)}\n"
        )
        return selected

    except (ValueError, IndexError):
        print("❌ 输入格式错误，已选择全部笔记本\n")
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
        all_notebooks = get_notebooks()

        # 交互式选择笔记本
        selected_notebooks = select_notebooks_interactive(all_notebooks)

        if not selected_notebooks:
            print("未选择任何笔记本，已退出")
            return

        print("正在导出笔记本结构...\n")
        for notebook in selected_notebooks:
            notebook_name = notebook["name"]
            docs = get_doc_tree(notebook["id"])
            print(f"✓ 笔记本 '{notebook_name}': 获取到 {len(docs)} 个文档")

        md_content = generate_markdown_page(selected_notebooks)

        with open(f"dist/{OUTPUT_NAME}.md", "w", encoding="utf-8") as f:
            f.write(md_content)

        print(f"\n✓ 已生成 {OUTPUT_NAME}.md")
        print("请用 Markdown 编辑器打开该文件查看")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    api_token = os.getenv("API_TOKEN")
    if not api_token:
        raise ValueError("API_TOKEN 未在 .env 文件中设置")
    baseurl = os.getenv("BASE_URL")
    if not baseurl:
        raise ValueError("BASE_URL 未在 .env 文件中设置")
    port = os.getenv("PORT")
    if not port:
        raise ValueError("PORT 未在 .env 文件中设置")
    output_name = os.getenv("OUTPUT_NAME")
    if not output_name:
        raise ValueError("OUTPUT_NAME 未在 .env 文件中设置")
    set_api_token(api_token)
    set_api_baseurl(baseurl, port)
    set_output_name(output_name)
    display_notebook_structure()
