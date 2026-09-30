"""المخزون Inventory"""
from . import items as I

class Inventory:
    def __init__(self, size=36):
        self.slots = [{"id": None, "count": 0, "dur": 0} for _ in range(size)]
        self.selected = 0  # 0..8 هوت بار

    def add(self, iid, count=1):
        # تراكم أولاً
        if not I.is_tool(iid):
            for s in self.slots:
                if s["id"] == iid and s["count"] < I.MAX_STACK:
                    take = min(count, I.MAX_STACK - s["count"])
                    s["count"] += take; count -= take
                    if count <= 0: return True
        for s in self.slots:
            if s["id"] is None:
                if I.is_tool(iid):
                    s["id"] = iid; s["count"] = 1; s["dur"] = I.tool_maxdur(iid)
                    count -= 1
                    if count <= 0: return True
                else:
                    take = min(count, I.MAX_STACK)
                    s["id"] = iid; s["count"] = take; s["dur"] = 0
                    count -= take
                    if count <= 0: return True
        return count <= 0

    def hotbar(self):
        return self.slots[:9]

    def held(self):
        return self.slots[self.selected]

    def consume_held(self, n=1):
        s = self.held()
        if s["id"] is None: return
        if I.is_tool(s["id"]):
            return  # الأدوات لا تُستهلك بالوضع
        s["count"] -= n
        if s["count"] <= 0:
            s["id"] = None; s["count"] = 0

    def damage_tool(self):
        s = self.held()
        if s["id"] and I.is_tool(s["id"]):
            s["dur"] -= 1
            if s["dur"] <= 0:
                s["id"] = None; s["count"] = 0; s["dur"] = 0
                return True  # انكسرت
        return False

    def to_data(self):
        return {"slots": self.slots, "selected": self.selected}

    def from_data(self, d):
        self.slots = d.get("slots", self.slots)
        self.selected = d.get("selected", 0)
