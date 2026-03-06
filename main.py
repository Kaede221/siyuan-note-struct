import requests
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = "http://127.0.0.1:6806"
API_TOKEN = ""


def set_api_token(token: str):
    """设置用于身份验证的 API token。"""
    global API_TOKEN
    API_TOKEN = token


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
    result = make_request("/api/filetree/listDocsByPath", {
        "notebook": notebook_id,
        "path": path
    })
    
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
            "subFileCount": file.get("subFileCount", 0)
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
        notebooks = get_notebooks()

        for notebook in notebooks:
            notebook_name = notebook["name"]
            docs = get_doc_tree(notebook["id"])
            print(f"笔记本 '{notebook_name}': 获取到 {len(docs)} 个文档")

        md_content = generate_markdown_page(notebooks)

        with open("笔记结构.md", "w", encoding="utf-8") as f:
            f.write(md_content)

        print("\n✓ 已生成 笔记结构.md")
        print("请用 Markdown 编辑器打开该文件查看")

    except Exception as e:
        print(f"错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    api_token = os.getenv("API_TOKEN")
    if not api_token:
        raise ValueError("API_TOKEN 未在 .env 文件中设置")
    set_api_token(api_token)
    display_notebook_structure()
