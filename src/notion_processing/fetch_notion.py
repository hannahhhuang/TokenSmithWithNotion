import os
import re
from pathlib import Path
from notion_client import Client


def get_page_title(notion, page_id):
    """Helper to extract a page's title safely from its properties."""
    try:
        page = notion.pages.retrieve(page_id=page_id)
        for prop_name, prop_data in page.get("properties", {}).items():
            if prop_data.get("type") == "title":
                title_array = prop_data.get("title", [])
                if title_array:
                    return title_array[0]["plain_text"]
    except Exception as e:
        print(f"Could not retrieve title for {page_id}: {e}")
    return "Untitled"

def parse_rich_text(rich_text_array):
    """Helper to parse Notion rich text into Markdown."""
    if not rich_text_array:
        return ""
    
    parsed = ""
    for rt in rich_text_array:
        text = rt.get("plain_text", "")
        annotations = rt.get("annotations", {})
        href = rt.get("href")
        
        if annotations.get("code"):
            text = f"`{text}`"
        if annotations.get("bold"):
            text = f"**{text}**"
        if annotations.get("italic"):
            text = f"*{text}*"
        if annotations.get("strikethrough"):
            text = f"~~{text}~~"
        if annotations.get("underline"):
            text = f"<u>{text}</u>"
            
        if href:
            text = f"{text}"
            
        parsed += text
    return parsed

def get_all_blocks(notion, block_id):
    """Recursively fetch all blocks for a given parent."""
    blocks = []
    has_more = True
    next_cursor = None
    
    while has_more:
        kwargs = {"block_id": block_id, "page_size": 100}
        if next_cursor:
            kwargs["start_cursor"] = next_cursor
            
        response = notion.blocks.children.list(**kwargs)
        blocks.extend(response.get("results", []))
        has_more = response.get("has_more", False)
        next_cursor = response.get("next_cursor")
        
    return blocks

def blocks_to_markdown(notion, blocks, indent_level=0):
    """Convert Notion blocks to a Markdown string."""
    md_lines = []
    list_number = 1
    
    for i, block in enumerate(blocks):
        b_type = block["type"]
        b_data = block.get(b_type, {})
        
        indent = "  " * indent_level
        
        # Reset list number if the previous block wasn't a numbered list
        if i > 0 and blocks[i-1]["type"] != "numbered_list_item" and b_type == "numbered_list_item":
            list_number = 1
            
        if b_type == "paragraph":
            text = parse_rich_text(b_data.get("rich_text", []))
            if text.strip() or indent_level == 0:
                md_lines.append(f"{indent}{text}\n")
            
        elif b_type == "heading_1":
            text = parse_rich_text(b_data.get("rich_text", []))
            md_lines.append(f"{indent}# {text}\n")
            
        elif b_type == "heading_2":
            text = parse_rich_text(b_data.get("rich_text", []))
            md_lines.append(f"{indent}## {text}\n")
            
        elif b_type == "heading_3":
            text = parse_rich_text(b_data.get("rich_text", []))
            md_lines.append(f"{indent}### {text}\n")
            
        elif b_type == "bulleted_list_item":
            text = parse_rich_text(b_data.get("rich_text", []))
            md_lines.append(f"{indent}- {text}")
            
        elif b_type == "numbered_list_item":
            text = parse_rich_text(b_data.get("rich_text", []))
            md_lines.append(f"{indent}{list_number}. {text}")
            list_number += 1
            
        elif b_type == "to_do":
            text = parse_rich_text(b_data.get("rich_text", []))
            checked = "x" if b_data.get("checked") else " "
            md_lines.append(f"{indent}- [{checked}] {text}")
            
        elif b_type == "toggle":
            text = parse_rich_text(b_data.get("rich_text", []))
            md_lines.append(f"{indent}<details><summary>{text}</summary>")
            
        elif b_type == "code":
            text = parse_rich_text(b_data.get("rich_text", []))
            lang = b_data.get("language", "")
            md_lines.append(f"{indent}```{lang}\n{text}\n{indent}```\n")
            
        elif b_type == "quote":
            text = parse_rich_text(b_data.get("rich_text", []))
            quote_text = "\n".join([f"{indent}> {line}" for line in text.split("\n")])
            md_lines.append(f"{quote_text}\n")
            
        elif b_type == "callout":
            text = parse_rich_text(b_data.get("rich_text", []))
            icon = b_data.get("icon", {}).get("emoji", "💡")
            md_lines.append(f"{indent}> {icon} **Callout:** {text}\n")
            
        elif b_type == "divider":
            md_lines.append(f"{indent}---\n")
            
        elif b_type == "image":
            img_type = b_data.get("type", "file")
            url = b_data.get(img_type, {}).get("url", "")
            caption = parse_rich_text(b_data.get("caption", []))
            md_lines.append(f"{indent}![{caption}]({url})\n")
            
        elif b_type in ["bookmark", "link_preview"]:
            url = b_data.get("url", "")
            md_lines.append(f"{indent}{url}\n")
            
        elif b_type == "equation":
            expression = b_data.get("expression", "")
            md_lines.append(f"{indent}$$\n{expression}\n{indent}$$\n")
            
        elif b_type == "table_row":
            cells = b_data.get("cells", [])
            cell_texts = [parse_rich_text(cell) for cell in cells]
            row = f"{indent}| " + " | ".join(cell_texts) + " |"
            md_lines.append(row)
            if i == 0:
                sep = f"{indent}|" + "|".join(["---" for _ in cells]) + "|"
                md_lines.append(sep)
            
        # Process children if any
        if block.get("has_children") and b_type != "child_page":
            child_blocks = get_all_blocks(notion, block["id"])
            child_md = blocks_to_markdown(notion, child_blocks, indent_level + 1)
            if child_md:
                md_lines.append(child_md)
            
        if b_type == "toggle":
            md_lines.append(f"{indent}</details>\n")
            
    result = "\n".join(md_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()

def process_page(notion, page_id, export_dir, page_title=None, recursive=True):
    """Exports a page and optionally searches its blocks for child pages."""

    if not page_title:
        page_title = get_page_title(notion, page_id)

    safe_title = "".join(c for c in page_title if c.isalnum()
                         or c in (' ', '_')).rstrip()
    filename = f"{safe_title}_{page_id}.md"
    filepath = os.path.join(export_dir, filename)

    print(f"\n[Exporting Page] {page_title} -> {filename}...")

   # 1. Convert the current Page to Markdown
    try:
        blocks = get_all_blocks(notion, page_id)
        md_content = blocks_to_markdown(notion, blocks)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)
    except Exception as e:
        print(f"Failed to export {page_id}: {e}")

    # 2. Check the recursive flag before scanning for children
    if not recursive:
        print(
            f"  -> Skipping child page scan for '{page_title}' (recursive=False)")
        return

    # 3. Look for nested child pages
    print(f"  -> Scanning '{page_title}' for nested child pages...")
    has_more = True
    next_cursor = None

    while has_more:
        kwargs = {"block_id": page_id, "page_size": 100}
        if next_cursor:
            kwargs["start_cursor"] = next_cursor

        response = notion.blocks.children.list(**kwargs)

        for block in response.get("results", []):
            if block["type"] == "child_page":
                child_id = block["id"]
                child_title = block["child_page"]["title"]
                print(f"  --> Found nested child page: {child_title}")

                # Pass the recursive flag down to the child
                process_page(notion, child_id, export_dir,
                             child_title, recursive=recursive)

        has_more = response.get("has_more", False)
        next_cursor = response.get("next_cursor")


def spool_notion_to_disk(token, root_page_id, recursive=True, export_dir=None):
    if not export_dir:
        project_root = Path(__file__).resolve().parent.parent.parent
        export_dir = str(project_root / "data")

    os.makedirs(export_dir, exist_ok=True)
    mode_text = "Recursive" if recursive else "Single-Page"
    print(f"Starting Notion Extraction ({mode_text} Mode) to {export_dir}...")

    # notion2md library uses the NOTION_TOKEN env var under the hood
    os.environ["NOTION_TOKEN"] = token
    notion = Client(auth=token)

    # Pass the argument to the first call
    process_page(notion, root_page_id, export_dir, recursive=recursive)

    print("\nExtraction complete. Files ready for TokenSmith ingestion.")


if __name__ == "__main__":
    token = os.getenv(
        "NOTION_TOKEN", "ntn_Y183469747018CPShvycuBQPfGciONsVZzDzUVMOXbqevV")
    root_id = os.getenv("NOTION_ROOT_PAGE_ID",
                        "32b06d5b42fe8044b4f7ce9db4b9e6f7")
    spool_notion_to_disk(token, root_id, recursive=False)
