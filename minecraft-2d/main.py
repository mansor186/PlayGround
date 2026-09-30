# -*- coding: utf-8 -*-
"""Minecraft 2D - Desktop (pygame). Full survival/creative sandbox.
Run:  pip install pygame  &&  python main.py
Controls (also shown in-game with F1):
  A/D or Left/Right : move | Space/W/Up : jump | E : inventory/crafting
  Left mouse (hold) : mine / attack | Right mouse : place block / eat (if food selected)
  1-9 / wheel : hotbar | F : eat selected food | G : fly (creative) | Esc : pause
  F1 : help | M : toggle creative/survival | F5 : save
"""
import math, os, sys, random, json, time, array
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from game_data import *
from world_gen import generate_world, get_tile, set_tile, save_world, load_world
from entities import move_entity, make_player, make_mob, mob_ai, GRAV, MOVE_SPEED, JUMP_VEL

import pygame

APP_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(APP_DIR, "saves")
os.makedirs(SAVE_DIR, exist_ok=True)

WIN_W, WIN_H = 1280, 720
FPS = 60

# ------------------------------------------------ textures
def _noise(rng, n=24):
    return [[rng.random() for _ in range(n)] for _ in range(n)]

def make_textures():
    rng = random.Random(7)
    tex = {}
    def surf():
        return pygame.Surface((TILE, TILE))
    def speckle(s, base, spots, n=26, sz=3):
        s.fill(base)
        for _ in range(n):
            x = rng.randint(0, TILE-sz); y = rng.randint(0, TILE-sz)
            c = rng.choice(spots)
            pygame.draw.rect(s, c, (x, y, sz, sz))
        return s
    # grass
    s = surf(); s.fill((121, 85, 58))
    for _ in range(30):
        pygame.draw.rect(s, rng.choice([(146, 104, 70), (101, 70, 48)]), (rng.randint(0,29), rng.randint(10,29), 3, 3))
    pygame.draw.rect(s, (86, 170, 70), (0, 0, TILE, 11))
    pygame.draw.rect(s, (74, 150, 60), (0, 11, TILE, 4))
    for x in range(0, TILE, 4):
        pygame.draw.rect(s, (86, 170, 70), (x, 13+rng.randint(0,3), 3, 4))
    tex[GRASS] = s
    tex[DIRT] = speckle(surf(), (121, 85, 58), [(146,104,70),(101,70,48),(134,95,64)])
    tex[STONE] = speckle(surf(), (128,128,132), [(110,110,114),(145,145,148),(100,100,104)], 34, 4)
    tex[COBBLE] = surf(); tex[COBBLE].fill((105,105,108))
    for _ in range(7):
        pygame.draw.rect(tex[COBBLE], rng.choice([(130,130,134),(90,90,94)]), (rng.randint(0,22), rng.randint(0,22), 9, 7), border_radius=2)
    pygame.draw.rect(tex[COBBLE], (70,70,74), (0,0,TILE,TILE), 2)
    s = surf(); s.fill((104, 78, 50))
    pygame.draw.rect(s, (70,50,32), (6,0,6,TILE)); pygame.draw.rect(s, (70,50,32), (20,0,6,TILE))
    pygame.draw.rect(s, (120,92,60), (8,0,2,TILE)); pygame.draw.rect(s, (120,92,60), (22,0,2,TILE))
    tex[LOG] = s
    s = surf(); s.fill((46, 125, 50))
    for _ in range(46):
        pygame.draw.rect(s, rng.choice([(34,100,40),(62,150,66),(40,115,45)]), (rng.randint(0,29), rng.randint(0,29), 3, 3))
    tex[LEAVES] = s
    s = surf(); s.fill((176, 142, 90))
    for y in (0, 8, 16, 24):
        pygame.draw.line(s, (120, 92, 58), (0, y), (TILE, y), 2)
    for _ in range(14):
        pygame.draw.rect(s, (150,118,74), (rng.randint(0,29), rng.randint(0,29), 2, 2))
    tex[PLANKS] = s
    tex[SAND] = speckle(surf(), (226, 206, 154), [(214,192,138),(238,220,170)], 30, 3)
    tex[SANDSTONE] = speckle(surf(), (214, 190, 140), [(190,168,120),(228,206,156)], 22, 5)
    pygame.draw.rect(tex[SANDSTONE], (180,158,112), (0,0,TILE,TILE), 2)
    def ore(base, gem):
        s = speckle(surf(), base, [(110,110,114),(145,145,148)], 20, 4)
        for _ in range(5):
            x, y = rng.randint(3,24), rng.randint(3,24)
            pygame.draw.rect(s, gem, (x, y, 6, 6))
            pygame.draw.rect(s, (255,255,255), (x, y, 2, 2))
        return s
    tex[COAL_ORE] = ore((128,128,132), (35,35,38))
    tex[IRON_ORE] = ore((128,128,132), (216,175,147))
    tex[GOLD_ORE] = ore((128,128,132), (250,210,80))
    tex[DIAMOND_ORE] = ore((128,128,132), (120,230,235))
    s = surf(); s.fill((30,30,34))
    for _ in range(10):
        pygame.draw.rect(s, (55,55,60), (rng.randint(0,26), rng.randint(0,26), 5, 5))
    tex[BEDROCK] = s
    s = surf(); s.fill((150,110,70))
    pygame.draw.rect(s, (100,70,44), (0,0,TILE,TILE), 3)
    pygame.draw.line(s, (100,70,44), (0,10),(TILE,10),2); pygame.draw.line(s, (100,70,44), (10,10),(10,TILE),2); pygame.draw.line(s, (100,70,44), (22,10),(22,TILE),2)
    tex[CRAFTING_TABLE] = s
    s = surf(); s.fill((120,120,124))
    pygame.draw.rect(s, (70,70,74), (0,0,TILE,TILE), 3)
    pygame.draw.rect(s, (30,30,32), (8,10,16,14))
    pygame.draw.rect(s, (255,140,30), (10,16,12,6))
    tex[FURNACE] = s
    s = surf(); s.fill((0,0,0)); s.set_colorkey((0,0,0))
    pygame.draw.rect(s, (120,80,40), (13,12,6,16))
    pygame.draw.rect(s, (255,200,60), (11,4,10,10))
    pygame.draw.rect(s, (255,240,170), (13,6,6,6))
    tex[TORCH] = s
    s = surf(); s.fill((185,225,240))
    pygame.draw.rect(s, (230,245,250), (4,4,10,10))
    pygame.draw.rect(s, (140,180,200), (0,0,TILE,TILE), 2)
    tex[GLASS] = s
    s = surf(); s.fill((170,80,70))
    for y in (0,8,16,24):
        pygame.draw.line(s, (120,55,48), (0,y),(TILE,y),2)
    pygame.draw.line(s, (120,55,48), (16,0),(16,8),2); pygame.draw.line(s, (120,55,48), (8,8),(8,16),2); pygame.draw.line(s, (120,55,48), (24,16),(24,24),2)
    tex[BRICK] = s
    s = surf(); s.fill((235,240,242))
    for _ in range(20):
        pygame.draw.rect(s, rng.choice([(225,232,235),(245,250,252)]), (rng.randint(0,29), rng.randint(8,29), 3, 3))
    pygame.draw.rect(s, (110,190,110), (0,0,TILE,8))
    tex[SNOW_GRASS] = s
    s = surf(); s.fill((0,0,0)); s.set_colorkey((0,0,0))
    pygame.draw.rect(s, (60,160,70), (11,4,10,24))
    pygame.draw.rect(s, (70,180,80), (13,4,3,24))
    for x in (6, 21):
        pygame.draw.rect(s, (60,160,70), (x,10,3,6))
    tex[CACTUS] = s
    s = surf(); s.fill((0,0,0)); s.set_colorkey((0,0,0))
    pygame.draw.rect(s, (40,140,50), (14,14,4,14))
    for (x,y,c) in ((11,6,(235,90,110)),(19,9,(235,120,140)),(14,3,(250,200,60))):
        pygame.draw.circle(s, c, (x,y), 4)
    tex[FLOWER] = s
    s = surf(); s.fill((0,0,0)); s.set_colorkey((0,0,0))
    for _ in range(7):
        x = rng.randint(4,26)
        pygame.draw.line(s, (60,150,60), (x,30),(x,rng.randint(8,18)),2)
    tex[TALLGRASS] = s
    return tex

def make_icon(iid, tex):
    s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
    if iid in tex:
        s.blit(tex[iid], (0, 0))
        return s
    s.fill((0,0,0)); s.set_colorkey((0,0,0))
    info = ITEMS.get(iid, {})
    tool = info.get("tool")
    if iid == STICK:
        pygame.draw.line(s, (150,110,70), (10,26),(22,6),5)
    elif iid == COAL:
        pygame.draw.circle(s, (40,40,44), (16,16), 9)
        pygame.draw.circle(s, (80,80,86), (13,13), 3)
    elif iid in (IRON_INGOT, GOLD_INGOT):
        c = (220,180,150) if iid == IRON_INGOT else (250,210,90)
        pygame.draw.rect(s, c, (6,12,20,10), border_radius=2)
        pygame.draw.rect(s, (255,255,255), (6,12,20,3), border_radius=2)
    elif iid == DIAMOND:
        pygame.draw.polygon(s, (120,230,235), [(16,4),(26,14),(16,28),(6,14)])
        pygame.draw.polygon(s, (220,255,255), [(16,4),(22,14),(16,18),(10,14)])
    elif iid in (PORK, BEEF):
        c = (230,150,140) if iid == PORK else (150,80,60)
        pygame.draw.ellipse(s, c, (4,10,24,14))
        pygame.draw.rect(s, (240,240,240), (22,12,6,8), border_radius=2)
    elif tool == "pickaxe":
        wood = iid == W_PICKAXE; stone = iid == S_PICKAXE; iron = iid == I_PICKAXE
        c = (176,142,90) if wood else ((140,140,144) if stone else ((220,220,225) if iron else (120,230,235)))
        pygame.draw.line(s, (150,110,70), (10,26),(20,8),4)
        pygame.draw.arc(s, c, (6,2,20,14), math.pi*0.9, math.pi*2.0, 4)
    elif tool == "axe":
        c = (176,142,90) if iid == W_AXE else (140,140,144)
        pygame.draw.line(s, (150,110,70), (10,26),(20,8),4)
        pygame.draw.polygon(s, c, [(18,4),(28,10),(22,18),(14,12)])
    elif tool == "shovel":
        c = (176,142,90) if iid == SHOVEL_W else (140,140,144)
        pygame.draw.line(s, (150,110,70), (10,26),(18,12),4)
        pygame.draw.ellipse(s, c, (14,2,12,12))
    elif "Sword" in info.get("en", "") or "Sword" in info.get("ar", "") or iid in (W_SWORD, S_SWORD, I_SWORD):
        blade = (200,170,120) if iid == W_SWORD else ((180,180,185) if iid == S_SWORD else (230,235,240))
        pygame.draw.line(s, blade, (8,24),(22,8),5)
        pygame.draw.line(s, (150,110,70), (6,26),(12,20),4)
        pygame.draw.line(s, (120,90,60), (4,22),(14,24),3)
    else:
        pygame.draw.rect(s, (200,80,80), (8,8,16,16))
    return s

# ------------------------------------------------ sounds (stdlib only)
def make_sounds():
    sounds = {}
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=1)
    except Exception:
        return sounds
    def tone(freq, ms, vol=0.25, slide=0):
        n = int(22050*ms/1000)
        buf = array.array("h")
        for i in range(n):
            f = freq + slide*i/n
            v = int(32767*vol*math.sin(2*math.pi*f*i/22050) * (1-i/n))
            buf.append(v)
        try:
            return pygame.mixer.Sound(buffer=buf.tobytes())
        except Exception:
            return None
    def noise(ms, vol=0.2):
        n = int(22050*ms/1000)
        buf = array.array("h")
        for i in range(n):
            v = int(32767*vol*(random.random()*2-1) * (1-i/n))
            buf.append(v)
        try:
            return pygame.mixer.Sound(buffer=buf.tobytes())
        except Exception:
            return None
    sounds["break"] = noise(140)
    sounds["place"] = tone(180, 90, 0.3, 60)
    sounds["pop"] = tone(700, 80, 0.25, 500)
    sounds["hurt"] = tone(160, 180, 0.35, -60)
    sounds["eat"] = tone(400, 110, 0.3, -150)
    sounds["craft"] = tone(520, 120, 0.3, 220)
    sounds["boom"] = noise(300, 0.3)
    return sounds

# ------------------------------------------------ game
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Minecraft 2D  -  ماين كرافت ثنائية الأبعاد")
        self.screen = pygame.display.set_mode((WIN_W, WIN_H), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("dejavusans", 18)
        self.big = pygame.font.SysFont("dejavusans", 42, bold=True)
        self.small = pygame.font.SysFont("dejavusans", 14)
        self.tex = make_textures()
        self.icons = {}
        for iid in list(BLOCKS.keys()) + list(ITEMS.keys()):
            try:
                self.icons[iid] = make_icon(iid, self.tex)
            except Exception:
                pass
        self.sounds = make_sounds()
        self.state = "menu"
        self.menu_idx = 0
        self.seed_text = str(random.randint(1000, 99999))
        self.mode_select = "survival"
        self.world = None; self.player = None; self.mobs = []
        self.inv = {}; self.hotbar = STARTER_HOTBAR[:]; self.sel = 0
        self.mode = "survival"
        self.cam = [0, 0]
        self.mine_prog = 0.0; self.mine_target = None
        self.particles = []; self.drops = []
        self.show_help = False; self.show_inv = False
        self.msg = ""; self.msg_t = 0
        self.fly = False
        self.time_acc = 0
        self.spawn_cd = 0
        self.craft_scroll = 0
        self.day = 1

    def sfx(self, name):
        s = self.sounds.get(name)
        if s:
            try: s.play()
            except Exception: pass

    # ---------- world mgmt
    def new_game(self, seed, mode):
        try: seed = int(seed)
        except Exception: seed = abs(hash(str(seed))) % 1000000
        self.world = generate_world(seed)
        sx, sy = self.world["spawn"]
        self.player = make_player(sx, sy)
        self.mobs = []
        self.inv = {LOG: 5, PLANKS: 4, TORCH: 4, COBBLE: 0}
        self.inv = {k: v for k, v in self.inv.items() if v > 0}
        self.hotbar = STARTER_HOTBAR[:]
        self.sel = 0
        self.mode = mode
        self.mine_prog = 0; self.mine_target = None
        self.particles = []; self.drops = []
        self.fly = False
        self.state = "play"
        self.say("Seed: %d  |  %s" % (seed, "Creative - ابداعي" if mode == "creative" else "Survival - بقاء"))
        # spawn some animals
        for _ in range(6):
            self.spawn_animal()

    def say(self, t, dur=3.0):
        self.msg = t; self.msg_t = dur

    def save_slot(self, slot=1):
        if not self.world: return
        path = os.path.join(SAVE_DIR, f"world{slot}.json")
        save_world(self.world, self.player, self.mobs, self.inv, self.hotbar, self.sel, self.mode, path)
        self.say(f"Saved -> {path}")

    def load_slot(self, slot=1):
        path = os.path.join(SAVE_DIR, f"world{slot}.json")
        if not os.path.exists(path):
            self.say("No save found!")
            return
        w, p, m, inv, hb, sel, mode = load_world(path)
        self.world = w; self.player = p; self.mobs = m or []
        self.inv = inv; self.hotbar = hb or STARTER_HOTBAR[:]
        self.sel = sel; self.mode = mode
        self.state = "play"
        self.say("World loaded!")

    # ---------- helpers
    def sel_item(self):
        if 0 <= self.sel < len(self.hotbar):
            return self.hotbar[self.sel]
        return None

    def add_item(self, iid, n=1):
        if self.mode == "creative":
            return
        self.inv[iid] = self.inv.get(iid, 0) + n
        # auto fill empty hotbar slots
        if iid not in self.hotbar:
            for i, h in enumerate(self.hotbar):
                if self.inv.get(h, 0) <= 0 and h not in BLOCKS:
                    pass
        if self.inv[iid] <= 0:
            self.inv.pop(iid, None)

    def count(self, iid):
        if self.mode == "creative":
            return 999
        if iid in BLOCKS or iid in ITEMS:
            hot = 1 if iid in self.hotbar else 0
            return self.inv.get(iid, 0) + (0 if iid in self.inv else (hot and 0 or 0)) + (hot if iid not in self.inv and self.mode == "creative" else 0)
        return self.inv.get(iid, 0)

    def has(self, iid, n=1):
        if self.mode == "creative":
            return True
        total = self.inv.get(iid, 0)
        # hotbar blocks are also from inv in survival; hotbar is just selection
        return total >= n

    def take(self, iid, n=1):
        if self.mode == "creative":
            return True
        if self.inv.get(iid, 0) < n:
            return False
        self.inv[iid] -= n
        if self.inv[iid] <= 0:
            self.inv.pop(iid, None)
        return True

    def tool_mult(self):
        iid = self.sel_item()
        info = ITEMS.get(iid, {})
        if info.get("tool") in ("pickaxe", "axe", "shovel"):
            return info.get("mult", 1.0), info.get("tool"), info.get("tier", 1)
        return 1.0, None, 0

    def break_time(self, bid):
        info = BLOCKS.get(bid)
        if not info: return 0.4
        if info["hard"] < 0: return float("inf")
        need = info.get("tool")
        mult, tool, tier = self.tool_mult()
        # ores need tier>=2 except coal
        if bid in (IRON_ORE, GOLD_ORE, DIAMOND_ORE) and (tool != "pickaxe" or tier < 2):
            if self.mode == "survival":
                return float("inf")  # can't drop without proper pick
        if need and tool == need:
            return info["hard"] / mult
        if need is None:
            return info["hard"]
        return info["hard"] * 1.6  # wrong tool penalty

    def spawn_animal(self):
        if not self.world: return
        w = self.world["w"]
        px = int(self.player["x"]//TILE)
        for _ in range(20):
            tx = max(2, min(w-3, px + random.randint(-40, 40)))
            # find surface
            for ty in range(0, self.world["h"]-1):
                if get_tile(self.world, tx, ty) == AIR and is_solid(get_tile(self.world, tx, ty+1)):
                    kind = random.choice(["pig", "pig", "cow"])
                    self.mobs.append(make_mob(kind, tx, ty-1))
                    return

    # ---------- update
    def update(self, dt):
        if self.state != "play" or not self.world:
            return
        p = self.player
        # time
        self.world["time"] = (self.world.get("time", 0.3) + dt/600.0) % 1.0
        t = self.world["time"]
        is_night = (t < 0.22 or t > 0.78)
        if t < dt/600.0:
            self.day += 1
        # input move
        keys = pygame.key.get_pressed()
        ax = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: ax -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: ax += 1
        p["face"] = ax if ax != 0 else p["face"]
        if self.fly and self.mode == "creative":
            p["vx"] = ax*420
            p["vy"] = 0
            if keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]: p["y"] -= 420*dt
            if keys[pygame.K_s] or keys[pygame.K_DOWN]: p["y"] += 420*dt
            p["x"] += p["vx"]*dt
            p["on_ground"] = False
        else:
            p["vx"] = ax*MOVE_SPEED
            if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and p.get("on_ground"):
                p["vy"] = JUMP_VEL
                p["on_ground"] = False
            move_entity(self.world, p, dt)
            # fall damage
            fd = p.pop("fall_damage", 0)
            if fd and self.mode == "survival":
                p["hp"] -= fd
                if fd > 1: self.sfx("hurt")
        # clamp world
        p["x"] = max(0, min(self.world["w"]*TILE-p["w"], p["x"]))
        # hunger
        if self.mode == "survival":
            p["hunger"] = max(0, p["hunger"] - dt*0.12)
            if p["hunger"] > 14 and p["hp"] < 20:
                p["hp"] = min(20, p["hp"] + dt*0.6)
                p["hunger"] = max(0, p["hunger"]-dt*0.3)
            if p["hunger"] <= 0:
                p["hp"] -= dt*1.0
            if p["hp"] <= 0:
                self.state = "dead"
                return
        # camera
        ww, wh = self.screen.get_size()
        self.cam[0] += ((p["x"]+p["w"]/2-ww/2) - self.cam[0])*min(1, dt*6)
        self.cam[1] += ((p["y"]+p["h"]/2-wh/2-40) - self.cam[1])*min(1, dt*6)
        self.cam[0] = max(-40, min(self.world["w"]*TILE-ww+40, self.cam[0]))
        self.cam[1] = max(-200, min(self.world["h"]*TILE-wh+40, self.cam[1]))
        # mining progress
        self.update_mining(dt)
        # mobs
        for m in self.mobs:
            mob_ai(self.world, m, p, dt, is_night)
            # zombie attack
            if m["kind"] == "zombie" and m.get("attack_cd", 0) <= 0:
                if abs(m["x"]-p["x"]) < 44 and abs(m["y"]-p["y"]) < 64:
                    if self.mode == "survival":
                        p["hp"] -= 3
                        self.sfx("hurt")
                        self.burst(p["x"], p["y"], (220, 60, 60))
                    m["attack_cd"] = 1.0
                    # knockback
                    p["vx"] = 260 if p["x"] > m["x"] else -260
        # remove dead mobs -> drops
        alive = []
        for m in self.mobs:
            if m["hp"] <= 0:
                if m["kind"] == "pig":
                    self.spawn_drop(m["x"], m["y"], PORK, 2)
                elif m["kind"] == "cow":
                    self.spawn_drop(m["x"], m["y"], BEEF, 2)
                else:
                    if random.random() < 0.4:
                        self.spawn_drop(m["x"], m["y"], COAL, 1)
                self.burst(m["x"], m["y"], (200, 60, 60))
                self.sfx("boom")
            elif m["hp"] < -50 or m["y"] > self.world["h"]*TILE+200:
                pass
            else:
                alive.append(m)
        self.mobs = alive
        # spawn hostile at night / passive by day
        self.spawn_cd -= dt
        if self.spawn_cd <= 0:
            self.spawn_cd = 6 if is_night else 12
            hostiles = sum(1 for m in self.mobs if m["kind"] == "zombie")
            passives = len(self.mobs)-hostiles
            if is_night and hostiles < 5:
                self.spawn_enemy()
            elif not is_night and passives < 6:
                self.spawn_animal()
        # drops physics
        for d in self.drops:
            d["t"] += dt
            d["vy"] += 1600*dt
            d["x"] += d["vx"]*dt; d["y"] += d["vy"]*dt
            tx, ty = int(d["x"]//TILE), int(d["y"]//TILE)
            if is_solid(get_tile(self.world, tx, ty+1)) or is_solid(get_tile(self.world, tx, ty)):
                d["y"] = (ty)*TILE-8 if is_solid(get_tile(self.world, tx, ty)) else d["y"]
                d["vy"] = 0; d["vx"] *= 0.9
            # magnet
            dx = (p["x"]+p["w"]/2)-d["x"]; dy = (p["y"]+p["h"]/2)-d["y"]
            dist = math.hypot(dx, dy)
            if dist < 110:
                d["x"] += dx/dist*260*dt; d["y"] += dy/dist*260*dt
            if dist < 26:
                d["dead"] = True
                self.add_item(d["id"], d["n"])
                self.sfx("pop")
        self.drops = [d for d in self.drops if not d.get("dead") and d["t"] < 90]
        # particles
        for pt in self.particles:
            pt["x"] += pt["vx"]*dt; pt["y"] += pt["vy"]*dt
            pt["vy"] += 900*dt; pt["life"] -= dt
        self.particles = [pt for pt in self.particles if pt["life"] > 0]
        if self.msg_t > 0:
            self.msg_t -= dt

    def spawn_enemy(self):
        w = self.world["w"]
        px = int(self.player["x"]//TILE)
        for _ in range(20):
            tx = max(2, min(w-3, px + random.choice([-1,1])*random.randint(14, 34)))
            for ty in range(0, self.world["h"]-1):
                if get_tile(self.world, tx, ty) == AIR and is_solid(get_tile(self.world, tx, ty+1)):
                    self.mobs.append(make_mob("zombie", tx, ty-1))
                    return

    def spawn_drop(self, x, y, iid, n):
        self.drops.append({"id": iid, "n": n, "x": x, "y": y-6,
                           "vx": random.uniform(-90, 90), "vy": random.uniform(-260, -80), "t": 0})

    def burst(self, x, y, color):
        for _ in range(10):
            self.particles.append({"x": x+11, "y": y+20, "vx": random.uniform(-160,160),
                                   "vy": random.uniform(-320,-40), "life": random.uniform(0.3,0.8), "c": color})

    def tile_burst(self, tx, ty, bid):
        base = {GRASS:(86,170,70), DIRT:(121,85,58), STONE:(140,140,144)}.get(bid, (180,180,180))
        self.burst(tx*TILE, ty*TILE, base)

    # ---------- mining
    def target_block(self):
        mx, my = pygame.mouse.get_pos()
        wx, wy = mx+self.cam[0], my+self.cam[1]
        tx, ty = int(wx//TILE), int(wy//TILE)
        px = (self.player["x"]+self.player["w"]/2)//TILE
        py = (self.player["y"]+self.player["h"]/2)//TILE
        if abs(tx-px)+abs(ty-py) > 9:
            return None
        b = get_tile(self.world, tx, ty)
        if b == AIR:
            return None
        return (tx, ty, b)

    def update_mining(self, dt):
        btns = pygame.mouse.get_pressed()
        if self.show_inv or self.state != "play":
            self.mine_prog = 0; self.mine_target = None
            return
        # attack mobs on click
        if btns[0]:
            if self.hit_mob():
                self.mine_prog = 0; return
            tb = self.target_block()
            if not tb:
                self.mine_prog = 0; self.mine_target = None
                return
            tx, ty, b = tb
            if (tx, ty) != self.mine_target:
                self.mine_target = (tx, ty); self.mine_prog = 0
            need = self.break_time(b)
            if need == float("inf"):
                self.mine_prog = 0
                return
            self.mine_prog += dt/need
            if self.mine_prog >= 1.0:
                self.break_block(tx, ty, b)
                self.mine_prog = 0; self.mine_target = None
        else:
            self.mine_prog = 0; self.mine_target = None

    def hit_mob(self):
        mx, my = pygame.mouse.get_pos()
        wx, wy = mx+self.cam[0], my+self.cam[1]
        iid = self.sel_item()
        dmg = ITEMS.get(iid, {}).get("dmg", 2) if iid else 2
        if iid in (W_SWORD, S_SWORD, I_SWORD):
            reach = 110
        else:
            reach = 80
        for m in self.mobs:
            if m["x"]-10 < wx < m["x"]+m["w"]+10 and m["y"]-10 < wy < m["y"]+m["h"]+10:
                px = self.player["x"]+self.player["w"]/2
                py = self.player["y"]+self.player["h"]/2
                if math.hypot(m["x"]-px, m["y"]-py) < 150:
                    m["hp"] -= dmg
                    m["hurt"] = 0.25
                    m["vx"] = 220 if m["x"] > px else -220
                    m["vy"] = -250
                    self.burst(m["x"], m["y"], (220,70,70))
                    self.sfx("hurt")
                    return True
        return False

    def break_block(self, tx, ty, b):
        info = BLOCKS.get(b, {})
        if info.get("hard", 1) < 0:
            return
        # higher-tier check
        if self.break_time(b) == float("inf"):
            self.say("Need stone pickaxe or better!")
            return
        set_tile(self.world, tx, ty, AIR)
        self.tile_burst(tx, ty, b)
        self.sfx("break")
        drop = info.get("drop")
        if b == STONE: drop = COBBLE
        if b == GRASS: drop = DIRT
        if drop:
            n = 1
            if b == LEAVES and random.random() < 0.85:
                return
            if self.mode == "survival":
                self.spawn_drop(tx*TILE+16, ty*TILE+16, drop, n)
            else:
                pass
        elif b == LEAVES:
            pass
        else:
            if self.mode == "survival" and b in (FLOWER, TALLGRASS):
                pass
        # crumble floating? skip physics for simplicity

    def try_place(self):
        if self.show_inv: return
        mx, my = pygame.mouse.get_pos()
        wx, wy = mx+self.cam[0], my+self.cam[1]
        tx, ty = int(wx//TILE), int(wy//TILE)
        iid = self.sel_item()
        if iid is None: return
        if iid not in BLOCKS:
            # food?
            if ITEMS.get(iid, {}).get("food"):
                self.eat(iid)
            return
        px = (self.player["x"]+self.player["w"]/2)//TILE
        py = (self.player["y"]+self.player["h"]/2)//TILE
        if abs(tx-px)+abs(ty-py) > 9:
            return
        cur = get_tile(self.world, tx, ty)
        if cur not in (AIR, FLOWER, TALLGRASS):
            return
        if not self.has(iid, 1):
            self.say("Empty! Mine or craft more.")
            return
        # don't place inside player/mobs
        pr = pygame.Rect(tx*TILE, ty*TILE, TILE, TILE)
        p = self.player
        if is_solid(iid) and pr.colliderect(pygame.Rect(p["x"], p["y"], p["w"], p["h"])):
            return
        for m in self.mobs:
            if is_solid(iid) and pr.colliderect(pygame.Rect(m["x"], m["y"], m["w"], m["h"])):
                return
        # support check for torch/plants
        if iid in NEEDS_SUPPORT and iid not in (CACTUS,):
            below = get_tile(self.world, tx, ty+1)
            if not is_solid(below):
                return
        set_tile(self.world, tx, ty, iid)
        self.take(iid, 1)
        self.sfx("place")

    def eat(self, iid=None):
        p = self.player
        if iid is None:
            iid = self.sel_item()
        info = ITEMS.get(iid, {})
        if not info.get("food"):
            # find any food
            for fid in (BEEF, PORK):
                if self.inv.get(fid, 0) > 0:
                    iid = fid; info = ITEMS[fid]; break
            else:
                return
        if p["hunger"] >= 20:
            self.say("Not hungry")
            return
        if not self.take(iid, 1):
            return
        p["hunger"] = min(20, p["hunger"]+info["food"])
        p["hp"] = min(20, p["hp"]+1)
        self.sfx("eat")
        self.say(f"Ate {info.get('ar','food')} +{info['food']} hunger")

    # ---------- crafting
    def can_craft(self, r):
        for iid, n in r["in"].items():
            if not self.has(iid, n):
                return False
        if r.get("table"):
            # need crafting table nearby (or in inv for simplicity: allow if has table placed within 6 or in inv)
            near = False
            px = int(self.player["x"]//TILE); py = int(self.player["y"]//TILE)
            for dy in range(-6, 7):
                for dx in range(-6, 7):
                    if get_tile(self.world, px+dx, py+dy) == CRAFTING_TABLE:
                        near = True; break
            if self.inv.get(CRAFTING_TABLE, 0) > 0:
                near = True
            if not near and self.mode == "survival":
                return False
        return True

    def do_craft(self, r):
        if not self.can_craft(r):
            return False
        if self.mode != "creative":
            for iid, n in r["in"].items():
                self.take(iid, n)
            self.add_item(r["out"], r["n"])
        self.sfx("craft")
        return True

    def do_smelt(self, inp):
        out = SMELT.get(inp)
        if out is None: return False
        if not self.has(inp, 1): return False
        if inp in (IRON_ORE, GOLD_ORE) and not self.has(COAL, 1):
            self.say("Need coal as fuel!")
            return False
        if self.mode != "creative":
            self.take(inp, 1)
            if inp in (IRON_ORE, GOLD_ORE):
                self.take(COAL, 1)
            self.add_item(out, 1)
        self.sfx("craft")
        return True

    # ############################################ RENDER
    def sky_color(self):
        t = self.world["time"]
        # day factor 0..1
        # sunrise ~0.22-0.3, sunset ~0.7-0.78
        def lerp(a, b, f): return tuple(int(a[i]+(b[i]-a[i])*f) for i in range(3))
        DAY = (135, 206, 235); NIGHT = (8, 10, 30); SET = (250, 140, 80)
        if 0.28 <= t <= 0.7:
            return DAY
        if t < 0.22 or t > 0.78:
            return NIGHT
        if 0.22 <= t < 0.28:
            f = (t-0.22)/0.06
            return lerp(NIGHT, DAY if f > 0.5 else SET, f)
        f = (t-0.7)/0.08
        return lerp(DAY, NIGHT if f > 0.5 else SET, f)

    def night_factor(self):
        t = self.world["time"]
        if 0.3 <= t <= 0.68: return 0.0
        if t < 0.22 or t > 0.78: return 1.0
        if 0.22 <= t < 0.3: return 1.0-(t-0.22)/0.08
        return (t-0.68)/0.10

    def draw(self):
        if self.state == "menu":
            self.draw_menu(); return
        if not self.world:
            return
        sky = self.sky_color()
        self.screen.fill(sky)
        ww, wh = self.screen.get_size()
        cx, cy = self.cam
        t = self.world["time"]
        # sun / moon
        sx = ww*(t) % (ww+200)-100
        sy = 90 + 60*math.sin(t*math.pi*2)
        if 0.24 <= t <= 0.76:
            pygame.draw.circle(self.screen, (255, 235, 120), (int(sx), int(sy)), 34)
            pygame.draw.circle(self.screen, (255, 245, 180), (int(sx), int(sy)), 26)
        else:
            pygame.draw.circle(self.screen, (235, 235, 245), (int(ww-sx), int(sy)), 24)
            pygame.draw.circle(self.screen, sky, (int(ww-sx)-8, int(sy)-5), 20)
        nf = self.night_factor()
        if nf > 0.3:
            for i in range(70):
                x = (i*173) % ww; y = (i*97) % (wh//2)
                a = int(200*nf*(0.4+0.6*((i*13)%10)/10))
                self.screen.fill((255,255,255), (x, y, 2, 2))
        # clouds
        for i in range(10):
            clx = ((i*420 + time.time()*8*(1+i%3*0.3)) % (self.world["w"]*TILE)) - cx*0.3
            cly = 40 + (i*53) % 140 - cy*0.05
            clx = clx % (ww+240)-120
            pygame.draw.ellipse(self.screen, (255,255,255,200) if nf < 0.5 else (90,90,110),
                                (clx, cly, 120, 28))
            pygame.draw.ellipse(self.screen, (255,255,255,200) if nf < 0.5 else (90,90,110),
                                (clx+25, cly-12, 70, 26))
        # tiles
        x0 = max(0, int(cx//TILE)-1); x1 = min(self.world["w"]-1, int((cx+ww)//TILE)+1)
        y0 = max(0, int(cy//TILE)-1); y1 = min(self.world["h"]-1, int((cy+wh)//TILE)+1)
        for ty in range(y0, y1+1):
            row = self.world["tiles"][ty]
            for tx in range(x0, x1+1):
                b = row[tx]
                if b == AIR: continue
                img = self.tex.get(b)
                if img:
                    # leaves transparency feel
                    self.screen.blit(img, (tx*TILE-cx, ty*TILE-cy))
                # mining crack
                if self.mine_target == (tx, ty) and self.mine_prog > 0:
                    a = int(120*self.mine_prog)+40
                    cr = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
                    cr.fill((0, 0, 0, 0))
                    for _ in range(int(4+self.mine_prog*10)):
                        pygame.draw.line(cr, (20,20,20,a), (random.randint(2,30), random.randint(2,30)),
                                         (random.randint(2,30), random.randint(2,30)), 1)
                    self.screen.blit(cr, (tx*TILE-cx, ty*TILE-cy))
        # block highlight
        tb = self.target_block() if self.state == "play" and not self.show_inv else None
        if tb:
            pygame.draw.rect(self.screen, (255,255,255), (tb[0]*TILE-cx-1, tb[1]*TILE-cy-1, TILE+2, TILE+2), 2)
        # drops
        for d in self.drops:
            ic = self.icons.get(d["id"])
            if ic:
                bob = math.sin(d["t"]*5)*3
                self.screen.blit(ic, (d["x"]-cx-16, d["y"]-cy-16+bob))
        # mobs
        for m in self.mobs:
            self.draw_mob(m, cx, cy)
        # player
        self.draw_player(cx, cy)
        # particles
        for pt in self.particles:
            pygame.draw.circle(self.screen, pt["c"], (int(pt["x"]-cx), int(pt["y"]-cy)), 3)
        # torch light glow (cheap additive look)
        if nf > 0.05:
            dark = pygame.Surface((ww, wh), pygame.SRCALPHA)
            dark.fill((6, 8, 30, int(150*nf)))
            # punch light: draw glow circles onto main screen AFTER dark using blend
            self.screen.blit(dark, (0, 0))
            for ty in range(y0, y1+1):
                for tx in range(x0, x1+1):
                    if self.world["tiles"][ty][tx] == TORCH:
                        lx, ly = int(tx*TILE+TILE/2-cx), int(ty*TILE-cy)
                        for r, a in ((90, 26), (60, 40), (30, 70)):
                            gl = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                            pygame.draw.circle(gl, (255, 200, 110, a), (r, r), r)
                            self.screen.blit(gl, (lx-r, ly-r), special_flags=pygame.BLEND_ADD)
            # player glow small
            lx, ly = int(self.player["x"]-cx), int(self.player["y"]-cy)
            gl = pygame.Surface((120, 120), pygame.SRCALPHA)
            pygame.draw.circle(gl, (200, 200, 255, 18), (60, 60), 60)
            self.screen.blit(gl, (lx-50, ly-30), special_flags=pygame.BLEND_ADD)
        self.draw_hud()
        if self.show_inv:
            self.draw_inventory()
        if self.show_help:
            self.draw_help()
        if self.state == "pause":
            self.draw_pause()
        if self.state == "dead":
            self.draw_dead()
        if self.msg_t > 0:
            ms = self.font.render(self.msg, True, (255, 255, 255))
            bg = pygame.Surface((ms.get_width()+20, ms.get_height()+10), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 150))
            self.screen.blit(bg, (ww//2-bg.get_width()//2, 70))
            self.screen.blit(ms, (ww//2-ms.get_width()//2, 75))

    def draw_player(self, cx, cy):
        p = self.player
        x, y = int(p["x"]-cx), int(p["y"]-cy)
        w, h = p["w"], p["h"]
        walk = math.sin(time.time()*10)*4 if abs(p["vx"]) > 20 and p.get("on_ground") else 0
        # legs
        pygame.draw.rect(self.screen, (60, 80, 160), (x+2, y+h-14+max(0,walk), 8, 14-max(0,walk)))
        pygame.draw.rect(self.screen, (60, 80, 160), (x+w-10, y+h-14+max(0,-walk), 8, 14-max(0,-walk)))
        # body (shirt)
        pygame.draw.rect(self.screen, (0, 180, 180), (x, y+18, w, 24))
        pygame.draw.rect(self.screen, (0, 150, 150), (x, y+18, w, 5))
        # arms
        pygame.draw.rect(self.screen, (230, 180, 130), (x-5, y+20, 5, 20))
        # held item
        iid = self.sel_item()
        if iid and iid in self.icons:
            img = pygame.transform.scale(self.icons[iid], (20, 20))
            hx = x+w if p["face"] >= 0 else x-15
            self.screen.blit(img, (hx, y+26))
            pygame.draw.rect(self.screen, (230, 180, 130), (x+(w-4 if p["face"] >= 0 else 0), y+28, 5, 12))
        else:
            pygame.draw.rect(self.screen, (230, 180, 130), (x+(w-4 if p["face"] >= 0 else -1), y+20, 5, 20))
        # head
        pygame.draw.rect(self.screen, (235, 190, 140), (x-1, y, w+2, 18))
        pygame.draw.rect(self.screen, (90, 60, 40), (x-1, y, w+2, 5))  # hair
        ex = x+5 if p["face"] >= 0 else x+w-11
        pygame.draw.rect(self.screen, (30, 30, 40), (ex, y+8, 4, 4))
        pygame.draw.rect(self.screen, (30, 30, 40), (ex+6 if p["face"] >= 0 else ex-6, y+8, 4, 4))
        if p.get("hurt_t", 0) > 0:
            pass

    def draw_mob(self, m, cx, cy):
        x, y = int(m["x"]-cx), int(m["y"]-cy)
        flash = m.get("hurt", 0) > 0 and int(time.time()*20) % 2 == 0
        if m["kind"] == "pig":
            c = (240, 150, 160) if not flash else (255, 255, 255)
            pygame.draw.ellipse(self.screen, c, (x, y+6, m["w"], m["h"]-6))
            hx = x+m["w"]-12 if m["dir"] >= 0 else x
            pygame.draw.rect(self.screen, c, (hx, y+10, 14, 12))
            pygame.draw.rect(self.screen, (220, 110, 120), (hx+(8 if m["dir"] >= 0 else -2), y+14, 6, 5))
            pygame.draw.rect(self.screen, (30,30,30), (hx+(3 if m["dir"] >= 0 else 5), y+12, 3, 3))
            for lx in (x+6, x+m["w"]-10):
                pygame.draw.rect(self.screen, (210,120,130), (lx, y+m["h"]-6, 5, 6))
        elif m["kind"] == "cow":
            c = (240,240,240) if not flash else (255,255,255)
            pygame.draw.ellipse(self.screen, c, (x, y+8, m["w"], m["h"]-8))
            for _ in [(x+8,y+10),(x+24,y+16)]:
                pygame.draw.ellipse(self.screen, (60,60,60), (_[0], _[1], 10, 7))
            hx = x+m["w"]-12 if m["dir"] >= 0 else x
            pygame.draw.rect(self.screen, c, (hx, y+8, 14, 14))
            pygame.draw.rect(self.screen, (230,180,180), (hx+(8 if m["dir"] >= 0 else -2), y+16, 6, 5))
            pygame.draw.rect(self.screen, (30,30,30), (hx+2, y+11, 3, 3))
        else:  # zombie
            c = (70, 140, 80) if not flash else (255,255,255)
            pygame.draw.rect(self.screen, (50, 80, 120), (x+2, y+m["h"]-14, 8, 14))
            pygame.draw.rect(self.screen, (50, 80, 120), (x+m["w"]-10, y+m["h"]-14, 8, 14))
            pygame.draw.rect(self.screen, (60, 120, 140), (x, y+18, m["w"], 24))
            pygame.draw.rect(self.screen, c, (x-1, y, m["w"]+2, 18))
            pygame.draw.rect(self.screen, (30,30,30), (x+5, y+8, 4, 4))
            pygame.draw.rect(self.screen, (30,30,30), (x+m["w"]-9, y+8, 4, 4))
            # arms forward
            pygame.draw.rect(self.screen, c, (x+(m["w"] if m["dir"]>0 else -8), y+22, 8, 16))
        # hp bar
        maxhp = 10 if m["kind"] == "pig" else (12 if m["kind"] == "cow" else 20)
        if m["hp"] < maxhp:
            w = 40
            pygame.draw.rect(self.screen, (0,0,0), (x+m["w"]/2-w/2, y-8, w, 5))
            pygame.draw.rect(self.screen, (220,50,50), (x+m["w"]/2-w/2, y-8, w*max(0,m["hp"])/maxhp, 5))

    def hearts(self, surf, x, y, val, maxv, full, half, empty):
        n = maxv//2
        for i in range(n):
            v = val-i*2
            c = full if v >= 2 else (half if v >= 1 else empty)
            cx0 = x+i*22
            # heart shape: two circles + triangle
            pygame.draw.circle(surf, c, (cx0+6, y+6), 6)
            pygame.draw.circle(surf, c, (cx0+14, y+6), 6)
            pygame.draw.polygon(surf, c, [(cx0+1, y+9), (cx0+19, y+9), (cx0+10, y+20)])

    def draw_hud(self):
        ww, wh = self.screen.get_size()
        p = self.player
        # hotbar
        n = 9
        bw, bh = 52, 52
        bx = ww//2-(n*bw)//2; by = wh-bh-12
        for i in range(n):
            iid = self.hotbar[i] if i < len(self.hotbar) else None
            r = pygame.Rect(bx+i*bw, by, bw, bh)
            sel = (i == self.sel)
            pygame.draw.rect(self.screen, (0,0,0,160) if False else (20,20,24), r, border_radius=6)
            pygame.draw.rect(self.screen, (255,255,255) if sel else (120,120,130), r, 3 if sel else 1, border_radius=6)
            if iid and iid in self.icons:
                self.screen.blit(pygame.transform.scale(self.icons[iid], (36, 36)), (r.x+8, r.y+4))
                cnt = self.inv.get(iid, 0)
                label = "inf" if self.mode == "creative" else str(cnt)
                if iid in self.hotbar and self.mode == "survival" and cnt <= 0 and iid in BLOCKS:
                    # ghost
                    ghost = self.small.render("0", True, (255, 90, 90))
                    self.screen.blit(ghost, (r.x+38, r.y+32))
                else:
                    txs = self.small.render(label, True, (255,255,255))
                    self.screen.blit(txs, (r.x+34, r.y+32))
            num = self.small.render(str(i+1), True, (200,200,200))
            self.screen.blit(num, (bx+i*bw+4, by+2))
        # hearts + hunger
        if self.mode == "survival":
            self.hearts(self.screen, bx, by-30, p["hp"], 20, (220,50,50), (220,120,50), (60,20,20))
            # hunger drumsticks simplified as bars
            for i in range(10):
                v = p["hunger"]-i*2
                c = (200,140,60) if v >= 2 else ((150,100,50) if v >= 1 else (60,40,20))
                pygame.draw.rect(self.screen, c, (bx+(n*bw)-20-i*22, by-26, 18, 12), border_radius=4)
        else:
            cr = self.font.render("CREATIVE - ابداعي  (G: fly, M: survival)", True, (255,255,120))
            self.screen.blit(cr, (bx, by-30))
        # top bar: time + day + mode + fps
        t = self.world["time"]
        hh = int(t*24); mm = int((t*24-hh)*60)
        info = f"Day {self.day}  {hh:02d}:{mm:02d}  | seed {self.world['seed']} | {len(self.mobs)} mobs | F1 help | E craft"
        txs = self.small.render(info, True, (255,255,255))
        bg = pygame.Surface((txs.get_width()+16, txs.get_height()+8), pygame.SRCALPHA)
        bg.fill((0,0,0,120))
        self.screen.blit(bg, (10, 10)); self.screen.blit(txs, (18, 14))
        # crosshair-ish selected name
        iid = self.sel_item()
        if iid:
            nm = item_name(iid)
            en = ITEMS.get(iid, {}).get("en", BLOCKS.get(iid, {}).get("en", ""))
            lbl = self.font.render(f"{nm}  ({en})", True, (255,255,255))
            self.screen.blit(lbl, (ww//2-lbl.get_width()//2, by-58))

    # ---------- inventory / crafting UI
    def draw_inventory(self):
        ww, wh = self.screen.get_size()
        w, h = min(760, ww-60), min(560, wh-60)
        x, y = (ww-w)//2, (wh-h)//2
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill((18, 18, 24, 235))
        self.screen.blit(panel, (x, y))
        pygame.draw.rect(self.screen, (200,200,210), (x, y, w, h), 2)
        title = self.font.render("Inventory - E close | Click recipe to craft | F eat | Smelt: ore+coal", True, (255,255,255))
        self.screen.blit(title, (x+16, y+10))
        # player items grid
        ix, iy = x+16, y+44
        self.inv_slots = []
        items = sorted(self.inv.items())
        # include hotbar-only? show all
        for idx, (iid, cnt) in enumerate(items):
            gx = ix+(idx%8)*70; gy = iy+(idx//8)*64
            if gy > y+h-190: break
            r = pygame.Rect(gx, gy, 62, 56)
            pygame.draw.rect(self.screen, (40,40,48), r, border_radius=5)
            pygame.draw.rect(self.screen, (120,120,130), r, 1, border_radius=5)
            if iid in self.icons:
                self.screen.blit(pygame.transform.scale(self.icons[iid], (32, 32)), (gx+6, gy+2))
            nm = self.small.render(item_name(iid)[:10], True, (220,220,220))
            self.screen.blit(nm, (gx+4, gy+36))
            cn = self.small.render(str(cnt), True, (255,255,150))
            self.screen.blit(cn, (gx+46, gy+4))
            self.inv_slots.append((r, iid))
        # recipes
        ry = iy+((len(items)+7)//8)*64+16
        if ry < y+120: ry = y+200
        self.recipe_slots = []
        rtitle = self.font.render("Crafting - الصنع:", True, (255,240,180))
        self.screen.blit(rtitle, (x+16, ry))
        ry += 28
        for i, r in enumerate(RECIPES[self.craft_scroll:self.craft_scroll+8]):
            ok = self.can_craft(r)
            rr = pygame.Rect(x+16, ry+i*38, w-32, 34)
            pygame.draw.rect(self.screen, (40,60,40) if ok else (50,40,40), rr, border_radius=5)
            ing = " + ".join(f"{item_name(k)}x{v}" for k, v in r["in"].items())
            txt = f"{r['name']}: {ing}  =>  {item_name(r['out'])}x{r['n']}" + (" [table]" if r.get("table") else "")
            c = (180,255,180) if ok else (255,150,150)
            self.screen.blit(self.small.render(txt[:90], True, c), (rr.x+40, rr.y+9))
            if r["out"] in self.icons:
                self.screen.blit(pygame.transform.scale(self.icons[r["out"]], (28, 28)), (rr.x+6, rr.y+3))
            self.recipe_slots.append((rr, r))
        # smelt row
        sy = ry+8*38+6
        if sy+30 < y+h:
            st = self.small.render("Smelt - صهر (click):", True, (255,240,180))
            self.screen.blit(st, (x+16, sy))
            self.smelt_slots = []
            for j, inp in enumerate([IRON_ORE, GOLD_ORE, SAND, COBBLE, LOG]):
                out = SMELT[inp]
                rr = pygame.Rect(x+170+j*110, sy-4, 104, 30)
                ok = self.has(inp, 1)
                pygame.draw.rect(self.screen, (40,60,60) if ok else (50,50,55), rr, border_radius=5)
                txs = self.small.render(f"{item_name(inp)}->{item_name(out)}", True, (200,255,255) if ok else (150,150,150))
                self.screen.blit(txs, (rr.x+6, rr.y+8))
                self.smelt_slots.append((rr, inp))
        hint = self.small.render("Hotbar: click an item then press 1-9 to assign | wheel/scroll recipes", True, (180,180,180))
        self.screen.blit(hint, (x+16, y+h-24))

    def draw_help(self):
        ww, wh = self.screen.get_size()
        lines = [
            "Help - مساعدة  (F1/Esc to close)",
            "A/D or Arrows: move | Space/W: jump",
            "Mouse LEFT (hold): mine block / hit mob",
            "Mouse RIGHT: place block (or eat if food selected)",
            "1-9 / wheel: select hotbar | E: inventory & crafting",
            "F: eat | M: creative/survival | G: fly (creative)",
            "F5: quick save | P or Esc: pause",
            "Goal: gather wood -> planks -> sticks -> tools,",
            "mine stone/coal/iron, smelt iron, survive nights!",
            "Zombies burn at day, come at night. Pigs/cows give food.",
        ]
        w = 640; h = len(lines)*30+30
        x, y = (ww-w)//2, (wh-h)//2
        pygame.draw.rect(self.screen, (10,10,16), (x, y, w, h), border_radius=10)
        pygame.draw.rect(self.screen, (220,220,230), (x, y, w, h), 2, border_radius=10)
        for i, ln in enumerate(lines):
            c = (255,240,180) if i == 0 else (240,240,240)
            self.screen.blit(self.font.render(ln, True, c), (x+24, y+16+i*30))

    def draw_menu(self):
        ww, wh = self.screen.get_size()
        # bg gradient dirt
        self.screen.fill((20, 26, 40))
        for i in range(0, wh, TILE):
            for j in range(0, ww, TILE):
                if (i+j) % 96 == 0:
                    self.screen.fill((30, 38, 58), (j, i, TILE, TILE))
        title = self.big.render("MINECRAFT 2D", True, (120, 230, 120))
        sub = self.font.render("نسخة ثنائية الأبعاد للكمبيوتر - Desktop (pygame)", True, (230,230,230))
        self.screen.blit(title, (ww//2-title.get_width()//2, 90))
        self.screen.blit(sub, (ww//2-sub.get_width()//2, 145))
        # seed + mode inputs
        labels = [
            f"Seed (empty=random): {self.seed_text}_",
            f"Mode: {self.mode_select}  (Tab to switch: survival/creative)",
            "ENTER: New world   |   L: Load save   |   H: Help",
        ]
        for i, ln in enumerate(labels):
            txs = self.font.render(ln, True, (255,255,255))
            self.screen.blit(txs, (ww//2-txs.get_width()//2, 220+i*40))
        opts = ["New World - عالم جديد", "Load Save - تحميل", "Help - مساعدة", "Quit - خروج"]
        for i, o in enumerate(opts):
            c = (255,240,150) if i == self.menu_idx else (200,200,200)
            txs = self.font.render(f"{'> ' if i==self.menu_idx else '  '}{o}", True, c)
            self.screen.blit(txs, (ww//2-txs.get_width()//2, 380+i*44))
        saves = [f for f in os.listdir(SAVE_DIR) if f.endswith(".json")]
        if saves:
            txs = self.small.render("Saves: " + ", ".join(saves), True, (160,200,160))
            self.screen.blit(txs, (ww//2-txs.get_width()//2, wh-60))
        ctl = self.small.render("Arrows/WASD move | Mouse mine/place | E inventory | F1 help", True, (150,150,160))
        self.screen.blit(ctl, (ww//2-ctl.get_width()//2, wh-32))

    def draw_pause(self):
        ww, wh = self.screen.get_size()
        ov = pygame.Surface((ww, wh), pygame.SRCALPHA); ov.fill((0,0,0,140))
        self.screen.blit(ov, (0,0))
        t = self.big.render("Paused", True, (255,255,255))
        self.screen.blit(t, (ww//2-t.get_width()//2, wh//2-90))
        for i, ln in enumerate(["Esc/P: resume", "F5: save", "Q: quit to menu", "M: toggle mode"]):
            txs = self.font.render(ln, True, (230,230,230))
            self.screen.blit(txs, (ww//2-txs.get_width()//2, wh//2-20+i*34))

    def draw_dead(self):
        ww, wh = self.screen.get_size()
        ov = pygame.Surface((ww, wh), pygame.SRCALPHA); ov.fill((120,0,0,160))
        self.screen.blit(ov, (0,0))
        t = self.big.render("You Died! - مت!", True, (255,255,255))
        self.screen.blit(t, (ww//2-t.get_width()//2, wh//2-60))
        h = self.font.render("Press R to respawn | Q for menu", True, (255,255,255))
        self.screen.blit(h, (ww//2-h.get_width()//2, wh//2+10))

    # ---------- events
    def handle_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if self.state == "menu":
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_UP: self.menu_idx = (self.menu_idx-1) % 4
                    elif ev.key == pygame.K_DOWN: self.menu_idx = (self.menu_idx+1) % 4
                    elif ev.key == pygame.K_TAB:
                        self.mode_select = "creative" if self.mode_select == "survival" else "survival"
                    elif ev.key == pygame.K_RETURN:
                        self.activate_menu()
                    elif ev.key == pygame.K_l: self.load_slot(1)
                    elif ev.key == pygame.K_h: self.show_help = not self.show_help
                    elif ev.key == pygame.K_BACKSPACE: self.seed_text = self.seed_text[:-1]
                    elif ev.unicode and (ev.unicode.isdigit() or ev.unicode.isalpha()):
                        if len(self.seed_text) < 12: self.seed_text += ev.unicode
                elif ev.type == pygame.MOUSEBUTTONDOWN:
                    ww, wh = self.screen.get_size()
                    for i in range(4):
                        r = pygame.Rect(ww//2-200, 380+i*44-4, 400, 36)
                        if r.collidepoint(ev.pos):
                            self.menu_idx = i; self.activate_menu()
                continue
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    if self.show_help: self.show_help = False
                    elif self.show_inv: self.show_inv = False
                    elif self.state == "play": self.state = "pause"
                    elif self.state == "pause": self.state = "play"
                elif ev.key == pygame.K_F1: self.show_help = not self.show_help
                elif ev.key == pygame.K_e:
                    if self.state == "play": self.show_inv = not self.show_inv
                elif ev.key == pygame.K_p:
                    if self.state == "play": self.state = "pause"
                    elif self.state == "pause": self.state = "play"
                elif ev.key == pygame.K_F5: self.save_slot(1)
                elif ev.key == pygame.K_f: self.eat()
                elif ev.key == pygame.K_m:
                    self.mode = "creative" if self.mode == "survival" else "survival"
                    self.say("Mode: " + self.mode)
                elif ev.key == pygame.K_g and self.mode == "creative":
                    self.fly = not self.fly; self.say("Fly: " + str(self.fly))
                elif ev.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
                                pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9):
                    n = ev.key-pygame.K_1
                    if self.show_inv and getattr(self, "picked", None) is not None:
                        self.hotbar[n] = self.picked; self.picked = None; self.sfx("pop")
                    else:
                        self.sel = n
                elif self.state == "dead" and ev.key == pygame.K_r:
                    sx, sy = self.world["spawn"]
                    self.player = make_player(sx, sy)
                    self.state = "play"
                elif (self.state in ("pause", "dead")) and ev.key == pygame.K_q:
                    self.state = "menu"
            if self.state == "play" and ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 3:  # place
                    if self.show_inv: pass
                    else: self.try_place()
                elif ev.button == 4:  # wheel up
                    if self.show_inv:
                        self.craft_scroll = max(0, self.craft_scroll-1)
                    else:
                        self.sel = (self.sel-1) % 9
                elif ev.button == 5:
                    if self.show_inv:
                        self.craft_scroll = min(max(0, len(RECIPES)-8), self.craft_scroll+1)
                    else:
                        self.sel = (self.sel+1) % 9
                elif ev.button == 1 and self.show_inv:
                    self.click_inventory(ev.pos)
        return True

    def activate_menu(self):
        if self.menu_idx == 0:
            seed = self.seed_text.strip() or str(random.randint(1000, 99999))
            self.new_game(seed, self.mode_select)
        elif self.menu_idx == 1:
            self.load_slot(1)
        elif self.menu_idx == 2:
            self.show_help = True
        else:
            pygame.quit(); sys.exit()

    def click_inventory(self, pos):
        for r, iid in getattr(self, "inv_slots", []):
            if r.collidepoint(pos):
                self.picked = iid
                self.say(f"{item_name(iid)}: press 1-9 to put in hotbar")
                self.sfx("pop")
                return
        for r, rec in getattr(self, "recipe_slots", []):
            if r.collidepoint(pos):
                if self.do_craft(rec):
                    self.say(f"Crafted {item_name(rec['out'])}!")
                else:
                    self.say("Missing materials / need crafting table nearby!")
                return
        for r, inp in getattr(self, "smelt_slots", []):
            if r.collidepoint(pos):
                if self.do_smelt(inp):
                    self.say(f"Smelted {item_name(SMELT[inp])}!")
                else:
                    self.say("Need material (+ coal fuel for ores)!")
                return

    def run(self):
        running = True
        while running:
            dt = min(0.05, self.clock.tick(FPS)/1000.0)
            running = self.handle_events()
            if self.state not in ("menu",):
                if self.state == "play":
                    self.update(dt)
                elif self.state == "pause":
                    if self.msg_t > 0: self.msg_t -= dt
            self.draw()
            if self.state == "menu" and self.show_help:
                self.draw_help()
            pygame.display.flip()
        pygame.quit()

def main():
    Game().run()

if __name__ == "__main__":
    main()
