"""توليد العالم + حفظ/تحميل"""
import random, json, os, gzip, math
from . import config as C
from . import blocks as B

def _make_value_noise(seed, size=512):
    rng = random.Random(seed)
    vals = [rng.random() for _ in range(size)]
    def noise1(x):
        xi = int(math.floor(x)) % size
        xf = x - math.floor(x)
        a = vals[xi]; b = vals[(xi + 1) % size]
        u = xf * xf * (3 - 2 * xf)
        return a + (b - a) * u
    return noise1

class World:
    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.randint(0, 999999)
        self.w = C.WORLD_W; self.h = C.WORLD_H
        self.tiles = [[B.AIR for _ in range(self.w)] for _ in range(self.h)]
        self.time = 6000  # 0-24000 (6000 = صباح)
        self.spawn = (self.w // 2, 40)
        self.biome = [0] * self.w  # 0 plains 1 desert 2 forest 3 snow
        self.height = [0] * self.w

    def get(self, x, y):
        if x < 0 or x >= self.w or y < 0 or y >= self.h: return B.BEDROCK if y >= self.h else B.AIR
        return self.tiles[y][x]

    def set(self, x, y, bid):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.tiles[y][x] = bid

    def is_solid(self, x, y):
        return B.is_solid(self.get(x, y))

    def generate(self):
        rng = random.Random(self.seed)
        n1 = _make_value_noise(self.seed, 512)
        n2 = _make_value_noise(self.seed + 999, 512)
        moist = _make_value_noise(self.seed + 5555, 512)
        for x in range(self.w):
            # تضاريس: عدة أوكتاف (y صغير = مرتفع)
            h_base = (n1(x * 0.03) * 0.6 + n1(x * 0.09) * 0.3 + n1(x * 0.25) * 0.1)
            hill = int(72 + h_base * 26)  # 72..98 (متوسط ~85 = نصف يابسة)
            # جبال أحياناً (ترفع التضاريس = y أصغر)
            if n2(x * 0.015) > 0.68:
                hill -= int((n2(x * 0.015) - 0.68) * 110)
            hill = max(12, min(C.SEA_LEVEL + 10, hill))
            self.height[x] = hill
            m = moist(x * 0.02)
            # بايوم (hill صغير = مرتفع = يابسة، hill كبير = منخفض = محيط)
            if abs(hill - C.SEA_LEVEL) <= 2 and m < 0.5:
                bio = 1  # شاطئ/صحراء قرب البحر
            elif m > 0.72:
                bio = 3  # ثلج
            elif m > 0.55:
                bio = 2  # غابة
            else:
                bio = 0
            self.biome[x] = bio
            top = B.GRASS
            under = B.DIRT
            if bio == 1: top, under = B.SAND, B.SAND
            elif bio == 3: top, under = B.SNOWY_GRASS, B.DIRT
            for y in range(self.h):
                if y < hill:
                    self.tiles[y][x] = B.AIR
                elif y == hill:
                    self.tiles[y][x] = top
                elif y <= hill + 3:
                    self.tiles[y][x] = under
                    if bio == 1 and y >= hill + 2:
                        self.tiles[y][x] = B.SANDSTONE
                else:
                    # حجر مع خامات
                    r = rng.random()
                    depth = y - hill
                    bid = B.STONE
                    if depth > 3 and r < 0.035: bid = B.COAL_ORE
                    elif depth > 8 and r < 0.045: bid = B.IRON_ORE
                    elif y > self.h - 30 and r < 0.03: bid = B.DIAMOND_ORE
                    elif r < 0.01: bid = B.COBBLE
                    self.tiles[y][x] = bid
            # ماء البحر: الأرض المنخفضة (hill > SEA) يغمرها الماء حتى مستوى السطح
            if hill > C.SEA_LEVEL:
                for y in range(C.SEA_LEVEL, hill):
                    self.tiles[y][x] = B.WATER
                # قاع رملي
                self.tiles[hill][x] = B.SAND
            # بيدروك
            self.tiles[self.h - 1][x] = B.BEDROCK
            if rng.random() < 0.5:
                self.tiles[self.h - 2][x] = B.BEDROCK
        # كهوف: نحت بضجيج ثنائي مبسط
        for _ in range(9000):
            cx = rng.randint(2, self.w - 3); cy = rng.randint(50, self.h - 5)
            if self.tiles[cy][cx] in (B.STONE, B.COAL_ORE, B.IRON_ORE, B.DIAMOND_ORE, B.COBBLE, B.DIRT):
                # لا تنحت قرب السطح كثيراً
                if cy - self.height[cx] > 4:
                    self.tiles[cy][cx] = B.AIR
                    if rng.random() < 0.4:
                        self.tiles[cy][cx + rng.choice([-1, 1])] = B.AIR
        # حمم في الأعماق
        for x in range(self.w):
            for y in range(self.h - 8, self.h - 1):
                if self.tiles[y][x] == B.AIR and rng.random() < 0.12:
                    self.tiles[y][x] = B.LAVA
        # أشجار (فقط فوق مستوى البحر = يابسة)
        for x in range(3, self.w - 3):
            hill = self.height[x]
            bio = self.biome[x]
            if hill <= C.SEA_LEVEL and self.tiles[hill][x] in (B.GRASS, B.SNOWY_GRASS):
                p = 0.06 if bio == 0 else (0.22 if bio == 2 else 0.01)
                if rng.random() < p and self.tiles[hill - 1][x] == B.AIR:
                    th = rng.randint(4, 6)
                    for i in range(1, th + 1):
                        if hill - i >= 0:
                            self.tiles[hill - i][x] = B.LOG
                    top_y = hill - th
                    for dx in range(-2, 3):
                        for dy in range(-2, 2):
                            xx, yy = x + dx, top_y + dy
                            if 0 <= xx < self.w and 0 <= yy < self.h:
                                if self.tiles[yy][xx] == B.AIR and abs(dx) + abs(dy) <= 4:
                                    self.tiles[yy][xx] = B.LEAVES
                    self.tiles[top_y - 1][x] = B.LEAVES
            # صبار/زهور/عشب (يابسة فقط)
            if hill <= C.SEA_LEVEL and self.tiles[hill - 1][x] == B.AIR:
                r = rng.random()
                if bio == 1 and r < 0.05:
                    self.tiles[hill - 1][x] = B.LOG  # صبار مبسط (جذع)
                elif bio != 1 and r < 0.10:
                    self.tiles[hill - 1][x] = B.FLOWER if r < 0.04 else B.TALLGRASS
        # نقطة الظهور: أقرب يابسة للمنتصف (hill <= SEA يعني فوق الماء)
        mid = self.w // 2
        found = False
        for d in range(0, self.w // 2):
            for x in (mid + d, mid - d):
                if not (1 <= x < self.w - 1): continue
                hh = self.height[x]
                if hh <= C.SEA_LEVEL and 2 <= hh < self.h - 1:
                    if self.tiles[hh - 1][x] == B.AIR and self.tiles[hh - 2][x] == B.AIR:
                        if self.tiles[hh][x] not in (B.WATER, B.LAVA):
                            self.spawn = (x, hh - 2)
                            found = True
                            break
            if found: break
        if not found:  # ملاذ أخير: فوق التضاريس مباشرة
            hh = self.height[mid]
            self.spawn = (mid, max(1, hh - 2))

    # ---- حفظ / تحميل ----
    def save(self, name):
        os.makedirs(os.path.join(os.path.dirname(__file__), C.SAVE_DIR), exist_ok=True)
        path = os.path.join(os.path.dirname(__file__), C.SAVE_DIR, name + ".json.gz")
        # نخزن الصفوف كقوائم (مضغوطة)
        data = {"seed": self.seed, "time": self.time, "w": self.w, "h": self.h,
                "tiles": self.tiles, "spawn": self.spawn}
        with gzip.open(path, "wt", encoding="utf-8") as f:
            json.dump(data, f)
        return path

    @classmethod
    def load(cls, name):
        path = os.path.join(os.path.dirname(__file__), C.SAVE_DIR, name + ".json.gz")
        with gzip.open(path, "rt", encoding="utf-8") as f:
            data = json.load(f)
        wobj = cls(seed=data["seed"])
        wobj.w, wobj.h = data["w"], data["h"]
        wobj.tiles = data["tiles"]
        wobj.time = data.get("time", 6000)
        wobj.spawn = tuple(data.get("spawn", (wobj.w // 2, 40)))
        # أعد حساب الارتفاعات
        for x in range(wobj.w):
            for y in range(wobj.h):
                if wobj.tiles[y][x] not in (B.AIR, B.WATER, B.LAVA, B.FLOWER, B.TALLGRASS, B.TORCH):
                    wobj.height[x] = y
                    break
        return wobj

    @staticmethod
    def list_saves():
        d = os.path.join(os.path.dirname(__file__), C.SAVE_DIR)
        if not os.path.isdir(d): return []
        return [f[:-8] for f in os.listdir(d) if f.endswith(".json.gz")]
