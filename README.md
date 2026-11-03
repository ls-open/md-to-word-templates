# md-to-word 模板库

各学校、各期刊的 `format.txt`，配一份**最小样稿** `sample.md`。两个文件一起读，
人和 AI 都能照着把 Markdown 稿件排成对方要的 Word，不用再从一份 `.docx` 里反推。

引擎在 [ls-open/md-to-word](https://github.com/ls-open/md-to-word)。

**Agent 接入**：检索与使用写在同一份 [AGENTS.md](AGENTS.md) 里——怎么从 `index.json` 选、两个文件
怎么一起用、什么时候不该用。人往下看即可。

## 取一份模板

看 [INDEX.md](INDEX.md) 找到你需要的目录，取两个文件：

```bash
curl -O https://raw.githubusercontent.com/ls-open/md-to-word-templates/main/templates/<目录>/format.txt
curl -O https://raw.githubusercontent.com/ls-open/md-to-word-templates/main/templates/<目录>/sample.md
```

```bash
md-to-word 你的稿件.md -f format.txt -o 你的稿件.docx
```

没有你要的学校？先用引擎内置预设导一版，或者用 `md-to-word-template 参考.docx -o format.txt`
从学校的参考文件反推草稿，核对完再提上来——下一个人就不用再走一遍。

## 库里放什么

| 放 | 不放 |
|:--|:--|
| `format.txt`：样式参数，来自公开的规范文件 | 学校或期刊的 `.docx` / `.dotx` 原件（版权在对方） |
| `sample.md`：**你自己写的**最小样稿 | 别人的论文、摘要原文 |
| `README.md`：头部元数据 + 人话说明 | 只有几行差异、没有说明的补丁 |
| 可选 `references.bib`、`figures/`：样稿要用到就带上 | 二进制之外的大文件 |

`format.txt` 是参数事实，不构成对来源文件的复制；`sample.md` 必须自己写。这条不接受例外。

## 一份模板长什么样

```
templates/cn-generic-thesis-master/
├── README.md      # 头部 YAML 是元数据，正文写适用范围与已知限制
├── format.txt     # ← 引擎读
├── sample.md      # ← 引擎读，覆盖 format.txt 声明的每一条样式
└── figures/       # 样稿里的图，可选
```

头部字段（`scripts/build_index.py` 会校验）：

| 字段 | 说明 |
|:--|:--|
| `id` | 与目录名一致 |
| `name` | 给人看的名字 |
| `org` / `unit` | 学校（或期刊）/ 学院；`unit` 留空 = 全校通用 |
| `kind` / `degree` | `thesis` `journal` `report` `proposal` / `bachelor` `master` `doctor`（期刊留空） |
| `spec_year` | 规范年份。换版就**新增**一份，旧份不删 |
| `state` | `current` 或 `deprecated` |
| `supersedes` | 这份取代了谁（新版本或纠错时填） |
| `source` | 来源说明；`README.md` 里还要有可点的公开链接 |
| `maintainers` | GitHub 用户名，谁改谁负责 |
| `updated` / `verified_with` | 最后更新日期 / 在哪个引擎版本上验过 |

## 提交

见 [CONTRIBUTING.md](CONTRIBUTING.md)。一句话：只改 `format.txt` 和 `sample.md` 也能提，
但必须能过 `python3 scripts/check.py`，且改动要有公开来源。

## 会不会过期

模板坏在这里，两头都会红：

- **本库 CI**：每次 PR 跑一遍导出（预检、对账、审计全开）；每周二、五另跑一次对着引擎 `main` 的检查。
- **引擎仓库**：定时拉本库跑同一套检查。引擎改动把模板改坏，红在改了引擎的那一边。

CI 还会把每份模板渲染出的 `.docx` 传成构建产物——你不用装 Python，下载打开看两页就能审。
