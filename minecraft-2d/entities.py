# -*- coding: utf-8 -*-
"""Physics + mob AI pure logic (testable without pygame)."""
from game_data import TILE, is_solid
from world_gen import get_tile

GRAV = 2200.0
MOVE_SPEED = 260.0
JUMP_VEL = -780.0

def _collides(world, px, py, w, h):
    x0 = int(px // TILE); x1 = int((px+w-0.01) // TILE)
    y0 = int(py // TILE); y1 = int((py+h-0.01) // TILE)
    for ty in range(y0, y1+1):
        for tx in range(x0, x1+1):
            b = get_tile(world, tx, ty)
            if is_solid(b):
                return True
    return False

def move_entity(world, ent, dt):
    """ent has x,y,vx,vy,w,h,on_ground. Mutates + returns."""
    # X axis
    nx = ent["x"] + ent["vx"]*dt
    if _collides(world, nx, ent["y"], ent["w"], ent["h"]):
        # step to contact
        step = 1 if ent["vx"] > 0 else -1
        while not _collides(world, nx, ent["y"], ent["w"], ent["h"]) is False:
            break
        # binary approach: move pixel by pixel
        while _collides(world, nx, ent["y"], ent["w"], ent["h"]):
            nx -= step
            if abs(ent["vx"]*dt) > 64:  # safety
                break
        ent["vx"] = 0
    ent["x"] = nx
    # Y axis
    ent["vy"] += GRAV*dt
    if ent["vy"] > 1200:
        ent["vy"] = 1200
    ny = ent["y"] + ent["vy"]*dt
    ent["on_ground"] = False
    if _collides(world, ent["x"], ny, ent["w"], ent["h"]):
        step = 1 if ent["vy"] > 0 else -1
        while _collides(world, ent["x"], ny, ent["w"], ent["h"]):
            ny -= step
            if abs(ent["vy"]*dt) > 128:
                ny = ent["y"]
                break
        if step > 0:
            ent["on_ground"] = True
        ent["vy"] = 0
    # fall distance tracking
    prev_fall = ent.get("fall", 0)
    if ent.get("on_ground"):
        if prev_fall > 420:  # pixels fallen
            ent["fall_damage"] = (prev_fall-420)/60.0
        else:
            ent["fall_damage"] = 0
        ent["fall"] = 0
    else:
        if ent["vy"] > 0:
            ent["fall"] = prev_fall + ent["vy"]*dt
    ent["y"] = ny
    return ent

def make_player(sx, sy):
    return {"x": sx*TILE+5, "y": sy*TILE, "vx": 0, "vy": 0,
            "w": 22, "h": 56, "on_ground": False, "fall": 0,
            "hp": 20.0, "hunger": 20.0, "face": 1}

def make_mob(kind, tx, ty):
    if kind == "pig":
        return {"kind": "pig", "x": tx*TILE, "y": ty*TILE, "vx": 0, "vy": 0,
                "w": 38, "h": 26, "on_ground": False, "fall": 0, "hp": 10,
                "dir": 1, "timer": 0, "hurt": 0}
    if kind == "cow":
        return {"kind": "cow", "x": tx*TILE, "y": ty*TILE, "vx": 0, "vy": 0,
                "w": 44, "h": 32, "on_ground": False, "fall": 0, "hp": 12,
                "dir": 1, "timer": 0, "hurt": 0}
    # zombie
    return {"kind": "zombie", "x": tx*TILE, "y": ty*TILE, "vx": 0, "vy": 0,
            "w": 24, "h": 54, "on_ground": False, "fall": 0, "hp": 20,
            "dir": -1, "timer": 0, "hurt": 0, "attack_cd": 0}

def mob_ai(world, mob, player, dt, is_night):
    import random
    mob["timer"] -= dt
    mob["hurt"] = max(0, mob.get("hurt", 0)-dt)
    mob["attack_cd"] = max(0, mob.get("attack_cd", 0)-dt)
    if mob["kind"] in ("pig", "cow"):
        if mob["timer"] <= 0:
            mob["timer"] = random.uniform(1.5, 4.0)
            mob["dir"] = random.choice([-1, 0, 0, 1])
        mob["vx"] = mob["dir"]*60
        # jump if blocked
        if mob["vx"] != 0 and mob.get("on_ground"):
            # probe ahead
            px = mob["x"] + (mob["w"]+2 if mob["dir"] > 0 else -3)
            py = mob["y"]+mob["h"]-6
            import math
            tx = int(px//TILE); ty = int(py//TILE)
            tb = get_tile(world, tx, ty)
            above = get_tile(world, tx, ty-1)
            if is_solid(tb) or (is_solid(get_tile(world, int((mob["x"]+mob["w"]/2+mob["dir"]*20)//TILE), int((mob["y"]+mob["h"]/2)//TILE)))):
                mob["vy"] = -650
    else:  # zombie chases
        dx = player["x"]-mob["x"]
        dist = abs(dx)
        if dist < 560:
            mob["dir"] = 1 if dx > 0 else -1
            mob["vx"] = mob["dir"]*130
            if mob.get("on_ground") and (dist > 40):
                # jump over obstacle
                ahead_x = mob["x"] + (mob["w"]+4 if mob["dir"] > 0 else -5)
                feet_ty = int((mob["y"]+mob["h"]-4)//TILE)
                ahead_tx = int(ahead_x//TILE)
                if is_solid(get_tile(world, ahead_tx, feet_ty)):
                    mob["vy"] = -750
            # daylight burn
            if not is_night:
                mob["hp"] -= 1.2*dt
        else:
            mob["vx"] = mob["dir"]*50
            if mob["timer"] <= 0:
                mob["timer"] = 3
                mob["dir"] *= -1
    move_entity(world, mob, dt)
    return mob
