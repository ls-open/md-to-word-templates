#!/usr/bin/env python3
"""模板库的唯一判据：每份模板都得真能导出，索引也得与头部一致。

    python3 scripts/check.py            # CI 跑这个
    python3 scripts/check.py --strict   # 连「样例没覆盖到的样式行」也算失败

判据只有三条，全部确定性：索引一致、导出退出码 0（预检/对账/审计全开）、
样例覆盖到它声明的每一条样式。覆盖率默认只报告不拦——拦下来会逼人为凑覆盖去改稿。
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_index as bi  # noqa: E402

ROOT = bi.ROOT
OUT = ROOT / "out"

# 样式 → 它的样例里必须出现的结构。按语义分组，中英词表都收，避免第二份真相源走样。
_GROUPS = {
    "table": ["表格", "表头", "紧凑", "表格题注", "表名", "表题", "表注",
              "Compact", "Table Caption", "Table Note"],
    "image": ["图", "图片题注", "图名", "图题", "Figure", "Captioned Figure", "Image Caption"],
    "abstract": ["摘要", "摘要标题", "关键词", "Abstract", "Abstract Title", "Keywords"],
    "toc": ["目录标题", "目录一级", "目录二级", "目录三级", "目录四级", "目录五级",
            "TOC Heading", "TOC 1", "TOC 2", "TOC 3", "TOC 4", "TOC 5"],
    "quote": ["引用块", "Block Text", "Block Quote"],
    "code": ["代码", "SourceCode", "Code"],
    "footnote": ["脚注", "Footnote", "Footnote Text"],
    "bib": ["参考文献", "参考文献标题", "Bibliography", "References Title", "Bibliography Title"],
    "section": ["页眉", "页脚", "页眉内容", "页脚内容", "Header", "Footer"],
    "title": ["文档标题", "论文标题", "副标题", "作者", "日期", "Title", "Subtitle", "Author", "Date"],
    "h1": ["一级标题", "Heading 1"], "h2": ["二级标题", "Heading 2"],
    "h3": ["三级标题", "Heading 3"], "h4": ["四级标题", "Heading 4"],
    "h5": ["五级标题", "Heading 5"], "h6": ["六级标题", "Heading 6"],
}
JUDGEABLE = {name: group for group, names in _GROUPS.items() for name in names}
# 正文类样式：任何稿子都有，无需在样例里找证据
ALWAYS = {"正文", "首段", "普通", "Body Text", "First Paragraph", "Normal"}


def declared_styles(format_path: Path) -> list[str]:
    names = []
    for line in format_path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("#") or "：" not in line and ":" not in line:
            continue
        name = re.split(r"[：:]", line, maxsplit=1)[0].strip()
        if name in JUDGEABLE or name in ALWAYS:
            names.append(name)
    return names


def sample_structures(text: str) -> set[str]:
    flags: set[str] = set()
    if "{{< toc" in text:
        flags.add("toc")
    if "{{< section" in text:
        flags.add("section")
    if "{{< pagebreak" in text:
        flags.add("section")
    if re.search(r"^\|.*\|", text, re.M):
        flags.add("table")
    if re.search(r"^!\[", text, re.M):
        flags.add("image")
    if re.search(r"%%.*(文档标题|论文标题|副标题|作者|日期)", text):
        flags.add("title")
    if re.search(r"%%.*(摘要|关键词)|^(abstract|keywords):", text, re.M | re.I):
        flags.add("abstract")
    if re.search(r"^```", text, re.M):
        flags.add("code")
    if re.search(r"^> ", text, re.M):
        flags.add("quote")
    if re.search(r"\[\^", text):
        flags.add("footnote")
    if re.search(r"^bibliography:", text, re.M) or "%% 参考文献标题" in text:
        flags.add("bib")
    for hashes in re.findall(r"^(#{1,6}) ", text, re.M):
        flags.add(f"h{len(hashes)}")
    return flags


def contract_gaps(format_text: str, sample_text: str, flags: set[str]) -> list[str]:
    """format 声明了、但只能靠稿件里的写法才成立的那几条。

    样式行管"长什么样"，这一半管"结构怎么搭"：目录收几级、章标题在哪、页眉从哪取章名。
    缺了它们导出不报错，只是悄悄不生效——所以单独点名。
    """
    gaps = []
    depths = re.findall(r"^目录([一二三四五])级[：:]", format_text, re.M)
    depth = max("一二三四五".index(d) + 1 for d in depths) if depths else 0
    toc = re.search(r"\{\{<\s*toc\s*(\d+)?", sample_text)
    if depth and not toc:
        gaps.append(f"声明了目录{depth}级，样稿里却没有 {{{{< toc >}}}}")
    elif depth and toc:
        want = int(toc.group(1) or 3)
        if want < depth:
            gaps.append(f"声明了目录{depth}级，样稿只写 {{{{< toc {want} >}}}}，那一级永远收不到")
    if re.search(r"页眉内容[：:].*样式标题", format_text) and "h1" not in flags:
        gaps.append("页眉按一级标题取章名，样稿里却没有 # 章标题，页眉会是空的")
    if re.search(r"^\s*chapters:\s*true", sample_text, re.M) and "h1" not in flags:
        gaps.append("开了按章编号，样稿里却没有 # 章标题，公式会编成 (0-1)")
    return gaps


def export(template: Path) -> tuple[bool, str]:
    OUT.mkdir(exist_ok=True)
    target = OUT / f"{template.name}.docx"
    cmd = [sys.executable, "-m", "md_to_word", "sample.md", "-f", "format.txt", "-o", str(target)]
    if (template / "cover.docx").is_file():
        cmd[3:3] = ["--base-template", "cover.docx"]
        for readme in (template / "README.md",):
            m = re.search(r"^cover_sections:\s*(\d+)", readme.read_text(encoding="utf-8"), re.M)
            if m:
                cmd += ["--cover-sections", m.group(1)]
    proc = subprocess.run(cmd, cwd=template, capture_output=True, text=True)
    if proc.returncode == 0 and target.is_file() and target.stat().st_size > 0:
        return True, ""
    tail = (proc.stderr or proc.stdout).strip().splitlines()[-12:]
    return False, "\n".join("      " + line for line in tail)


def main(argv: list[str]) -> int:
    strict = "--strict" in argv
    entries, errors = bi.load()
    for err in errors:
        print(f"❌ {err}", file=sys.stderr)
    if errors:
        return 1

    stale = [n for n, want in (("index.json", bi.render_json(entries)), ("INDEX.md", bi.render_md(entries)))
             if not (ROOT / n).is_file() or (ROOT / n).read_text(encoding="utf-8") != want]
    if stale:
        print(f"❌ {'、'.join(stale)} 与模板头部不一致：请运行 python3 scripts/build_index.py",
              file=sys.stderr)
        return 1

    failed, uncovered_total = 0, 0
    for entry in entries:
        template = ROOT / entry["path"]
        format_text = (template / "format.txt").read_text(encoding="utf-8")
        sample_text = (template / "sample.md").read_text(encoding="utf-8")
        declared = declared_styles(template / "format.txt")
        structures = sample_structures(sample_text)
        gaps = contract_gaps(format_text, sample_text, structures)
        uncovered = [n for n in declared if n not in ALWAYS and JUDGEABLE[n] not in structures]
        uncovered_total += len(uncovered)

        ok, detail = export(template)
        print(f"{'✓' if ok else '❌'} {entry['id']}  样式 {len(declared)} 条  未覆盖 {len(uncovered)} 条")
        if detail:
            print(detail)
        if uncovered:
            print(f"      未覆盖：{'、'.join(uncovered)}")
        for gap in gaps:
            print(f"      结构缺项：{gap}")
        uncovered_total += len(gaps)
        failed += 0 if ok else 1

    print()
    if failed:
        print(f"❌ {failed} 份模板没通过导出。上面的最后几行就是失败原因，改到能导出为止。", file=sys.stderr)
        return 1
    if uncovered_total and strict:
        print(f"❌ 有 {uncovered_total} 条声明的样式在样例里找不到证据（--strict）。", file=sys.stderr)
        return 1
    print(f"✓ {len(entries)} 份模板全部导出通过；未覆盖样式 {uncovered_total} 条（不拦）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
