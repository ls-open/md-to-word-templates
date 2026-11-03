# 给 Agent 的检索契约

这个库只提供一样东西：**一份 `format.txt`（样式参数）+ 一份 `sample.md`（结构范例）**。
引擎是 [md-to-word](https://github.com/ls-open/md-to-word)。人看 [README.md](README.md)，
这里只讲"怎么找到、怎么用、什么时候别用"。

## 一、怎么找

```bash
curl -s https://raw.githubusercontent.com/ls-open/md-to-word-templates/main/index.json
```

`index.json` 是唯一入口，每条有：`id` `name` `org` `unit` `kind` `degree` `spec_year` `lang`
`state` `aliases` `raw_format` `raw_sample` `cover_sections` `maintainers` `updated`。

选哪份，按这个顺序判，**不要自己猜**：

1. `state` 必须是 `current`（`deprecated` 的只作历史参考）。
2. `degree` 必须对得上（`bachelor` / `master` / `doctor`；期刊留空）。
3. **`unit` 非空优先于空**：学院级规则压过学校级。
4. 同一层里 `spec_year` 取最大的那个。
5. 还找不到，就用 `aliases` 再匹配一次（学院改过名）。

找到后取两个文件，用 `raw_format` 与 `raw_sample` 两个字段里的 URL：

```bash
curl -O <raw_format>     # format.txt
curl -O <raw_sample>     # sample.md
md-to-word 稿件.md -f format.txt -o 稿件.docx
```

## 二、怎么用（三条硬规矩）

1. **两个文件一起读，缺一半就实现不了。** `format.txt` 决定"长什么样"，`sample.md` 决定"结构怎么搭"
   ——分节标记、目录域、按章编号、页眉靠一级标题取章名，这些只有稿件里才表达得了。
   改稿件时照着 `sample.md` 的结构抄，别自创。
2. **不要改 `format.txt` 去"让它跑通"。** 跑不通通常是稿件缺结构，不是参数不对。
   真要改（用户明确提了新要求），先读模板的 `README.md` 里「已知限制」，改完说明改了哪几行。
3. **`cover_sections` 不为 0 时**，说明这份模板配了一份学校模板（`cover.docx`，本库不托管）。
   用户手上有原件时用 `--base-template cover.docx --cover-sections <N>`，让封面保持原样；
   手上没有就只排正文，别自己拼封面。

## 三、没有合适的模板怎么办

按代价从低到高：

1. 用引擎内置预设（`zh-academic` / `en-nature`），先出一版合规的。
2. 用户手上有参考 `.docx`：`md-to-word-template 参考.docx -o format.txt` 反推草稿，
   核对草稿末尾的「待确认」清单后再用。
3. 都没有：按稿件语种用默认预设，交付时说明"用的是通用规范，不是你们学校/期刊的"。

**不要凭印象编一份 `format.txt`**：词表是封闭的，编出来的词会被引擎逐条报错。

## 四、要不要提交回来

用户明确要提、或者这份格式文件是刚反推出来并核对过的，可以走 [CONTRIBUTING.md](CONTRIBUTING.md)。
提交前必须本地跑通：

```bash
python3 scripts/check.py --strict
```

它做三件事：真调一次引擎导出（预检、对账、审计全开）、校验索引与头部一致、检查样稿是否覆盖了
`format.txt` 声明的每条样式。过不了就别提——库里不收"看着差不多"的模板。
