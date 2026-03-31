# 智能分段功能调试指南

## 问题：段落11、11.1-11.4、11.5没有合并

### 调试步骤

1. **打开浏览器开发者工具**
   - 按 F12 或右键 → 检查

2. **检查类是否正确添加**

   在 Console 中执行：
   ```javascript
   // 检查body类
   console.log('Body has merge-paragraphs:', document.body.classList.contains('merge-paragraphs'));

   // 检查段落11
   const p11 = document.querySelector('a[id="pn-11"]').parentElement;
   console.log('段落11的类:', p11.className);
   console.log('段落11的display:', getComputedStyle(p11).display);

   // 检查ul
   const ul = document.querySelector('ul.has-sub-paragraph');
   console.log('UL存在:', !!ul);
   if (ul) {
       console.log('UL的类:', ul.className);
       console.log('UL的display:', getComputedStyle(ul).display);
   }

   // 检查li 11.1
   const li111 = document.querySelector('a[id="pn-11.1"]').parentElement;
   console.log('Li 11.1的类:', li111.className);
   console.log('Li 11.1的display:', getComputedStyle(li111).display);

   // 检查段落11.5
   const p115 = document.querySelector('a[id="pn-11.5"]').parentElement;
   console.log('段落11.5的类:', p115.className);
   console.log('段落11.5的display:', getComputedStyle(p115).display);
   ```

3. **预期结果**
   ```
   Body has merge-paragraphs: true
   段落11的类: top-paragraph
   段落11的display: block
   UL存在: true
   UL的类: has-sub-paragraph
   UL的display: inline
   Li 11.1的类: sub-paragraph
   Li 11.1的display: inline
   段落11.5的类: sub-paragraph
   段落11.5的display: inline
   ```

4. **检查CSS加载**

   ```javascript
   // 检查CSS规则是否存在
   const styles = Array.from(document.styleSheets);
   const shijiStyles = styles.find(s => s.href && s.href.includes('shiji-styles.css'));
   console.log('shiji-styles.css loaded:', !!shijiStyles);

   // 搜索merge-paragraphs规则
   if (shijiStyles) {
       const rules = Array.from(shijiStyles.cssRules || shijiStyles.rules);
       const mergeRules = rules.filter(r => r.selectorText && r.selectorText.includes('merge-paragraphs'));
       console.log('找到的merge-paragraphs规则数:', mergeRules.length);
       mergeRules.forEach(r => console.log(r.selectorText));
   }
   ```

5. **手动测试CSS**

   如果类都正确，但display不对，在 Console 中手动设置：
   ```javascript
   // 强制设置display
   document.querySelectorAll('li.sub-paragraph').forEach(li => {
       li.style.display = 'inline';
       li.style.margin = '0';
       li.style.listStyle = 'none';
   });

   document.querySelectorAll('ul.has-sub-paragraph').forEach(ul => {
       ul.style.display = 'inline';
       ul.style.margin = '0';
       ul.style.padding = '0';
   });

   document.querySelectorAll('p.sub-paragraph').forEach(p => {
       p.style.display = 'inline';
       p.style.margin = '0';
   });
   ```

6. **检查元素结构**

   在 Elements 面板中，找到段落11附近的HTML：
   ```html
   <p class="top-paragraph">...</p>  <!-- 应该有这个类 -->
   <ul class="has-sub-paragraph">     <!-- 应该有这个类 -->
     <li class="sub-paragraph">...</li>  <!-- 应该有这个类 -->
     ...
   </ul>
   <p class="sub-paragraph">...</p>   <!-- 11.5应该有这个类 -->
   ```

## 可能的问题

### 问题1：JavaScript没有执行
- **症状**：元素没有 sub-paragraph/top-paragraph 类
- **解决**：检查Console是否有JavaScript错误

### 问题2：CSS没有加载
- **症状**：元素有类，但display仍是block
- **解决**：清除浏览器缓存，强制刷新（Ctrl+Shift+R）

### 问题3：CSS被其他规则覆盖
- **症状**：Elements面板中看到样式被划掉
- **解决**：在CSS中使用 !important（已添加）

### 问题4：浏览器缓存
- **症状**：修改代码后没有变化
- **解决**：
  1. 清除缓存
  2. 硬性重新加载（Ctrl+Shift+R）
  3. 或者在隐身模式中打开

## 快速修复脚本

如果以上都不行，在Console中执行这个完整的修复脚本：

```javascript
// 完整的段落合并脚本
(function() {
    // 1. 为所有段落和列表项添加类
    document.querySelectorAll('p, li').forEach(elem => {
        const paraNum = elem.querySelector('a.para-num');
        if (paraNum && paraNum.id && paraNum.id.startsWith('pn-')) {
            const numPart = paraNum.id.substring(3);
            const topLevelNum = numPart.split('.')[0];

            if (numPart.includes('.')) {
                elem.classList.add('sub-paragraph');
                elem.setAttribute('data-top-level', topLevelNum);

                if (elem.tagName === 'LI') {
                    const parentUl = elem.parentElement;
                    if (parentUl && parentUl.tagName === 'UL') {
                        parentUl.classList.add('has-sub-paragraph');
                    }
                }

                // 直接设置样式
                elem.style.display = 'inline';
                elem.style.margin = '0';
                elem.style.padding = '0';
                if (elem.tagName === 'LI') {
                    elem.style.listStyle = 'none';
                }

                // 隐藏编号
                if (paraNum) {
                    paraNum.style.display = 'none';
                }
            } else {
                elem.classList.add('top-paragraph');
                elem.setAttribute('data-top-level', topLevelNum);
            }
        }
    });

    // 2. 处理ul
    document.querySelectorAll('ul.has-sub-paragraph').forEach(ul => {
        ul.style.display = 'inline';
        ul.style.margin = '0';
        ul.style.padding = '0';
    });

    console.log('段落合并脚本执行完成！');
    console.log('顶级段落:', document.querySelectorAll('.top-paragraph').length);
    console.log('子段落:', document.querySelectorAll('.sub-paragraph').length);
    console.log('含子段落的UL:', document.querySelectorAll('.has-sub-paragraph').length);
})();
```

执行后应该立即看到段落合并效果。
