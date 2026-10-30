"""Hàm dùng chung cho mọi nhóm tool."""


def spec(name, description, props=None, required=()):
    """Schema một tool theo định dạng function-calling của Ollama."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": props or {},
                "required": list(required),
            },
        },
    }


def s(desc):
    return {"type": "string", "description": desc}


def find_by_name(items, name, kind):
    """Tìm mục theo tên: khớp chính xác trước, sau đó khớp một phần."""
    key = name.strip().lower()
    exact = [i for i in items if i["name"].lower() == key]
    if exact:
        return exact[0]
    partial = [i for i in items if key in i["name"].lower()]
    if len(partial) == 1:
        return partial[0]
    if not partial:
        raise LookupError(f"Không tìm thấy {kind} nào tên '{name}'.")
    names = ", ".join(i["name"] for i in partial[:10])
    raise LookupError(
        f"Có nhiều {kind} khớp với '{name}': {names}. Hãy hỏi người dùng muốn chọn cái nào."
    )
