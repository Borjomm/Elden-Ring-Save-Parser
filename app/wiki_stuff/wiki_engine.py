import re
import sqlite3
import json
import markdown
import frontmatter
from pathlib import Path

class EldenWikiEngine:
    tag_pattern = re.compile(r'\{%\s*(if|elif|else|endif)(?:\s+(.*?))?\s*%\}')
    condition_pattern = re.compile(r'(\w+):(\d+)')
    wikilink_pattern = re.compile(r'\[\[([^|\]]+)(?:\|([^\]]+))?\]\]')

    @classmethod
    def extract_all_ids(cls, text):
        """
        Scans text for tags and returns a dict: 
        {'events': {'10000800', ...}, 'items': {'1073749834', ...}}
        """
        events = set()
        items = set()
        
        # 1. Find all if/elif tags
        for match in cls.tag_pattern.finditer(text):
            condition_str = match.group(2) # The "event:123" part
            
            # 2. Extract type:id pairs from that condition
            for type_name, id_val in cls.condition_pattern.findall(condition_str):
                # Map 'event' -> 'events' to match your state dict keys
                if type_name == "event":
                    events.add(id_val)
                elif type_name == "item":
                    items.add(id_val)

                    
        return {"events": list(events), "items": list(items)}

    @staticmethod
    def evaluate(cond, state):
        if not cond: return True
        # Simple logic: 'event:123' -> True if '123' in events
        t, v = cond.split(':')
        inner = state.get(t + "s")
        if inner is None:
            return False
        return inner.get(v, False)
    
    @staticmethod
    def evaluate_all(state: dict):
        
        return all(not category.values() for category in state.values()) or any(value for category in state.values() for value in category.values())
    
    @classmethod
    def _process_logic(cls, text, state):
        lines = text.splitlines()
        output = []
        # stack stores: [has_any_branch_fired, is_current_branch_visible]
        stack = [[False, True]] 

        for line in lines:
            # Check if there is a tag on this line
            match = cls.tag_pattern.search(line)
            
            if match:
                tag, cond = match.groups()
                
                # Determine if this is a "Standalone Block Tag" (the only thing on the line)
                # or a "Suffix Tag" (content exists before the tag)
                content_before = line[:match.start()].strip()
                is_standalone = content_before == ""

                if is_standalone:
                    # --- BLOCK LOGIC ---
                    if tag == "if":
                        res = cls.evaluate(cond, state)
                        active = stack[-1][1] and res
                        stack.append([active, active])
                    elif tag == "elif":
                        parent_visible, has_fired = stack[-2][1], stack[-1][0]
                        if parent_visible and not has_fired and cls.evaluate(cond, state):
                            stack[-1] = [True, True]
                        else: stack[-1][1] = False
                    elif tag == "else":
                        parent_visible, has_fired = stack[-2][1], stack[-1][0]
                        stack[-1][1] = parent_visible and not has_fired
                    elif tag == "endif":
                        if len(stack) > 1: stack.pop()
                    
                    continue # Do not print standalone tag lines
                
                else:
                    # --- SUFFIX ONE-LINER LOGIC ---
                    # Only process if the current block context is visible
                    if stack[-1][1] and tag == "if":
                        if cls.evaluate(cond, state):
                            output.append(content_before)
                    continue

            # --- REGULAR TEXT ---
            if stack[-1][1]:
                output.append(line)

        return "\n".join(output)
    
    @classmethod
    def process(cls, text, state, hidden_md, unlock_ids = None):
        def link_replacer(match):
            raw_target = match.group(1).strip()
            alias = match.group(2).strip() if match.group(2) else None
            
            # 1. Strip 'public/' if it exists
            if raw_target.startswith("public/"):
                target = raw_target.removeprefix("public/")
            else:
                target = raw_target

            # 2. If no alias was provided, default to the stripped target
            # So [[public/Radahn]] becomes "Radahn" instead of "public/Radahn"
            if not alias:
                alias = target
                
            # We use a custom 'wiki://' protocol so PySide knows it's an internal link
            return f"[{alias}](wiki://{target})"
        if unlock_ids is not None and not any(cls.evaluate(cond, state) for cond in unlock_ids) or not cls.evaluate_all(state):
            text = f"# This page is locked!\n{hidden_md}"
        else:
            text = cls._process_logic(text, state)
        text = cls.wikilink_pattern.sub(link_replacer, text)

        return markdown.markdown(text, extensions=['fenced_code', 'tables'])


        
    
    @classmethod
    def build_db(cls, conn: sqlite3.Connection, root_path: Path):

        if not root_path.is_dir():
            raise ValueError(f"Expected directory, got {root_path}")
        conn.execute("DROP TABLE IF EXISTS entries")
        conn.execute(f"""
            CREATE TABLE entries (
                name TEXT,
                filepath TEXT PRIMARY KEY,
                conditions TEXT,
                markdown TEXT
            )
        """)
        cursor = conn.cursor()
        items = root_path.rglob("*.md")
        for item in items:
            md = item.read_text(encoding = "utf-8")
            conditions = json.dumps(cls.extract_all_ids(md))
            path = item.relative_to(root_path).as_posix()
            md = frontmatter.loads(md).content
            cursor.execute("INSERT INTO entries (name, filepath, conditions, markdown) VALUES (?, ?, ?, ?)", (item.stem, path, conditions, md))
        conn.commit()
        
