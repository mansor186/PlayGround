"""تعريف البلوكات وخصائصها + توليد خامات بكسل إجرائياً"""
import pygame
import random

# IDs
AIR = 0
GRASS = 1
DIRT = 2
STONE = 3
LOG = 4
LEAVES = 5
PLANKS = 6
SAND = 7
GLASS = 8
BRICK = 9
TORCH = 10
COAL_ORE = 11
IRON_ORE = 12
DIAMOND_ORE = 13
BEDROCK = 14
SNOWY_GRASS = 15
FLOWER = 16
TALLGRASS = 17
CRAFTING = 18
FURNACE = 19
CHEST = 20
WATER = 21
LAVA = 22
SNOW = 23
COBBLE = 24
SANDSTONE = 25
COAL_BLOCK = 26
BOOKSHELF = 27

BLOCKS = {
    AIR: dict(name="هواء", solid=False, hard=-1, tool=None, drop=None, transparent=True, light=0, fluid=None, color=(0, 0, 0)),
    GRASS: dict(name="عشب", solid=True, hard=0.9, tool="shovel", drop="block:2", transparent=False, light=0, fluid=None, color=(106, 176, 76)),
    DIRT: dict(name="تراب", solid=True, hard=0.8, tool="shovel", drop="block:2", transparent=False, light=0, fluid=None, color=(134, 96, 67)),
    STONE: dict(name="حجر", solid=True, hard=2.2, tool="pickaxe", drop="block:24", transparent=False, light=0, fluid=None, color=(128, 128, 132)),
    LOG: dict(name="جذع", solid=True, hard=1.6, tool="axe", drop="block:4", transparent=False, light=0, fluid=None, color=(104, 82, 50)),
    LEAVES: dict(name="أوراق", solid=True, hard=0.4, tool=None, drop="stick", transparent=True, light=0, fluid=None, color=(45, 135, 45)),
    PLANKS: dict(name="ألواح", solid=True, hard=1.4, tool="axe", drop="block:6", transparent=False, light=0, fluid=None, color=(172, 140, 88)),
    SAND: dict(name="رمل", solid=True, hard=0.8, tool="shovel", drop="block:7", transparent=False, light=0, fluid=None, color=(220, 200, 140)),
    GLASS: dict(name="زجاج", solid=True, hard=0.6, tool=None, drop=None, transparent=True, light=0, fluid=None, color=(200, 230, 240)),
    BRICK: dict(name="طوب", solid=True, hard=2.5, tool="pickaxe", drop="block:9", transparent=False, light=0, fluid=None, color=(150, 60, 50)),
    TORCH: dict(name="مشعل", solid=False, hard=0.1, tool=None, drop="block:10", transparent=True, light=14, fluid=None, color=(255, 200, 80)),
    COAL_ORE: dict(name="فحم خام", solid=True, hard=2.8, tool="pickaxe", drop="coal", transparent=False, light=0, fluid=None, color=(90, 90, 95)),
    IRON_ORE: dict(name="حديد خام", solid=True, hard=3.2, tool="pickaxe", drop="raw_iron", transparent=False, light=0, fluid=None, color=(160, 130, 110)),
    DIAMOND_ORE: dict(name="ألماس خام", solid=True, hard=4.0, tool="pickaxe", drop="diamond", transparent=False, light=0, fluid=None, color=(100, 200, 220)),
    BEDROCK: dict(name="بيدروك", solid=True, hard=-1, tool=None, drop=None, transparent=False, light=0, fluid=None, color=(40, 40, 45)),
    SNOWY_GRASS: dict(name="عشب ثلجي", solid=True, hard=0.9, tool="shovel", drop="block:2", transparent=False, light=0, fluid=None, color=(200, 220, 200)),
    FLOWER: dict(name="زهرة", solid=False, hard=0.05, tool=None, drop="block:16", transparent=True, light=0, fluid=None, color=(220, 60, 60)),
    TALLGRASS: dict(name="عشب طويل", solid=False, hard=0.05, tool=None, drop=None, transparent=True, light=0, fluid=None, color=(90, 160, 70)),
    CRAFTING: dict(name="طاولة صناعة", solid=True, hard=1.4, tool="axe", drop="block:18", transparent=False, light=0, fluid=None, color=(150, 110, 70)),
    FURNACE: dict(name="فرن", solid=True, hard=2.8, tool="pickaxe", drop="block:19", transparent=False, light=0, fluid=None, color=(100, 100, 105)),
    CHEST: dict(name="صندوق", solid=True, hard=1.2, tool="axe", drop="block:20", transparent=False, light=0, fluid=None, color=(180, 130, 60)),
    WATER: dict(name="ماء", solid=False, hard=-1, tool=None, drop=None, transparent=True, light=0, fluid="water", color=(60, 120, 220)),
    LAVA: dict(name="حمم", solid=False, hard=-1, tool=None, drop=None, transparent=True, light=15, fluid="lava", color=(255, 90, 10)),
    SNOW: dict(name="ثلج", solid=True, hard=0.7, tool="shovel", drop="block:23", transparent=False, light=0, fluid=None, color=(240, 245, 250)),
    COBBLE: dict(name="حصى", solid=True, hard=2.3, tool="pickaxe", drop="block:24", transparent=False, light=0, fluid=None, color=(110, 110, 115)),
    SANDSTONE: dict(name="حجر رملي", solid=True, hard=2.0, tool="pickaxe", drop="block:25", transparent=False, light=0, fluid=None, color=(215, 190, 130)),
    COAL_BLOCK: dict(name="كتلة فحم", solid=True, hard=3.0, tool="pickaxe", drop="block:26", transparent=False, light=0, fluid=None, color=(35, 35, 38)),
    BOOKSHELF: dict(name="مكتبة", solid=True, hard=1.4, tool="axe", drop="block:27", transparent=False, light=0, fluid=None, color=(140, 100, 60)),
}

def is_solid(bid):
    return BLOCKS.get(bid, BLOCKS[AIR]).get("solid", False)

def is_fluid(bid):
    return BLOCKS.get(bid, {}).get("fluid") is not None

# ---- توليد خامات بكسل ----
_tex_cache = {}

def make_texture(bid, size=32):
    if bid in _tex_cache:
        return _tex_cache[bid]
    rng = random.Random(bid * 7919 + 13)
    s = pygame.Surface((size, size))
    base = BLOCKS.get(bid, BLOCKS[STONE])["color"]
    s.fill(base)
    # ضجيج بكسل
    px = pygame.PixelArray(s)
    for y in range(size):
        for x in range(size):
            v = rng.randint(-14, 14)
            r = max(0, min(255, base[0] + v + rng.randint(-6, 6)))
            g = max(0, min(255, base[1] + v + rng.randint(-6, 6)))
            b = max(0, min(255, base[2] + v + rng.randint(-6, 6)))
            # نقوش خاصة
            if bid in (GRASS, SNOWY_GRASS):
                if y < 8:
                    g = min(255, base[1] + 25 + rng.randint(-8, 8)); r = 95 + rng.randint(-10, 10); b = 65 + rng.randint(-8, 8)
                    if bid == SNOWY_GRASS and y < 4:
                        r, g, b = 240, 245, 250
                else:
                    r, g, b = 134 + rng.randint(-12, 12), 96 + rng.randint(-10, 10), 67 + rng.randint(-8, 8)
            elif bid == LOG:
                if x % 7 == 0:
                    r, g, b = 70, 55, 32
            elif bid == LEAVES:
                if rng.random() < 0.12:
                    r, g, b = 25, 90, 25
            elif bid == STONE and rng.random() < 0.05:
                r, g, b = 100, 100, 105
            elif bid in (COAL_ORE, IRON_ORE, DIAMOND_ORE):
                r, g, b = 125, 125, 130
                if (x * 7 + y * 13) % 11 < 2 or rng.random() < 0.06:
                    if bid == COAL_ORE: r, g, b = 25, 25, 28
                    elif bid == IRON_ORE: r, g, b = 210, 160, 130
                    else: r, g, b = 120, 230, 250
            elif bid == BRICK:
                if y % 8 == 0 or x % 8 == 0:
                    r, g, b = 200, 200, 200
            elif bid == PLANKS:
                if y % 8 == 0:
                    r, g, b = 120, 95, 55
            elif bid == GLASS:
                r, g, b = 205, 235, 245
                if x == 0 or y == 0 or x == size - 1 or y == size - 1:
                    r, g, b = 240, 250, 255
                if x == y or x + y == size:
                    r, g, b = 250, 255, 255
            elif bid == TORCH:
                r, g, b = 120, 85, 40
                if 12 <= x <= 19 and 4 <= y <= 14:
                    r, g, b = 255, 200, 60
                if 13 <= x <= 18 and 5 <= y <= 10:
                    r, g, b = 255, 240, 160
            elif bid == FLOWER:
                r, g, b = 90, 160, 70
                if 10 <= x <= 22 and 6 <= y <= 18:
                    r, g, b = 220, 60, 60
                if 14 <= x <= 18 and 10 <= y <= 14:
                    r, g, b = 255, 230, 80
            elif bid == TALLGRASS:
                r, g, b = 0, 0, 0  # سيُرسم شفاف
            elif bid == WATER:
                r, g, b = 55 + rng.randint(-8, 12), 115 + rng.randint(-8, 12), 220
                if y % 6 == 0:
                    r, g, b = 90, 150, 255
            elif bid == LAVA:
                r, g, b = 230 + rng.randint(-20, 25), 80 + rng.randint(-20, 40), 10
                if rng.random() < 0.08:
                    r, g, b = 255, 220, 80
            elif bid == CRAFTING:
                r, g, b = 150 + rng.randint(-10, 10), 110 + rng.randint(-8, 8), 70
                if 4 <= y <= 12:
                    r, g, b = 110, 80, 50
            elif bid == FURNACE:
                r, g, b = 95 + rng.randint(-8, 8), 95 + rng.randint(-8, 8), 100
                if 10 <= x <= 22 and 12 <= y <= 22:
                    r, g, b = 30, 30, 32
            elif bid == BEDROCK:
                v2 = rng.randint(-20, 20)
                r, g, b = 45 + v2, 45 + v2, 50 + v2
            px[x, y] = (r, g, b)
    del px
    # عشب طويل / زهرة: خلفية شفافة
    if bid in (TALLGRASS, FLOWER):
        s.set_colorkey((0, 0, 0))
        # أعد الرسم بشفافية: امسح ثم ارسم سيقان
        s2 = pygame.Surface((size, size))
        s2.fill((0, 0, 0))
        s2.set_colorkey((0, 0, 0))
        for i in range(7):
            x = 4 + i * 4 + rng.randint(-2, 2)
            pygame.draw.line(s2, (80, 160, 60), (x, 30), (x + rng.randint(-3, 3), 12 + rng.randint(0, 6)), 2)
        if bid == FLOWER:
            pygame.draw.line(s2, (60, 140, 60), (16, 30), (16, 14), 3)
            pygame.draw.circle(s2, (220, 60, 60), (16, 10), 6)
            pygame.draw.circle(s2, (255, 230, 80), (16, 10), 3)
        s = s2
    if bid in (WATER, LAVA):
        s.set_alpha(190)
    _tex_cache[bid] = s
    return s
