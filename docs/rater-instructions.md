# Rating instructions · 评分说明

Run: `pilot-or` (ten targets, two language tracks, about 100 pairs per track). English first, 中文在下面。

## English

**What this is.** You will see pairs of short roasts of the same thing: a font, a programming language, a fruit, a city, a shoe. Pick the one that hits harder: funnier, sharper, more specific to that thing. Both were written by AI models; you will not know which. It takes about 30 minutes. Stop whenever you like.

**Open the page.** Double-click `runs/pilot-or/rate/index.html`. It works in any browser without internet. If you received a zip, unzip it first and open `index.html` inside. (If the local server is up: http://localhost:8765/runs/pilot-or/rate/index.html.)

**Rater card.** Name or handle (it only names your export file), language track (English or 中文: pick the one you read comedy in; you may do both, one at a time, exporting each), languages you speak, what you find funny, dark-humor tolerance 1–5, anything off-limits.

**How to judge.** Read both roasts. The target's fact sheet is shown beside them: a roast that invents facts should lose. A roast that explains its own joke should lose. Politeness is not a virtue here, and neither is length.

- `←` left wins · `→` right wins
- `B` both bad (neither would get a laugh)
- `S` skip (you do not know the thing well enough to judge)
- `1` / `2` flag the left / right roast as crossing a line (then still vote)
- `U` undo · `E` export

Some pairs are checks in which one version was deliberately damaged. Just rate honestly. Do not discuss pairs with other raters until everyone has exported, and do not try to guess which model wrote what.

**Finish.** Click Export. A JSON file downloads; send it back to me. Progress autosaves in your browser, so you can close the page and continue later in the same browser under the same name.

**Owner.** Drop the files into `runs/pilot-or/votes/` and run `uv run python analyze.py --run pilot-or`.

## 中文

**这是什么。** 你会看到一对一对的短段子，吐槽的都是同一个东西：一种字体、一门编程语言、一种水果、一座城市、一双鞋。选出更狠的那段——更好笑、更尖锐、更贴着这个东西本身。两段都是 AI 写的，你不知道是谁写的。大概半小时，随时可以停。

**打开页面。** 双击 `runs/pilot-or/rate/index.html`，任何浏览器都行，不用联网。收到的是压缩包就先解压，再打开里面的 `index.html`。（本地服务开着的话也可以访问 http://localhost:8765/runs/pilot-or/rate/index.html。）

**评分人卡片。** 填个名字或网名（只用来给导出的文件命名）；选语言（English 或 中文，选你平时看段子的那种；两种都想评也行，一次一种，各导出一次）；会的语言；平时觉得什么好笑；对黑色幽默的接受度 1–5；有没有不想看到的内容。

**怎么判。** 两段都读完再选。旁边有这个对象的事实清单：编造事实的段子该输；自己解释笑点的段子该输。客气不加分，写得长也不加分。

- `←` 左边赢 · `→` 右边赢
- `B` 都不行（哪段都笑不出来）
- `S` 跳过（不了解这个东西，判不了）
- `1` / `2` 标记左 / 右那段“过线了”（标完照样要选）
- `U` 撤销 · `E` 导出

有些对子是检查题，其中一段被故意改坏了，按真实感受评就行。所有人都导出之前，别跟其他评分人讨论具体的对子，也别猜是哪个模型写的。

**结束。** 点“导出”，浏览器会下载一个 JSON 文件，发回给我。进度会自动存在你的浏览器里，关掉页面以后用同一个浏览器、同一个名字打开，能接着评。

**整理者。** 把文件放进 `runs/pilot-or/votes/`，运行 `uv run python analyze.py --run pilot-or`。
