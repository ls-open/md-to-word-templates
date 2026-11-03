#!/usr/bin/env python3
"""把每份模板 README 的 YAML 头部汇总成 index.json 与 INDEX.md。

README 头部是唯一真相源，这两个文件是派生物：只由本脚本写，不手改。

    python3 scripts/build_index.py            # 重写两个派生物
    python3 scripts/build_index.py --check    # 只比对，不一致退出 1（CI 用）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
REPO = "ls-open/md-to-word-templates"
RAW = f"https://raw.githubusercontent.com/{REPO}/main/templates"

KINDS = {"thesis", "journal", "report", "proposal"}
DEGREES = {"", "bachelor", "master", "doctor"}
STATES = {"current", "deprecated"}
REQUIRED = ("id", "name", "org", "kind", "degree", "spec_year", "lang",
            "state", "source", "updated", "verified_with", "maintainers")


def front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path} 缺少 YAML 头部（第一行必须是 ---）")
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError(f"{path} 的 YAML 头部没有结束标记 ---")
    return yaml.safe_load(text[4:end]) or {}


def load() -> tuple[list[dict], list[str]]:
    """读出全部模板并校验；返回 (按主键排序的条目, 错误列表)。"""
    entries, errors = [], []
    for readme in sorted(TEMPLATES.glob("*/README.md")):
        folder = readme.parent
        try:
            meta = front_matter(readme)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        entry = {k: meta.get(k, "") for k in REQUIRED}
        entry["unit"] = meta.get("unit") or ""
        entry["supersedes"] = meta.get("supersedes") or ""
        entry["aliases"] = meta.get("aliases") or []
        entry["cover_sections"] = int(meta.get("cover_sections") or 0)
        entry["id"] = entry["id"] or folder.name
        entry["updated"] = str(entry["updated"])   # YAML 会把 2026-11-03 读成 date
        entry["path"] = f"templates/{folder.name}"
        entry["raw_format"] = f"{RAW}/{folder.name}/format.txt"
        entry["raw_sample"] = f"{RAW}/{folder.name}/sample.md"

        if entry["id"] != folder.name:
            errors.append(f"{folder.name}: id 是 {entry['id']!r}，与目录名不一致")
        for key in REQUIRED:
            if key in ("degree",) or key in ("maintainers",):
                continue
            if not str(entry[key]).strip():
                errors.append(f"{folder.name}: 头部缺少 {key}")
        if entry["kind"] not in KINDS:
            errors.append(f"{folder.name}: kind={entry['kind']!r} 不在 {sorted(KINDS)}")
        if entry["degree"] not in DEGREES:
            errors.append(f"{folder.name}: degree={entry['degree']!r} 不在 {sorted(DEGREES)}")
        if entry["state"] not in STATES:
            errors.append(f"{folder.name}: state={entry['state']!r} 不在 {sorted(STATES)}")
        if entry["cover_sections"] and not (folder / "cover.docx").is_file():
            errors.append(
                f"{folder.name}: 声明了 cover_sections={entry['cover_sections']}，"
                f"但目录里没有 cover.docx（学校模板不入库，但要放在本地才验得了）"
            )
        if not isinstance(entry["maintainers"], list) or not entry["maintainers"]:
            errors.append(f"{folder.name}: maintainers 必须是非空列表")
        for needed in ("format.txt", "sample.md"):
            if not (folder / needed).is_file():
                errors.append(f"{folder.name}: 缺 {needed}")
        entries.append(entry)

    # 主键唯一：(学校, 学院, 类型, 层次, 规范年份)
    seen: dict[tuple, str] = {}
    for e in entries:
        key = (e["org"], e["unit"], e["kind"], e["degree"], str(e["spec_year"]))
        if key in seen:
            errors.append(
                f"主键重复：{seen[key]} 与 {e['id']} 都声明 {key}。"
                f"要么改现有那份，要么在头部写 supersedes: {seen[key]}"
            )
        else:
            seen[key] = e["id"]
    known = {e["id"] for e in entries}
    for e in entries:
        if e["supersedes"] and e["supersedes"] not in known:
            errors.append(f"{e['id']}: supersedes 指向不存在的 {e['supersedes']!r}")
        if e["supersedes"] == e["id"]:
            errors.append(f"{e['id']}: supersedes 不能指向自己")

    entries.sort(key=lambda e: (e["org"], e["unit"], e["kind"], e["degree"], -int(e["spec_year"])))
    return entries, errors


def render_json(entries: list[dict]) -> str:
    return json.dumps(entries, ensure_ascii=False, indent=2) + "\n"


def render_md(entries: list[dict]) -> str:
    lines = [
        "# 模板索引",
        "",
        "> 本文件由 `scripts/build_index.py` 从各模板 README 的头部生成，**不要手改**。",
        "> 机器可读版见 [index.json](index.json)。",
        "",
        "## 怎么取一份模板",
        "",
        "```bash",
        f"curl -O {RAW}/<模板目录>/format.txt",
        f"curl -O {RAW}/<模板目录>/sample.md",
        "```",
        "",
        "`sample.md` 与 `format.txt` 一起读：前者是稿件的结构范例，后者是样式参数，条目一一对应。",
        "",
    ]
    org = None
    for e in entries:
        if e["org"] != org:
            org = e["org"]
            lines += [f"## {org}", "",
                      "| 模板 | 单位 | 类型 / 层次 | 规范年份 | 状态 | 维护者 | 目录 |",
                      "|:--|:--|:--|:--|:--|:--|:--|"]
        state = e["state"] if e["state"] == "current" else f"deprecated（{e['supersedes'] or '已被取代'}）"
        lines.append(
            f"| {e['name']} | {e['unit'] or '全校通用'} | {e['kind']} / {e['degree'] or '—'} "
            f"| {e['spec_year']} | {state} | {', '.join(e['maintainers'])} | [{e['id']}]({e['path']}/) |"
        )
    return "\n".join(lines) + "\n"


def write(entries: list[dict]) -> None:
    (ROOT / "index.json").write_text(render_json(entries), encoding="utf-8")
    (ROOT / "INDEX.md").write_text(render_md(entries), encoding="utf-8")


def main(argv: list[str]) -> int:
    entries, errors = load()
    if errors:
        for err in errors:
            print(f"❌ {err}", file=sys.stderr)
        return 1
    if "--check" not in argv:
        write(entries)
        print(f"✓ 已写入 index.json 与 INDEX.md（{len(entries)} 份模板）")
        return 0
    stale = [
        name for name, want in (("index.json", render_json(entries)), ("INDEX.md", render_md(entries)))
        if not (ROOT / name).is_file() or (ROOT / name).read_text(encoding="utf-8") != want
    ]
    if stale:
        print(f"❌ {'、'.join(stale)} 与模板头部不一致，请运行 python3 scripts/build_index.py", file=sys.stderr)
        return 1
    print(f"✓ 索引一致（{len(entries)} 份模板）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
