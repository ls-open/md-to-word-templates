# 怎么提交一份模板

## 三条硬规矩

1. **只提交参数与自写样稿**：`format.txt` 的每个数值都要能在公开来源页上找到依据；`sample.md`
   必须自己写。学校/期刊的 `.docx` `.dotx` 原件一律不收。
2. **必须能导出**：`python3 scripts/check.py` 退出码 0。它会真的调一次引擎导出，预检、对账、
   审计全开——导出不过的模板进库没有意义。
3. **样稿要覆盖声明**：`format.txt` 声明了 `表格` 就要有真表格。加 `--strict` 把未覆盖也当失败，
   提交前请用严格模式跑一遍。

## 建一份新模板

```bash
mkdir -p templates/<id>/ && cd templates/<id>
md-to-word-template 参考.docx -o format.txt    # 有参考文件就反推，没有就抄同学校已有的一份
cp ../../cn-generic-thesis-master/sample.md .  # 照结构改成这所学校的要求
python3 ../../scripts/build_index.py           # 头部写好后生成索引
python3 ../../scripts/check.py --strict
```

命名：`<国别>-<学校或期刊简写>-<kind>-<degree?>-<unit?>`，例如 `cn-uestc-thesis-master`、
`cn-uestc-thesis-master-sice`。目录名只是给人定位，查询一律走头部字段。

## 更新：三种情况三种做法

| 情况 | 做法 |
|:--|:--|
| 参数写错了（同一年份、同一适用范围） | 直接改那个目录，`updated` 改日期，不升版本 |
| 对方换版（比如 2024 新规） | **新增**一个目录，`spec_year` 写新年份，旧份 `state: deprecated` 并写 `supersedes` |
| 有争议或没人维护 | `state: deprecated` + 在 README「已知限制」里写原因。**不删**，去年答辩的人还要用 |

唯一主键是 `(org, unit, kind, degree, spec_year)`。CI 拒收主键撞车的新目录——撞上了只有两条路：
改现有那份，或者写 `supersedes` 说清替代关系。别让两份都躺着，用户不知道该用哪份。

## 学校模板（封面、声明页）怎么办

学校给的 `.docx` 模板**不入库**——版权在对方，收了要下架。但你可以让模板库记住"前置件到第几节"：

```yaml
cover_sections: 3      # 底模前 3 节是封面/声明，原样保留
```

自己把学校模板另存为 `templates/<id>/cover.docx`（`.gitignore` 里已忽略），本地跑一次：

```bash
md-to-word sample.md -f format.txt --base cover.docx --keep-pages 6 -o /tmp/x.docx
```

`--keep-pages` 会告诉你「前 6 页 = 前 3 节」，把那个节数写进 `cover_sections`。之后 CI 只要发现目录里有
`cover.docx`，就会用 `--base` 跑一遍并**逐页验真**；没有这个文件（别人的机器、GitHub Actions）就只跑
无底模的那一遍，并在头部声明不为 0 时提示缺文件。

这是刻意的：**库不托管学校模板，但托管"这份模板该怎么用"**。

## 学院粒度

有的学校每个学院要求不同。学院模板**必须自带完整 `format.txt`**，从学校版复制再改，
不要期待继承——库不做 include/覆盖，这样任何一份文件都能独立读懂。

```yaml
org: 电子科技大学
unit: 信息与通信工程学院
aliases: [信通学院]        # 学院改名就加这里，别让用户猜
```

选哪份的顺序：学院 > 学校；同层取 `spec_year` 新的；`degree` 必须对上；`state` 必须是 `current`。

## 谁有权改别人的模板

- `maintainers` 里的人：直接提 PR。
- 不在名单：PR 里 @ 原维护者。**14 天无回应**，核心维护者可以合并，并把提交者加进 `maintainers`。
- 错别字、失效链接、`updated` 日期：任何人可改，不必等。

这件事靠人和 PR 模板判，CI 判不了「谁有权」，也不该判。

## 审核看什么

1. `format.txt` 的数值有没有来源依据（对照 `source` 链接）。
2. `sample.md` 是不是自写、是否覆盖了声明的样式。
3. 下载 CI 产物里的 `.docx`，用 Word 打开看两页——**肉眼这一步不能省**，预检排不掉所有问题。
4. 头部字段是否齐全，主键是否与已有条目冲突。

## 引擎发版后

`.github/workflows/check.yml` 里的 `md-to-word==3.2.0` 要手动提到新版本。忘了提不会立刻出事：
每周的 `upstream` 任务会对着引擎 `main` 跑，红着就说明该跟进了。
