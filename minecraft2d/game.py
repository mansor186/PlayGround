"""المحرك الرئيسي + الواجهات + الرسم"""
import os, sys, math, random, time
import pygame
from . import config as C
from . import blocks as B
from . import items as I
from . import recipes as R
from . import sound as S
from .world import World
from .inventory import Inventory
from .entities import Player, Mob, Drop, Particle

TILE = C.TILE

def lerp(a, b, t): return a + (b - a) * t
def lerp_color(c1, c2, t):
    return (int(lerp(c1[0], c2[0], t)), int(lerp(c1[1], c2[1], t)), int(lerp(c1[2], c2[2], t)))

def get_font(size):
    # خط يدعم العربية قدر الإمكان
    for name in ("dejavu", "arial", "freesans", "noto", None):
        try:
            f = pygame.font.SysFont(name, size) if name else pygame.font.Font(None, size)
            return f
        except Exception:
            continue
    return pygame.font.Font(None, size)

class Game:
    def __init__(self, width=C.SCREEN_W, height=C.SCREEN_H):
        pygame.init()
        S.init()
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption("Minecraft 2D - ماين كرافت ثنائية الأبعاد")
        self.clock = pygame.time.Clock()
        self.font = get_font(20)
        self.big = get_font(44)
        self.small = get_font(16)
        self.state = "menu"  # menu, create, load, play, pause, dead, help
        self.world = None
        self.player = None
        self.inv = None
        self.mobs = []
        self.drops = []
        self.particles = []
        self.cam = [0, 0]
        self.breaking = None  # (tx,ty,progress,need)
        self.inv_open = False
        self.craft_grid = [None] * 9
        self.craft_out = None
        self.chest_inv = None
        self.chest_open = False
        self.msg = ""
        self.msg_t = 0
        self.debug = False
        self.menu_sel = 0
        self.create_seed = ""
        self.create_mode = "survival"
        self.create_name = "world1"
        self.load_sel = 0
        self.clouds = [(random.randint(0, 4000), random.randint(20, 160)) for _ in range(14)]
        self.zoom = 1.0
        self.spawn_t = 0
        # ستارتر: أدوات بداية في الإبداعي
        self.mouse_down_l = False
        self.mouse_down_r = False
        self.place_cd = 0

    # ---------- أدوات مساعدة ----------
    def say(self, t, dur=150):
        self.msg = t; self.msg_t = dur

    def new_world(self, name, seed_str, mode):
        try: seed = int(seed_str)
        except Exception:
            seed = abs(hash(seed_str)) % 10**8 if seed_str else random.randint(0, 999999)
        self.world = World(seed=seed)
        self.world.generate()
        self.inv = Inventory()
        self.player = Player(self.world, self.inv)
        self.player.gamemode = mode
        if mode == "creative":
            for iid in ("block:6", "block:9", "block:8", "block:10", "pickaxe_diamond", "axe_diamond", "sword_diamond"):
                self.inv.add(iid, 64 if iid.startswith("block") else 1)
            self.player.fly = False
        else:
            self.inv.add("block:18", 1)
            self.inv.add("block:10", 8)
        self.mobs = []; self.drops = []; self.particles = []
        self.chest_inv = Inventory(size=27)
        self.world_name = name or "world1"
        self.world.save(self.world_name)
        self.state = "play"

    def load_world(self, name):
        self.world = World.load(name)
        self.world_name = name
        # حمّل اللاعب إن وُجد
        import gzip, json
        p = os.path.join(os.path.dirname(__file__), C.SAVE_DIR, name + ".player.json")
        self.inv = Inventory()
        self.player = Player(self.world, self.inv)
        if os.path.exists(p):
            try:
                with open(p, encoding="utf-8") as f: d = json.load(f)
                self.player.rect.x = d["x"]; self.player.rect.y = d["y"]
                self.player.hp = d.get("hp", 20); self.player.hunger = d.get("hunger", 20)
                self.player.gamemode = d.get("mode", "survival")
                self.inv.from_data(d.get("inv", {"slots": self.inv.slots, "selected": 0}))
            except Exception as e:
                print("load player failed", e)
        self.mobs = []; self.drops = []; self.particles = []
        self.chest_inv = Inventory(size=27)
        # حمّل الصندوق
        cp = os.path.join(os.path.dirname(__file__), C.SAVE_DIR, name + ".chest.json")
        if os.path.exists(cp):
            try:
                import json as J
                with open(cp, encoding="utf-8") as f: self.chest_inv.from_data(J.load(f))
            except Exception: pass
        self.state = "play"

    def save_all(self):
        if not self.world: return
        self.world.save(self.world_name)
        import json
        d = os.path.join(os.path.dirname(__file__), C.SAVE_DIR)
        with open(os.path.join(d, self.world_name + ".player.json"), "w", encoding="utf-8") as f:
            json.dump({"x": self.player.rect.x, "y": self.player.rect.y, "hp": self.player.hp,
                       "hunger": self.player.hunger, "mode": self.player.gamemode,
                       "inv": self.inv.to_data()}, f)
        with open(os.path.join(d, self.world_name + ".chest.json"), "w", encoding="utf-8") as f:
            json.dump(self.chest_inv.to_data(), f)
        self.say("Saved! تم الحفظ")

    # ---------- حلقة ----------
    def run(self):
        while True:
            dt = self.clock.tick(C.FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
            pygame.display.flip()

    def handle_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                if self.state == "play": self.save_all()
                pygame.quit(); sys.exit()
            elif ev.type == pygame.KEYDOWN:
                self.on_key(ev.key, ev.unicode)
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if self.state == "play":
                    if ev.button == 1: self.click_left(ev.pos)
                    elif ev.button == 3: self.click_right(ev.pos)
                    elif ev.button == 2: self.pick_block(ev.pos)
                    elif ev.button == 4: self.inv.selected = (self.inv.selected - 1) % 9
                    elif ev.button == 5: self.inv.selected = (self.inv.selected + 1) % 9
            elif ev.type == pygame.MOUSEBUTTONUP:
                pass
            elif ev.type == pygame.VIDEORESIZE:
                pass

    def on_key(self, key, uni):
        if self.state == "menu":
            if key in (pygame.K_UP, pygame.K_w): self.menu_sel = (self.menu_sel - 1) % 4
            if key in (pygame.K_DOWN, pygame.K_s): self.menu_sel = (self.menu_sel + 1) % 4
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.menu_sel == 0: self.state = "create"; self.create_seed = str(random.randint(0, 99999))
                elif self.menu_sel == 1: self.state = "load"; self.load_sel = 0
                elif self.menu_sel == 2: self.state = "help"
                elif self.menu_sel == 3: pygame.quit(); sys.exit()
            if key == pygame.K_ESCAPE: pygame.quit(); sys.exit()
        elif self.state == "help":
            if key in (pygame.K_ESCAPE, pygame.K_RETURN): self.state = "menu"
        elif self.state == "create":
            if key == pygame.K_ESCAPE: self.state = "menu"
            elif key == pygame.K_TAB: self.create_mode = "creative" if self.create_mode == "survival" else "survival"
            elif key == pygame.K_RETURN:
                self.new_world(self.create_name or "world1", self.create_seed, self.create_mode)
            elif key == pygame.K_BACKSPACE:
                # نحذف من الحقل النشط (الاسم)
                self.create_name = self.create_name[:-1]
            elif uni and uni.isprintable() and len(self.create_name) < 16:
                if uni not in ("/", "\\"):
                    self.create_name += uni
        elif self.state == "load":
            saves = World.list_saves()
            if key == pygame.K_ESCAPE: self.state = "menu"
            if key == pygame.K_UP: self.load_sel = max(0, self.load_sel - 1)
            if key == pygame.K_DOWN: self.load_sel = max(0, self.load_sel + (1 if saves else 0) - 1) if saves else 0
            if key == pygame.K_RETURN and saves:
                self.load_world(saves[self.load_sel % len(saves)])
        elif self.state == "play":
            if key == pygame.K_ESCAPE:
                if self.inv_open or self.chest_open:
                    self.inv_open = False; self.chest_open = False
                else:
                    self.state = "pause"; self.save_all()
            elif key == pygame.K_e:
                self.inv_open = not self.inv_open; self.chest_open = False
            elif key == pygame.K_F3: self.debug = not self.debug
            elif key == pygame.K_f and self.player.gamemode == "creative":
                self.player.fly = not self.player.fly
                self.say("Fly ON" if self.player.fly else "Fly OFF")
            elif key == pygame.K_g:
                self.player.gamemode = "creative" if self.player.gamemode == "survival" else "survival"
                self.say(f"Mode: {self.player.gamemode}")
            elif key == pygame.K_q: self.drop_held()
            elif key == pygame.K_r: self.player.eat() and S.play("eat")
            elif key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9):
                self.inv.selected = key - pygame.K_1
        elif self.state == "pause":
            if key == pygame.K_ESCAPE or key == pygame.K_RETURN: self.state = "play"
            elif key == pygame.K_s: self.save_all()
            elif key == pygame.K_m: self.save_all(); self.state = "menu"
        elif self.state == "dead":
            if key == pygame.K_RETURN:
                self.player.respawn(); self.player.hp = 20; self.state = "play"
                self.say("Respawned!")

    # ---------- تفاعل ----------
    def screen_to_world_tile(self, pos):
        mx, my = pos
        wx = mx + self.cam[0]; wy = my + self.cam[1]
        return wx // TILE, wy // TILE, wx, wy

    def target_tile(self, pos):
        tx, ty, wx, wy = self.screen_to_world_tile(pos)
        px, py = self.player.rect.centerx, self.player.rect.centery
        if math.hypot(wx - px, wy - py) > C.REACH_DIST + TILE:
            return None
        return (tx, ty)

    def held_tool_info(self):
        s = self.inv.held()
        iid = s["id"]
        if iid is None: return (None, 0, 1.0)
        if I.is_tool(iid): return (I.tool_kind(iid), I.tool_level(iid), I.tool_damage(iid) * 2)
        return (None, 0, 1.0)

    def mine_speed(self, bid):
        prop = B.BLOCKS.get(bid, {})
        hard = prop.get("hard", 1)
        if hard is None or hard < 0: return 0
        need = max(1, int(hard * 40))
        kind, lvl, _ = self.held_tool_info()
        need_tool = prop.get("tool")
        mult = 1.0
        if need_tool and kind == need_tool:
            mult = {1: 2.2, 2: 4.0, 3: 6.0, 4: 9.0}.get(lvl, 1.0)
        elif kind in ("pickaxe", "axe", "shovel") and need_tool is None:
            mult = 1.4
        # الإبداعي: فوري
        if self.player.gamemode == "creative": return (1, 1)
        return (int(need / mult), mult)

    def click_left(self, pos):
        # إذا المخزون مفتوح: التقاط/وضع عبر UI
        if self.inv_open or self.chest_open:
            self.inv_click(pos, right=False); return
        t = self.target_tile(pos)
        if not t: return
        tx, ty = t
        bid = self.world.get(tx, ty)
        if bid == B.AIR or bid == B.WATER or bid == B.LAVA: 
            # ضرب وحش؟
            self.attack_mobs(pos)
            return
        if bid == B.BEDROCK:
            self.say("Bedrock! لا يمكن كسر البيدروك"); return
        # تحقق مستوى الأداة
        req = I.REQUIRED_LEVEL.get(bid, 0)
        _, lvl, _ = self.held_tool_info()
        # اليد تستطيع كسر التراب والخشب فقط بسرعة؛ الحجر يحتاج معول
        # نسمح بالكسر لكن بدون دروب إذا المستوى ناقص
        need, _ = self.mine_speed(bid)
        self.breaking = (tx, ty, 0, max(1, need))
        S.play("hit")

    def attack_mobs(self, pos):
        mx, my = pos
        wx, wy = mx + self.cam[0], my + self.cam[1]
        s = self.inv.held()
        dmg = I.tool_damage(s["id"]) if s["id"] else 1.0
        if s and I.tool_kind(s["id"]) == "sword": dmg *= 1.0
        else: dmg = dmg if s["id"] and I.is_tool(s["id"]) else 1.5
        for m in self.mobs:
            if m.rect.collidepoint(wx, wy) or math.hypot(m.rect.centerx - wx, m.rect.centery - wy) < 46:
                m.hit(dmg)
                S.play("hit")
                for _ in range(6):
                    self.particles.append(Particle(m.rect.centerx, m.rect.centery, (200, 60, 60)))
                if self.player.gamemode == "survival" and s["id"] and I.tool_kind(s["id"]) == "sword":
                    if self.inv.damage_tool(): self.say("انكسر السيف!")
                break

    def click_right(self, pos):
        if self.inv_open or self.chest_open:
            self.inv_click(pos, right=True); return
        t = self.target_tile(pos)
        if not t: return
        tx, ty = t
        bid = self.world.get(tx, ty)
        # تفاعل: طاولة / فرن / صندوق
        if bid == B.CRAFTING:
            self.inv_open = True; self.say("طاولة الصناعة: استخدم الشبكة 3x3"); return
        if bid == B.FURNACE:
            self.smelt(); return
        if bid == B.CHEST:
            self.chest_open = True; self.inv_open = False; return
        # أكل؟
        # بناء
        held = self.inv.held()
        if held["id"] is None: 
            # زر يمين فارغ = أكل إن أمكن
            if self.player.eat(): S.play("eat")
            return
        if not I.is_block_item(held["id"]): 
            if self.player.eat(): S.play("eat")
            return
        place_id = I.block_id_of(held["id"])
        # لا تبنِ مكان كتلة صلبة موجودة
        if bid not in (B.AIR, B.WATER, B.LAVA, B.FLOWER, B.TALLGRASS, B.TORCH):
            return
        # لا تبنِ داخل اللاعب/الوحوش
        r = pygame.Rect(tx * TILE, ty * TILE, TILE, TILE)
        if r.colliderect(self.player.rect) and B.is_solid(place_id): return
        for m in self.mobs:
            if r.colliderect(m.rect) and B.is_solid(place_id): return
        # مشعل يُبنى على جدار؟ نبسط: يُبنى في الهواء
        self.world.set(tx, ty, place_id)
        S.play("place")
        if self.player.gamemode == "survival":
            self.inv.consume_held(1)

    def pick_block(self, pos):
        t = self.target_tile(pos)
        if not t: return
        bid = self.world.get(t[0], t[1])
        if bid == B.AIR: return
        iid = f"block:{bid}"
        # ابحث في الهوت بار
        for i in range(9):
            if self.inv.slots[i]["id"] == iid:
                self.inv.selected = i; return
        if self.player.gamemode == "creative":
            self.inv.slots[self.inv.selected] = {"id": iid, "count": 64, "dur": 0}

    def drop_held(self):
        s = self.inv.held()
        if s["id"] is None: return
        self.drops.append(Drop(self.player.rect.centerx, self.player.rect.centery, s["id"], 1))
        if I.is_tool(s["id"]):
            s["id"] = None; s["count"] = 0; s["dur"] = 0
        else:
            s["count"] -= 1
            if s["count"] <= 0: s["id"] = None; s["count"] = 0

    def smelt(self):
        # صهر مبسط: خام حديد + فحم -> سبيكة
        has_iron = has_coal = False
        for sl in self.inv.slots:
            if sl["id"] == "raw_iron" and sl["count"] > 0: has_iron = sl
            if sl["id"] == "coal" and sl["count"] > 0: has_coal = sl
        if has_iron and has_coal:
            has_iron["count"] -= 1
            if has_iron["count"] <= 0: has_iron["id"] = None
            has_coal["count"] -= 1
            if has_coal["count"] <= 0: has_coal["id"] = None
            self.inv.add("iron_ingot", 1)
            S.play("craft"); self.say("تم الصهر: + سبيكة حديد")
        else:
            self.say("الفرن يحتاج: حديد خام + فحم في مخزونك")

    # ---------- UI مخزون ----------
    def slot_rects(self):
        sw, sh = self.screen.get_size()
        rects = []
        # هوت بار + مخزون (4x9)
        base_y = sh - 70
        for i in range(9):
            rects.append(pygame.Rect(sw // 2 - 9 * 27 + i * 54, base_y, 50, 50))
        if self.inv_open:
            for r in range(3):
                for c_ in range(9):
                    idx = 9 + r * 9 + c_
                    rects.append(pygame.Rect(sw // 2 - 9 * 27 + c_ * 54, base_y - 170 + r * 54, 50, 50))
        return rects

    def inv_click(self, pos, right=False):
        # شبكة الصناعة + المخرج + المخزون
        sw, sh = self.screen.get_size()
        # صناعة 3x3 أعلى المخزون
        cx0 = sw // 2 - 81; cy0 = sh - 400
        for i in range(9):
            r_ = pygame.Rect(cx0 + (i % 3) * 54, cy0 + (i // 3) * 54, 50, 50)
            if r_.collidepoint(pos):
                cur = self.craft_grid[i]
                held = self._cursor()
                if not right:
                    self.craft_grid[i], self._set_cursor(cur)
                else:
                    if held and cur is None: self.craft_grid[i] = held; self._dec_cursor(1)
                    elif held is None and cur: self.craft_grid[i] = None; self._set_cursor(cur)
                self.refresh_craft()
                return
        out_r = pygame.Rect(cx0 + 200, cy0 + 54, 50, 50)
        if out_r.collidepoint(pos) and self.craft_out:
            if self._give(self.craft_out[0], self.craft_out[1]):
                # استهلاك الشبكة
                for i in range(9):
                    if self.craft_grid[i]:
                        # إنقاص 1
                        iid, c = self.craft_grid[i]
                        c -= 1
                        self.craft_grid[i] = (iid, c) if c > 0 else None
                S.play("craft")
                self.refresh_craft()
            return
        # خانات المخزون
        rects = self.slot_rects()
        # indices: أول 9 هوت بار ثم 27
        order = list(range(9)) + list(range(9, 36))
        for k, idx in enumerate(order):
            if k < len(rects) and rects[k].collidepoint(pos):
                s = self.inv.slots[idx]
                cur = self._cursor()
                s_tuple = (s["id"], s["count"]) if s["id"] else None
                if not right:
                    # تبادل
                    if cur is None and s_tuple:
                        self._set_cursor(s_tuple); s["id"] = None; s["count"] = 0
                    elif cur and s_tuple is None:
                        s["id"], s["count"] = cur; s["dur"] = I.tool_maxdur(cur[0]) if I.is_tool(cur[0]) else 0
                        self._set_cursor(None)
                    elif cur and s_tuple:
                        if cur[0] == s_tuple[0] and not I.is_tool(cur[0]):
                            tot = cur[1] + s_tuple[1]
                            s["count"] = min(I.MAX_STACK, tot)
                            rest = tot - s["count"]
                            self._set_cursor((cur[0], rest) if rest > 0 else None)
                        else:
                            self._set_cursor(s_tuple); s["id"], s["count"] = cur
                    # حدث الأدوات
                else:
                    # يمين: وضع حبة واحدة / أخذ نصف
                    if cur and s_tuple is None:
                        s["id"] = cur[0]; s["count"] = 1; self._dec_cursor(1)
                    elif cur is None and s_tuple:
                        half = (s_tuple[1] + 1) // 2
                        self._set_cursor((s_tuple[0], half))
                        s["count"] -= half
                        if s["count"] <= 0: s["id"] = None
                    elif cur and s_tuple and cur[0] == s_tuple[0] and not I.is_tool(cur[0]):
                        if s["count"] < I.MAX_STACK:
                            s["count"] += 1; self._dec_cursor(1)
                return
        # صندوق؟
        if self.chest_open:
            pass

    _cursor_stack = None
    def _cursor(self): return Game._cursor_stack
    def _set_cursor(self, v): Game._cursor_stack = v
    def _dec_cursor(self, n):
        c = Game._cursor_stack
        if not c: return
        c = (c[0], c[1] - n)
        Game._cursor_stack = c if c[1] > 0 else None
    def _give(self, iid, n):
        c = self._cursor()
        if c is None:
            self._set_cursor((iid, n)); return True
        if c[0] == iid and c[1] + n <= 64:
            self._set_cursor((iid, c[1] + n)); return True
        # حاول المخزون
        return self.inv.add(iid, n)

    def refresh_craft(self):
        grid = []
        for cell in self.craft_grid:
            grid.append(cell[0] if cell else None)
        r = R.match_recipe(grid)
        self.craft_out = r

    # ---------- تحديث ----------
    def update(self, dt):
        if self.state != "play" or self.world is None:
            return
        # الوقت
        self.world.time = (self.world.time + dt * 24000 / C.DAY_LENGTH_SEC) % 24000
        is_night = self.world.time > 13000 and self.world.time < 23000
        keys = {}
        if not (self.inv_open or self.chest_open):
            k = pygame.key.get_pressed()
            keys = {"left": k[pygame.K_a] or k[pygame.K_LEFT], "right": k[pygame.K_d] or k[pygame.K_RIGHT],
                    "jump": k[pygame.K_SPACE] or k[pygame.K_w] or k[pygame.K_UP],
                    "down": k[pygame.K_s] or k[pygame.K_DOWN],
                    "sprint": k[pygame.K_LSHIFT] or k[pygame.K_RSHIFT]}
        self.player.update(keys, dt)
        if self.player.dead and self.state == "play":
            self.state = "dead"
        # كاميرا
        sw, sh = self.screen.get_size()
        self.cam[0] = int(self.player.rect.centerx - sw / 2)
        self.cam[1] = int(self.player.rect.centery - sh / 2)
        self.cam[0] = max(-50, min(self.world.w * TILE - sw + 50, self.cam[0]))
        self.cam[1] = max(-200, min(self.world.h * TILE - sh + 100, self.cam[1]))
        # تكسير مستمر
        mouse = pygame.mouse.get_pressed()
        if mouse[0] and not (self.inv_open or self.chest_open):
            pos = pygame.mouse.get_pos()
            t = self.target_tile(pos)
            if t and self.breaking and (t[0], t[1]) == (self.breaking[0], self.breaking[1]):
                tx, ty = t
                bid = self.world.get(tx, ty)
                if bid in (B.AIR, B.WATER, B.LAVA, B.BEDROCK):
                    self.breaking = None
                else:
                    _, _, mult = self.held_tool_info()
                    # سرعة إضافية للأداة الصحيحة
                    prop = B.BLOCKS[bid]
                    step = mult * (2.0 if prop.get("tool") and self.held_tool_info()[0] == prop.get("tool") else 1.0)
                    p = self.breaking[2] + step
                    need = self.breaking[3]
                    # جسيمات
                    if random.random() < 0.3:
                        self.particles.append(Particle(tx * TILE + 16, ty * TILE + 16, prop["color"]))
                    if p >= need:
                        self.break_block(tx, ty)
                        self.breaking = None
                    else:
                        self.breaking = (tx, ty, p, need)
            elif t and not self.breaking:
                self.click_left(pos)
        else:
            if self.breaking and self.breaking[2] <= 0:
                self.breaking = None
            # إبقاء التقدم؟ نُصفّره تدريجياً
            if self.breaking and not mouse[0]:
                self.breaking = None
        if self.place_cd > 0: self.place_cd -= 1
        # زر يمين مستمر للبناء
        if mouse[2] and not (self.inv_open or self.chest_open) and self.place_cd <= 0:
            self.click_right(pygame.mouse.get_pos())
            self.place_cd = 12
        # وحوش
        self.spawn_t += 1
        if self.spawn_t > 110:
            self.spawn_t = 0
            self.try_spawn(is_night)
        for m in self.mobs:
            m.update(self.player, is_night)
            if m.dead:
                # دروبات
                if m.kind == "pig": self.drops.append(Drop(m.rect.centerx, m.rect.centery, "pork", random.randint(1, 2)))
                elif m.kind == "sheep": self.drops.append(Drop(m.rect.centerx, m.rect.centery, "wool", 1))
                elif m.kind == "zombie":
                    if random.random() < 0.5: self.drops.append(Drop(m.rect.centerx, m.rect.centery, "apple", 1))
                elif m.kind == "skeleton":
                    if random.random() < 0.5: self.drops.append(Drop(m.rect.centerx, m.rect.centery, "stick", 2))
                S.play("hit")
        self.mobs = [m for m in self.mobs if not m.dead][:24]
        # قطرات
        for d in self.drops:
            d.update(self.world)
            if math.hypot(d.rect.centerx - self.player.rect.centerx, d.rect.centery - self.player.rect.centery) < 90:
                # مغناطيس
                d.rect.x += 1 if d.rect.centerx < self.player.rect.centerx else -1
                d.rect.x += 1 if d.rect.centerx < self.player.rect.centerx else -1
            if d.rect.colliderect(self.player.rect):
                if self.inv.add(d.iid, d.count):
                    d.dead = True; S.play("pickup")
        self.drops = [d for d in self.drops if not d.dead]
        # جسيمات
        for p in self.particles: p.update()
        self.particles = [p for p in self.particles if not p.dead][:300]
        # غيوم
        for i, (x, y) in enumerate(self.clouds):
            self.clouds[i] = (x + 0.3, y)
            if x > 4500: self.clouds[i] = (-300, random.randint(20, 160))
        if self.msg_t > 0: self.msg_t -= 1

    def break_block(self, tx, ty):
        bid = self.world.get(tx, ty)
        prop = B.BLOCKS.get(bid, {})
        # تحقق الأداة
        req = I.REQUIRED_LEVEL.get(bid, 0)
        _, lvl, _ = self.held_tool_info()
        drop = prop.get("drop")
        gets_drop = True
        if req > 0 and lvl < req:
            gets_drop = False  # كسر بدون دروب (مثل الألماس باليد)
            if bid in (B.DIAMOND_ORE, B.IRON_ORE, B.COAL_ORE):
                self.say("تحتاج معول أقوى! (حجر/حديد/ألماس)")
        self.world.set(tx, ty, B.AIR)
        S.play("break")
        for _ in range(10):
            self.particles.append(Particle(tx * TILE + 16, ty * TILE + 16, prop.get("color", (120, 120, 120))))
        # دروب
        if self.player.gamemode == "creative":
            return
        kind, _, _ = self.held_tool_info()
        # إتلاف الأداة إذا مناسبة
        if prop.get("tool") and kind == prop.get("tool"):
            if self.inv.damage_tool(): self.say("انكسرت الأداة!")
        elif bid in (B.STONE, B.COBBLE, B.SAND, B.DIRT, B.GRASS, B.LOG):
            if random.random() < 0.25 and self.inv.held()["id"] and I.is_tool(self.inv.held()["id"]):
                if self.inv.damage_tool(): self.say("انكسرت الأداة!")
        # أوراق تسقط تفاح/عصا
        if bid == B.LEAVES:
            r = random.random()
            if r < 0.06: self.drops.append(Drop(tx * TILE + 16, ty * TILE + 16, "apple", 1))
            elif r < 0.15: self.drops.append(Drop(tx * TILE + 16, ty * TILE + 16, "stick", 1))
            return
        if drop and gets_drop:
            # حصى من حجر إلخ
            if drop.startswith("block:"):
                self.drops.append(Drop(tx * TILE + 16, ty * TILE + 16, drop, 1))
            else:
                n = 1
                if drop == "coal": n = random.randint(1, 2)
                self.drops.append(Drop(tx * TILE + 16, ty * TILE + 16, drop, n))
                if bid == B.IRON_ORE:
                    # خام حديد كعنصر
                    pass
        elif bid == B.STONE or bid == B.COBBLE:
            if gets_drop:
                self.drops.append(Drop(tx * TILE + 16, ty * TILE + 16, "block:24", 1))

    def try_spawn(self, is_night):
        if len(self.mobs) >= 14: return
        px = self.player.rect.centerx // TILE
        for _ in range(3):
            x = px + random.randint(-24, 24)
            if not (0 < x < self.world.w - 1): continue
            # سطح
            y = None
            for yy in range(max(1, self.player.rect.y // TILE - 12), min(self.world.h - 2, self.player.rect.y // TILE + 12)):
                if self.world.get(x, yy) == B.AIR and self.world.get(x, yy + 1) not in (B.AIR, B.WATER, B.LAVA) and B.is_solid(self.world.get(x, yy + 1)):
                    y = yy; break
            if y is None: continue
            dist = abs(x * TILE - self.player.rect.centerx)
            if dist < 5 * TILE: continue
            if is_night:
                kind = random.choice(["zombie", "zombie", "skeleton"])
                self.mobs.append(Mob(self.world, kind, x * TILE, (y - 1) * TILE))
            else:
                if random.random() < 0.35:
                    kind = random.choice(["pig", "sheep"])
                    self.mobs.append(Mob(self.world, kind, x * TILE, y * TILE))
            break

    # ---------- رسم ----------
    def draw(self):
        if self.state == "menu": self.draw_menu(); return
        if self.state == "help": self.draw_help(); return
        if self.state == "create": self.draw_create(); return
        if self.state == "load": self.draw_load(); return
        if self.world is None: self.draw_menu(); return
        self.draw_world()
        if self.state == "pause": self.draw_pause()
        elif self.state == "dead": self.draw_dead()

    def sky_color(self):
        t = self.world.time
        # 6000 ظهر، 18000 منتصف الليل
        if 5000 <= t <= 12000: return C.SKY_DAY
        if 13000 <= t <= 22000: return C.SKY_NIGHT
        # شروق/غروب
        if t < 5000:
            k = 1 - abs(t - 2500) / 2500
            return lerp_color(C.SKY_NIGHT, (250, 150, 80), max(0, k) * 0.7)
        # 12000-13000 غروب، 22000-24000+0-5000 شروق
        if 12000 <= t <= 13000:
            k = (t - 12000) / 1000
            return lerp_color(C.SKY_DAY, (240, 130, 60), k * 0.8)
        if 22000 <= t <= 24000:
            k = (t - 22000) / 2000
            return lerp_color((240, 130, 60), C.SKY_NIGHT, k)
        return C.SKY_DAY

    def draw_world(self):
        sw, sh = self.screen.get_size()
        sky = self.sky_color()
        self.screen.fill(sky)
        is_night = self.world.time > 13000 and self.world.time < 23000
        # نجوم
        if is_night:
            for i in range(90):
                x = (i * 173 + 50) % sw; y = (i * 97 + 30) % (sh // 2)
                tw = 120 + 100 * math.sin(time.time() * 2 + i)
                if tw > 150:
                    self.screen.set_at((x, y), (255, 255, 255))
        # شمس / قمر
        ang = (self.world.time / 24000) * 2 * math.pi
        sx = sw // 2 + int(math.cos(ang) * sw * 0.4)
        sy = sh // 2 - int(math.sin(ang) * sh * 0.4)
        if not is_night:
            pygame.draw.circle(self.screen, (255, 230, 80), (sx, sy), 30)
            pygame.draw.circle(self.screen, (255, 245, 150), (sx, sy), 24)
        else:
            pygame.draw.circle(self.screen, (220, 220, 230), (sx, sy), 22)
            pygame.draw.circle(self.screen, sky, (sx + 8, sy - 4), 18)
        # غيوم
        for (x, y) in self.clouds:
            cx = int(x - self.cam[0] * 0.3) % (sw + 300) - 150
            pygame.draw.rect(self.screen, (255, 255, 255, 180), (cx, y - self.cam[1] * 0.1, 120, 24), border_radius=8)
            pygame.draw.rect(self.screen, (255, 255, 255, 180), (cx + 20, y - 12 - self.cam[1] * 0.1, 80, 24), border_radius=8)
        # بلاطات
        x0 = max(0, self.cam[0] // TILE - 1); x1 = min(self.world.w, (self.cam[0] + sw) // TILE + 2)
        y0 = max(0, self.cam[1] // TILE - 1); y1 = min(self.world.h, (self.cam[1] + sh) // TILE + 2)
        # خلفية ترابية للكهوف
        for ty in range(y0, y1):
            for tx in range(x0, x1):
                bid = self.world.get(tx, ty)
                sxp, syp = tx * TILE - self.cam[0], ty * TILE - self.cam[1]
                if bid == B.AIR:
                    # خلفية الكهف فقط تحت سطح الأرض (y أكبر من ارتفاع العمود)
                    try:
                        ground = self.world.height[tx]
                    except Exception:
                        ground = 0
                    if ty > ground:
                        self.screen.fill((28, 22, 18), (sxp, syp, TILE, TILE))
                    continue
                tex = B.make_texture(bid, TILE)
                self.screen.blit(tex, (sxp, syp))
                # ماء متموج
                if bid == B.WATER:
                    w = math.sin(time.time() * 3 + tx) * 3
                    pygame.draw.line(self.screen, (140, 190, 255), (sxp, syp + 8 + w), (sxp + TILE, syp + 8 + w), 2)
        # تمييز البلوك المستهدف + تشقق
        mpos = pygame.mouse.get_pos()
        if not (self.inv_open or self.chest_open) and self.state == "play":
            t = self.target_tile(mpos)
            if t:
                bid = self.world.get(t[0], t[1])
                if bid not in (B.AIR, B.WATER, B.LAVA):
                    r = pygame.Rect(t[0] * TILE - self.cam[0], t[1] * TILE - self.cam[1], TILE, TILE)
                    pygame.draw.rect(self.screen, (255, 255, 255), r, 2)
                    if self.breaking and (t[0], t[1]) == (self.breaking[0], self.breaking[1]):
                        k = self.breaking[2] / max(1, self.breaking[3])
                        # تشقق: خطوط
                        for i in range(int(k * 6)):
                            x_ = r.x + (i * 13) % TILE; y_ = r.y + (i * 29) % TILE
                            pygame.draw.line(self.screen, (20, 20, 20), (x_, y_), (x_ + 8, y_ + 8), 2)
        # قطرات
        for d in self.drops:
            p = (d.rect.centerx - self.cam[0], d.rect.centery - self.cam[1])
            bob = math.sin(time.time() * 4 + d.age * 0.1) * 3
            self.draw_item_icon(d.iid, p[0] - 10, p[1] - 10 + bob, 20)
        # وحوش
        for m in self.mobs:
            self.draw_mob(m)
        # اللاعب
        self.draw_player()
        # جسيمات
        for p in self.particles:
            self.screen.fill(p.color, (p.x - self.cam[0], p.y - self.cam[1], 4, 4))
        # إضاءة ليلية
        self.draw_lighting(x0, x1, y0, y1, is_night)
        # HUD
        self.draw_hud()
        if self.inv_open: self.draw_inventory_ui()
        if self.chest_open: self.draw_chest_ui()
        if self.msg_t > 0:
            txt = self.font.render(self.msg, True, (255, 255, 255))
            bg = pygame.Surface((txt.get_width() + 16, txt.get_height() + 10)); bg.fill((0, 0, 0)); bg.set_alpha(150)
            self.screen.blit(bg, (sw // 2 - bg.get_width() // 2, 60))
            self.screen.blit(txt, (sw // 2 - txt.get_width() // 2, 65))
        if self.debug: self.draw_debug()

    def draw_lighting(self, x0, x1, y0, y1, is_night):
        sw, sh = self.screen.get_size()
        t = self.world.time
        # ظلام أساسي 0..170
        if 6000 <= t <= 12000: dark = 0
        elif 13000 <= t <= 22000: dark = 150
        elif 12000 < t < 13000: dark = int((t - 12000) / 1000 * 150)
        elif 22000 < t <= 24000: dark = int(150 - (t - 22000) / 2000 * 150)
        else: dark = int(60 + 40 * math.sin(t / 1000))
        # العمق يزيد الظلام
        overlay = pygame.Surface((sw, sh))
        overlay.fill((5, 5, 25))
        overlay.set_alpha(min(190, dark))
        # ثقوب ضوء حول المشاعل والحمم واللاعب (نرسم شفاف)
        # نبسط: نرسم دوائر مظلمة أقل عبر مسح overlay؟ أسهل: نرسم overlay ثم نرسم دوائر radial مضيئة بـ BLEND
        self.screen.blit(overlay, (0, 0))
        # أضواء
        lights = []
        px, py = self.player.rect.centerx - self.cam[0], self.player.rect.centery - self.cam[1]
        # ضوء خافت حول اللاعب ليلاً
        if dark > 40: lights.append((px, py, 130, 60))
        for ty in range(y0, y1):
            for tx in range(x0, x1):
                b = self.world.get(tx, ty)
                L = B.BLOCKS.get(b, {}).get("light", 0)
                if L:
                    lights.append((tx * TILE + 16 - self.cam[0], ty * TILE + 16 - self.cam[1], L * 14, 110))
        for (x, y, r, a) in lights[:80]:
            # توهج بسيط
            for rr, aa in ((r, 40), (r // 2, 70)):
                s = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 200, 100, aa), (rr, rr), rr)
                self.screen.blit(s, (x - rr, y - rr), special_flags=pygame.BLEND_ADD)

    def draw_player(self):
        r = pygame.Rect(self.player.rect.x - self.cam[0], self.player.rect.y - self.cam[1],
                        self.player.rect.w, self.player.rect.h)
        # جسم (ستيف مبسط)
        hurt = self.player.hurt_t > 0 and (self.player.hurt_t // 3) % 2 == 0
        skin = (220, 150, 110) if not hurt else (255, 80, 80)
        shirt = (0, 170, 170); pants = (60, 60, 200)
        # أرجل
        pygame.draw.rect(self.screen, pants, (r.x + 4, r.y + r.h - 16, 9, 16))
        pygame.draw.rect(self.screen, pants, (r.x + r.w - 13, r.y + r.h - 16, 9, 16))
        # جسم
        pygame.draw.rect(self.screen, shirt, (r.x + 2, r.y + 20, r.w - 4, 22))
        # رأس
        pygame.draw.rect(self.screen, skin, (r.x, r.y, r.w, 20))
        pygame.draw.rect(self.screen, (50, 35, 20), (r.x, r.y, r.w, 6))  # شعر
        # عيون حسب الاتجاه
        ex = r.x + r.w - 10 if self.player.face > 0 else r.x + 4
        pygame.draw.rect(self.screen, (255, 255, 255), (ex, r.y + 9, 6, 5))
        pygame.draw.rect(self.screen, (30, 60, 200), (ex + (2 if self.player.face > 0 else 0), r.y + 10, 3, 3))
        # أداة محمولة
        held = self.inv.held()
        if held["id"]:
            hx = r.x + r.w if self.player.face > 0 else r.x - 18
            self.draw_item_icon(held["id"], hx, r.y + 24, 22)

    def draw_mob(self, m):
        r = pygame.Rect(m.rect.x - self.cam[0], m.rect.y - self.cam[1], m.rect.w, m.rect.h)
        if m.kind == "pig":
            pygame.draw.rect(self.screen, (240, 150, 160), r, border_radius=6)
            pygame.draw.rect(self.screen, (230, 120, 130), (r.x + 4, r.y + r.h - 8, 6, 8))
            pygame.draw.rect(self.screen, (230, 120, 130), (r.x + r.w - 10, r.y + r.h - 8, 6, 8))
            pygame.draw.circle(self.screen, (255, 180, 190), (r.centerx, r.centery), 5)  # أنف
            pygame.draw.circle(self.screen, (30, 30, 30), (r.x + 6, r.y + 7), 2)
        elif m.kind == "sheep":
            pygame.draw.rect(self.screen, (235, 235, 235), r, border_radius=8)
            pygame.draw.rect(self.screen, (220, 170, 140), (r.x + r.w - 12, r.y + 6, 10, 10))
            pygame.draw.circle(self.screen, (30, 30, 30), (r.x + r.w - 6, r.y + 10), 2)
        elif m.kind == "zombie":
            c = (60, 120, 70) if m.hurt <= 0 else (255, 100, 100)
            pygame.draw.rect(self.screen, (40, 60, 140), (r.x + 3, r.y + 22, r.w - 6, 20))
            pygame.draw.rect(self.screen, c, (r.x + 1, r.y, r.w - 2, 22))
            pygame.draw.rect(self.screen, (30, 30, 30), (r.x + 7, r.y + 9, 5, 4))
            pygame.draw.rect(self.screen, (30, 30, 30), (r.x + r.w - 12, r.y + 9, 5, 4))
        elif m.kind == "skeleton":
            c = (220, 220, 220) if m.hurt <= 0 else (255, 120, 120)
            pygame.draw.rect(self.screen, (190, 190, 190), (r.x + 3, r.y + 22, r.w - 6, 20))
            pygame.draw.rect(self.screen, c, (r.x + 1, r.y, r.w - 2, 22))
            pygame.draw.rect(self.screen, (20, 20, 20), (r.x + 7, r.y + 9, 5, 5))
            pygame.draw.rect(self.screen, (20, 20, 20), (r.x + r.w - 12, r.y + 9, 5, 5))
        # شريط صحة
        if m.hp < 20 and m.hostile() or (m.kind in ("pig", "sheep") and m.hp < 10):
            maxhp = 20 if m.hostile() else 10
            w = 30
            pygame.draw.rect(self.screen, (0, 0, 0), (r.centerx - w // 2, r.y - 8, w, 5))
            pygame.draw.rect(self.screen, (220, 40, 40), (r.centerx - w // 2, r.y - 8, w * max(0, m.hp / maxhp), 5))

    def draw_item_icon(self, iid, x, y, size=32):
        r = pygame.Rect(x, y, size, size)
        if I.is_block_item(iid):
            bid = I.block_id_of(iid)
            tex = B.make_texture(bid, 32)
            self.screen.blit(pygame.transform.scale(tex, (size, size)), r)
        elif iid in ("stick", "coal", "raw_iron", "iron_ingot", "diamond", "apple", "pork", "wool"):
            cols = {"stick": (150, 110, 60), "coal": (30, 30, 30), "raw_iron": (200, 170, 150),
                    "iron_ingot": (220, 220, 225), "diamond": (120, 230, 250),
                    "apple": (220, 50, 50), "pork": (240, 150, 140), "wool": (240, 240, 240)}
            pygame.draw.rect(self.screen, (60, 40, 25), r, border_radius=4)
            c = cols.get(iid, (200, 200, 200))
            if iid == "stick":
                pygame.draw.line(self.screen, c, (x + 6, y + size - 6), (x + size - 6, y + 6), 5)
            elif iid == "apple":
                pygame.draw.circle(self.screen, c, (x + size // 2, y + size // 2 + 2), size // 3)
                pygame.draw.rect(self.screen, (60, 140, 60), (x + size // 2 - 1, y + 3, 3, 7))
            elif iid == "diamond":
                pygame.draw.polygon(self.screen, c, [(x + size // 2, y + 4), (x + size - 5, y + size // 2), (x + size // 2, y + size - 4), (x + 5, y + size // 2)])
            else:
                pygame.draw.rect(self.screen, c, (x + 5, y + 8, size - 10, size - 14), border_radius=3)
                pygame.draw.rect(self.screen, (255, 255, 255), (x + 5, y + 8, size - 10, 4))
        else:
            # أدوات: مقبض + رأس
            kind = I.tool_kind(iid) or "pickaxe"
            lvl = I.tool_level(iid)
            cols = {1: (170, 130, 80), 2: (130, 130, 135), 3: (225, 225, 230), 4: (110, 220, 240)}
            hc = cols.get(lvl, (150, 150, 150))
            pygame.draw.rect(self.screen, (50, 40, 30), r, border_radius=4)
            pygame.draw.line(self.screen, (150, 110, 60), (x + 7, y + size - 6), (x + size - 9, y + 8), 4)
            if kind == "pickaxe":
                pygame.draw.arc(self.screen, hc, (x + 4, y + 2, size - 8, 14), 3.4, 6.0, 5)
            elif kind == "axe":
                pygame.draw.rect(self.screen, hc, (x + size - 14, y + 4, 10, 10), border_radius=2)
            elif kind == "shovel":
                pygame.draw.rect(self.screen, hc, (x + size - 14, y + 3, 9, 12), border_radius=3)
            else:
                pygame.draw.polygon(self.screen, hc, [(x + size - 12, y + 3), (x + size - 4, y + 3), (x + size - 4, y + size - 8), (x + size - 12, y + size - 8)])

    def draw_hud(self):
        sw, sh = self.screen.get_size()
        # هوت بار
        for i in range(9):
            x = sw // 2 - 9 * 27 + i * 54; y = sh - 66
            r = pygame.Rect(x, y, 50, 50)
            col = (0, 0, 0, 160)
            s = pygame.Surface((50, 50), pygame.SRCALPHA); s.fill((0, 0, 0, 140))
            self.screen.blit(s, (x, y))
            pygame.draw.rect(self.screen, (255, 255, 255) if i == self.inv.selected else (120, 120, 120), r, 3 if i == self.inv.selected else 1)
            sl = self.inv.slots[i]
            if sl["id"]:
                self.draw_item_icon(sl["id"], x + 5, y + 5, 40)
                if sl["count"] > 1 and not I.is_tool(sl["id"]):
                    t = self.small.render(str(sl["count"]), True, (255, 255, 255))
                    self.screen.blit(t, (x + 34, y + 32))
                if I.is_tool(sl["id"]):
                    mx = I.tool_maxdur(sl["id"]); d = sl.get("dur", mx)
                    pygame.draw.rect(self.screen, (0, 0, 0), (x + 5, y + 44, 40, 4))
                    pygame.draw.rect(self.screen, (80, 220, 80), (x + 5, y + 44, 40 * d / max(1, mx), 4))
            # رقم
            n = self.small.render(str(i + 1), True, (200, 200, 200))
            self.screen.blit(n, (x + 3, y + 2))
        # قلوب وجوع
        for i in range(10):
            x = sw // 2 - 9 * 27 + i * 26; y = sh - 96
            hp = self.player.hp / 2
            col = (220, 40, 40) if i < hp else (60, 20, 20)
            if i < hp - 0.5 or (hp - i) >= 1: full = True
            else: full = (hp - i) > 0
            pygame.draw.circle(self.screen, col, (x + 8, y + 8), 8)
            if not full and i >= hp: pygame.draw.circle(self.screen, (30, 30, 30), (x + 8, y + 8), 8, 2)
        for i in range(10):
            x = sw // 2 + 20 + i * 26; y = sh - 96
            hu = self.player.hunger / 2
            col = (200, 130, 40) if i < hu else (60, 40, 20)
            pygame.draw.rect(self.screen, col, (x, y, 16, 14), border_radius=3)
        # أكسجين
        if self.player.oxygen < 20:
            for i in range(10):
                x = sw // 2 - 9 * 27 + i * 26; y = sh - 120
                if i < self.player.oxygen / 2:
                    pygame.draw.circle(self.screen, (80, 160, 255), (x + 8, y + 8), 7)
        # وقت + وضع
        hh = int(self.world.time // 1000); mm = int((self.world.time % 1000) / 1000 * 60)
        t = self.small.render(f"{hh:02d}:{mm:02d}  {self.player.gamemode}  {'FLY' if self.player.fly else ''}", True, (255, 255, 255))
        self.screen.blit(t, (10, 10))
        # إحداثيات
        c = self.small.render(f"XYZ: {self.player.rect.centerx // TILE}, {self.player.rect.centery // TILE}", True, (230, 230, 230))
        self.screen.blit(c, (10, 32))

    def draw_inventory_ui(self):
        sw, sh = self.screen.get_size()
        over = pygame.Surface((sw, sh)); over.fill((0, 0, 0)); over.set_alpha(140)
        self.screen.blit(over, (0, 0))
        title = self.font.render("المخزون (E للخروج) + صناعة 3x3", True, (255, 255, 255))
        self.screen.blit(title, (sw // 2 - title.get_width() // 2, sh - 470))
        # شبكة صناعة
        cx0 = sw // 2 - 81; cy0 = sh - 400
        lbl = self.small.render("Crafting", True, (255, 255, 255))
        self.screen.blit(lbl, (cx0, cy0 - 22))
        for i in range(9):
            r = pygame.Rect(cx0 + (i % 3) * 54, cy0 + (i // 3) * 54, 50, 50)
            pygame.draw.rect(self.screen, (70, 70, 70), r); pygame.draw.rect(self.screen, (200, 200, 200), r, 2)
            cell = self.craft_grid[i]
            if cell: self.draw_item_icon(cell[0], r.x + 5, r.y + 5, 40)
        # مخرج
        out = pygame.Rect(cx0 + 200, cy0 + 54, 50, 50)
        pygame.draw.rect(self.screen, (90, 120, 70), out); pygame.draw.rect(self.screen, (255, 255, 255), out, 2)
        if self.craft_out:
            self.draw_item_icon(self.craft_out[0], out.x + 5, out.y + 5, 40)
            n = self.small.render(str(self.craft_out[1]), True, (255, 255, 255))
            self.screen.blit(n, (out.x + 34, out.y + 32))
        arr = self.small.render(">>", True, (255, 255, 255)); self.screen.blit(arr, (cx0 + 170, cy0 + 70))
        # خانات
        for k, idx in enumerate(list(range(9)) + list(range(9, 36))):
            rects = self.slot_rects()
            if k >= len(rects): break
            r = rects[k]
            pygame.draw.rect(self.screen, (60, 60, 60), r); pygame.draw.rect(self.screen, (220, 220, 220), r, 1)
            s = self.inv.slots[idx]
            if s["id"]:
                self.draw_item_icon(s["id"], r.x + 5, r.y + 5, 40)
                if not I.is_tool(s["id"]):
                    t = self.small.render(str(s["count"]), True, (255, 255, 255))
                    self.screen.blit(t, (r.x + 32, r.y + 30))
        # مؤشر
        c = self._cursor()
        if c:
            mp = pygame.mouse.get_pos()
            self.draw_item_icon(c[0], mp[0] - 15, mp[1] - 15, 30)

    def draw_chest_ui(self):
        sw, sh = self.screen.get_size()
        over = pygame.Surface((sw, sh)); over.fill((0, 0, 0)); over.set_alpha(140)
        self.screen.blit(over, (0, 0))
        t = self.font.render("الصندوق (ESC للخروج) — التخزين الكامل قريباً: استخدم E", True, (255, 255, 255))
        self.screen.blit(t, (sw // 2 - t.get_width() // 2, 120))
        # عرض 27 خانة للصندوق (قراءة فقط مبسطة: انقل بالنقر)
        for i in range(27):
            r = pygame.Rect(sw // 2 - 4.5 * 54 + (i % 9) * 54, 170 + (i // 9) * 54, 50, 50)
            pygame.draw.rect(self.screen, (80, 60, 30), r); pygame.draw.rect(self.screen, (255, 255, 255), r, 1)
            s = self.chest_inv.slots[i]
            if s["id"]:
                self.draw_item_icon(s["id"], r.x + 5, r.y + 5, 40)
                tx = self.small.render(str(s["count"]), True, (255, 255, 255))
                self.screen.blit(tx, (r.x + 32, r.y + 30))
            if r.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
                # نقل سريع بسيط
                pass

    def draw_debug(self):
        sw, _ = self.screen.get_size()
        lines = [f"FPS: {self.clock.get_fps():.0f}", f"Pos: {self.player.rect.x},{self.player.rect.y}",
                 f"Time: {self.world.time:.0f}", f"Mobs: {len(self.mobs)} Drops: {len(self.drops)}",
                 f"Seed: {self.world.seed}", f"HEALTH BUG? hp={self.player.hp:.1f} hunger={self.player.hunger:.1f}"]
        for i, ln in enumerate(lines):
            t = self.small.render(ln, True, (255, 255, 0))
            self.screen.blit(t, (10, 60 + i * 20))

    # ---------- قوائم ----------
    def draw_menu(self):
        sw, sh = self.screen.get_size()
        # خلفية متدرجة + مكعبات
        self.screen.fill((20, 25, 40))
        for i in range(60):
            x = (i * 137) % sw; y = (i * 89) % sh
            c = (40 + (i * 13) % 40, 60 + (i * 7) % 30, 50)
            pygame.draw.rect(self.screen, c, (x, y, 40, 40))
            pygame.draw.rect(self.screen, (25, 30, 45), (x, y, 40, 40), 2)
        title = self.big.render("MINECRAFT 2D", True, (120, 220, 120))
        sub = self.font.render("ماين كرافت ثنائية الأبعاد — نسخة سطح المكتب", True, (255, 255, 255))
        self.screen.blit(title, (sw // 2 - title.get_width() // 2, 120))
        self.screen.blit(sub, (sw // 2 - sub.get_width() // 2, 175))
        items = ["عالم جديد  (New World)", "تحميل عالم  (Load)", "المساعدة  (Help)", "خروج  (Quit)"]
        for i, it in enumerate(items):
            y = 260 + i * 60
            sel = i == self.menu_sel
            r = pygame.Rect(sw // 2 - 200, y, 400, 48)
            pygame.draw.rect(self.screen, (90, 140, 70) if sel else (70, 70, 80), r, border_radius=8)
            pygame.draw.rect(self.screen, (255, 255, 255), r, 2 if sel else 1, border_radius=8)
            t = self.font.render(it, True, (255, 255, 255))
            self.screen.blit(t, (sw // 2 - t.get_width() // 2, y + 12))
        f = self.small.render("WASD/Arrows move - Space jump - Mouse break/place - E inventory - F3 debug", True, (180, 180, 180))
        self.screen.blit(f, (sw // 2 - f.get_width() // 2, sh - 40))

    def draw_help(self):
        sw, sh = self.screen.get_size()
        self.screen.fill((30, 32, 45))
        t = self.big.render("HELP / المساعدة", True, (255, 255, 255))
        self.screen.blit(t, (sw // 2 - t.get_width() // 2, 40))
        lines = [
            "A/D or Arrows: Move | Space/W: Jump | Shift: Sprint",
            "Left Click (hold): Break | Right Click: Place / Use",
            "Middle Click: Pick block | Wheel / 1-9: Hotbar",
            "E: Inventory + Crafting 3x3 | Q: Drop | R: Eat",
            "F: Fly (creative) | G: Gamemode | F3: Debug | ESC: Pause",
            "",
            "الفرن: ضع حديد خام + فحم في مخزونك ثم كليك يمين على الفرن",
            "التفاح من الأوراق، اللحم من الخنازير، الصوف من الغنم",
            "احذر الزومبي والهياكل ليلاً! اصنع سيفاً ومشاعل",
            "الحجر يحتاج معول خشب على الأقل، الحديد يحتاج حجر، الألماس يحتاج حديد",
        ]
        for i, ln in enumerate(lines):
            s = self.font.render(ln, True, (230, 230, 230))
            self.screen.blit(s, (sw // 2 - s.get_width() // 2, 120 + i * 32))
        b = self.font.render("[ESC] رجوع", True, (150, 220, 150))
        self.screen.blit(b, (sw // 2 - b.get_width() // 2, sh - 60))

    def draw_create(self):
        sw, sh = self.screen.get_size()
        self.screen.fill((25, 30, 45))
        t = self.big.render("New World / عالم جديد", True, (255, 255, 255))
        self.screen.blit(t, (sw // 2 - t.get_width() // 2, 80))
        l1 = self.font.render(f"Name: {self.create_name}_  (اكتب الاسم)", True, (255, 255, 255))
        l2 = self.font.render(f"Seed: {self.create_seed}  (TAB = mode: {self.create_mode})", True, (255, 255, 200))
        l3 = self.font.render("[ENTER] ابدأ  |  [TAB] بقاء/إبداعي  |  [ESC] رجوع", True, (150, 220, 150))
        self.screen.blit(l1, (sw // 2 - l1.get_width() // 2, 220))
        self.screen.blit(l2, (sw // 2 - l2.get_width() // 2, 270))
        self.screen.blit(l3, (sw // 2 - l3.get_width() // 2, 340))
        # تغيير البذرة بزر؟
        h = self.small.render("ملاحظة: البذرة تُولّد عشوائياً، اكتب الاسم ثم ENTER", True, (180, 180, 180))
        self.screen.blit(h, (sw // 2 - h.get_width() // 2, 400))

    def draw_load(self):
        sw, sh = self.screen.get_size()
        self.screen.fill((25, 30, 45))
        t = self.big.render("Load World / تحميل", True, (255, 255, 255))
        self.screen.blit(t, (sw // 2 - t.get_width() // 2, 80))
        saves = World.list_saves()
        if not saves:
            s = self.font.render("لا توجد عوالم — أنشئ عالماً جديداً", True, (255, 200, 200))
            self.screen.blit(s, (sw // 2 - s.get_width() // 2, 220))
        for i, sname in enumerate(saves):
            y = 200 + i * 55
            r = pygame.Rect(sw // 2 - 200, y, 400, 46)
            sel = i == self.load_sel
            pygame.draw.rect(self.screen, (90, 140, 70) if sel else (60, 60, 70), r, border_radius=8)
            tt = self.font.render(sname, True, (255, 255, 255))
            self.screen.blit(tt, (sw // 2 - tt.get_width() // 2, y + 10))
        b = self.font.render("[ENTER] تحميل  [ESC] رجوع", True, (150, 220, 150))
        self.screen.blit(b, (sw // 2 - b.get_width() // 2, sh - 60))

    def draw_pause(self):
        sw, sh = self.screen.get_size()
        o = pygame.Surface((sw, sh)); o.fill((0, 0, 0)); o.set_alpha(150)
        self.screen.blit(o, (0, 0))
        t = self.big.render("PAUSED / إيقاف", True, (255, 255, 255))
        self.screen.blit(t, (sw // 2 - t.get_width() // 2, 200))
        l = self.font.render("[ESC/ENTER] استمرار   [S] حفظ   [M] القائمة", True, (255, 255, 255))
        self.screen.blit(l, (sw // 2 - l.get_width() // 2, 280))

    def draw_dead(self):
        sw, sh = self.screen.get_size()
        o = pygame.Surface((sw, sh)); o.fill((120, 0, 0)); o.set_alpha(160)
        self.screen.blit(o, (0, 0))
        t = self.big.render("YOU DIED! / لقد مت!", True, (255, 255, 255))
        self.screen.blit(t, (sw // 2 - t.get_width() // 2, 220))
        l = self.font.render("[ENTER] إحياء Respawn", True, (255, 255, 255))
        self.screen.blit(l, (sw // 2 - l.get_width() // 2, 300))
