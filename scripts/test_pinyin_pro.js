#!/usr/bin/env node
/**
 * 测试 pinyin-pro 对词组的拼音转换结果
 * 用于验证 special-pronunciation.json 中的词条是否真的需要特殊标注
 */

const { pinyin } = require('pinyin-pro');
const fs = require('fs');

// 读取 special-pronunciation.json
const specialPronFile = 'docs/data/special-pronunciation.json';
const data = JSON.parse(fs.readFileSync(specialPronFile, 'utf-8'));

console.log('=== 测试 pinyin-pro 对 special-pronunciation.json 词条的处理 ===\n');

let totalEntries = 0;
let correctEntries = 0;
let incorrectEntries = 0;

const needsSpecialHandling = [];
const unnecessaryEntries = [];

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
    correctEntries++;
    unnecessaryEntries.push({
      index: index + 1,
      text,
      pinyin: expectedPinyin,
      note: entry.note
    });
  } else {
    incorrectEntries++;
    needsSpecialHandling.push({
      index: index + 1,
      text,
      expected: expectedPinyin,
      actual: actualPinyin,
      note: entry.note
    });
  }
});

console.log(`总词条数: ${totalEntries}`);
console.log(`pinyin-pro 正确: ${correctEntries} (${(correctEntries/totalEntries*100).toFixed(1)}%)`);
console.log(`pinyin-pro 错误: ${incorrectEntries} (${(incorrectEntries/totalEntries*100).toFixed(1)}%)`);
console.log('\n');

if (unnecessaryEntries.length > 0) {
  console.log('=== pinyin-pro 已正确处理（可删除的词条）===\n');
  unnecessaryEntries.forEach(item => {
    console.log(`[${item.index}] ${item.text}`);
    console.log(`  拼音: ${item.pinyin.join(' ')}`);
    console.log(`  说明: ${item.note}`);
    console.log('');
  });
}

if (needsSpecialHandling.length > 0) {
  console.log('\n=== pinyin-pro 处理错误（需要保留的词条）===\n');
  needsSpecialHandling.forEach(item => {
    console.log(`[${item.index}] ${item.text}`);
    console.log(`  期望: ${item.expected.join(' ')}`);
    console.log(`  实际: ${item.actual.join(' ')}`);
    console.log(`  说明: ${item.note}`);
    console.log('');
  });
}

// 统计结果
console.log('\n=== 统计结果 ===');
console.log(`需要保留的词条: ${needsSpecialHandling.length}`);
console.log(`可以删除的词条: ${unnecessaryEntries.length}`);
console.log(`\n建议: 删除 ${unnecessaryEntries.length} 个不必要的词条，只保留 pinyin-pro 无法正确处理的 ${needsSpecialHandling.length} 个词条。`);
