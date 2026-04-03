# 禁止命令分析与建议

## 一、当前 `.claude/settings.json` 中的 deny 列表

```json
"deny": [
  "Bash(git checkout *)",
  "Bash(git restore *)",
  "Bash(git reset --hard*)"
]
```

## 二、需要添加的禁止命令（基于SKILL分析）

### 2.1 Git破坏性命令（高优先级）

#### 已有禁令（保持）
```json
"Bash(git checkout *)",      // 覆盖工作区文件
"Bash(git restore *)",        // 同上
"Bash(git reset --hard*)"     // 完全重置，丢失所有修改
```

#### 建议新增
```json
// Git强制操作
"Bash(git push --force*)",           // 强制推送，覆盖远程历史
"Bash(git push -f*)",                // 同上（简写）
"Bash(git push --force-with-lease*)", // 带租约的强制推送（除非用户明确授权）

// Git提交修改（需用户明确授权）
"Bash(git commit --amend*)",         // 修改最近提交（可能覆盖他人commit）
"Bash(git commit --no-verify*)",     // 跳过pre-commit hooks
"Bash(git commit -n*)",              // 同上（简写）

// Git历史重写
"Bash(git rebase -i*)",              // 交互式变基（需要交互输入）
"Bash(git rebase --interactive*)",   // 同上
"Bash(git filter-branch*)",          // 重写Git历史（极度危险）

// Git添加文件（擅自添加未暂存文件）
"Bash(git add -A*)",                 // 添加所有文件
"Bash(git add .*)",                  // 添加所有文件（glob模式）
"Bash(git add --all*)",              // 同上（完整写法）
```

### 2.2 文件破坏性操作（高优先级）

```json
// 删除操作（不可逆）
"Bash(rm -rf*)",                     // 递归强制删除
"Bash(rm -fr*)",                     // 同上
"Bash(rm --recursive --force*)",     // 完整写法

// 覆盖操作
"Bash(mv -f*)",                      // 强制覆盖移动
"Bash(cp -rf*)",                     // 递归强制复制覆盖

// 编辑器自动修改（批量修改风险）
"Bash(sed -i*)",                     // 直接修改文件（除非用户明确要求）
```

### 2.3 标注完整性破坏（中优先级）

根据 SKILL_03a 和 SKILL_01g，标注工作严禁修改原文字符。以下命令可能破坏标注完整性：

```json
// 批量文本替换（可能破坏原文）
"Bash(*sed -i*chapter_md/*)",        // 对标注文件使用sed
"Bash(*awk*chapter_md/*-i*)",        // 对标注文件使用awk -i

// 字符编码转换（可能改变字符）
"Bash(iconv*)",                      // 编码转换
"Bash(dos2unix*chapter_md/*)",       // 换行符转换
"Bash(unix2dos*chapter_md/*)",       // 同上
```

**注意**：这些命令并非绝对禁止，但需要通过专门的Python脚本执行，并验证文本完整性。

### 2.4 数据文件直接修改（中优先级）

```json
// 核心数据文件（应通过脚本生成）
"Write(kg/entities/data/entity_index.json)",           // 实体索引（应由脚本生成）
"Write(kg/entities/data/disambiguation_map.json)",     // 消歧映射（应由脚本生成）
"Write(kg/entities/data/entity_aliases.json)",         // 别名映射（应由脚本生成）
```

**原因**：这些文件由脚本自动生成，手动修改会被下次构建覆盖，且容易引入不一致。

## 三、分级禁止策略

### Level 1：绝对禁止（无论任何理由）
```json
"Bash(git checkout *-- *)",          // git checkout恢复文件
"Bash(git restore *)",               // git restore恢复文件
"Bash(git reset --hard*)",           // 硬重置
"Bash(rm -rf /)",                    // 删除根目录（极度危险）
"Bash(rm -rf ~/*)",                  // 删除用户目录
```

### Level 2：需用户明确授权（默认禁止，用户确认后可执行）
```json
"Bash(git push --force*)",           // 强制推送
"Bash(git add -A*)",                 // 批量添加
"Bash(git commit --amend*)",         // 修改提交
"Bash(rm -rf*)",                     // 递归删除
"Bash(sed -i*chapter_md/*)",         // 修改标注文件
```

### Level 3：需验证完整性（执行后必须验证）
```json
"Edit(*chapter_md/*.tagged.md)",     // 编辑标注文件（需验证）
"Write(*chapter_md/*.tagged.md)",    // 写入标注文件（需验证）
```

## 四、建议的 `.claude/settings.json` 完整配置

```json
{
  "permissions": {
    "allow": [
      "Bash(env)",
      "Read(//home/baojie/**)",
      "Read(/**)",
      // ...（保留现有allow规则）
    ],
    "deny": [
      // === Git破坏性命令 ===
      "Bash(git checkout *-- *)",
      "Bash(git checkout -- *)",
      "Bash(git restore *)",
      "Bash(git reset --hard*)",
      "Bash(git push --force*)",
      "Bash(git push -f *)",
      "Bash(git push --force-with-lease*)",
      "Bash(git commit --amend*)",
      "Bash(git commit --no-verify*)",
      "Bash(git commit -n *)",
      "Bash(git rebase -i*)",
      "Bash(git rebase --interactive*)",
      "Bash(git filter-branch*)",
      "Bash(git add -A*)",
      "Bash(git add .*)",
      "Bash(git add --all*)",

      // === 文件破坏性操作 ===
      "Bash(rm -rf /*)",
      "Bash(rm -rf ~/*)",
      "Bash(rm -rf /home/*)",
      "Bash(rm -rf /usr/*)",
      "Bash(rm -rf /var/*)",
      "Bash(rm -rf /etc/*)",
      "Bash(mv -f *chapter_md/*)",

      // === 批量文本修改（标注文件） ===
      "Bash(sed -i *chapter_md/*)",
      "Bash(awk *chapter_md/* -i*)",
      "Bash(dos2unix *chapter_md/*)",
      "Bash(unix2dos *chapter_md/*)",

      // === 核心数据文件直接修改 ===
      "Write(kg/entities/data/entity_index.json)",
      "Write(kg/entities/data/disambiguation_map.json)",
      "Write(kg/entities/data/entity_aliases.json)"
    ],
    "additionalDirectories": [
      "/",
      "kg/chronology/data"
    ]
  }
}
```

## 五、特殊情况处理

### 5.1 允许的Git操作（安全）

```bash
# 查看状态（安全）
git status
git diff
git log
git show

# 提交（只提交已暂存文件，用户已控制）
git commit -m "message"

# 推送（非强制）
git push

# 添加特定文件（用户明确指定）
git add 具体文件路径
```

### 5.2 标注文件修改的正确流程

```bash
# ❌ 错误：直接使用sed修改
sed -i 's/〖@/〖#/g' chapter_md/*.tagged.md

# ✅ 正确：使用专门脚本
python scripts/migrate_official_to_identity.py --execute

# ✅ 验证完整性
python scripts/lint_text_integrity.py
```

### 5.3 数据文件更新的正确流程

```bash
# ❌ 错误：直接编辑JSON
Edit(kg/entities/data/entity_index.json)

# ✅ 正确：重新生成
python kg/entities/scripts/build_entity_index.py
```

## 六、执行清单

### 执行前检查
- [ ] 命令在deny列表中？→ 停止，告知用户
- [ ] 命令会修改工作区文件？→ 询问用户确认
- [ ] 命令会修改标注文件？→ 准备验证完整性

### 执行后验证
- [ ] 修改了标注文件？→ 运行 `lint_text_integrity.py`
- [ ] 修改了数据文件？→ 检查git diff确认变更合理
- [ ] 执行了Git操作？→ 运行 `git status` 确认状态

## 七、与SKILL文档的对应关系

| 禁止命令 | 依据SKILL | 章节 |
|---------|----------|------|
| `git checkout -- <file>` | SKILL_10c_Git代码版本管理规范 | §1.1禁止1 |
| `git add -A` | SKILL_10c_Git代码版本管理规范 | §1.1禁止2 |
| `git commit --no-verify` | SKILL_10c_Git代码版本管理规范 | §1.1禁止3 |
| `sed -i *chapter_md/*` | SKILL_03a_实体标注 | §1.4标注规则 |
| 编辑标注文件 | SKILL_03a_实体标注 | §1.4标注规则 |
| 直接修改数据JSON | SKILL_03a_实体标注 | §2.5阶段5 |

## 八、FAQ

### Q1: 为什么禁止 `git add -A`？
**A**: 可能添加用户不想提交的文件（临时文件、调试代码等）。应该让用户手动 `git add` 指定文件。

### Q2: 为什么禁止 `git commit --amend`？
**A**: 可能修改他人的提交。应该先检查 `git log -1 --format='%an %ae'` 确认作者。

### Q3: 为什么禁止 `sed -i` 修改标注文件？
**A**: 可能破坏原文字符。应该使用专门的Python脚本，并验证文本完整性。

### Q4: 为什么禁止直接写入数据JSON文件？
**A**: 这些文件由脚本自动生成，手动修改会被覆盖，且容易引入不一致。

---

**生成时间**：2026-04-03
**基于文档**：
- `SKILL_10c_Git代码版本管理规范.md`
- `SKILL_03a_实体标注.md`
- `SKILL_01g_标注符号集合原则.md`
- `CLAUDE.md`
