"""Gọi Trello REST API và các tool model được phép gọi."""

import requests

from .config import TRELLO_API, TRELLO_BOARD, TRELLO_KEY, TRELLO_TOKEN


def trello(method, path, **params):
    params.update(key=TRELLO_KEY, token=TRELLO_TOKEN)
    resp = requests.request(method, f"{TRELLO_API}{path}", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _columns():
    return trello("GET", f"/boards/{TRELLO_BOARD}/lists", fields="name")


def _cards():
    return trello(
        "GET", f"/boards/{TRELLO_BOARD}/cards",
        fields="name,idList,due,dueComplete,shortUrl",
    )


def _find(items, name, kind):
    """Tìm cột/thẻ theo tên: khớp chính xác trước, sau đó khớp một phần."""
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


# ----- Các tool model được phép gọi -----
def list_columns():
    return [c["name"] for c in _columns()]


def list_cards(column=None):
    cols = {c["id"]: c["name"] for c in _columns()}
    cards = _cards()
    if column:
        col = _find([{"id": k, "name": v} for k, v in cols.items()], column, "cột")
        cards = [c for c in cards if c["idList"] == col["id"]]
    return [
        {
            "name": c["name"],
            "column": cols.get(c["idList"], "?"),
            "due": c["due"],
            "done": c["dueComplete"],
            "url": c["shortUrl"],
        }
        for c in cards
    ]


def create_card(name, column, description="", due=None):
    col = _find(_columns(), column, "cột")
    params = {"idList": col["id"], "name": name, "desc": description}
    if due:
        params["due"] = due
    card = trello("POST", "/cards", **params)
    return {"created": card["name"], "column": col["name"], "url": card["shortUrl"]}


def move_card(card, column):
    c = _find(_cards(), card, "thẻ")
    col = _find(_columns(), column, "cột")
    trello("PUT", f"/cards/{c['id']}", idList=col["id"])
    return {"moved": c["name"], "to": col["name"]}


def add_comment(card, text):
    c = _find(_cards(), card, "thẻ")
    trello("POST", f"/cards/{c['id']}/actions/comments", text=text)
    return {"commented_on": c["name"]}
