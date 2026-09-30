"""اللاعب والوحوش والقطرات والجسيمات"""
import random, math
import pygame
from . import config as C
from . import blocks as B
from . import items as I

TILE = C.TILE

def collide_move(rect, dx, dy, world):
    """حركة مع تصادم بلاطات. rect: pygame.Rect بالبكسل. تُرجع (on_ground, hit_head, in_water, in_lava)"""
    on_ground = False
    # X
    rect.x += int(dx)
    for ty in range(rect.top // TILE, rect.bottom // TILE + 1):
        for tx in range(rect.left // TILE, rect.right // TILE + 1):
            bid = world.get(tx, ty)
            if B.is_solid(bid):
                t = pygame.Rect(tx * TILE, ty * TILE, TILE, TILE)
                if rect.colliderect(t):
                    if dx > 0: rect.right = t.left
                    elif dx < 0: rect.left = t.right
    # Y
    rect.y += int(dy)
    hit_head = False
    for ty in range(rect.top // TILE, rect.bottom // TILE + 1):
        for tx in range(rect.left // TILE, rect.right // TILE + 1):
            bid = world.get(tx, ty)
            if B.is_solid(bid):
                t = pygame.Rect(tx * TILE, ty * TILE, TILE, TILE)
                if rect.colliderect(t):
                    if dy > 0:
                        rect.bottom = t.top; on_ground = True
                    elif dy < 0:
                        rect.top = t.bottom; hit_head = True
    # سوائل
    in_water = in_lava = False
    cx, cy = rect.centerx // TILE, rect.centery // TILE
    for (xx, yy) in ((cx, cy), (rect.centerx // TILE, rect.bottom // TILE)):
        b = world.get(xx, yy)
        if b == B.WATER: in_water = True
        if b == B.LAVA: in_lava = True
    return on_ground, hit_head, in_water, in_lava

class Player:
    def __init__(self, world, inv):
        self.world = world
        self.inv = inv
        sx, sy = world.spawn
        self.rect = pygame.Rect(sx * TILE + 4, sy * TILE, TILE - 8, TILE * 2 - 6)
        self.vx = 0; self.vy = 0
        self.face = 1
        self.on_ground = False
        self.hp = 20; self.hunger = 20; self.oxygen = 20
        self.hunger_t = 0; self.regen_t = 0; self.hurt_t = 0
        self.fall_start = None
        self.gamemode = "survival"  # أو creative
        self.fly = False
        self.dead = False
        self.attack_cd = 0

    def update(self, keys, dt):
        if self.dead: return
        sprint = keys.get("sprint", False)
        sp = C.MOVE_SPEED * (C.SPRINT_MULT if sprint else 1.0)
        move = 0
        if keys.get("left"): move -= sp
        if keys.get("right"): move += sp
        if move != 0: self.face = 1 if move > 0 else -1
        # طيران إبداعي
        if self.gamemode == "creative" and self.fly:
            self.vx = move
            self.vy = 0
            if keys.get("jump"): self.vy = -5
            if keys.get("down"): self.vy = 5
            self.rect.x += int(self.vx); self.rect.y += int(self.vy)
            # تصادم بسيط: أخرج من الصلب
            for ty in range(self.rect.top // TILE, self.rect.bottom // TILE + 1):
                for tx in range(self.rect.left // TILE, self.rect.right // TILE + 1):
                    if B.is_solid(self.world.get(tx, ty)):
                        t = pygame.Rect(tx * TILE, ty * TILE, TILE, TILE)
                        if self.rect.colliderect(t):
                            # ادفع للخارج
                            self.rect.y -= int(self.vy)
                            self.rect.x -= int(self.vx)
                            break
            return
        self.vx = move
        # فيزياء الماء
        _, _, in_water, in_lava = self._sense()
        if in_water:
            self.vy += C.GRAVITY * 0.35
            self.vy = min(self.vy, 3.2)
            if keys.get("jump"): self.vy = C.SWIM_UP
            self.vx *= 0.7
        elif in_lava:
            self.vy += C.GRAVITY * 0.4
            self.vy = min(self.vy, 3.5)
            if keys.get("jump"): self.vy = C.SWIM_UP * 0.8
        else:
            self.vy += C.GRAVITY
            self.vy = min(self.vy, 14)
            if keys.get("jump") and self.on_ground:
                self.vy = C.JUMP_VEL
                self.on_ground = False
        prev_bottom = self.rect.bottom
        if self.fall_start is None and not self.on_ground and self.vy >= 0:
            self.fall_start = prev_bottom
        was_air = not self.on_ground
        self.rect.x += 0  # X عبر collide
        og, hh, iw2, il2 = collide_move(self.rect, self.vx, 0, self.world)
        og2, hh2, iw3, il3 = collide_move(self.rect, 0, self.vy, self.world)
        if og2:
            # ضرر السقوط
            if self.gamemode == "survival" and self.fall_start is not None:
                fall = self.rect.bottom - self.fall_start
                if fall > 4 * TILE and not iw3:
                    self.damage((fall - 4 * TILE) // TILE * 2 + 1, cause="fall")
            self.fall_start = None
            if self.vy > 0: self.vy = 0
            self.on_ground = True
        else:
            if self.vy < 0 and hh2: self.vy = 0
            self.on_ground = False
        # حمم + غرق + جوع
        if self.gamemode == "survival":
            if il3:
                self.damage(0.15, cause="lava")
                if random.random() < 0.1: self.hurt_t = 10
            # غرق
            head = self.world.get(self.rect.centerx // TILE, self.rect.top // TILE)
            if head == B.WATER:
                self.oxygen -= 0.05
                if self.oxygen <= 0:
                    self.oxygen = 0; self.damage(0.08, cause="drown")
            else:
                self.oxygen = min(20, self.oxygen + 0.3)
            # جوع وتجدد
            self.hunger_t += 1
            moving = abs(move) > 0.1
            if self.hunger_t > (140 if moving else 300):
                self.hunger_t = 0
                if self.hunger > 0: self.hunger -= 0.5
                else: self.damage(0.5, cause="starve")
            if self.hunger > 14 and self.hp < 20:
                self.regen_t += 1
                if self.regen_t > 90:
                    self.regen_t = 0; self.hp = min(20, self.hp + 0.5); self.hunger -= 0.5
            if self.hurt_t > 0: self.hurt_t -= 1
            if self.attack_cd > 0: self.attack_cd -= 1

    def _sense(self):
        cx, cy = self.rect.centerx // TILE, self.rect.centery // TILE
        iw = self.world.get(cx, cy) == B.WATER
        il = self.world.get(cx, cy) == B.LAVA
        return False, False, iw, il

    def damage(self, amt, cause=""):
        if self.gamemode == "creative": return
        if self.hurt_t > 0 and cause not in ("lava", "drown", "starve", "fall"): return
        self.hp -= amt
        if cause not in ("drown", "starve"): self.hurt_t = 25
        if self.hp <= 0:
            self.hp = 0; self.dead = True

    def heal(self, amt):
        self.hp = min(20, self.hp + amt)

    def eat(self):
        s = self.inv.held()
        if s["id"] == "apple":
            self.inv.consume_held(1); self.heal(4); self.hunger = min(20, self.hunger + 4); return True
        if s["id"] == "pork":
            self.inv.consume_held(1); self.heal(6); self.hunger = min(20, self.hunger + 8); return True
        return False

    def respawn(self):
        sx, sy = self.world.spawn
        self.rect.x, self.rect.y = sx * TILE + 4, sy * TILE
        self.vx = self.vy = 0
        self.hp = 20; self.hunger = 20; self.oxygen = 20; self.dead = False


class Mob:
    def __init__(self, world, kind, x, y):
        self.world = world; self.kind = kind
        self.rect = pygame.Rect(x, y, 26, 26 if kind in ("pig", "sheep") else 30)
        if kind in ("zombie", "skeleton"):
            self.rect.height = 52
        self.vx = 0; self.vy = 0
        self.hp = {"pig": 10, "sheep": 8, "zombie": 20, "skeleton": 20}[kind]
        self.dir = random.choice([-1, 1])
        self.t = random.randint(0, 120)
        self.hurt = 0; self.dead = False
        self.attack_cd = 0

    def hostile(self):
        return self.kind in ("zombie", "skeleton")

    def update(self, player, is_night):
        if self.dead: return
        self.t += 1; self.vy = min(self.vy + C.GRAVITY, 13)
        self.vx = 0
        if self.kind in ("pig", "sheep"):
            if self.t % 150 == 0:
                self.dir = random.choice([-1, 0, 1])
            self.vx = self.dir * 0.8
            # اقفز فوق عائق
            if self.t % 30 == 0 and self._blocked_ahead():
                self.vy = -8
        else:
            # وحوش ليلية: تطارد اللاعب إذا قريب
            dx = player.rect.centerx - self.rect.centerx
            dist = abs(dx)
            should = is_night and dist < 420 and not player.dead
            if should:
                self.vx = 1.6 if dx > 0 else -1.6
                self.dir = 1 if dx > 0 else -1
                if self._blocked_ahead() and self.on_ground:
                    self.vy = -10
            else:
                if self.t % 170 == 0: self.dir = random.choice([-1, 0, 1])
                self.vx = self.dir * 0.9
                if self._blocked_ahead() and getattr(self, "on_ground", False):
                    self.vy = -9
            # احتراق الشمس
            if not is_night and self.world.time < 12000:
                pass
            # هجوم
            if dist < 34 and abs(player.rect.centery - self.rect.centery) < 44:
                if self.attack_cd <= 0 and player.gamemode == "survival":
                    player.damage(3 if self.kind == "zombie" else 2.5)
                    self.attack_cd = 50
        if self.attack_cd > 0: self.attack_cd -= 1
        if self.hurt > 0: self.hurt -= 1
        og, hh, iw, il = collide_move(self.rect, self.vx, 0, self.world)
        og2, hh2, iw2, il2 = collide_move(self.rect, 0, self.vy, self.world)
        self.on_ground = og2
        if og2 and self.vy > 0: self.vy = 0
        if hh2 and self.vy < 0: self.vy = 0
        if il2:
            self.hp -= 0.2
            if self.hp <= 0: self.dead = True
        # سقوك العالم
        if self.rect.y > self.world.h * TILE + 200: self.dead = True

    def _blocked_ahead(self):
        nx = (self.rect.centerx + self.dir * 18) // TILE
        ny = (self.rect.bottom - 4) // TILE
        ny2 = (self.rect.bottom - TILE) // TILE
        return B.is_solid(self.world.get(nx, ny)) and B.is_solid(self.world.get(nx, ny2)) is False and B.is_solid(self.world.get(nx, ny))

    def hit(self, dmg):
        self.hp -= dmg; self.hurt = 12
        self.vy = -5; self.vx = 0
        if self.hp <= 0: self.dead = True


class Drop:
    def __init__(self, x, y, iid, count=1):
        self.rect = pygame.Rect(x - 7, y - 7, 14, 14)
        self.iid = iid; self.count = count
        self.vx = random.uniform(-1.5, 1.5); self.vy = random.uniform(-5, -2)
        self.age = 0; self.dead = False

    def update(self, world):
        self.age += 1
        self.vy = min(self.vy + 0.4, 10)
        og, _, _, _ = collide_move(self.rect, self.vx, 0, world)
        og2, _, _, _ = collide_move(self.rect, 0, self.vy, world)
        if og2 and self.vy > 0:
            self.vy = 0; self.vx *= 0.8
        if self.age > 20 * 300: self.dead = True  # 5 دقائق


class Particle:
    def __init__(self, x, y, color):
        self.x = x; self.y = y
        self.vx = random.uniform(-2.5, 2.5); self.vy = random.uniform(-4, -1)
        self.life = random.randint(20, 45)
        self.color = color

    def update(self):
        self.x += self.vx; self.y += self.vy; self.vy += 0.3; self.life -= 1

    @property
    def dead(self): return self.life <= 0
