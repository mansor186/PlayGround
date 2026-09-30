"""وصفات الصناعة Crafting"""
# كل وصفة: (شبكة 3x3 كقائمة سطور، الناتج id، العدد)
# الرموز: P=planks, L=log, S=stick, C=cobble, I=iron_ingot, D=diamond, O=coal, G=glass, B=brick, W=wool
# نستخدم أسماء عناصر مبسطة

RECIPES = [
    # ألواح من جذع
    (["L", None, "planks_shapeless"], "block:6", 4),
    # عصي
    (["P/P", None, "sticks"], "stick", 4),
    # طاولة صناعة
    (["PP/PP", None, "craft"], "block:18", 1),
    # مشعل
    (["O/S", None, "torch"], "block:10", 4),
    # فرن
    (["CCC/C C/CCC", None, "furnace"], "block:19", 1),
    # أدوات خشبية
    (["PPP/ S / S ", "pickaxe_wood", 1]),
    (["PP/ S/ S", "axe_wood", 1]),
    (["P/ S/ S", "shovel_wood", 1]),
    (["P/P/S", "sword_wood", 1]),
    # حجرية
    (["CCC/ S / S ", "pickaxe_stone", 1]),
    (["CC/ S/ S", "axe_stone", 1]),
    (["C/ S/ S", "shovel_stone", 1]),
    (["C/C/S", "sword_stone", 1]),
    # حديدية
    (["III/ S / S ", "pickaxe_iron", 1]),
    (["II/ S/ S", "axe_iron", 1]),
    (["I/ S/ S", "shovel_iron", 1]),
    (["I/I/S", "sword_iron", 1]),
    # ألماسية
    (["DDD/ S / S ", "pickaxe_diamond", 1]),
    (["DD/ S/ S", "axe_diamond", 1]),
    (["D/ S/ S", "shovel_diamond", 1]),
    (["D/D/S", "sword_diamond", 1]),
    # طوب / زجاج / مكتبة / كتلة فحم / حجر رملي
    (["BB/BB", None, "brick_simple"], "block:9", 1),
    (["OOO/OOO/OOO", None, "coalblock"], "block:26", 1),
    (["PP P/PPP/PP P", "bookshelf_fix"], "block:27", 1),
]

# وصفات شبكية مبسطة للفحص السريع: نطابق المواد المطلوبة (count) بدل الشكل الدقيق لتسهيل اللعب 2D
SHAPELESS = {
    # المفتاح: tuple مرتب من المواد -> (الناتج، العدد)
    (("block:4", 1),): ("block:6", 4),
    (("block:6", 2),): ("stick", 4),
    (("block:6", 4),): ("block:18", 1),
    (("coal", 1), (("stick", 1),)[0] if False else ("stick", 1)): ("block:10", 4),
    (("block:24", 8),): ("block:19", 1),
    (("block:6", 3), (("stick", 2),)[0] if False else ("stick", 2)): ("pickaxe_wood", 1),
}

def _norm_grid(grid3):
    """grid3: list 9 of item-id or None -> dict counts (للأدوات: نميز الخامة)"""
    counts = {}
    for c in grid3:
        if c is None: continue
        # تحويل block:6 -> planks رمز
        key = c
        counts[key] = counts.get(key, 0) + 1
    return counts

def match_recipe(grid3):
    """تُرجع (out_id, out_count) أو None. تدعم الشكل + shapeless مبسط."""
    cells = [c for c in grid3 if c]
    if not cells:
        return None
    counts = _norm_grid(grid3)

    def has(**kw):
        for k, v in kw.items():
            if counts.get(k, 0) < v: return False
        # يجب ألا توجد مواد زائدة (باستثناء الفراغ)
        total_need = sum(kw.values())
        if len(cells) != total_need: return False
        return True

    # 1) ألواح
    if has(**{"block:4": 1}): return ("block:6", 4)
    # 2) عصي
    if has(**{"block:6": 2}): return ("stick", 4)
    # 3) طاولة
    if has(**{"block:6": 4}): return ("block:18", 1)
    # 4) مشعل: فحم + عصا
    if has(**{"coal": 1, "stick": 1}): return ("block:10", 4)
    # 5) فرن
    if has(**{"block:24": 8}): return ("block:19", 1)
    # 6) صندوق: ألواح*8
    if has(**{"block:6": 8}): return ("block:20", 1)
    # 7) زجاج من رمل (يحتاج فرن — نبسط: 4 رمل = 2 زجاج)
    if has(**{"block:7": 4}): return ("block:8", 2)
    # 8) طوب من حجر رملي؟ نبسط
    if has(**{"block:25": 2}): return ("block:9", 2)
    # 9) كتلة فحم
    if has(**{"coal": 9}): return ("block:26", 1)
    # فحم -> 9 فحم من الكتلة (تفكيك)
    if has(**{"block:26": 1}): return ("coal", 9)
    # 10) أدوات: نميز حسب الخامة
    for mat, prefix in (("block:6", "wood"), ("block:24", "stone"), ("iron_ingot", "iron"), ("diamond", "diamond")):
        if has(**{mat: 3, "stick": 2}): return (f"pickaxe_{prefix}", 1)
        if has(**{mat: 3, "stick": 2}):
            pass
    # فأس: خامة*3؟ نبسط: خامة 3 + عصا 2 = pickaxe، خامة 2 + عصا 2 = axe؟ نفرق بالترتيب
    # للتبسيط: نستخدم عدد الخامة للتمييز:
    #  axe يحتاج 3 خامة؟ لا — سنعتمد على مواضع: إذا كان الصف العلوي ممتلئاً = pickaxe وإلا axe/sword
    # نفحص الشكل الفعلي:
    g = [(c) for c in grid3]  # 9 عناصر
    def at(r, c_): return g[r * 3 + c_]
    for mat, prefix in (("block:6", "wood"), ("block:24", "stone"), ("iron_ingot", "iron"), ("diamond", "diamond")):
        sticks2 = counts.get("stick", 0) == 2 and len(cells) == 5
        sticks1 = counts.get("stick", 0) == 1 and len(cells) == 3
        m = counts.get(mat, 0)
        if sticks2 and m == 3:
            # صف علوي كامل = pickaxe
            if at(0, 0) == mat and at(0, 1) == mat and at(0, 2) == mat:
                return (f"pickaxe_{prefix}", 1)
            else:
                return (f"axe_{prefix}", 1)
        if counts.get("stick", 0) == 2 and m == 1 and len(cells) == 3:
            return (f"shovel_{prefix}", 1)
        if counts.get("stick", 0) == 1 and m == 2 and len(cells) == 3:
            return (f"sword_{prefix}", 1)
    # سبيكة حديد من خام (صهر مبسط: 1 خام + 1 فحم = 1 سبيكة)
    if has(**{"raw_iron": 1, "coal": 1}): return ("iron_ingot", 1)
    return None
