# -*- coding: utf-8 -*-
"""Procedural world generation + save/load (no pygame dependency)."""
import json, math, os, random
from game_data import *

def _interp_noise(rng, n, wavelength, amp=1.0):
    """Smooth value noise: random control points every `wavelength` px, smoothstep interp."""
    nctrl = n//wavelength + 3
    ctrl = [rng.random() for _ in range(nctrl)]
    out = [0.0]*n
    for i in range(n):
        f = (i % wavelength)/wavelength
        k = i//wavelength
        a, b = ctrl[k], ctrl[k+1]
        s = f*f*(3-2*f)
        out[i] = (a*(1-s)+b*s)*amp
    return out

def _smooth_noise(rng, n, octaves=4):
    out = [0.0]*n
    amp, wave = 1.0, max(8, n//8)
    for o in range(octaves):
        layer = _interp_noise(rng, n, max(4, wave), amp)
        for i in range(n):
            out[i] += layer[i]
        amp *= 0.5; wave = max(4, wave//2)
    mn, mx = min(out), max(out)
    rng_ = (mx-mn) or 1
    return [(v-mn)/rng_ for v in out]

def generate_world(seed=None, w=WORLD_W, h=WORLD_H):
    rng = random.Random(seed)
    hills = _smooth_noise(rng, w, 3)
    hills2 = _smooth_noise(rng, w, 2)
    surf = []
    for x in range(w):
        base = 52 + int(hills[x]*14) + int((hills2[x]-0.5)*5)
        # limit slope to max 2 per column for walkable terrain
        if surf and abs(base-surf[-1]) > 2:
            base = surf[-1] + (2 if base > surf[-1] else -2)
        surf.append(max(20, min(h-30, base)))
    # biomes by x: desert / plains / forest / snow
    biome_noise = _smooth_noise(rng, w, 2)
    tiles = [[AIR]*w for _ in range(h)]
    for x in range(w):
        bn = biome_noise[x]
        if bn < 0.28:
            biome = "desert"
        elif bn < 0.45:
            biome = "plains"
        elif bn < 0.75:
            biome = "forest"
        else:
            biome = "snow"
        sy = surf[x]
        depth_dirt = 4 if biome != "desert" else 6
        for y in range(sy, h):
            d = y - sy
            if y == h-1:
                tiles[y][x] = BEDROCK
            elif y >= h-3 and rng.random() < 0.5:
                tiles[y][x] = BEDROCK if rng.random() < 0.3 else STONE
            elif d == 0:
                if biome == "desert":
                    tiles[y][x] = SAND
                elif biome == "snow":
                    tiles[y][x] = SNOW_GRASS
                else:
                    tiles[y][x] = GRASS
            elif d <= depth_dirt:
                tiles[y][x] = SAND if biome == "desert" else DIRT
            else:
                tiles[y][x] = STONE
        # ores
        for y in range(sy+4, h-2):
            r = rng.random()
            depth = (y-sy)/(h-sy)
            if r < 0.02 and y > sy+3:
                tiles[y][x] = COAL_ORE
            elif r < 0.028 and depth > 0.25:
                tiles[y][x] = IRON_ORE
            elif r < 0.032 and depth > 0.45:
                tiles[y][x] = GOLD_ORE
            elif r < 0.034 and depth > 0.6:
                tiles[y][x] = DIAMOND_ORE
        # sandstone under desert
        if biome == "desert":
            for y in range(sy+1, min(sy+5, h)):
                if tiles[y][x] == SAND and y > sy+2:
                    tiles[y][x] = SANDSTONE
        # caves: carve with random walkers
        # (done globally below)
    # caves
    for _ in range(26):
        cx = rng.randint(4, w-5)
        cy = rng.randint(max(surf)+6, h-8)
        length = rng.randint(12, 40)
        for _ in range(length):
            for dy in range(-1, 2):
                for dx in range(-2, 3):
                    xx, yy = cx+dx, cy+dy
                    if 0 <= xx < w and 0 <= yy < h:
                        if tiles[yy][xx] not in (BEDROCK,):
                            if abs(dx)+abs(dy) <= 2 and rng.random() < 0.8:
                                tiles[yy][xx] = AIR
            cx += rng.choice([-1, 0, 1, 1])
            cy += rng.choice([-1, 0, 0, 1])
            cx = max(2, min(w-3, cx)); cy = max(10, min(h-3, cy))
    # trees & plants
    for x in range(2, w-2):
        bn = biome_noise[x]
        sy = surf[x]
        if tiles[sy][x] != AIR:
            continue
        below = tiles[sy+1][x] if sy+1 < h else STONE
        if bn >= 0.45 and below in (GRASS, DIRT):  # forest/plains
            if rng.random() < (0.10 if bn < 0.75 else 0.06):
                th = rng.randint(3, 5)
                for i in range(1, th+1):
                    if sy-i >= 0:
                        tiles[sy-i][x] = LOG
                top = sy-th
                for dy in range(-2, 2):
                    for dx in range(-2, 3):
                        xx, yy = x+dx, top+dy
                        if 0 <= xx < w and 0 <= yy < h and tiles[yy][xx] == AIR:
                            if abs(dx)+abs(dy) <= 3 and not (dy == -2 and abs(dx) == 2):
                                tiles[yy][xx] = LEAVES
            elif rng.random() < 0.12:
                tiles[sy][x] = FLOWER if rng.random() < 0.4 else TALLGRASS
        elif bn < 0.28 and below == SAND:  # desert cactus
            if rng.random() < 0.03:
                ch = rng.randint(2, 3)
                for i in range(ch):
                    if sy-i >= 0 and tiles[sy-i][x] == AIR:
                        tiles[sy-i][x] = CACTUS
    spawn_x = w//2
    spawn_y = surf[spawn_x]-3
    # ensure spawn clear
    for dy in range(-4, 1):
        yy = spawn_y+dy
        if 0 <= yy < h:
            if tiles[yy][spawn_x] in (LOG, LEAVES):
                tiles[yy][spawn_x] = AIR
    return {
        "seed": seed if seed is not None else rng.randint(0, 999999),
        "w": w, "h": h,
        "tiles": tiles,
        "surface": surf,
        "spawn": [spawn_x, spawn_y],
        "time": 0.3,
    }

def get_tile(world, x, y):
    if x < 0 or y < 0 or x >= world["w"] or y >= world["h"]:
        return BEDROCK if y >= world["h"] else AIR
    return world["tiles"][y][x]

def set_tile(world, x, y, v):
    if 0 <= x < world["w"] and 0 <= y < world["h"]:
        world["tiles"][y][x] = v

def save_world(world, player, mobs, inv, hotbar, sel, mode, path):
    data = {
        "seed": world["seed"], "w": world["w"], "h": world["h"],
        "tiles": world["tiles"],
        "spawn": world["spawn"], "time": world.get("time", 0.3),
        "player": player, "mobs": mobs,
        "inv": {str(k): v for k, v in inv.items()},
        "hotbar": hotbar, "sel": sel, "mode": mode,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)

def load_world(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    world = {"seed": data["seed"], "w": data["w"], "h": data["h"],
             "tiles": data["tiles"], "spawn": data["spawn"],
             "time": data.get("time", 0.3)}
    inv = {int(k): v for k, v in data.get("inv", {}).items()}
    return world, data.get("player"), data.get("mobs", []), inv, data.get("hotbar"), data.get("sel", 0), data.get("mode", "survival")
