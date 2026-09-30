"""الأدوات والعناصر (Items)"""
import pygame

# عنصر = معرف نصي مثل "block:1" أو "stick" أو "pickaxe_wood"
ITEM_NAMES = {
    "block:1": "كتلة عشب", "block:2": "تراب", "block:3": "حجر",
    "block:4": "جذع", "block:5": "أوراق", "block:6": "ألواح",
    "block:7": "رمل", "block:8": "زجاج", "block:9": "طوب",
    "block:10": "مشعل", "block:11": "فحم خام", "block:12": "حديد خام",
    "block:13": "ألماس خام", "block:14": "بيدروك", "block:15": "عشب ثلجي",
    "block:16": "زهرة", "block:17": "عشب طويل", "block:18": "طاولة صناعة",
    "block:19": "فرن", "block:20": "صندوق", "block:21": "ماء",
    "block:22": "حمم", "block:23": "ثلج", "block:24": "حصى",
    "block:25": "حجر رملي", "block:26": "كتلة فحم", "block:27": "مكتبة",
    "stick": "عصا", "coal": "فحم", "raw_iron": "حديد خام",
    "iron_ingot": "سبيكة حديد", "diamond": "ألماسة", "apple": "تفاحة",
    "pork": "لحم", "wool": "صوف",
    "pickaxe_wood": "فأس حجري؟ (خشبي)", "pickaxe_stone": "معول حجري",
    "pickaxe_iron": "معول حديدي", "pickaxe_diamond": "معول ألماسي",
    "axe_wood": "فأس خشبي", "axe_stone": "فأس حجري",
    "axe_iron": "فأس حديدي", "axe_diamond": "فأس ألماسي",
    "shovel_wood": "مجرفة خشبية", "shovel_stone": "مجرفة حجرية",
    "shovel_iron": "مجرفة حديدية", "shovel_diamond": "مجرفة ألماسية",
    "sword_wood": "سيف خشبي", "sword_stone": "سيف حجري",
    "sword_iron": "سيف حديدي", "sword_diamond": "سيف ألماسي",
}

# قوة الأداة: (نوع_الأداة، مستوى)
# المستويات: يد=0 خشب=1 حجر=2 حديد=3 ألماس=4
TOOL_STATS = {
    "pickaxe_wood": ("pickaxe", 1, 60, 2.0), "pickaxe_stone": ("pickaxe", 2, 132, 3.5),
    "pickaxe_iron": ("pickaxe", 3, 251, 5.0), "pickaxe_diamond": ("pickaxe", 4, 1562, 8.0),
    "axe_wood": ("axe", 1, 60, 2.0), "axe_stone": ("axe", 2, 132, 3.5),
    "axe_iron": ("axe", 3, 251, 5.0), "axe_diamond": ("axe", 4, 1562, 8.0),
    "shovel_wood": ("shovel", 1, 60, 2.0), "shovel_stone": ("shovel", 2, 132, 3.5),
    "shovel_iron": ("shovel", 3, 251, 5.0), "shovel_diamond": ("shovel", 4, 1562, 8.0),
    "sword_wood": ("sword", 1, 60, 4.0), "sword_stone": ("sword", 2, 132, 5.0),
    "sword_iron": ("sword", 3, 251, 6.0), "sword_diamond": ("sword", 4, 1562, 7.5),
}

# صلابة تتطلب مستوى أداة
REQUIRED_LEVEL = {
    3: 1, 24: 1, 11: 1, 12: 2, 13: 3, 9: 1, 19: 1, 25: 1, 26: 1,
}

MAX_STACK = 64

def item_name(iid):
    return ITEM_NAMES.get(iid, iid)

def is_tool(iid):
    return iid in TOOL_STATS

def is_block_item(iid):
    return iid.startswith("block:")

def block_id_of(iid):
    try:
        return int(iid.split(":")[1])
    except Exception:
        return 0

def tool_kind(iid):
    if iid in TOOL_STATS:
        return TOOL_STATS[iid][0]
    return None

def tool_level(iid):
    if iid in TOOL_STATS:
        return TOOL_STATS[iid][1]
    return 0

def tool_damage(iid):
    if iid in TOOL_STATS:
        return TOOL_STATS[iid][3]
    return 1.0  # اليد

def tool_maxdur(iid):
    if iid in TOOL_STATS:
        return TOOL_STATS[iid][2]
    return 0
