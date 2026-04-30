# Butler 候选队列

> 由 bootstrap.sh 于 2026-04-25 填充.
> P0 高优 / P1 中优 / P2 低优. 每次 invocation 只做 1 条, 按 W1 优先级选.
>
> **2026-05-01 状态**：featured→premium 管道全部清空（50侯国+多批person/sanwen/event升级完成）。
> 剩余 561 个 standard/basic 实体页（person=330, place=129, concept=26, event=25, sanwen=16, story=9, state=6）
> 可考虑下一阶段升级策略。

## P0 [ARCH] 架构提案待批准（2026-04-30 W5 发现）

- [ ] P0 | [[架构：SQLite 迁移]] | 四项指标超临界线（pages.json=5347KB, pages=20408, person=4327, history=20227）| 见 `wiki/memory/reflections/2026-04-30_arch.md`

## ⭐ 用户想要 (P0)
- [x] **[想要]** 曹参征战时间线: `create-stub` [P0] [2026-04-26] [用户请求] <!-- 页面已存在，featured质量，早前会话已完成 -->

## 来自 discover_kg (kg top-N 缺 wiki 页)

## 来自 discover_sku (ontology-v2 SKU 缺 topic 页)

---

## P1 premium-upgrade 候选（2026-04-28 R9990 W1 探索，featured→premium）

- [x] P1 | [[汲黯]] | 371行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[淳于意]] | 347行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[扁鹊]] | 326行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[窦婴]] | 283行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[商鞅]] | 282行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[田蚡]] | 274行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[范睢]] | 250行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[李斯]] | 238行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[梁孝王]] | 231行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[荆轲]] | 230行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[商鞅变法]] | 416行 · featured · type=concept | action: premium-upgrade

## P1 premium-upgrade 候选（2026-04-28 R10001 W1 探索第二批，featured→premium）

- [x] P1 | [[齐桓公]] | 222行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[曹参]] | 220行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[陈馀]] | 220行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[灌夫]] | 217行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[樊哙]] | 216行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[赵高]] | 215行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[周勃]] | 212行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[张汤]] | 212行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[垓下之战]] | 230行 · featured · type=event | action: premium-upgrade

## P1 premium-upgrade 候选（2026-04-28 R10012 W1 探索第三批，featured→premium）

- [x] P1 | [[李广]] | 210行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[晁错]] | 208行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[范蠡]] | 207行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[楚平王]] | 207行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[舜]] | 220行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[周公]] | 211行 · featured · type=person | action: premium-upgrade

## P1 premium-upgrade 候选（2026-04-28 R10019 W1 探索第四批，featured→premium）

- [x] P1 | [[秦献公]] | 208行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[齐景公]] | 207行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[刘长]] | 206行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[薄太后]] | 205行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[巨鹿之战]] | 203行 · featured · type=event | action: premium-upgrade
- [x] P1 | [[吴起]] | 200行 · featured · type=person | action: premium-upgrade

## P2 低优 (手动加入)

（留给用户手动追加的低优任务）


---

## P1 standard→featured 第十八批（2026-05-01，standard→featured 4600B档）✓ 完成

- [x] R11407 | [[伯夷叔齐]] | 4699B→12646B · type=person · src=周本纪/孔子世家/伯夷列传 | action: enrich-quality
- [x] R11408 | [[儋]] | 4692B→11053B · type=person · src=周本纪/秦本纪/封禅书 | action: enrich-quality
- [x] R11410 | [[番系]] | 4685B→10666B · type=person · src=河渠书/平准书 | action: enrich-quality
- [x] R11411 | [[卫君角]] | 4671B→10681B · type=person · src=六国年表/卫康叔世家 | action: enrich-quality
- [x] R11412 | [[鲁釐公]] | 4657B→10947B · type=person · src=齐太公世家/鲁周公世家 | action: enrich-quality
- [x] R11413 | [[子周]] | 4656B→9748B · type=person · src=周本纪/晋世家/仲尼弟子列传 | action: enrich-quality
- [x] R11414 | [[颜异]] | 4637B→10114B · type=person · src=平准书 | action: enrich-quality
- [x] R11415 | [[卫不疑]] | 4635B→10017B · type=person · src=建元以来侯者年表/卫将军骠骑列传 | action: enrich-quality
- [x] R11416 | [[玄成]] | 4632B→10656B · type=person · src=建元以来侯者年表/张丞相列传 | action: enrich-quality
- [x] R11417 | [[卓子]] | 4632B→10917B · type=person · src=秦本纪/十二诸侯年表/齐太公世家/晋世家 | action: enrich-quality
- [x] R11418 | [[驩兜]] | 4628B→10294B · type=person · src=五帝本纪/夏本纪 | action: enrich-quality
- [x] R11419 | [[高厚]] | 4619B→10057B · type=person · src=十二诸侯年表/齐太公世家 | action: enrich-quality
- [x] R11420 | [[陈庄公]] | 4618B→12223B · type=person · src=十二诸侯年表/陈杞世家/田敬仲完世家 | action: enrich-quality
- [x] R11421 | [[屈完]] | 4589B→11657B · type=person · src=十二诸侯年表/齐太公世家 | action: enrich-quality
- [x] R11422 | [[临江哀王]] | 4588B→11848B · type=person · src=汉兴以来诸侯王年表/五宗世家 | action: enrich-quality
- [x] R11423 | [[刘馀]] | 4584B→12792B · type=person · src=孝景本纪/汉兴以来诸侯王年表/五宗世家 | action: enrich-quality
- [x] R11424 | [[国惠子]] | 4577B→12958B · type=person · src=齐太公世家/田敬仲完世家 | action: enrich-quality

## P1 standard→featured 第十九批（2026-05-01，standard→featured 4500B档）

- [x] R11425 | [[石碏]] | 4571B→11797B · type=person · src=十二诸侯年表/卫康叔世家 | action: enrich-quality
- [x] R11426 | [[曹惠伯]] | 4568B→11400B · type=person · src=十二诸侯年表/管蔡世家 | action: enrich-quality
- [x] R11428 | [[申公巫臣]] | 4566B→12391B · type=person · src=晋世家/郑世家/吴太伯世家 | action: enrich-quality
- [x] R11429 | [[蔡武侯]] | 4565B→11029B · type=person · src=十二诸侯年表/管蔡世家 | action: enrich-quality
- [x] R11430 | [[赵武公]] | 4564B→11292B · type=person · src=赵世家/六国年表 | action: enrich-quality
- [ ] P1 | [[吴回]] | 4562B · type=person · src=楚世家/太史公自序 | action: enrich-quality
- [ ] P1 | [[赵桓子]] | 4560B · type=person · src=赵世家/六国年表 | action: enrich-quality
- [ ] P1 | [[风后]] | 4557B · type=person · src=五帝本纪/太史公自序 | action: enrich-quality
- [ ] P1 | [[赵豹]] | 4546B · type=person · src=赵世家/白起王翦列传 | action: enrich-quality
- [ ] P1 | [[鲍牧]] | 4546B · type=person · src=齐太公世家/田敬仲完世家 | action: enrich-quality
- [ ] P1 | [[接舆]] | 4542B · type=person · src=孔子世家/老子韩非列传 | action: enrich-quality
- [ ] P1 | [[鲁孝公]] | 4540B · type=person · src=十二诸侯年表/鲁周公世家 | action: enrich-quality
- [ ] P1 | [[鲁惠公]] | 4539B · type=person · src=十二诸侯年表/鲁周公世家 | action: enrich-quality
- [ ] P1 | [[丕郑]] | 4538B · type=person · src=晋世家 | action: enrich-quality
- [ ] P1 | [[张尚]] | 4516B · type=person · src=吴太伯世家/楚世家 | action: enrich-quality
- [ ] P1 | [[卫嗣君]] | 4514B · type=person · src=卫康叔世家/六国年表 | action: enrich-quality
- [ ] P1 | [[东周惠王]] | 4512B · type=person · src=周本纪/赵世家 | action: enrich-quality

## P1 expand-content 候选（2026-04-25 补充，按 refs 排序）

- [x] P1 | [[刘舜]] | 42行 · refs=81 · type=person | action: expand-content
- [x] P1 | [[雍王]] | 37行 · refs=79 · type=person | action: expand-content
- [x] P1 | [[张楚楚隐王]] | 41行 · refs=71 · type=person | action: expand-content <!-- R5850: 已完成 -->
- [x] P1 | [[蔡庄侯]] | 20行 · refs=28 · type=person | action: expand-content <!-- R5287: 已完成 -->
- [x] P1 | [[晋哀侯]] | 37行 · refs=26 · type=person | action: expand-content
- [x] P1 | [[蔡共侯]] | 36行 · refs=24 · type=person | action: expand-content
- [x] P1 | [[蔡夷侯]] | 20行 · refs=24 · type=person | action: expand-content <!-- R5288: 已完成 -->

## P1 expand-content 候选（2026-04-27 R6079 W5 补充，按 refs 排序）

- [x] P1 | [[王]] | 82行 · refs=40 · type=person | action: expand-content <!-- R9700: 已完成（王子克生平） -->
- [x] P1 | [[西魏王]] | 44行 · refs=37 · type=person | action: expand-content <!-- type=redirect，跳过 -->
- [x] P1 | [[楚王]] | 52行 · refs=35 · type=person | action: expand-content <!-- R9701: 已完成（楚隆生平） -->
- [x] P1 | [[殷契]] | 51行 · refs=25 · type=person | action: expand-content <!-- R6820: 已完成 -->
- [x] P1 | [[新垣衍]] | 102行 · refs=15 · type=person | action: expand-content <!-- 已有生平节，跳过 -->
- [x] P1 | [[宋昭公]] | 40行 · refs=15 · type=person | action: expand-content <!-- 已有生平节，跳过 -->
- [x] P1 | [[晋昭公]] | 67行 · refs=15 · type=person | action: expand-content <!-- 已有生平节，跳过 -->
- [x] P1 | [[文侯申]] | 48行 · refs=14 · type=person | action: expand-content <!-- 已有生平节，跳过 -->
- [x] P1 | [[秦惠公]] | 51行 · refs=14 · type=person | action: expand-content <!-- R6821: 已完成 -->
- [x] P1 | [[蔡戴侯]] | 44行 · refs=14 · type=person | action: expand-content <!-- 已有生平节，跳过 -->
- [x] P1 | [[蔡灵侯]] | 48行 · refs=14 · type=person | action: expand-content <!-- 已有生平节，跳过 -->
- [x] P1 | [[赵敬肃王]] | 38行 · refs=14 · type=person | action: expand-content <!-- 仅thin源，跳过 -->
- [x] P1 | [[公孙衍]] | 124行 · refs=13 · type=person | action: expand-content <!-- 已有生平节，跳过 -->
- [x] P1 | [[吴广]] | 142行 · refs=13 · type=person | action: expand-content <!-- 已有生平节，跳过 -->
- [x] P1 | [[姬喜]] | 62行 · refs=13 · type=person | action: expand-content <!-- 已有生平节，跳过 -->
- [x] P1 | [[赵国赵桓子]] | 45行 · refs=13 · type=person | action: expand-content <!-- basic质量/1处引用，跳过 -->
- [x] P1 | [[韩懿侯]] | 62行 · refs=13 · type=person | action: expand-content <!-- R6822: 已完成 -->
- [x] P1 | [[齐康公]] | 43行 · refs=13 · type=person | action: expand-content <!-- 已有生平节，跳过 -->
- [x] P1 | [[东周哀王]] | 44行 · refs=12 · type=person | action: expand-content <!-- 仅1个非thin源，跳过 -->
- [x] P1 | [[姬阖闾]] | 55行 · refs=12 · type=person | action: expand-content <!-- type=redirect，跳过 -->
- [x] P1 | [[楚子西]] | 36行 · refs=12 · type=person | action: expand-content <!-- basic质量/1源，跳过 -->
- [x] P1 | [[赵幽缪王]] | 53行 · refs=12 · type=person | action: expand-content <!-- basic质量/3处引用，跳过 -->
- [x] P1 | [[阎乐]] | 65行 · refs=12 · type=person | action: expand-content <!-- 已有生平节，跳过 -->

## P1 expand-content 候选（2026-04-27 R6823 W5 补充，refs≥5+无生平节）

- [x] P1 | [[卫顷侯]] | 59行 · refs=19 · type=person | action: expand-content <!-- R8987: 已完成 -->
- [x] P1 | [[曹奇]] | 36行 · refs=14 · type=person | action: expand-content <!-- R8988: 已完成 -->
- [x] P1 | [[江都易王]] | 50行 · refs=13 · type=person | action: expand-content <!-- R8989: 已完成 -->
- [x] P1 | [[燕惠侯]] | 51行 · refs=12 · type=person | action: expand-content <!-- R8990: 已完成 -->
- [x] P1 | [[菑川懿王]] | 35行 · refs=12 · type=person | action: expand-content <!-- 已有生平节，跳过 -->
- [x] P1 | [[平阳公主]] | 62行 · refs=11 · type=person | action: expand-content <!-- R8991: 已完成 -->
- [x] P1 | [[故安节侯]] | 35行 · refs=11 · type=person | action: expand-content <!-- R8992: 已完成 -->
- [x] P1 | [[晋出公]] | 65行 · refs=11 · type=person | action: expand-content <!-- R8993: 已完成 -->
- [x] P1 | [[晋武侯]] | 50行 · refs=11 · type=person | action: expand-content <!-- R8994: 已完成 -->
- [x] P1 | [[代共王]] | 42行 · refs=10 · type=person | action: expand-content <!-- 已有生平节，跳过 -->
- [x] P1 | [[卫殇公]] | 41行 · refs=10 · type=person | action: expand-content <!-- 已有生平节，跳过 -->
- [x] P1 | [[姬昌]] | 77行 · refs=10 · type=person | action: expand-content <!-- 已有生平节，跳过 -->
- [x] P1 | [[杨熊]] | 54行 · refs=10 · type=person | action: expand-content <!-- R8995: 已完成 -->
- [x] P1 | [[楚康王]] | 59行 · refs=10 · type=person | action: expand-content <!-- R8996: 已完成 -->
- [x] P1 | [[秦嘉]] | 66行 · refs=10 · type=person | action: expand-content <!-- R8997: 已完成 -->
- [x] P1 | [[蔡景侯]] | 44行 · refs=10 · type=person | action: expand-content <!-- 已有生平节，跳过 -->
- [x] P1 | [[陈申公]] | 34行 · refs=10 · type=person | action: expand-content <!-- 已有生平节，跳过 -->
- [x] P1 | [[（淮南王，谋反自杀，无谥）]] | 49行 · refs=10 · type=person | action: expand-content <!-- R9003: 已完成 -->
- [x] P1 | [[傅则]] | 34行 · refs=9 · type=person | action: expand-content <!-- 已有生平节，跳过 -->
- [x] P1 | [[公孙敢]] | 37行 · refs=9 · type=person | action: expand-content <!-- 已有生平节，跳过 -->
- [x] P1 | [[南越明王]] | 38行 · refs=9 · type=person | action: expand-content <!-- 已有生平节，跳过 -->
- [x] P1 | [[卫平侯]] | 49行 · refs=9 · type=person | action: expand-content <!-- 已有生平节，跳过 -->
- [x] P1 | [[广川惠王]] | 50行 · refs=9 · type=person | action: expand-content <!-- R8998: 已完成 -->
- [x] P1 | [[张次公]] | 50行 · refs=9 · type=person | action: expand-content <!-- R8999: 已完成 -->
- [x] P1 | [[武庚]] | 61行 · refs=9 · type=person | action: expand-content <!-- R9000: 已完成 -->
- [x] P1 | [[胶东哀王]] | 51行 · refs=9 · type=person | action: expand-content <!-- 已有生平节，跳过 -->
- [x] P1 | [[胶西于王]] | 36行 · refs=9 · type=person | action: expand-content <!-- R9001: 已完成 -->
- [x] P1 | [[蔡悼侯]] | 49行 · refs=9 · type=person | action: expand-content <!-- 已有生平节，跳过 -->
- [x] P1 | [[刘据]] | 53行 · refs=8 · type=person | action: expand-content <!-- R9002: 已完成 -->
- [x] P1 | [[刘端]] | 52行 · refs=8 · type=person | action: expand-content <!-- 已有生平节，跳过 -->

## P1 premium-upgrade 候选（2026-04-27 R6823 W5 补充）

- [x] P1 | [[周武王]] | 225行 · refs=131 · type=person | action: premium-upgrade <!-- 已是premium -->
- [x] P1 | [[二世皇帝]] | 163行 · refs=108 · type=person | action: premium-upgrade <!-- 已是premium -->
- [x] P1 | [[汉景帝]] | 171行 · refs=102 · type=person | action: premium-upgrade <!-- 已是premium -->
- [x] P1 | [[周文王]] | 197行 · refs=97 · type=person | action: premium-upgrade <!-- 已是premium -->
- [x] P1 | [[晋文公]] | 182行 · refs=95 · type=person | action: premium-upgrade <!-- 已是premium -->
- [x] P1 | [[黄帝]] | 223行 · refs=92 · type=person | action: premium-upgrade <!-- 已是premium -->
- [x] P1 | [[秦昭襄王]] | 194行 · refs=89 · type=person | action: premium-upgrade <!-- R9961 done -->
- [x] P1 | [[项梁]] | 215行 · refs=89 · type=person | action: premium-upgrade <!-- R9962 done -->
- [x] P1 | [[袁盎]] | 192行 · refs=86 · type=person | action: premium-upgrade <!-- 已是premium -->
- [x] P1 | [[秦缪公]] | 210行 · refs=76 · type=person | action: premium-upgrade <!-- R9963 done -->

## P1 premium-upgrade 候选（2026-04-27 R6079 W5 补充）

- [x] P1 | [[楚怀王]] | 260行 · refs=75 · type=person | action: premium-upgrade <!-- R9964 done -->
- [x] P1 | [[彭越]] | 243行 · refs=69 · type=person | action: premium-upgrade <!-- R9965 done -->
- [x] P1 | [[伍子胥]] | 223行 · refs=65 · type=person | action: premium-upgrade <!-- 已是premium -->
- [x] P1 | [[姬旦]] | 214行 · refs=63 · type=person | action: premium-upgrade <!-- 已是premium -->
- [x] P1 | [[公孙弘]] | 216行 · refs=62 · type=person | action: premium-upgrade <!-- R9968 done -->
- [x] P1 | [[蔺相如]] | 161行 · refs=61 · type=person | action: premium-upgrade <!-- 已是premium -->
- [x] P1 | [[萧何]] | 261行 · refs=59 · type=person | action: premium-upgrade <!-- 已是premium -->
- [x] P1 | [[陈豨]] | 203行 · refs=59 · type=person | action: premium-upgrade <!-- R9969 done -->
- [x] P1 | [[周成王]] | 219行 · refs=56 · type=person | action: premium-upgrade <!-- R9970 done -->
- [x] P1 | [[卫青]] | 215行 · refs=54 · type=person | action: premium-upgrade <!-- R9971 done -->
- [x] P1 | [[城阳顷王]] | 17行 · refs=22 · type=person | action: expand-content <!-- R5269: 已完成 -->
- [x] P1 | [[汉昭帝]] | 39行 · refs=22 · type=person | action: expand-content
- [x] P1 | [[宋平公]] | 20行 · refs=21 · type=person | action: expand-content <!-- R5269: 已完成 -->
- [x] P1 | [[汉宣帝]] | 41行 · refs=21 · type=person | action: expand-content
- [x] P1 | [[卫顷侯]] | 29行 · refs=19 · type=person | action: expand-content
- [x] P1 | [[晋靖侯]] | 29行 · refs=19 · type=person | action: expand-content
- [x] P1 | [[鲁景公]] | 21行 · refs=19 · type=person | action: expand-content <!-- R5293: 已完成 -->
- [x] P1 | [[城阳共王]] | 21行 · refs=16 · type=person | action: expand-content
- [x] P1 | [[太子建]] | 39行 · refs=16 · type=person | action: expand-content
- [x] P1 | [[晋孝侯]] | 40行 · refs=16 · type=person | action: expand-content
- [x] P1 | [[王黄]] | 49行 · refs=16 · type=person | action: expand-content
- [x] P1 | [[卫绾]] | 45行 · refs=15 · type=person | action: expand-content
- [x] P1 | [[楚顷襄王]] | 41行 · refs=15 · type=person | action: expand-content
- [x] P1 | [[阳虎]] | 42行 · refs=15 · type=person | action: expand-content
- [x] P1 | [[鲁昭公]] | 44行 · refs=15 · type=person | action: expand-content
- [x] P1 | [[卫伉]] | 28行 · refs=14 · type=person | action: expand-content
- [x] P1 | [[庄青翟]] | 37行 · refs=14 · type=person | action: expand-content
- [x] P1 | [[晋武公]] | 43行 · refs=14 · type=person | action: expand-content
- [x] P1 | [[李少君]] | 38行 · refs=14 · type=person | action: expand-content
- [x] P1 | [[李由]] | 39行 · refs=14 · type=person | action: expand-content
- [x] P1 | [[赵信]] | 50行 · refs=14 · type=person | action: expand-content
- [x] P1 | [[郑文公]] | 46行 · refs=14 · type=person | action: expand-content
- [x] P1 | [[霍嬗]] | 24行 · refs=14 · type=person | action: expand-content
- [x] P1 | [[韩厥]] | 50行 · refs=14 · type=person | action: expand-content
- [x] P1 | [[刘泽]] | 41行 · refs=13 · type=person | action: expand-content
- [x] P1 | [[周孝王]] | 33行 · refs=13 · type=person | action: expand-content
- [x] P1 | [[张武]] | 44行 · refs=13 · type=person | action: expand-content
- [x] P1 | [[栾大]] | 39行 · refs=13 · type=person | action: expand-content
- [x] P1 | [[楚考烈王]] | 29行 · refs=13 · type=person | action: expand-content
- [x] P1 | [[济北贞王]] | 17行 · refs=13 · type=person | action: expand-content
- [x] P1 | [[田乞]] | 37行 · refs=13 · type=person | action: expand-content
- [x] P1 | [[韩说]] | 38行 · refs=13 · type=person | action: expand-content
- [x] P1 | [[刘遂]] | 25行 · refs=12 · type=person | action: expand-content


## P1 premium-upgrade 候选（2026-04-25 补充，按 refs 排序）

- [x] P1 | [[周武王]] | 133行 · refs=131 · type=person | action: premium-upgrade
- [x] P1 | [[二世皇帝]] | 122行 · refs=108 · type=person | action: premium-upgrade (already featured)
- [x] P1 | [[汉景帝]] | 127行 · refs=102 · type=person | action: premium-upgrade (already featured)
- [x] P1 | [[周文王]] | 118行 · refs=97 · type=person | action: premium-upgrade (already featured)
- [x] P1 | [[晋文公]] | 127行 · refs=95 · type=person | action: premium-upgrade (already featured)
- [x] P1 | [[黄帝]] | 128行 · refs=92 · type=person | action: premium-upgrade (already featured)
- [x] P1 | [[秦昭襄王]] | 134行 · refs=89 · type=person | action: premium-upgrade
- [x] P1 | [[项梁]] | 150行 · refs=89 · type=person | action: premium-upgrade
- [x] P1 | [[袁盎]] | 140行 · refs=86 · type=person | action: premium-upgrade (already featured)
- [x] P1 | [[秦缪公]] | 139行 · refs=76 · type=person | action: premium-upgrade
- [x] P1 | [[赵高]] | 138行 · refs=75 · type=person | action: premium-upgrade
- [x] P1 | [[尧]] | 136行 · refs=72 · type=person | action: premium-upgrade (already featured)
- [x] P1 | [[廉颇]] | 138行 · refs=68 · type=person | action: premium-upgrade (already featured)
- [x] P1 | [[管仲]] | 138行 · refs=65 · type=person | action: premium-upgrade (already featured)
- [x] P1 | [[李斯]] | 146行 · refs=64 · type=person | action: premium-upgrade

## P1 expand-content 候选（2026-04-28 R9959 W5 补充，refs≥12+无生平节）

- [x] P1 | [[城阳共王]] | 58行 · refs=16 | action: expand-content <!-- R9989 done -->
- [x] P1 | [[卫伉]] | 81行 · refs=14 · type=person | action: expand-content <!-- R9981 done -->
- [x] P1 | [[文侯申]] | 101行 · refs=14 | action: expand-content <!-- R9988 done -->
- [x] P1 | [[秦惠公]] | 68行 · refs=14 | action: expand-content <!-- R9987 done -->
- [x] P1 | [[蔡戴侯]] | 85行 · refs=14 · type=person | action: expand-content <!-- R9982 done -->
- [x] P1 | [[蔡灵侯]] | 100行 · refs=14 · type=person | action: expand-content <!-- R9975 done -->
- [x] P1 | [[赵敬肃王]] | 87行 · refs=14 · type=person | action: expand-content <!-- R9976 done -->
- [x] P1 | [[霍嬗]] | 67行 · refs=14 · type=person | action: expand-content <!-- R9977 done -->
- [x] P1 | [[东周惠王]] | 76行 · refs=13 · type=person | action: expand-content <!-- R9983 done -->
- [x] P1 | [[公孙衍]] | 150行 · refs=13 · type=person | action: expand-content <!-- R9973 done -->
- [x] P1 | [[吴广]] | 164行 · refs=13 · type=person | action: expand-content <!-- R9972 done -->
- [x] P1 | [[姬喜]] | 125行 · refs=13 · type=person | action: expand-content <!-- R9974 done -->
- [x] P1 | [[韩懿侯]] | 95行 · refs=13 · type=person | action: expand-content <!-- R9978 done -->
- [x] P1 | [[齐康公]] | 100行 · refs=13 · type=person | action: expand-content <!-- R9979 done -->
- [x] P1 | [[东周哀王]] | 48行 · refs=12 | action: expand-content <!-- 跳过: 页面描述有误，refs全为汉代年表 -->
- [x] P1 | [[楚子西]] | 36行 · refs=12 | action: expand-content <!-- 跳过: frontmatter id混淆 -->
- [x] P1 | [[赵国赵桓子]] | 62行 · refs=13 | action: expand-content <!-- R9986 done -->

## 第五批 premium-upgrade 候选（R10028 W1-explore）

- [x] P1 | [[太史公]] | 247行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[季札]] | 229行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[崔杼]] | 219行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[秦襄公]] | 207行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[任安]] | 206行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[箕子]] | 203行 · featured · type=person | action: premium-upgrade

## 第六批 premium-upgrade 候选（R10036 W1-explore）

- [x] P1 | [[晋灵公]] | 202行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[周昌]] | 201行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[赵武灵王]] | 201行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[秦孝文王]] | 201行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[荆轲刺秦王]] | 227行 · featured · type=story | action: premium-upgrade
- [x] P1 | [[陈完奔齐]] | 240行 · featured · type=story | action: premium-upgrade

## 第七批 premium-upgrade 候选（R10044 W1-explore）

- [x] P1 | [[子贡]] | 199行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[孙武]] | 199行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[宋襄公]] | 199行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[晋厉公]] | 200行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[赵孝成王]] | 200行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[吕产]] | 199行 · featured · type=person | action: premium-upgrade

## 第八批 premium-upgrade 候选（R10053 W1-explore）

- [x] P1 | [[白起]] | 197行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[蔡泽]] | 199行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[郭解]] | 199行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[伊尹]] | 196行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[太子丹]] | 196行 · featured · type=person | action: premium-upgrade
- [x] P1 | [[卢绾]] | 197行 · featured · type=person | action: premium-upgrade

## 第九批 premium-upgrade 候选（R10062 W1-explore）

- [x] P1 | [[章邯]] | 196行 · featured · type=person | action: premium-upgrade ✓ R10063
- [x] P1 | [[叔孙通]] | 195行 · featured · type=person | action: premium-upgrade ✓ R10064
- [x] P1 | [[吕禄]] | 195行 · featured · type=person | action: premium-upgrade ✓ R10066
- [x] P1 | [[张苍]] | 196行 · featured · type=person | action: premium-upgrade ✓ R10067
- [x] P1 | [[秦武王]] | 195行 · featured · type=person | action: premium-upgrade ✓ R10068
- [x] P1 | [[楚成王]] | 194行 · featured · type=person | action: premium-upgrade ✓ R10069

## 第十批 premium-upgrade 候选（R10070 W1-explore）

- [x] P1 | [[赵胜]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[灌婴]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[赵简子]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[姒句践]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[田常]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[周厉王]] | featured · type=person | action: premium-upgrade

## 第十一批 premium-upgrade 候选（R10077 W1-explore）

- [x] P1 | [[仲由]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[后稷]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[晋献公]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[秦惠王]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[英布]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[楚庄王]] | featured · type=person | action: premium-upgrade

## 第十二批 premium-upgrade 候选（R10085 W1-explore）

- [x] P1 | [[窦太后]] | featured · type=person | action: premium-upgrade
- [~] P1 | [[西周幽王]] | featured · skip-content-thin · type=person | action: premium-upgrade
- [x] P1 | [[魏冉]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[秦孝公]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[秦庄襄王]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[齐威王]] | featured · type=person | action: premium-upgrade

## 第十三批 premium-upgrade 候选（R10092 W1-explore）

- [x] P1 | [[蒙恬]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[齐湣王]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[周亚夫]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[楚灵王]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[韩王信]] | featured · type=person | action: premium-upgrade

## 第十四批 premium-upgrade 候选（R10098 W1-explore）

- [x] P1 | [[吴王阖闾]] | featured · type=person | action: premium-upgrade
- [~] P1 | [[汉武帝]] | featured · skip-data-issue(段干子.md) · type=person | action: premium-upgrade
- [x] P1 | [[田文]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[刘濞]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[魏无忌]] | featured · type=person | action: premium-upgrade

## 第十五批 premium-upgrade 候选（R10105 W1-explore）✓

- [x] P1 | [[周宣王]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[秦子婴]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[齐襄公]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[楚昭王]] | featured · type=person | action: premium-upgrade

## 第十六批 premium-upgrade 候选（R10110 W1-explore）
- [x] P1 | [[郦食其]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[魏惠王]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[李牧]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[黄歇]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[田单]] | featured · type=person | action: premium-upgrade
- [~] 刘舜 | skip-content-thin (78行)
- [~] 张楚楚隐王 | skip-content-thin (71行)

## 第十七批 premium-upgrade 候选（R10117 W1-explore）
- [x] P1 | [[王子城父]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[公孙卿]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[主父偃]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[张骞]] | featured · type=person | action: premium-upgrade

## 第十八批 premium-upgrade 候选（R10122 W1-explore）
- [x] P1 | [[赵敬侯]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[齐悼惠王]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[老子]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[赵奢]] | featured · type=person | action: premium-upgrade

## 第十九批 premium-upgrade 候选（R10127 W1-explore）
- [x] P1 | [[赵襄子]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[齐宣王]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[晏婴]] | featured · type=person | action: premium-upgrade
- [~] 晋哀侯 | skip-content-thin (70行)

## 第二十批 premium-upgrade 候选（R10131 W1-explore）
- [x] P1 | [[淮南厉王]] | featured · type=person | action: premium-upgrade <!-- skip-already-premium R10153 -->
- [x] P1 | [[燕召公]] | featured · type=person | action: premium-upgrade <!-- skip-already-premium R10153 -->
- [x] P1 | [[苏代]] | featured · type=person | action: premium-upgrade <!-- skip-already-premium R10153 -->

## 第二十一批 premium-upgrade 候选（R10134 W1-explore）
- [x] P1 | [[燕召公]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[苏代]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[韩安国]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[魏文侯]] | featured · type=person | action: premium-upgrade
- [~] 晋哀侯 | skip-content-thin (70行)
- [~] 东周平王 | skip-content-thin (52行)

## 第二十二批 premium-upgrade 候选（R10139 W1-explore）
- [x] P1 | [[中山靖王]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[晋平公]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[赵括]] | featured · type=person | action: premium-upgrade
- [x] P1 | [[鲁隐公]] | featured · type=person | action: premium-upgrade

## 第二十三批 世系补全（R10145 batch-侯主）
- [x] P1 | 115个侯国页面 | 批量添加历代侯主表 | action: batch-世系补全 | accept
  - 来源：018/019/020年表JSON数据
  - 覆盖范围：018=17页, 019=48页, 020=50页（共115页）

## 剩余待处理的侯国页（无规则可提取，共43页）
- [ ] P3 | 义阳侯国/乐平侯国/乐成侯国/乐昌侯国等43页 | 年表无标准侯主记录 | 暂搁置

## P1 premium-upgrade 候选（2026-04-28 R10153 W1 探索第N批，featured→premium）

- [x] P1 | [[淮南厉王]] | 194行 · featured · refs=26 | action: premium-upgrade <!-- skip-already-premium R10153 -->
- [x] P1 | [[燕召公]] | 158行 · featured · refs=26 | action: premium-upgrade <!-- skip-already-premium R10153 -->
- [x] P1 | [[苏代]] | 161行 · featured · refs=26 | action: premium-upgrade <!-- skip-already-premium R10153 -->
- [x] P1 | [[王离]] | 194行 · featured · refs=18 | action: premium-upgrade <!-- already-premium R10815 -->
- [x] P1 | [[田横]] | 192行 · featured · refs=17 | action: premium-upgrade <!-- already-premium -->
- [x] P1 | [[魏豹]] | 192行 · featured · refs=18 | action: premium-upgrade <!-- already-premium -->
- [x] P1 | [[鲁桓公]] | 191行 · featured · refs=18 | action: premium-upgrade <!-- already-premium -->
- [x] P1 | [[戚夫人]] | 190行 · featured · refs=17 | action: premium-upgrade <!-- already-premium -->
- [x] P1 | [[楚惠王]] | 190行 · featured · refs=17 | action: premium-upgrade <!-- already-premium -->
- [x] P1 | [[燕昭王]] | 189行 · featured · refs=18 | action: premium-upgrade <!-- already-premium -->
- [x] P1 | [[春申君]] | 186行 · featured · refs=15 | action: premium-upgrade <!-- already-premium -->
- [x] P1 | [[陆贾]] | 186行 · featured · refs=17 | action: premium-upgrade <!-- already-premium -->
- [x] P1 | [[张释之]] | 185行 · featured · refs=17 | action: premium-upgrade <!-- already-premium -->
- [x] P1 | [[里克]] | 181行 · featured · refs=19 | action: premium-upgrade <!-- already-premium -->

## P1 premium-upgrade 候选（2026-04-28 R10159 W1 探索第N+1批，featured→premium）

- [x] P1 | [[申屠嘉]] | 194行 · featured · refs=12 | action: premium-upgrade <!-- already-premium -->
- [x] P1 | [[魏武侯]] | 188行 · featured · refs=16 | action: premium-upgrade <!-- already-premium -->
- [x] P1 | [[比干]] | 183行 · featured · refs=18 | action: premium-upgrade <!-- already-premium -->
- [x] P1 | [[郑厉公]] | 183行 · featured · refs=17 | action: premium-upgrade <!-- already-premium -->
- [x] P1 | [[刘敬]] | 186行 · featured · refs=16 | action: premium-upgrade <!-- already-premium -->
- [x] P1 | [[季布]] | 181行 · featured · refs=12 | action: premium-upgrade <!-- already-premium -->
- [x] P1 | [[鲁哀公]] | 181行 · featured · refs=16 | action: premium-upgrade <!-- already-premium -->
- [x] P1 | [[田荣]] | 181行 · featured · refs=14 | action: premium-upgrade <!-- already-premium -->

## New premium-upgrade 候选（2026-04-30 R10816 W1 探索，featured→premium）

- [x] P1 | [[子之]] | 6675B · featured · type=person | action: premium-upgrade <!-- R10816 done -->
- [x] P1 | [[荀卿]] | 5764B · featured · type=person | action: premium-upgrade <!-- R10817 done -->
- [~] P1 | [[武丁]] | 5541B · featured · type=person | action: premium-upgrade <!-- skip: pages.json quality=f但文件quality=standard -->
- [x] P1 | [[朱家]] | 5518B · featured · type=person | action: premium-upgrade <!-- R10819 done -->
- [x] P1 | [[王夫人]] | 5450B · featured · type=person | action: premium-upgrade <!-- R10820 done -->
- [x] P1 | [[审食其]] | 5371B · featured · type=person | action: premium-upgrade <!-- R10821 done -->
- [x] P1 | [[吴王刘濞]] | 5371B · featured · type=person | action: premium-upgrade <!-- R10822 done -->
- [~] P1 | [[汉武帝]] | 5233B · featured · type=person | action: premium-upgrade <!-- skip: frontmatter数据异常(id=河间刚王) -->

## 第二批 premium-upgrade 候选（2026-04-30 R10823 W1 探索，featured→premium）

- [x] P1 | [[义帝]] | 4923B · featured · type=person | action: premium-upgrade <!-- R10824 done -->
- [x] P1 | [[穨当]] | 4901B · featured · type=person | action: premium-upgrade <!-- R10825 done -->
- [x] P1 | [[州吁]] | 4791B · featured · type=person | action: premium-upgrade <!-- R10826 done -->
- [x] P1 | [[子夏]] | 4776B · featured · type=person | action: premium-upgrade <!-- R10827 done -->
- [x] P1 | [[唐都]] | 4755B · featured · type=person | action: premium-upgrade <!-- R10828 done -->
- [x] P1 | [[杨仆]] | 4733B · featured · type=person | action: premium-upgrade <!-- R10829 done -->
- [x] P1 | [[周苛]] | 4720B · featured · type=person | action: premium-upgrade <!-- R10830 done -->
- [x] P1 | [[启]] | 4687B · featured · type=person | action: premium-upgrade <!-- R10831 done -->
- [x] P1 | [[任鄙]] | 4672B · featured · type=person | action: premium-upgrade <!-- R10832 done -->
- [x] P1 | [[师旷]] | 4625B · featured · type=person | action: premium-upgrade <!-- R10833 done -->

## 第三批 premium-upgrade 候选（2026-04-30 R10834 W1 探索，featured→premium）

- [x] P1 | [[夏姬]] | 4599B · featured · type=person | action: premium-upgrade <!-- R10834 done -->
- [x] P1 | [[彭祖]] | 4562B · featured · type=person | action: premium-upgrade <!-- R10835 done -->
- [x] P1 | [[所忠]] | 4541B · featured · type=person | action: premium-upgrade <!-- R10836 done -->
- [x] P1 | [[祖伊]] | 4478B · featured · type=person | action: premium-upgrade <!-- R10837 done -->
- [x] P1 | [[子兰]] | 4457B · featured · type=person | action: premium-upgrade <!-- R10838 done -->
- [x] P1 | [[南子]] | 4453B · featured · type=person | action: premium-upgrade <!-- R10839 done -->
- [x] P1 | [[王稽]] | 4401B · featured · type=person | action: premium-upgrade <!-- R10840 done -->
- [x] P1 | [[周丘]] | 4380B · featured · type=person | action: premium-upgrade <!-- R10841 done -->
- [x] P1 | [[子反]] | 4360B · featured · type=person | action: premium-upgrade <!-- R10842 done -->
- [x] P1 | [[张羽]] | 4355B · featured · type=person | action: premium-upgrade <!-- R10843 done -->

## 第四批 premium-upgrade 候选（2026-04-30 R10844 W1 探索，featured→premium）

- [x] P1 | [[神农]] | 4288B · featured · type=person | action: premium-upgrade <!-- R10844 done -->
- [x] P1 | [[任敖]] | 4252B · featured · type=person | action: premium-upgrade <!-- R10845 done -->
- [x] P1 | [[契]] | 4239B · featured · type=person | action: premium-upgrade <!-- R10846 done -->
- [x] P1 | [[有若]] | 4233B · featured · type=person | action: premium-upgrade <!-- R10847 done -->
- [x] P1 | [[叔向]] | 4161B · featured · type=person | action: premium-upgrade <!-- R10848 done -->
- [x] P1 | [[淖齿]] | 4101B · featured · type=person | action: premium-upgrade <!-- R10849 done -->
- [x] P1 | [[文成]] | 4087B · featured · type=person | action: premium-upgrade <!-- R10850 done -->
- [x] P1 | [[苏武]] | 4063B · featured · type=person | action: premium-upgrade <!-- R10851 done -->
- [x] P1 | [[益]] | 4026B · featured · type=person | action: premium-upgrade <!-- R10852 done -->
- [x] P1 | [[周殷]] | 4023B · featured · type=person | action: premium-upgrade <!-- R10853 done -->

## 第五批 premium-upgrade 候选（2026-04-30 R10855 W1 探索，featured→premium）

- [x] P1 | [[吴王僚]] | 4016B · featured · type=person | action: premium-upgrade
- [x] P1 | [[慎到]] | 4006B · featured · type=person | action: premium-upgrade
- [x] P1 | [[叶公]] | 3989B · featured · type=person | action: premium-upgrade
- [x] P1 | [[乌获]] | 3920B · featured · type=person | action: premium-upgrade
- [x] P1 | [[章平]] | 3886B · featured · type=person | action: premium-upgrade
- [x] P1 | [[先轸]] | 3880B · featured · type=person | action: premium-upgrade
- [x] P1 | [[王然于]] | 3855B · featured · type=person | action: premium-upgrade
- [x] P1 | [[仲弓]] | 3800B · featured · type=person | action: premium-upgrade
- [x] P1 | [[荀彘]] | 3755B · featured · type=person | action: premium-upgrade
- [x] P1 | [[缪贤]] | 3687B · featured · type=person | action: premium-upgrade

## 第六批 premium-upgrade 候选（2026-04-30 R10865 W1 探索，featured→premium）

- [x] P1 | [[田骈]] | 3650B · featured · type=person | action: premium-upgrade
- [x] P1 | [[湣公]] | 3531B · featured · type=person | action: premium-upgrade
- [x] P1 | [[硃亥]] | 3518B · featured · type=person | action: premium-upgrade
- [x] P1 | [[许负]] | 3496B · featured · type=person | action: premium-upgrade
- [x] P1 | [[屈丐]] | 3492B · featured · type=person | action: premium-upgrade
- [x] P1 | [[向寿]] | 3490B · featured · type=person | action: premium-upgrade
- [x] P1 | [[子西]] | 3387B · featured · type=person | action: premium-upgrade
- [x] P1 | [[伊陟]] | 3349B · featured · type=person | action: premium-upgrade
- [x] P1 | [[目夷]] | 3256B · featured · type=person | action: premium-upgrade
- [x] P1 | [[武涉]] | 3245B · featured · type=person | action: premium-upgrade

## 第七批 premium-upgrade 候选（2026-04-30 R10878 W1 探索，featured→premium）

- [x] P1 | [[召平]] | 3232B · featured · type=person | action: premium-upgrade
- [x] P1 | [[翟公]] | 3229B · featured · type=person | action: premium-upgrade
- [x] P1 | [[许历]] | 3218B · featured · type=person | action: premium-upgrade
- [x] P1 | [[子羔]] | 3168B · featured · type=person | action: premium-upgrade
- [x] P1 | [[田禄伯]] | 3130B · featured · type=person | action: premium-upgrade
- [x] P1 | [[田子方]] | 3126B · featured · type=person | action: premium-upgrade
- [x] P1 | [[奚齐]] | 3119B · featured · type=person | action: premium-upgrade
- [x] P1 | [[庄生]] | 3118B · featured · type=person | action: premium-upgrade
- [x] P1 | [[孟舒]] | 3061B · featured · type=person | action: premium-upgrade
- [x] P1 | [[侯生]] | 3057B · featured · type=person | action: premium-upgrade

## 第八批 premium-upgrade 候选（2026-04-30 R10889 W1 探索，featured→premium）

- [x] P1 | [[徐来]] | 3055B · featured · type=person | action: premium-upgrade
- [x] P1 | [[田仁]] | 3024B · featured · type=person | action: premium-upgrade
- [x] P1 | [[子韦]] | 2999B · featured · type=person | action: premium-upgrade
- [x] P1 | [[优旃]] | 2764B · featured · type=person | action: premium-upgrade
- [x] P1 | [[弥子瑕]] | 2687B · featured · type=person | action: premium-upgrade
- [x] P1 | [[王生]] | 2668B · featured · type=person | action: premium-upgrade
- [x] P1 | [[无采]] | 2502B · featured · type=person | action: premium-upgrade
- [x] P1 | [[石奢]] | 2381B · featured · type=person | action: premium-upgrade
- [x] P1 | [[毋寡]] | 2359B · featured · type=person | action: premium-upgrade
- [x] P1 | [[程姬]] | 2355B · featured · type=person | action: premium-upgrade

## 第九批 premium-upgrade 候选（2026-04-30 R10889 W1 探索，featured→premium）

- [x] P1 | [[苏代谏齐王释帝号]] | 6942B · featured · type=sanwen | action: premium-upgrade ✓ R11145
- [x] P1 | [[汉文帝遗诏]] | 6734B · featured · type=sanwen | action: premium-upgrade ✓ R11146
- [x] P1 | [[召公谏厉王止谤]] | 6654B · featured · type=sanwen | action: premium-upgrade ✓ R11147
- [x] P1 | [[伍被谏淮南王不可反]] | 6647B · featured · type=sanwen | action: premium-upgrade ✓ R11148
- [x] P1 | [[太史公发愤著书]] | 6609B · featured · type=sanwen | action: premium-upgrade ✓ R11149
- [x] P1 | [[苏代为齐阴遗穰侯书]] | 6591B · featured · type=sanwen | action: premium-upgrade ✓ R11150
- [x] P1 | [[冯唐论将]] | 6452B · featured · type=sanwen | action: premium-upgrade ✓ R11151
- [x] P1 | [[娄敬谏都关中]] | 6375B · featured · type=sanwen | action: premium-upgrade ✓ R11152
- [x] P1 | [[缇萦救父上书]] | 6353B · featured · type=sanwen | action: premium-upgrade ✓ R11153
- [x] P1 | [[宝鼎奏议]] | 6331B · featured · type=sanwen | action: premium-upgrade ✓ R11154

## 第十批 premium-upgrade 候选（2026-04-30 R10889 W1 探索，featured→premium）

- [x] P1 | [[李克论相]] | 6270B · featured · type=sanwen | action: premium-upgrade ✓ R11155
- [x] P1 | [[穆王甫刑]] | 6236B · featured · type=sanwen | action: premium-upgrade ✓ R11156
- [x] P1 | [[苏代见韩相国（高都）]] | 6099B · featured · type=sanwen | action: premium-upgrade ✓ R11157
- [x] P1 | [[汉景帝追尊文帝庙乐诏]] | 6088B · featured · type=sanwen | action: premium-upgrade ✓ R11158

## 第十一批 premium-upgrade 候选（2026-05-01 W1 探索，侯国 featured→premium）

- [x] R11161 | [[绛侯国]] | 16394B→18971B · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11162 | [[曲逆侯国]] | 13864B→15966B · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11163 | [[平阳侯国]] | 13723B→16037B · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11164 | [[建成侯国]] | 13018B→14761B · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11165 | [[颍阴侯国]] | 12732B→14695B · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11166 | [[淮阴侯国]] | 12495B→14917B · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11167 | [[盖侯国]] | 12480B→14136B · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11168 | [[武安侯国]] | 12264B→14097B · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11169 | [[棘蒲侯国]] | 11921B→13659B · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11170 | [[平津侯国]] | 11514B→13515B · featured→premium · type=侯国 | action: premium-upgrade

## 第十二批 premium-upgrade 候选（2026-05-01，侯国 featured→premium）

- [x] R11173 | [[辟阳侯国]] | 10918B→14892B(+3977) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11174 | [[留侯国]] | 10841B→14286B(+3448) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11175 | [[宣平侯国]] | 10750B→14117B(+3370) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11176 | [[长平侯国]] | 10549B→13608B(+3062) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11177 | [[曲周侯国]] | 10235B→13456B(+3224) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11178 | [[安国侯国]] | 10150B→13594B(+3447) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11179 | [[沛侯国]] | 9810B→13005B(+3195) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11180 | [[博望侯国]] | 9254B→12794B(+3540) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11181 | [[漯阴侯国]] | 9229B→12575B(+3349) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11183 | [[舞阳侯国]] | 8972B→12405B(+3436) · featured→premium · type=侯国 | action: premium-upgrade

## 第十三批 premium-upgrade 候选（2026-05-01，侯国 featured→premium）

- [x] R11184 | [[汾阴侯国]] | 8685B→12292B(+3610) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11185 | [[周阳侯国]] | 8360B→12269B(+3912) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11186 | [[东城侯国]] | 8330B→11723B(+3396) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11187 | [[章武侯国]] | 8249B→11973B(+3727) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11188 | [[堂邑侯国]] | 8136B→11489B(+3356) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11189 | [[翕侯国]] | 7925B→10595B(+2670) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11190 | [[南皮侯国]] | 7811B→10587B(+2779) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11191 | [[魏其侯国]] | 7796B→11019B(+3223) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11192 | [[从骠侯国]] | 7773B→10810B(+3037) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11193 | [[合骑侯国]] | 7518B→10763B(+3245) · featured→premium · type=侯国 | action: premium-upgrade

## 第十四批 premium-upgrade 候选（2026-05-01，侯国 featured→premium）

- [x] R11194 | [[汝阴侯国]] | 7220B→11532B(+4315) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11195 | [[冠军侯国]] | 7206B→10883B(+3680) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11197 | [[蒲侯国]] | 7103B→9961B(+2861) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11198 | [[建陵侯国]] | 7102B→11001B(+3902) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11199 | [[戴侯国]] | 7062B→10431B(+3372) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11200 | [[臧马侯国]] | 6831B→10449B(+3621) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11201 | [[阳陵侯国]] | 6776B→10160B(+3387) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11202 | [[衍侯国]] | 6689B→9938B(+3252) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11203 | [[弓高侯国]] | 6613B→10934B(+4324) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11204 | [[乐安侯国]] | 6534B→10500B(+3966) · featured→premium · type=侯国 | action: premium-upgrade
## 第十五批 premium-upgrade 候选（2026-05-01，侯国 featured→premium）
- [x] R11206 | [[汁方侯国]] | 6130B→9398B(+3271) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11207 | [[宁陵侯国]] | 5970B→9549B(+3582) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11208 | [[杜衍侯国]] | 5591B→8780B(+3192) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11209 | [[安丘侯国]] | 5544B→8205B(+2664) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11210 | [[昌武侯国]] | 5541B→8167B(+2629) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11211 | [[浩侯国]] | 5400B→8846B(+3446) · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11212 | [[离侯国]] | 5335B→6679B · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11213 | [[安阳侯国]] | 5188B→9547B · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11214 | [[信武侯国]] | 5110B→9426B · featured→premium · type=侯国 | action: premium-upgrade
- [x] R11215 | [[故安侯国]] | 5010B→10025B · featured→premium · type=侯国 | action: premium-upgrade

## 第一批 standard→featured 升级候选（2026-05-01 W1 探索，standard person → featured）

- [x] R11216 | [[吴广]] | 7690B→11091B(+3401) · standard→featured · type=person | action: enrich-quality
- [x] R11217 | [[韩康子]] | 7291B · standard · type=person | action: enrich-quality
- [x] R11218 | [[新垣衍]] | 6819B · standard · type=person | action: enrich-quality
- [x] R11219 | [[魏齐]] | 6302B · standard · type=person | action: enrich-quality
- [x] R11220 | [[鲁文公]] | 6283B · standard · type=person | action: enrich-quality
- [x] R11221 | [[公孙衍]] | 6187B · standard · type=person | action: enrich-quality
- [x] R11222 | [[陈宣公]] | 6132B · standard · type=person | action: enrich-quality
- [x] R11224 | [[汉惠帝]] | 5791B · standard · type=person | action: enrich-quality

## 第二批 standard→featured 升级候选（2026-05-01，standard person → featured）

- [x] R11226 | [[武庚禄父]] | 6353B · standard · type=person | action: enrich-quality
- [x] R11227 | [[赵食其]] | 6211B · standard · type=person | action: enrich-quality
- [x] R11228 | [[魏尚]] | 6167B · standard · type=person | action: enrich-quality
- [x] R11229 | [[广国]] | 6143B · standard · type=person | action: enrich-quality
- [x] R11230 | [[卫黔牟]] | 6103B · standard · type=person | action: enrich-quality
- [x] R11231 | [[郑简公]] | 6100B · standard · type=person | action: enrich-quality
- [x] R11232 | [[姬喜]] | 6037B · standard · type=person | action: enrich-quality
- [x] R11233 | [[华督]] | 6004B · standard · type=person | action: enrich-quality

## 第三批 standard→featured 升级候选（2026-05-01，standard person → featured）

- [x] R11234 | [[蘧伯玉]] | 5992B · standard · type=person | action: enrich-quality
- [x] R11235 | [[叔瞻]] | 5984B · standard · type=person | action: enrich-quality
- [x] R11236 | [[田文子]] | 5915B · standard · type=person | action: enrich-quality
- [x] R11237 | [[华元]] | 5894B · standard · type=person | action: enrich-quality
- [x] R11238 | [[栗太子]] | 5874B · standard · type=person | action: enrich-quality
- [x] R11239 | [[馀祭]] | 5827B · standard · type=person | action: enrich-quality
- [x] R11240 | [[专诸]] | 5798B · standard · type=person | action: enrich-quality
- [x] R11241 | [[卫元君]] | 5781B · standard · type=person | action: enrich-quality

## 第四批 standard→featured 升级候选（2026-05-01，standard person → featured）

- [x] R11242 | [[庞涓]] | 5706B · standard · type=person | action: enrich-quality
- [x] R11243 | [[平阳主]] | 5611B · standard · type=person | action: enrich-quality
- [x] R11244 | [[尹齐]] | 5457B · standard · type=person | action: enrich-quality
- [x] R11245 | [[胶西王刘卬]] | 5445B · standard · type=person | action: enrich-quality
- [x] R11246 | [[乐臣公]] | 5418B · standard · type=person | action: enrich-quality
- [x] R11247 | [[季文子]] | 5405B · standard · type=person | action: enrich-quality
- [x] R11248 | [[徐厉]] | 5254B · standard · type=person | action: enrich-quality
- [x] R11249 | [[石乞]] | 5227B · standard · type=person | action: enrich-quality

## 第五批 standard→featured 升级候选（2026-05-01，standard person → featured）

- [x] R11250 | [[子玉]] | 5226B · standard · type=person | action: enrich-quality
- [x] R11252 | [[周舍]] | 5193B · standard · type=person | action: enrich-quality
- [x] R11253 | [[卫太子]] | 5178B · standard · type=person | action: enrich-quality
- [x] R11254 | [[宰予]] | 5120B · standard · type=person | action: enrich-quality
- [x] R11255 | [[优孟]] | 5119B · standard · type=person | action: enrich-quality
- [x] R11256 | [[酈商]] | 5103B · standard · type=person | action: enrich-quality
- [x] R11257 | [[萧望之]] | 5055B · standard · type=person | action: enrich-quality
- [x] R11258 | [[蔡女]] | 5032B · standard · type=person | action: enrich-quality

## 第六批 standard→featured 升级候选（2026-05-01，standard person → featured）
- [x] R11259 | [[吕须]] | qs=46 · standard · type=person | action: enrich-quality
- [x] R11260 | [[中衍]] | qs=45 · standard · type=person | action: enrich-quality
- [x] R11261 | [[于定国]] | qs=45 · standard · type=person | action: enrich-quality
- [x] R11262 | [[伉]] | qs=45 · standard · type=person | action: enrich-quality
- [x] R11263 | [[公子比]] | qs=45 · standard · type=person | action: enrich-quality
- [x] R11264 | [[养由基]] | qs=45 · standard · type=person | action: enrich-quality
- [x] R11265 | [[叔振铎]] | qs=45 · standard · type=person | action: enrich-quality
- [x] R11266 | [[大骆]] | qs=45 · standard · type=person | action: enrich-quality

## 第七批 standard→featured 升级候选（2026-05-01，standard person → featured）
- [x] R11267 | [[宁成]] | qs=45 · standard · type=person | action: enrich-quality
- [x] R11268 | [[宋昭公]] | qs=45 · standard · type=person | action: enrich-quality
- [x] R11269 | [[李敢]] | qs=45 · standard · type=person | action: enrich-quality
- [x] R11270 | [[董安于]] | qs=45 · standard · type=person | action: enrich-quality
- [x] R11271 | [[蔡仲]] | qs=45 · standard · type=person | action: enrich-quality
- [x] R11272 | [[蔡灵侯]] | qs=45 · standard · type=person | action: enrich-quality
- [x] R11273 | [[虢叔]] | qs=45 · standard · type=person | action: enrich-quality
- [x] R11274 | [[许由]] | qs=45 · standard · type=person | action: enrich-quality

## 第八批 standard→featured 升级候选（2026-05-01，standard person → featured）
- [x] R11276 | [[高不识]] | qs=45 · standard · type=person | action: enrich-quality
- [x] R11277 | [[韩懿侯]] | qs=45 · standard · type=person | action: enrich-quality
- [x] R11278 | [[龙贾]] | qs=44 · standard · type=person | action: enrich-quality
- [x] R11279 | [[齐晏孺子]] | qs=44 · standard · type=person | action: enrich-quality
- [x] R11280 | [[齐昭公]] | qs=44 · standard · type=person | action: enrich-quality
- [x] R11281 | [[齐懿公]] | qs=44 · standard · type=person | action: enrich-quality
- [x] R11282 | [[齐康公]] | qs=44 · standard · type=person | action: enrich-quality
- [x] R11283 | [[齐哀王]] | qs=44 · standard · type=person | action: enrich-quality

---

## P1 standard→featured 候选人（2026-05-01 W1 探索，standard→featured）

- [x] R11286 | [[秦简公]] | 5689B · type=person · src=秦本纪/秦始皇本纪/十二诸侯年表/六国年表 | action: enrich-quality
- [x] R11287 | [[原宪]] | 5664B · type=person · src=仲尼弟子列传/游侠列传/货殖列传 | action: enrich-quality
- [x] R11288 | [[齐厉王]] | 5662B · type=person · src=齐悼惠王世家/汉兴以来诸侯王年表/太史公自序 | action: enrich-quality
- [x] R11290 | [[邴吉]] | 5628B · type=person · src=建元以来侯者年表/张丞相列传 | action: enrich-quality
- [x] R11289 | [[苌弘]] | 5582B · type=person · src=乐书/天官书/封禅书 | action: enrich-quality
- [x] R11291 | [[晋昭公]] | 5548B · type=person · src=晋世家/十二诸侯年表/齐太公世家 | action: enrich-quality
- [x] R11292 | [[秦康公]] | 5441B · type=person · src=秦本纪/十二诸侯年表 | action: enrich-quality
- [x] R11293 | [[管至父]] | 5458B · type=person · src=齐太公世家/十二诸侯年表 | action: enrich-quality

## 来自 discover_kg (kg top-N 缺 wiki 页)

- [ ] 宣孟: `create-stub` (refs=22/章=5) [源:A] [P1] [2026-05-01]

---

## P1 standard→featured 第十批（2026-05-01 W1 探索，standard→featured）

- [x] R11294 | [[代成君]] | 5635B · type=person · src=赵世家/六国年表 | action: enrich-quality
- [x] R11295 | [[韩釐王]] | 5735B · type=person · src=韩世家/留侯世家 | action: enrich-quality
- [x] R11297 | [[魏相]] | 5619B · type=person · src=建元以来侯者年表/张丞相列传 | action: enrich-quality
- [x] R11300 | [[破奴]] | 5556B · type=person · src=大宛列传/建元以来侯者年表 | action: enrich-quality
- [x] R11302 | [[右渠]] | 5537B · type=person · src=朝鲜列传 | action: enrich-quality
- [x] R11305 | [[陈招]] | 5523B · type=person · src=陈杞世家 | action: enrich-quality
- [x] R11307 | [[薛泽]] | 5488B · type=person · src=张丞相列传/韩长孺列传 | action: enrich-quality
- [x] R11309 | [[周昭王]] | 5479B · type=person · src=周本纪 | action: enrich-quality

## P1 standard→featured 第十一批（2026-05-01，standard→featured）

- [x] R11312 | [[武丁]] | 5541B · type=person · src=殷本纪 | action: enrich-quality
- [x] R11314 | [[胶东康王]] | 5539B · type=person · src=汉兴以来诸侯王年表/三王世家/齐悼惠王世家 | action: enrich-quality
- [x] R11316 | [[宋元公]] | 5460B · type=person · src=宋微子世家 | action: enrich-quality
- [x] R11318 | [[子纠]] | 5455B · type=person · src=齐太公世家/鲁周公世家/管晏列传 | action: enrich-quality
- [x] R11320 | [[宋桓公]] | 5436B · type=person · src=宋微子世家 | action: enrich-quality
- [x] R11322 | [[柳下惠]] | 5371B · type=person · src=鲁周公世家/管晏列传/太史公自序 | action: enrich-quality
- [x] R11324 | [[匡衡]] | 5367B · type=person · src=建元以来侯者年表/张丞相列传 | action: enrich-quality
- [x] R11326 | [[隰朋]] | 5336B · type=person · src=齐太公世家/管晏列传 | action: enrich-quality

## P1 standard→featured 第十二批（2026-05-01，standard→featured）

- [x] R11330 | [[鲁元]] | 5314B · type=person · src=鲁周公世家 | action: enrich-quality
- [x] R11331 | [[孺子]] | 5298B · type=person · src=齐太公世家/十二诸侯年表 | action: enrich-quality
- [x] R11332 | [[韩献子]] | 5278B · type=person · src=晋世家/韩世家 | action: enrich-quality
- [x] R11333 | [[郑悼公]] | 5263B · type=person · src=郑世家/十二诸侯年表 | action: enrich-quality
- [x] R11334 | [[无彊]] | 5259B · type=person · src=越王句践世家 | action: enrich-quality
- [x] R11335 | [[卫釐侯]] | 5256B · type=person · src=卫康叔世家/十二诸侯年表 | action: enrich-quality
- [x] R11336 | [[厓有]] | 5246B · type=person · src=建元以来侯者年表/卫将军骠骑列传 | action: enrich-quality
- [x] R11337 | [[楚幽王]] | 5246B · type=person · src=楚世家/六国年表 | action: enrich-quality

## P1 standard→featured 第十三批（2026-05-01，standard→featured）

- [x] R11339 | [[李哆]] | 5236B · type=person · src=大宛列传 | action: enrich-quality
- [x] R11340 | [[东周釐王]] | 5225B · type=person · src=周本纪/晋世家 | action: enrich-quality
- [x] R11341 | [[郑声公]] | 5190B · type=person · src=郑世家/十二诸侯年表/六国年表 | action: enrich-quality
- [x] R11342 | [[张仲]] | 5173B · type=person · src=陈丞相世家/张释之冯唐列传/日者列传 | action: enrich-quality
- [x] R11343 | [[程郑]] | 5172B · type=person · src=司马相如列传/货殖列传 | action: enrich-quality
- [x] R11344 | [[韦玄成]] | 5171B · type=person · src=张丞相列传/汉兴以来将相名臣年表 | action: enrich-quality
- [x] R11345 | [[司马昌]] | 5154B · type=person · src=太史公自序 | action: enrich-quality
- [x] R11346 | [[秦桓公]] | 5142B · type=person · src=秦本纪/十二诸侯年表 | action: enrich-quality

## P1 standard→featured 第十四批（2026-05-01，standard→featured）

- [x] R11347 | [[宰孔]] | 5135B · type=person · src=齐太公世家/晋世家 | action: enrich-quality
- [x] R11348 | [[越人]] | 5130B · type=person · src=六国年表/扁鹊仓公列传 | action: enrich-quality
- [x] R11349 | [[子服景伯]] | 5126B · type=person · src=鲁周公世家/仲尼弟子列传 | action: enrich-quality
- [x] R11350 | [[赵惠后]] | 5122B · type=person · src=赵世家/六国年表 | action: enrich-quality
- [x] R11352 | [[姬辄]] | 5119B · type=person · src=卫康叔世家 | action: enrich-quality
- [x] R11353 | [[解扬]] | 5113B · type=person · src=郑世家/晋世家 | action: enrich-quality
- [x] R11354 | [[司马卬]] | 5102B · type=person · src=太史公自序/项羽本纪 | action: enrich-quality
- [x] R11355 | [[伯服]] | 5101B · type=person · src=周本纪/郑世家 | action: enrich-quality

## P1 standard→featured 第十五批（2026-05-01，standard→featured）

- [x] R11356 | [[缪嬴]] | 5093B · type=person · src=晋世家 | action: enrich-quality
- [x] R11357 | [[蔡平侯]] | 5083B · type=person · src=管蔡世家/十二诸侯年表 | action: enrich-quality
- [x] R11358 | [[匈奴单于头曼]] | 5074B · type=person · src=十二诸侯年表/宋微子世家/匈奴列传 | action: enrich-quality
- [x] R11359 | [[张黡]] | 5071B · type=person · src=张耳陈馀列传 | action: enrich-quality
- [x] R11360 | [[郁成王]] | 5069B · type=person · src=大宛列传 | action: enrich-quality
- [x] R11361 | [[齐懿仲]] | 5068B · type=person · src=陈杞世家/田敬仲完世家 | action: enrich-quality
- [x] R11362 | [[周灵王]] | 5057B · type=person · src=周本纪/十二诸侯年表/封禅书 | action: enrich-quality
- [x] R11363 | [[孔父]] | 5052B · type=person · src=十二诸侯年表/宋微子世家/郑世家 | action: enrich-quality
- [x] R11364 | [[楚简王]] | 5051B · type=person · src=楚世家/六国年表 | action: enrich-quality
- [x] R11365 | [[赵胡]] | 5047B · type=person · src=南越列传 | action: enrich-quality
- [x] R11366 | [[楚王刘戊]] | 5036B · type=person · src=吴王濞列传 | action: enrich-quality
- [x] R11367 | [[周共王]] | 5035B · type=person · src=周本纪/汉兴以来诸侯王年表 | action: enrich-quality
- [x] R11368 | [[周灶]] | 5033B · type=person · src=高祖功臣侯者年表/汉兴以来将相名臣年表/匈奴列传 | action: enrich-quality
- [x] R11369 | [[他]] | 5029B · type=person · src=十二诸侯年表/田敬仲完世家 | action: enrich-quality
- [x] R11370 | [[孟懿子]] | 5001B · type=person · src=鲁周公世家/孔子世家 | action: enrich-quality

## P1 standard→featured 第十六批（2026-05-01，standard→featured 4800B档）✓ 完成

- [x] R11371 | [[子带]] | 4999B · type=person · src=周本纪/匈奴列传 | action: enrich-quality
- [x] R11372 | [[张子卿]] | 4985B · type=person · src=荆燕世家 | action: enrich-quality
- [x] R11373 | [[襄仲]] | 4962B · type=person · src=十二诸侯年表/鲁周公世家 | action: enrich-quality
- [x] R11374 | [[荀林父]] | 4950B · type=person · src=十二诸侯年表/晋世家 | action: enrich-quality
- [x] R11376 | [[子驷]] | 4927B · type=person · src=十二诸侯年表/郑世家 | action: enrich-quality
- [x] R11377 | [[范献子]] | 4922B · type=person · src=晋世家/魏世家 | action: enrich-quality
- [x] R11378 | [[淮南太子迁]] | 4914B · type=person · src=淮南衡山列传 | action: enrich-quality
- [x] R11381 | [[济南王（反诛）]] | 4912B · type=person · src=孝景本纪/齐悼惠王世家/汉兴以来诸侯王年表 | action: enrich-quality
- [x] R11382 | [[宋成公]] | 4892B · type=person · src=十二诸侯年表/宋微子世家 | action: enrich-quality
- [x] R11383 | [[周定公]] | 4866B · type=person · src=周本纪/燕召公世家 | action: enrich-quality
- [x] R11384 | [[周兰]] | 4835B · type=person · src=高祖本纪/曹相国世家/樊郦滕灌列传 | action: enrich-quality
- [x] R11385 | [[公孙戎奴]] | 4828B · type=person · src=建元以来侯者年表/卫将军骠骑列传 | action: enrich-quality
- [x] R11386 | [[郑子亹]] | 4815B · type=person · src=十二诸侯年表/郑世家 | action: enrich-quality
- [x] R11387 | [[楚宣王]] | 4808B · type=person · src=六国年表/楚世家 | action: enrich-quality
- [x] R11388 | [[陈穆公]] | 4804B · type=person · src=十二诸侯年表/陈杞世家 | action: enrich-quality

## P1 standard→featured 第十七批（2026-05-01，standard→featured 4700B档）

- [x] P1 | [[刘胡]] | 4789B→8747B · type=person · src=汉兴以来诸侯王年表/建元已来王子侯者年表 | action: enrich-quality
- [x] P1 | [[鬼臾区]] | 4789B→9517B · type=person · src=孝武本纪/封禅书 | action: enrich-quality
- [x] P1 | [[郑昌]] | 4784B→10005B · type=person · src=项羽本纪/高祖本纪/秦楚之际月表 | action: enrich-quality
- [x] P1 | [[张侈]] | 4782B→9900B · type=person · src=吕太后本纪/惠景间侯者年表/张耳陈馀列传 | action: enrich-quality
- [x] P1 | [[晋幽公]] | 4778B→10331B · type=person · src=晋世家/六国年表/十二诸侯年表 | action: enrich-quality
- [x] P1 | [[暴鸢]] | 4766B→10426B · type=person · src=秦本纪/六国年表/韩世家/穰侯列传 | action: enrich-quality
- [x] P1 | [[臧文仲]] | 4765B→10097B · type=person · src=十二诸侯年表/宋微子世家/仲尼弟子列传 | action: enrich-quality
- [x] P1 | [[魏景湣王]] | 4760B→10168B · type=person · src=六国年表/魏世家 | action: enrich-quality
- [x] P1 | [[宋庄公]] | 4753B→10064B · type=person · src=十二诸侯年表/郑世家/田敬仲完世家 | action: enrich-quality
- [x] P1 | [[公子咎]] | 4747B→10232B · type=person · src=周本纪/韩世家 | action: enrich-quality
- [x] P1 | [[岑娶]] | 4746B→10373B · type=person · src=大宛列传 | action: enrich-quality
- [x] P1 | [[蔡叔度]] | 4743B→10029B · type=person · src=周本纪/三代世表/管蔡世家 | action: enrich-quality
- [x] P1 | [[虢射]] | 4741B→10043B · type=person · src=秦本纪/晋世家 | action: enrich-quality
- [x] P1 | [[周最]] | 4735B→9857B · type=person · src=秦始皇本纪/孟尝君列传 | action: enrich-quality
- [x] P1 | [[侯公]] | 4728B→9638B · type=person · src=秦始皇本纪/项羽本纪/高祖功臣侯者年表 | action: enrich-quality
- [x] P1 | [[象]] | 4720B→10116B · type=person · src=五帝本纪 | action: enrich-quality
- [x] P1 | [[申差]] | 4709B→10239B · type=person · src=秦本纪/六国年表/韩世家/张仪列传 | action: enrich-quality
