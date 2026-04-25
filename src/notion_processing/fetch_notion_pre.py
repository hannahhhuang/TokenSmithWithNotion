import os
from pathlib import Path
from notion_client import Client
from notion2md.exporter.block import StringExporter


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
        md_content = StringExporter(block_id=page_id).export()

        # --- NEW SCRUBBING LOGIC ---
        # 1. Remove the annoying hardcoded library comments
        md_content = md_content.replace(
            "[//]: # (child_page is not supported)", "")
        # 2. Clean up any awkward double-spacing or stray breaks left behind
        md_content = md_content.replace("\n\n\n<br/>\n\n\n", "\n\n")
        md_content = md_content.replace("\n\n\n", "\n\n")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content.strip())  # .strip() removes trailing whitespace
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
