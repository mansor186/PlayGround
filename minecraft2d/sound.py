"""أصوات إجرائية بسيطة (بدون ملفات خارجية)"""
import math, random
import pygame

_enabled = False
_sounds = {}

def init():
    global _enabled
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=1)
        _enabled = True
    except Exception:
        _enabled = False

def _tone(freq, dur_ms, vol=0.25, kind="square"):
    if not _enabled: return None
    rate = 22050
    n = int(rate * dur_ms / 1000)
    buf = bytearray()
    import struct
    for i in range(n):
        t = i / rate
        env = 1.0 - i / n
        if kind == "square":
            v = 1 if math.sin(2 * math.pi * freq * t) > 0 else -1
        elif kind == "noise":
            v = random.uniform(-1, 1)
        else:
            v = math.sin(2 * math.pi * freq * t)
        s = int(v * env * vol * 32767)
        buf += struct.pack("<h", max(-32767, min(32767, s)))
    snd = pygame.mixer.Sound(buffer=bytes(buf))
    return snd

def get(name):
    if name in _sounds: return _sounds[name]
    if not _enabled: return None
    specs = {
        "break": (220, 120, 0.3, "noise"),
        "place": (330, 90, 0.25, "square"),
        "hit": (150, 70, 0.3, "noise"),
        "pickup": (880, 90, 0.2, "sine"),
        "hurt": (180, 180, 0.3, "square"),
        "eat": (500, 120, 0.25, "sine"),
        "craft": (660, 140, 0.25, "sine"),
        "splash": (400, 150, 0.2, "noise"),
    }
    f, d, v, k = specs.get(name, (440, 100, 0.2, "sine"))
    s = _tone(f, d, v, k)
    _sounds[name] = s
    return s

def play(name):
    try:
        s = get(name)
        if s: s.play()
    except Exception:
        pass
