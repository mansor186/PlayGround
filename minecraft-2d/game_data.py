# -*- coding: utf-8 -*-
"""Block/item definitions, recipes, constants - shared logic (no pygame needed)."""

TILE = 32
WORLD_W = 256
WORLD_H = 128

AIR = 0
GRASS = 1
DIRT = 2
STONE = 3
LOG = 4
LEAVES = 5
PLANKS = 6
SAND = 7
COAL_ORE = 8
IRON_ORE = 9
GOLD_ORE = 10
DIAMOND_ORE = 11
BEDROCK = 12
CRAFTING_TABLE = 13
FURNACE = 14
TORCH = 15
GLASS = 16
BRICK = 17
COBBLE = 18
SANDSTONE = 19
SNOW_GRASS = 20
CACTUS = 21
FLOWER = 22
TALLGRASS = 23
COAL = 100
IRON_INGOT = 101
GOLD_INGOT = 102
DIAMOND = 103
STICK = 104
PORK = 105
BEEF = 106
TORCH_ITEM = 15  # torch is both
W_PICKAXE = 110
S_PICKAXE = 111
I_PICKAXE = 112
D_PICKAXE = 113
W_AXE = 114
S_AXE = 115
W_SWORD = 116
S_SWORD = 117
I_SWORD = 118
SHOVEL_W = 119
SHOVEL_S = 120

# block info: name_ar, hardness(sec), tool, drop, solid, placeable handled separately
BLOCKS = {
    GRASS:          dict(ar="عشب",      en="Grass",      hard=0.55, tool="shovel", drop=DIRT),
    DIRT:           dict(ar="تراب",     en="Dirt",       hard=0.5,  tool="shovel", drop=DIRT),
    STONE:          dict(ar="حجر",      en="Stone",      hard=1.6,  tool="pickaxe", drop=COBBLE),
    LOG:            dict(ar="جذع",      en="Log",        hard=1.0,  tool="axe",    drop=LOG),
    LEAVES:         dict(ar="أوراق",    en="Leaves",     hard=0.25, tool=None,     drop=None),
    PLANKS:         dict(ar="ألواح",    en="Planks",     hard=0.9,  tool="axe",    drop=PLANKS),
    SAND:           dict(ar="رمل",      en="Sand",       hard=0.5,  tool="shovel", drop=SAND),
    COAL_ORE:       dict(ar="فحم خام",  en="Coal Ore",   hard=2.0,  tool="pickaxe", drop=COAL),
    IRON_ORE:       dict(ar="حديد خام", en="Iron Ore",   hard=2.4,  tool="pickaxe", drop=IRON_ORE),
    GOLD_ORE:       dict(ar="ذهب خام",  en="Gold Ore",   hard=2.4,  tool="pickaxe", drop=GOLD_ORE),
    DIAMOND_ORE:    dict(ar="ألماس خام",en="Diamond Ore",hard=3.0,  tool="pickaxe", drop=DIAMOND),
    BEDROCK:        dict(ar="صخر الأساس",en="Bedrock",   hard=-1,   tool=None,     drop=None),
    CRAFTING_TABLE: dict(ar="طاولة صنع",en="Crafting",   hard=0.9,  tool="axe",    drop=CRAFTING_TABLE),
    FURNACE:        dict(ar="فرن",      en="Furnace",    hard=2.0,  tool="pickaxe", drop=FURNACE),
    TORCH:          dict(ar="مشعل",     en="Torch",      hard=0.1,  tool=None,     drop=TORCH),
    GLASS:          dict(ar="زجاج",     en="Glass",      hard=0.6,  tool=None,     drop=None),
    BRICK:          dict(ar="طوب",      en="Bricks",     hard=1.8,  tool="pickaxe", drop=BRICK),
    COBBLE:         dict(ar="حصى",      en="Cobble",     hard=1.7,  tool="pickaxe", drop=COBBLE),
    SANDSTONE:      dict(ar="حجر رملي", en="Sandstone",  hard=1.5,  tool="pickaxe", drop=SANDSTONE),
    SNOW_GRASS:     dict(ar="ثلج",      en="Snow",       hard=0.55, tool="shovel", drop=DIRT),
    CACTUS:         dict(ar="صبار",     en="Cactus",     hard=0.6,  tool=None,     drop=CACTUS),
    FLOWER:         dict(ar="وردة",     en="Flower",     hard=0.05, tool=None,     drop=None),
    TALLGRASS:      dict(ar="عشب طويل", en="Tall Grass", hard=0.05, tool=None,     drop=None),
}

ITEMS = {
    COAL:      dict(ar="فحم",      en="Coal"),
    IRON_ORE:  dict(ar="حديد خام", en="Iron Ore (item)"),
    GOLD_ORE:  dict(ar="ذهب خام",  en="Gold Ore (item)"),
    IRON_INGOT:dict(ar="سبيكة حديد",en="Iron Ingot"),
    GOLD_INGOT:dict(ar="سبيكة ذهب", en="Gold Ingot"),
    DIAMOND:   dict(ar="ألماسة",   en="Diamond"),
    STICK:     dict(ar="عصا",      en="Stick"),
    PORK:      dict(ar="لحم خنزير",en="Pork", food=6),
    BEEF:      dict(ar="لحم بقر",  en="Beef", food=8),
    W_PICKAXE: dict(ar="معول خشبي", en="Wood Pick", tool="pickaxe", mult=2.0, tier=1),
    S_PICKAXE: dict(ar="معول حجري", en="Stone Pick", tool="pickaxe", mult=3.5, tier=2),
    I_PICKAXE: dict(ar="معول حديدي",en="Iron Pick", tool="pickaxe", mult=5.5, tier=3),
    D_PICKAXE: dict(ar="معول ألماسي",en="Diamond Pick", tool="pickaxe", mult=8.0, tier=3),
    W_AXE:     dict(ar="فأس خشبي", en="Wood Axe", tool="axe", mult=2.0, tier=1),
    S_AXE:     dict(ar="فأس حجري", en="Stone Axe", tool="axe", mult=3.5, tier=2),
    W_SWORD:   dict(ar="سيف خشبي", en="Wood Sword", dmg=4),
    S_SWORD:   dict(ar="سيف حجري", en="Stone Sword", dmg=6),
    I_SWORD:   dict(ar="سيف حديدي",en="Iron Sword", dmg=8),
    SHOVEL_W:  dict(ar="مجرفة خشب",en="Wood Shovel", tool="shovel", mult=2.0, tier=1),
    SHOVEL_S:  dict(ar="مجرفة حجر",en="Stone Shovel", tool="shovel", mult=3.5, tier=2),
}

# item names for blocks too
for bid, b in BLOCKS.items():
    ITEMS.setdefault(bid, dict(ar=b["ar"], en=b["en"]))

NON_SOLID = {AIR, TORCH, FLOWER, TALLGRASS}
NO_COLLIDE_PLANTS = {FLOWER, TALLGRASS, TORCH}
NEEDS_SUPPORT = {FLOWER, TALLGRASS, TORCH, CACTUS}

# Crafting recipes: list of (inputs dict, output id, output count, need_table)
RECIPES = [
    ({"in": {LOG: 1}, "out": PLANKS, "n": 4, "table": False, "name": "ألواح من جذع"}),
    ({"in": {PLANKS: 2}, "out": STICK, "n": 4, "table": False, "name": "عصي"}),
    ({"in": {PLANKS: 4}, "out": CRAFTING_TABLE, "n": 1, "table": False, "name": "طاولة صنع"}),
    ({"in": {PLANKS: 3, STICK: 2}, "out": W_PICKAXE, "n": 1, "table": True, "name": "معول خشبي"}),
    ({"in": {PLANKS: 3, STICK: 2}, "out": W_AXE, "n": 1, "table": True, "name": "فأس خشبي"}),
    ({"in": {PLANKS: 2, STICK: 1}, "out": W_SWORD, "n": 1, "table": True, "name": "سيف خشبي"}),
    ({"in": {PLANKS: 1, STICK: 1}, "out": SHOVEL_W, "n": 1, "table": True, "name": "مجرفة خشب"}),
    ({"in": {COBBLE: 3, STICK: 2}, "out": S_PICKAXE, "n": 1, "table": True, "name": "معول حجري"}),
    ({"in": {COBBLE: 3, STICK: 2}, "out": S_AXE, "n": 1, "table": True, "name": "فأس حجري"}),
    ({"in": {COBBLE: 2, STICK: 1}, "out": S_SWORD, "n": 1, "table": True, "name": "سيف حجري"}),
    ({"in": {COBBLE: 1, STICK: 1}, "out": SHOVEL_S, "n": 1, "table": True, "name": "مجرفة حجر"}),
    ({"in": {COAL: 1, STICK: 1}, "out": TORCH, "n": 4, "table": False, "name": "مشاعل"}),
    ({"in": {COBBLE: 8}, "out": FURNACE, "n": 1, "table": True, "name": "فرن"}),
    ({"in": {IRON_INGOT: 3, STICK: 2}, "out": I_PICKAXE, "n": 1, "table": True, "name": "معول حديدي"}),
    ({"in": {IRON_INGOT: 2, STICK: 1}, "out": I_SWORD, "n": 1, "table": True, "name": "سيف حديدي"}),
    ({"in": {DIAMOND: 3, STICK: 2}, "out": D_PICKAXE, "n": 1, "table": True, "name": "معول ألماسي"}),
    ({"in": {STONE: 4}, "out": BRICK, "n": 4, "table": True, "name": "طوب"}),
    ({"in": {SAND: 4}, "out": SANDSTONE, "n": 1, "table": False, "name": "حجر رملي"}),
    ({"in": {LOG: 1, PLANKS: 1}, "out": CRAFTING_TABLE, "n": 1, "table": False, "name": "طاولة (بديل)"}),
]

SMELT = {
    IRON_ORE: IRON_INGOT,
    GOLD_ORE: GOLD_INGOT,
    SAND: GLASS,
    COBBLE: STONE,
    LOG: COAL,  # charcoal
}

STARTER_HOTBAR = [GRASS, DIRT, STONE, PLANKS, LOG, GLASS, TORCH, BRICK, CRAFTING_TABLE]

def item_name(iid):
    if iid in BLOCKS:
        return BLOCKS[iid]["ar"]
    if iid in ITEMS:
        return ITEMS[iid]["ar"]
    return f"#{iid}"

def is_solid(bid):
    return bid not in NON_SOLID and bid != AIR
