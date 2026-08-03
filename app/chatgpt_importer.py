import os
import json
import zipfile
import io

def extract_part_text(p) -> str:
    if isinstance(p, str):
        return p.strip()
    if isinstance(p, dict):
        if "text" in p and isinstance(p["text"], str):
            return p["text"].strip()
        if "val" in p and isinstance(p["val"], str):
            return p["val"].strip()
    return ""

def parse_chatgpt_export(file_bytes: bytes, filename: str) -> list:
    """
    Parses a ChatGPT export file (conversations.json, a Zip containing conversations.json,
    or a single .json / .md thread export).
    Returns a list of dicts: [{"title": ..., "content": ...}, ...]
    """
    parsed_threads = []
    lower_name = filename.lower()

    # Case 1: Zip file
    if lower_name.endswith(".zip"):
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                names = z.namelist()
                
                # Priority A: Check for conversations.json
                conv_file = next((n for n in names if n.lower().endswith("conversations.json")), None)
                if conv_file:
                    json_bytes = z.read(conv_file)
                    threads = _parse_conversations_json(json_bytes)
                    if threads:
                        return threads

                # Priority B: Process other json/md/html files in zip
                for name in names:
                    base_n = os.path.basename(name).lower()
                    if base_n.startswith(".") or name.startswith("__MACOSX"):
                        continue
                    if base_n in {"user.json", "message_feedback.json", "model_comparisons.json", "shared_conversations.json", "settings.json"}:
                        continue
                    
                    if base_n.endswith(".json"):
                        json_bytes = z.read(name)
                        parsed_threads.extend(_parse_conversations_json(json_bytes))
                    elif base_n.endswith(".md") or base_n.endswith(".txt"):
                        text = z.read(name).decode("utf-8", errors="ignore").strip()
                        if text:
                            title = os.path.splitext(os.path.basename(name))[0].replace("_", " ").replace("-", " ").title()
                            parsed_threads.append({"title": f"[ChatGPT] {title}", "content": text})
            return parsed_threads
        except Exception as exc:
            print(f"Warning: Zip extraction error ({exc}), falling back to text decode.")

    # Case 2: JSON file
    if lower_name.endswith(".json"):
        return _parse_conversations_json(file_bytes)

    # Case 3: Markdown or TXT file
    text_content = file_bytes.decode("utf-8", errors="ignore").strip()
    title = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").title()
    if text_content:
        parsed_threads.append({"title": f"[ChatGPT] {title}", "content": text_content})

    return parsed_threads

def _parse_conversations_json(json_bytes: bytes) -> list:
    threads = []
    try:
        data = json.loads(json_bytes.decode("utf-8", errors="ignore"))
        if not isinstance(data, list):
            if isinstance(data, dict):
                if "title" in data:
                    data = [data]
                elif "mapping" in data:
                    data = [data]
                elif "conversations" in data and isinstance(data["conversations"], list):
                    data = data["conversations"]
                else:
                    return threads
            else:
                return threads

        for conv in data:
            if not isinstance(conv, dict):
                continue
            title = conv.get("title") or "Conversación ChatGPT"
            mapping = conv.get("mapping", {})
            dialogue_parts = []

            nodes_list = list(mapping.values()) if isinstance(mapping, dict) else []
            
            for node in nodes_list:
                if not isinstance(node, dict):
                    continue
                msg = node.get("message")
                if not msg or not isinstance(msg, dict):
                    continue

                author_role = msg.get("author", {}).get("role", "")
                if author_role not in {"user", "assistant"}:
                    continue

                content = msg.get("content", {})
                if not isinstance(content, dict):
                    continue

                parts = content.get("parts", [])
                text_parts = []
                for p in parts:
                    txt = extract_part_text(p)
                    if txt:
                        text_parts.append(txt)

                if text_parts:
                    full_text = "\n".join(text_parts).strip()
                    if author_role == "user":
                        dialogue_parts.append(f"**Usuario:** {full_text}")
                    elif author_role == "assistant":
                        dialogue_parts.append(f"**ChatGPT:** {full_text}")

            if dialogue_parts:
                combined_content = "\n\n".join(dialogue_parts)
                threads.append({
                    "title": f"[ChatGPT] {title}",
                    "content": combined_content
                })
    except Exception as exc:
        print(f"Error parsing conversations.json: {exc}")

    return threads
