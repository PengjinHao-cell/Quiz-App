"""
构建离线英汉词库
- 来源：ECDICT（skywind3000/ECDICT）
- 按词频排序取前 20,000 条
- 输出 data/dict_cache.json：{ "word": "abandon", "meaning": "放弃；遗弃" }

用法：
    python build_dict.py                  # 完整构建
    python build_dict.py --top 15000      # 自定义条数
    python build_dict.py --force          # 强制重新下载
    python build_dict.py --lemma          # 只生成词形还原规则表
"""
import csv
import json
import os
import re
import sys
import urllib.request
import gzip
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
OUTPUT = os.path.join(DATA_DIR, "dict_cache.json")
CSV_PATH = os.path.join(DATA_DIR, "ecdict_full.csv")
CSV_URL = "https://github.com/skywind3000/ECDICT/raw/master/ecdict.csv"

TOP_N = 20000
FORCE = False
LEMMA_ONLY = False

args = sys.argv[1:]
i = 0
while i < len(args):
    if args[i] == "--top" and i + 1 < len(args):
        TOP_N = int(args[i + 1])
        i += 2
    elif args[i] == "--force":
        FORCE = True
        i += 1
    elif args[i] == "--lemma":
        LEMMA_ONLY = True
        i += 1
    else:
        i += 1


def download_csv():
    """下载 ECDICT CSV（约 200MB，建议有稳定网络）"""
    if os.path.exists(CSV_PATH) and not FORCE:
        size_mb = os.path.getsize(CSV_PATH) / (1024 * 1024)
        print(f"📦 已有词库文件：{CSV_PATH} ({size_mb:.1f} MB)")
        return

    print(f"⬇️  正在下载 ECDICT（约 200MB，请耐心等待）...")
    print(f"   源：{CSV_URL}")

    try:
        with urllib.request.urlopen(CSV_URL, timeout=600) as resp:
            with open(CSV_PATH, "wb") as f:
                shutil.copyfileobj(resp, f)
        size_mb = os.path.getsize(CSV_PATH) / (1024 * 1024)
        print(f"✅ 下载完成：{size_mb:.1f} MB")
    except Exception as e:
        print(f"❌ 下载失败：{e}")
        print("💡 提示：可以手动下载 ecdict.csv 放到 data/ 目录后重试")
        sys.exit(1)


def build():
    print(f"🔨 构建词库（取词频前 {TOP_N} 条）...")

    # 读取 CSV，收集 (bnc_freq, word, translation)
    entries = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = row.get("word", "").strip()
            translation = row.get("translation", "").strip()
            bnc_str = row.get("bnc", "0").strip()

            # 跳过空词条、短语（含空格）、无翻译
            if not word or " " in word or not translation:
                continue
            # 只保留纯英文单词
            if not all(c.isascii() and (c.isalpha() or c == "-" or c == "'") for c in word):
                continue
            if len(word) < 1:
                continue

            # BNC: 真实值 1~45000（排名，越低越常见），≥50000 是人为编码，排除
            # FRQ: COCA 词频排名，1=最常见
            # Collins: 星级 1-5，越高越重要
            try:
                bnc = int(bnc_str)
            except ValueError:
                bnc = 0

            # 排除人为编码值（>= 45000）
            if bnc >= 45000:
                bnc = 0

            entries.append((bnc, word, translation))

    print(f"   原始条目（过滤后）：{len(entries)} 个")

    # 排序：有 BNC 排名的优先（升序，1=最常见），无排名的排后面
    entries.sort(key=lambda x: (0 if 0 < x[0] < 45000 else 1, x[0]))

    # 取前 TOP_N
    selected = entries[:TOP_N]

    # 构建 {word: meaning} 字典
    result = {}
    for bnc, word, translation in selected:
        # 简化翻译
        meaning = translation
        # 替换 \n（字面量）为分号
        meaning = meaning.replace("\\n", "；")
        # 去掉词性缩写 (n. / vt. / adj. / art. 等)
        meaning = re.sub(r'\b[a-z]+\.\s*', '', meaning)
        # 只取第一义项
        meaning = meaning.split("；")[0].split(";")[0].strip()
        # 限制长度
        if len(meaning) > 100:
            meaning = meaning[:100]
        if meaning:
            result[word] = meaning

    print(f"   有效词条（含释义）：{len(result)} 个")

    # 保存 JSON
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)

    print(f"✅ 词库构建完成：{OUTPUT}")
    print(f"   词条数：{len(result)}")
    # 示例
    samples = list(result.items())[:5]
    for w, m in samples:
        print(f"   {w}: {m}")


# ========================= 词形还原规则表 =========================

LEMMA_OUTPUT = os.path.join(DATA_DIR, "lemma_rules.json")

# 不规则动词：过去式/过去分词/第三人称单数 → 原形
IRREGULAR_VERBS = {
    # 高频不规则动词
    "was": "be", "were": "be", "been": "be", "being": "be",
    "had": "have", "has": "have", "having": "have",
    "did": "do", "does": "do", "done": "do", "doing": "do",
    "said": "say", "says": "say", "saying": "say",
    "went": "go", "goes": "go", "gone": "go", "going": "go",
    "made": "make", "makes": "make", "making": "make",
    "took": "take", "takes": "take", "taken": "take", "taking": "take",
    "came": "come", "comes": "come", "coming": "come",
    "saw": "see", "sees": "see", "seen": "see", "seeing": "see",
    "knew": "know", "knows": "know", "known": "know", "knowing": "know",
    "got": "get", "gets": "get", "gotten": "get", "getting": "get",
    "gave": "give", "gives": "give", "given": "give", "giving": "give",
    "found": "find", "finds": "find", "finding": "find",
    "thought": "think", "thinks": "think", "thinking": "think",
    "told": "tell", "tells": "tell", "telling": "tell",
    "became": "become", "becomes": "become", "becoming": "become",
    "left": "leave", "leaves": "leave", "leaving": "leave",
    "felt": "feel", "feels": "feel", "feeling": "feel",
    "put": "put", "puts": "put", "putting": "put",
    "brought": "bring", "brings": "bring", "bringing": "bring",
    "began": "begin", "begins": "begin", "begun": "begin", "beginning": "begin",
    "kept": "keep", "keeps": "keep", "keeping": "keep",
    "held": "hold", "holds": "hold", "holding": "hold",
    "wrote": "write", "writes": "write", "written": "write", "writing": "write",
    "stood": "stand", "stands": "stand", "standing": "stand",
    "heard": "hear", "hears": "hear", "hearing": "hear",
    "let": "let", "lets": "let", "letting": "let",
    "meant": "mean", "means": "mean", "meaning": "mean",
    "set": "set", "sets": "set", "setting": "set",
    "met": "meet", "meets": "meet", "meeting": "meet",
    "ran": "run", "runs": "run", "running": "run",
    "paid": "pay", "pays": "pay", "paying": "pay",
    "sat": "sit", "sits": "sit", "sitting": "sit",
    "spoke": "speak", "speaks": "speak", "spoken": "speak", "speaking": "speak",
    "lay": "lie", "lies": "lie", "lain": "lie", "lying": "lie",
    "led": "lead", "leads": "lead", "leading": "lead",
    "read": "read", "reads": "read", "reading": "read",
    "grew": "grow", "grows": "grow", "grown": "grow", "growing": "grow",
    "lost": "lose", "loses": "lose", "losing": "lose",
    "fell": "fall", "falls": "fall", "fallen": "fall", "falling": "fall",
    "sent": "send", "sends": "send", "sending": "send",
    "built": "build", "builds": "build", "building": "build",
    "understood": "understand", "understands": "understand", "understanding": "understand",
    "drew": "draw", "draws": "draw", "drawn": "draw", "drawing": "draw",
    "broke": "break", "breaks": "break", "broken": "break", "breaking": "break",
    "spent": "spend", "spends": "spend", "spending": "spend",
    "cut": "cut", "cuts": "cut", "cutting": "cut",
    "rose": "rise", "rises": "rise", "risen": "rise", "rising": "rise",
    "drove": "drive", "drives": "drive", "driven": "drive", "driving": "drive",
    "bought": "buy", "buys": "buy", "buying": "buy",
    "wore": "wear", "wears": "wear", "worn": "wear", "wearing": "wear",
    "chose": "choose", "chooses": "choose", "chosen": "choose", "choosing": "choose",
    "sought": "seek", "seeks": "seek", "seeking": "seek",
    "threw": "throw", "throws": "throw", "thrown": "throw", "throwing": "throw",
    "caught": "catch", "catches": "catch", "catching": "catch",
    "dealt": "deal", "deals": "deal", "dealing": "deal",
    "won": "win", "wins": "win", "winning": "win",
    "taught": "teach", "teaches": "teach", "teaching": "teach",
    "sold": "sell", "sells": "sell", "selling": "sell",
    "bit": "bite", "bites": "bite", "bitten": "bite", "biting": "bite",
    "blew": "blow", "blows": "blow", "blown": "blow", "blowing": "blow",
    "drank": "drink", "drinks": "drink", "drunk": "drink", "drinking": "drink",
    "ate": "eat", "eats": "eat", "eaten": "eat", "eating": "eat",
    "flew": "fly", "flies": "fly", "flown": "fly", "flying": "fly",
    "forgot": "forget", "forgets": "forget", "forgotten": "forget", "forgetting": "forget",
    "froze": "freeze", "freezes": "freeze", "frozen": "freeze", "freezing": "freeze",
    "hid": "hide", "hides": "hide", "hidden": "hide", "hiding": "hide",
    "hit": "hit", "hits": "hit", "hitting": "hit",
    "hung": "hang", "hangs": "hang", "hanging": "hang",
    "hurt": "hurt", "hurts": "hurt", "hurting": "hurt",
    "laid": "lay", "lays": "lay", "laying": "lay",
    "lent": "lend", "lends": "lend", "lending": "lend",
    "lit": "light", "lights": "light", "lighting": "light",
    "proved": "prove", "proves": "prove", "proven": "prove", "proving": "prove",
    "rode": "ride", "rides": "ride", "ridden": "ride", "riding": "ride",
    "rang": "ring", "rings": "ring", "rung": "ring", "ringing": "ring",
    "sang": "sing", "sings": "sing", "sung": "sing", "singing": "sing",
    "sank": "sink", "sinks": "sink", "sunk": "sink", "sinking": "sink",
    "slept": "sleep", "sleeps": "sleep", "sleeping": "sleep",
    "slid": "slide", "slides": "slide", "sliding": "slide",
    "stole": "steal", "steals": "steal", "stolen": "steal", "stealing": "steal",
    "struck": "strike", "strikes": "strike", "striking": "strike",
    "swam": "swim", "swims": "swim", "swum": "swim", "swimming": "swim",
    "swore": "swear", "swears": "swear", "sworn": "swear", "swearing": "swear",
    "swept": "sweep", "sweeps": "sweep", "sweeping": "sweep",
    "swung": "swing", "swings": "swing", "swinging": "swing",
    "tore": "tear", "tears": "tear", "torn": "tear", "tearing": "tear",
    "woke": "wake", "wakes": "wake", "woken": "wake", "waking": "wake",
    "withdrew": "withdraw", "withdraws": "withdraw", "withdrawn": "withdraw",
    "wound": "wind", "winds": "wind", "winding": "wind",
    "bore": "bear", "bears": "bear", "borne": "bear", "bearing": "bear",
    "beat": "beat", "beats": "beat", "beaten": "beat", "beating": "beat",
    "bent": "bend", "bends": "bend", "bending": "bend",
    "bet": "bet", "bets": "bet", "betting": "bet",
    "bid": "bid", "bids": "bid", "bidding": "bid",
    "bled": "bleed", "bleeds": "bleed", "bleeding": "bleed",
    "broadcast": "broadcast", "broadcasts": "broadcast",
    "burst": "burst", "bursts": "burst", "bursting": "burst",
    "cost": "cost", "costs": "cost", "costing": "cost",
    "crept": "creep", "creeps": "creep", "creeping": "creep",
    "dug": "dig", "digs": "dig", "digging": "dig",
    "fed": "feed", "feeds": "feed", "feeding": "feed",
    "fled": "flee", "flees": "flee", "fleeing": "flee",
    "forbade": "forbid", "forbids": "forbid", "forbidden": "forbid",
    "fought": "fight", "fights": "fight", "fighting": "fight",
    "forgave": "forgive", "forgives": "forgive", "forgiven": "forgive",
    "froze": "freeze", "freezes": "freeze", "frozen": "freeze",
    "ground": "grind", "grinds": "grind", "grinding": "grind",
    "knelt": "kneel", "kneels": "kneel", "kneeling": "kneel",
    "knit": "knit", "knits": "knit", "knitting": "knit",
    "leapt": "leap", "leaps": "leap", "leaping": "leap",
    "meant": "mean", "means": "mean", "meaning": "mean",
    "mistook": "mistake", "mistakes": "mistake", "mistaken": "mistake",
    "overcame": "overcome", "overcomes": "overcome", "overcoming": "overcome",
    "overthrew": "overthrow", "overthrows": "overthrow", "overthrown": "overthrow",
    "quit": "quit", "quits": "quit", "quitting": "quit",
    "sewed": "sew", "sews": "sew", "sewn": "sew", "sewing": "sew",
    "shook": "shake", "shakes": "shake", "shaken": "shake", "shaking": "shake",
    "shone": "shine", "shines": "shine", "shining": "shine",
    "shot": "shoot", "shoots": "shoot", "shooting": "shoot",
    "shrank": "shrink", "shrinks": "shrink", "shrunk": "shrink",
    "shut": "shut", "shuts": "shut", "shutting": "shut",
    "slit": "slit", "slits": "slit", "slitting": "slit",
    "sowed": "sow", "sows": "sow", "sown": "sow", "sowing": "sow",
    "sped": "speed", "speeds": "speed", "speeding": "speed",
    "spelt": "spell", "spells": "spell", "spelling": "spell",
    "spilled": "spill", "spills": "spill", "spilling": "spill",
    "spun": "spin", "spins": "spin", "spinning": "spin",
    "spit": "spit", "spits": "spit", "spitting": "spit",
    "split": "split", "splits": "split", "splitting": "split",
    "spoilt": "spoil", "spoils": "spoil", "spoiling": "spoil",
    "spread": "spread", "spreads": "spread", "spreading": "spread",
    "sprang": "spring", "springs": "spring", "sprung": "spring",
    "stuck": "stick", "sticks": "stick", "sticking": "stick",
    "stung": "sting", "stings": "sting", "stinging": "sting",
    "stank": "stink", "stinks": "stink", "stunk": "stink",
    "strode": "stride", "strides": "stride", "stridden": "stride",
    "strove": "strive", "strives": "strive", "striven": "strive",
    "swore": "swear", "swears": "swear", "sworn": "swear",
    "swelled": "swell", "swells": "swell", "swollen": "swell",
    "trod": "tread", "treads": "tread", "trodden": "tread",
    "underwent": "undergo", "undergoes": "undergo", "undergone": "undergo",
    "undertook": "undertake", "undertakes": "undertake", "undertaken": "undertake",
    "upset": "upset", "upsets": "upset", "upsetting": "upset",
    "wept": "weep", "weeps": "weep", "weeping": "weep",
    "withheld": "withhold", "withholds": "withhold",
    "withstood": "withstand", "withstands": "withstand",
    "wrung": "wring", "wrings": "wring", "wringing": "wring",
    # 补充更多常见不规则
    "arose": "arise", "arises": "arise", "arisen": "arise",
    "awoke": "awake", "awakes": "awake", "awoken": "awake",
    "befell": "befall", "befalls": "befall", "befallen": "befall",
    "beheld": "behold", "beholds": "behold",
    "beset": "beset", "besets": "beset",
    "bespoke": "bespeak", "bespeaks": "bespeak", "bespoken": "bespeak",
    "bestrode": "bestride", "bestrides": "bestride", "bestridden": "bestride",
    "bethought": "bethink", "bethinks": "bethink",
    "bound": "bind", "binds": "bind", "binding": "bind",
    "bred": "breed", "breeds": "breed", "breeding": "breed",
    "browbeaten": "browbeat", "browbeats": "browbeat",
    "burned": "burn", "burns": "burn", "burning": "burn",
    "cast": "cast", "casts": "cast", "casting": "cast",
    "clad": "clothe", "clothes": "clothe", "clothing": "clothe",
    "cleaved": "cleave", "cleaves": "cleave",
    "clung": "cling", "clings": "cling", "clinging": "cling",
    "clothed": "clothe", "clothes": "clothe",
    "contend": "contend", "contends": "contend",
    "crept": "creep", "creeps": "creep",
    "dealt": "deal", "deals": "deal",
    "dreamt": "dream", "dreams": "dream", "dreaming": "dream",
    "dwelt": "dwell", "dwells": "dwell", "dwelling": "dwell",
    "flung": "fling", "flings": "fling", "flinging": "fling",
    "forbore": "forbear", "forbears": "forbear", "forborne": "forbear",
    "forecast": "forecast", "forecasts": "forecast",
    "foresaw": "foresee", "foresees": "foresee", "foreseen": "foresee",
    "foretold": "foretell", "foretells": "foretell",
    "forsook": "forsake", "forsakes": "forsake", "forsaken": "forsake",
    "hamstrung": "hamstring", "hamstrings": "hamstring",
    "heaved": "heave", "heaves": "heave",
    "hewn": "hew", "hews": "hew", "hewed": "hew",
    "inlaid": "inlay", "inlays": "inlay",
    "input": "input", "inputs": "input",
    "inset": "inset", "insets": "inset",
    "interwove": "interweave", "interweaves": "interweave", "interwoven": "interweave",
    "kept": "keep", "keeps": "keep",
    "knelt": "kneel", "kneels": "kneel",
    "leaned": "lean", "leans": "lean", "leant": "lean",
    "leaped": "leap", "leaps": "leap",
    "learned": "learn", "learns": "learn", "learnt": "learn",
    "misled": "mislead", "misleads": "mislead",
    "misread": "misread", "misreads": "misread",
    "misspelt": "misspell", "misspells": "misspell",
    "mowed": "mow", "mows": "mow", "mown": "mow",
    "outdid": "outdo", "outdoes": "outdo", "outdone": "outdo",
    "outgrew": "outgrow", "outgrows": "outgrow", "outgrown": "outgrow",
    "outran": "outrun", "outruns": "outrun",
    "outsold": "outsell", "outsells": "outsell",
    "overate": "overeat", "overeats": "overeat", "overeaten": "overeat",
    "overfed": "overfeed", "overfeeds": "overfeed",
    "overhung": "overhang", "overhangs": "overhang",
    "overheard": "overhear", "overhears": "overhear",
    "overlaid": "overlay", "overlays": "overlay",
    "overpaid": "overpay", "overpays": "overpay",
    "overrode": "override", "overrides": "override", "overridden": "override",
    "overran": "overrun", "overruns": "overrun",
    "oversaw": "oversee", "oversees": "oversee", "overseen": "oversee",
    "overshot": "overshoot", "overshoots": "overshoot",
    "overslept": "oversleep", "oversleeps": "oversleep",
    "overtook": "overtake", "overtakes": "overtake", "overtaken": "overtake",
    "partook": "partake", "partakes": "partake", "partaken": "partake",
    "pleaded": "plead", "pleads": "plead",
    "preset": "preset", "presets": "preset",
    "proofread": "proofread", "proofreads": "proofread",
    "rebuilt": "rebuild", "rebuilds": "rebuild",
    "recast": "recast", "recasts": "recast",
    "redid": "redo", "redoes": "redo", "redone": "redo",
    "relaid": "relay", "relays": "relay",
    "remade": "remake", "remakes": "remake",
    "rent": "rend", "rends": "rend", "rent": "rend",
    "repaid": "repay", "repays": "repay",
    "reran": "rerun", "reruns": "rerun",
    "resold": "resell", "resells": "resell",
    "reset": "reset", "resets": "reset",
    "retold": "retell", "retells": "retell",
    "rewrote": "rewrite", "rewrites": "rewrite", "rewritten": "rewrite",
    "rid": "rid", "rids": "rid",
    "rived": "rive", "rives": "rive", "riven": "rive",
    "sawed": "saw", "saws": "saw", "sawn": "saw",
    "seethed": "seethe", "seethes": "seethe",
    "shed": "shed", "sheds": "shed",
    "sheared": "shear", "shears": "shear", "shorn": "shear",
    "shod": "shoe", "shoes": "shoe",
    "shred": "shred", "shreds": "shred",
    "slain": "slay", "slays": "slay", "slew": "slay",
    "slunk": "slink", "slinks": "slink",
    "smelt": "smell", "smells": "smell",
    "smote": "smite", "smites": "smite", "smitten": "smite",
    "snuck": "sneak", "sneaks": "sneak",
    "spat": "spit", "spits": "spit",
    "spoiled": "spoil", "spoils": "spoil",
    "sprang": "spring", "springs": "spring",
    "staved": "stave", "staves": "stave",
    "strewed": "strew", "strews": "strew", "strewn": "strew",
    "stridden": "stride", "strides": "stride",
    "strung": "string", "strings": "string",
    "sunken": "sink", "sinks": "sink",
    "swelled": "swell", "swells": "swell",
    "throve": "thrive", "thrives": "thrive", "thriven": "thrive",
    "thrust": "thrust", "thrusts": "thrust",
    "unbent": "unbend", "unbends": "unbend",
    "unbound": "unbind", "unbinds": "unbind",
    "underbid": "underbid", "underbids": "underbid",
    "undercut": "undercut", "undercuts": "undercut",
    "underfed": "underfeed", "underfeeds": "underfeed",
    "underlay": "underlie", "underlies": "underlie", "underlain": "underlie",
    "underpaid": "underpay", "underpays": "underpay",
    "undersold": "undersell", "undersells": "undersell",
    "undertaken": "undertake", "undertakes": "undertake",
    "underwritten": "underwrite", "underwrites": "underwrite", "underwrote": "underwrite",
    "undid": "undo", "undoes": "undo", "undone": "undo",
    "unfroze": "unfreeze", "unfreezes": "unfreeze", "unfrozen": "unfreeze",
    "unhung": "unhang", "unhangs": "unhang",
    "unknit": "unknit", "unknits": "unknit",
    "unlaid": "unlay", "unlays": "unlay",
    "unmade": "unmake", "unmakes": "unmake",
    "unslung": "unsling", "unslings": "unsling",
    "unspoke": "unspeak", "unspeaks": "unspeak", "unspoken": "unspeak",
    "unstrung": "unstring", "unstrings": "unstring",
    "unstuck": "unstick", "unsticks": "unstick",
    "unwound": "unwind", "unwinds": "unwind",
    "upheld": "uphold", "upholds": "uphold",
    "uprose": "uprise", "uprises": "uprise", "uprisen": "uprise",
    "waylaid": "waylay", "waylays": "waylay",
    "withdrew": "withdraw", "withdraws": "withdraw",
    "wreathed": "wreathe", "wreathes": "wreathe",
    "wrote": "write", "writes": "write",
    "zinc": "zinc", "zincs": "zinc",
}

# 不规则名词复数 → 单数
IRREGULAR_PLURALS = {
    "children": "child",
    "mice": "mouse",
    "feet": "foot",
    "teeth": "tooth",
    "geese": "goose",
    "men": "man",
    "women": "woman",
    "oxen": "ox",
    "lice": "louse",
    "people": "person",
    "phenomena": "phenomenon",
    "criteria": "criterion",
    "data": "datum",
    "media": "medium",
    "bacteria": "bacterium",
    "analyses": "analysis",
    "theses": "thesis",
    "hypotheses": "hypothesis",
    "crises": "crisis",
    "axes": "axis",
    "syntheses": "synthesis",
    "diagnoses": "diagnosis",
    "parentheses": "parenthesis",
    "emphases": "emphasis",
    "foci": "focus",
    "fungi": "fungus",
    "nuclei": "nucleus",
    "stimuli": "stimulus",
    "syllabi": "syllabus",
    "alumni": "alumnus",
    "radii": "radius",
    "cacti": "cactus",
    "larvae": "larva",
    "antennae": "antenna",
    "formulae": "formula",
    "vertebrae": "vertebra",
    "algae": "alga",
    "indices": "index",
    "appendices": "appendix",
    "matrices": "matrix",
    "vertices": "vertex",
    "codices": "codex",
    "sheep": "sheep",
    "deer": "deer",
    "fish": "fish",
    "species": "species",
    "series": "series",
    "means": "means",
    "offspring": "offspring",
    "aircraft": "aircraft",
    "salmon": "salmon",
    "trout": "trout",
    "moose": "moose",
    "swine": "swine",
    "knives": "knife",
    "lives": "life",
    "wives": "wife",
    "wolves": "wolf",
    "shelves": "shelf",
    "elves": "elf",
    "halves": "half",
    "selves": "self",
    "thieves": "thief",
    "leaves": "leaf",
    "loaves": "loaf",
    "scarves": "scarf",
    "hooves": "hoof",
    "dwarves": "dwarf",
}

# 不规则比较级/最高级 → 原级
IRREGULAR_COMPARATIVES = {
    "better": "good",
    "best": "good",
    "worse": "bad",
    "worst": "bad",
    "more": "much",
    "most": "much",
    "less": "little",
    "least": "little",
    "farther": "far",
    "farthest": "far",
    "further": "far",
    "furthest": "far",
    "elder": "old",
    "eldest": "old",
    "older": "old",
    "oldest": "old",
}


def generate_lemma_rules():
    """生成词形还原规则表，输出 data/lemma_rules.json"""
    rules = {}
    rules.update(IRREGULAR_VERBS)
    rules.update(IRREGULAR_PLURALS)
    rules.update(IRREGULAR_COMPARATIVES)

    # 额外修正：去掉误添加的同形异义词（key == value 的不需要）
    rules = {k: v for k, v in rules.items() if k != v}

    # 按 key 排序输出
    sorted_rules = dict(sorted(rules.items()))

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LEMMA_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(sorted_rules, f, ensure_ascii=False, indent=2)

    print(f"✅ 词形还原规则表已生成：{LEMMA_OUTPUT}")
    print(f"   不规则映射：{len(sorted_rules)} 条")
    # 示例
    samples = list(sorted_rules.items())[:10]
    for w, l in samples:
        print(f"   {w} → {l}")


if __name__ == "__main__":
    if LEMMA_ONLY:
        generate_lemma_rules()
        sys.exit(0)

    if not os.path.exists(CSV_PATH) or FORCE:
        download_csv()
    build()
