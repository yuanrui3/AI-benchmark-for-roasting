# Rating instructions · 评分说明

Run: `pilot` (the full Claude-side run, 11 Nov 2026). **Rated in Chinese only** (owner's decision, 9 Nov 2026). There are two pools; the pages also offer an English track, leave it alone. 中文说明在下面。

The earlier pool `runs/pilot-or/rate/` (OpenRouter models, 10 targets) stays valid; the owner's 100 votes on it are in `runs/pilot-or/votes/`.

## English (for context)

You will see pairs of short roasts of the same thing and pick the one that hits harder. Both were written by AI models. The first time a target comes up, the page asks how well you know it (know it well / heard of it / no idea, keys 7 / 8 / 9) and unlocks voting once you answer. The Chinese track is the one being rated; if you only read English, skip this round.

Two pools, each its own page and its own export:

1. **Framing pool** `runs/pilot/rate-frame/index.html` (zip: `rate-frame-pilot.zip`): 100 Chinese pairs, 10 of them checks. Every real pair is the same model (Opus 5.5) on the same target, once told to roast the thing and once told to roast the people doing it. This is the test of "a roast is about someone doing something". Do this one first; it is one sitting.
2. **Main pool** `runs/pilot/rate/index.html` (zip: `rate-pilot.zip`): 250 Chinese pairs, 25 of them checks, across four Opus 5.5 prompts (plain, with the fact sheet, the house-style skill, the people framing) and a bland control. Stop whenever you like; progress is saved.

## 中文

**这是什么。** 你会看到一对一对的短段子，吐槽的都是同一个东西：一种字体、一门编程语言、一种水果、一座城市、一双鞋。选出更狠的那段——更好笑、更尖锐、更贴着这个东西本身。两段都是 AI 写的，你不知道是谁写的。随时可以停。

**两个池子，先做第一个。**

1. **框架池** `runs/pilot/rate-frame/index.html`（压缩包 `rate-frame-pilot.zip`）：100 对，其中 10 对是检查题。每一对都是同一个模型、同一个对象，一段是“吐槽这个东西”，一段是“吐槽干这件事的人”。大概半小时，一次做完最好。
2. **主池** `runs/pilot/rate/index.html`（压缩包 `rate-pilot.zip`）：250 对，其中 25 对是检查题，几种不同写法混在一起。做多少算多少，进度会自动存。

**打开页面。** 双击 `index.html`，任何浏览器都行，不用联网。收到的是压缩包就先解压，再打开里面的 `index.html`。两个池子的进度和导出文件互不干扰。

**评分人卡片。** 填个名字或网名（只用来给导出的文件命名，两个池子用同一个名字）；语言选 **中文**（English 这轮不评）；会的语言；平时觉得什么好笑；对黑色幽默的接受度 1–5；有没有不想看到的内容；最后四道口味题按真实感受选。

**先答熟不熟。** 每个对象第一次出现时，页面会先问你对它熟不熟：很熟 / 听说过 / 不知道（快捷键 7 / 8 / 9），答完才能投票。照实答，这个答案用来区分“懂行的人”和“路人”各自觉得什么好笑，不影响你的票。

**怎么判。** 两段都读完再选。旁边有这个对象的事实清单：编造事实的段子该输；自己解释笑点的段子该输。客气不加分，写得长也不加分。

- `←` 左边赢 · `→` 右边赢
- `B` 都不行（哪段都笑不出来）
- `S` 跳过（不了解这个东西，判不了——比如完全不懂 PHP 就跳过 PHP）
- `1` / `2` 标记左 / 右那段“过线了”（标完照样要选）
- `U` 撤销 · `E` 导出

有些对子是检查题，其中一段被故意改坏了，按真实感受评就行。所有人都导出之前，别跟其他评分人讨论具体的对子，也别猜是哪个模型写的。

**结束。** 点“导出”，浏览器会下载一个 JSON 文件，发回给我。进度会自动存在你的浏览器里，关掉页面以后用同一个浏览器、同一个名字打开，能接着评。

**整理者。** 框架池的导出放进 `runs/pilot/votes-frame/`，运行 `uv run python frame_test.py --run pilot`；主池的导出放进 `runs/pilot/votes/`，运行 `uv run python analyze.py --run pilot`。
