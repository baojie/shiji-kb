#!/usr/bin/env node
/**
 * Lint工具：验证 special-pronunciation.json
 *
 * 功能：
 * 1. 检测pinyin-pro已正确处理的词条（应删除）
 * 2. 检测需要保留的词条（pinyin-pro处理错误）
 * 3. 自动清理模式：删除不必要的词条
 *
 * 用法：
 *   node scripts/lint_pronunciation_dict.js              # 检查模式
 *   node scripts/lint_pronunciation_dict.js --fix        # 自动修复模式
 */

const { pinyin } = require('pinyin-pro');
const fs = require('fs');

const specialPronFile = 'docs/data/special-pronunciation.json';

function lintPronunciationDict(autoFix = false) {
  // 读取文件
  const data = JSON.parse(fs.readFileSync(specialPronFile, 'utf-8'));

  let totalEntries = 0;
  let unnecessaryCount = 0;
  let necessaryCount = 0;

  const unnecessaryEntries = [];
  const necessaryEntries = [];

  // 检查每个词条
  data.entries.forEach((entry, index) => {
    totalEntries++;
    const text = entry.text;
    const expectedPinyin = entry.pinyin;

    // 使用 pinyin-pro 转换
    const actualPinyin = pinyin(text, {
      toneType: 'symbol',
      type: 'array'
    });

    // 比较结果
    const isCorrect = JSON.stringify(actualPinyin) === JSON.stringify(expectedPinyin);

    if (isCorrect) {
      unnecessaryCount++;
      unnecessaryEntries.push({
        index: index,
        text,
        pinyin: expectedPinyin,
        note: entry.note
      });
    } else {
      necessaryCount++;
      necessaryEntries.push(entry);
    }
  });

  // 输出结果
  console.log('=== 拼音词表Lint检查结果 ===\n');
  console.log(`文件: ${specialPronFile}`);
  console.log(`总词条数: ${totalEntries}`);
  console.log(`✓ 需要保留: ${necessaryCount} (pinyin-pro处理错误)`);
  console.log(`✗ 应该删除: ${unnecessaryCount} (pinyin-pro已正确处理)`);
  console.log('');

  if (unnecessaryCount > 0) {
    console.log('=== 应该删除的词条（pinyin-pro已正确处理）===\n');
    unnecessaryEntries.forEach(item => {
      console.log(`  [${item.index + 1}] ${item.text} (${item.pinyin.join(' ')})`);
    });
    console.log('');
  }

  // 自动修复模式
  if (autoFix && unnecessaryCount > 0) {
    console.log('🔧 自动修复模式：删除不必要的词条...\n');

    // 更新版本号
    const oldVersion = data.version;
    const versionParts = oldVersion.split('.');
    versionParts[1] = String(parseInt(versionParts[1]) + 1);
    const newVersion = versionParts.join('.');

    // 构建新数据
    const newData = {
      version: newVersion,
      description: data.description,
      lastUpdate: new Date().toISOString().split('T')[0],
      entries: necessaryEntries
    };

    // 备份原文件
    const backupFile = specialPronFile + '.backup';
    fs.copyFileSync(specialPronFile, backupFile);
    console.log(`✓ 已备份原文件到: ${backupFile}`);

    // 写入新文件
    fs.writeFileSync(
      specialPronFile,
      JSON.stringify(newData, null, 2) + '\n',
      'utf-8'
    );

    console.log(`✓ 已更新 ${specialPronFile}`);
    console.log(`  - 删除词条: ${unnecessaryCount} 个`);
    console.log(`  - 保留词条: ${necessaryCount} 个`);
    console.log(`  - 版本号: ${oldVersion} → ${newVersion}`);
    console.log('');
  } else if (unnecessaryCount > 0) {
    console.log('💡 提示: 使用 --fix 参数自动删除不必要的词条\n');
    process.exit(1);
  }

  if (unnecessaryCount === 0) {
    console.log('✓ 所有词条都是必需的（pinyin-pro无法正确处理）\n');
  }
}

// 命令行参数
const autoFix = process.argv.includes('--fix');

try {
  lintPronunciationDict(autoFix);
} catch (error) {
  console.error('错误:', error.message);
  process.exit(1);
}
