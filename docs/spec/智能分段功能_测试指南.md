# 智能分段功能测试指南

## 快速测试步骤

1. **启动服务器**
   ```bash
   cd /home/baojie/work/knowledge/shiji-kb
   ./serve.sh
   ```

2. **打开测试页面**
   - 在浏览器中访问：`http://localhost:8000/chapters/001_五帝本纪.html`

3. **测试功能**
   - 点击页面右上角的 ⚙️ 设置按钮
   - 找到"智能分段"选项（默认应该是勾选状态）
   - 取消勾选"智能分段"

4. **验证效果**

   **测试位置1**：查看页面开头的"黄帝"部分

   **智能分段开启时**（默认）：
   ```
   1 黄帝者，少典之子，姓公孙，名曰轩辕。生而神灵，弱而能言，幼而徇齐，长而敦敏，成而聪明。

   1.1 轩辕之时，神农氏世衰。诸侯相侵伐...（三战，然後得其志。）

   1.2 蚩尤作乱，不用帝命。於是黄帝乃徵师诸侯...（遂禽杀蚩尤。）

   1.3 而诸侯咸尊轩辕为天子...
   ```

   **智能分段关闭后**：
   ```
   1 黄帝者，少典之子，姓公孙，名曰轩辕。生而神灵，弱而能言，幼而徇齐，长而敦敏，成而聪明。轩辕之时，神农氏世衰。诸侯相侵伐...（三战，然後得其志。）蚩尤作乱，不用帝命。於是黄帝乃徵师诸侯...（遂禽杀蚩尤。）而诸侯咸尊轩辕为天子...
   ```

   **测试位置2**：查看"历法与农时"部分（段落11及其子段落）

   **智能分段开启时**（默认）：
   ```
   11 乃命羲、和，敬顺昊天，数法日月星辰，敬授民时。

   11.1 分命羲仲，居郁夷，曰旸谷...

   11.2 申命羲叔，居南交...

   11.3 申命和仲，居西土...

   11.4 申命和叔；居北方...

   11.5 岁三百六十六日，以闰月正四时...
   ```

   **智能分段关闭后**：
   ```
   11 乃命羲、和，敬顺昊天，数法日月星辰，敬授民时。分命羲仲，居郁夷，曰旸谷...申命羲叔，居南交...申命和仲，居西土...申命和叔；居北方...岁三百六十六日，以闰月正四时...
   ```

   注意：
   - 所有子段落编号（1.1、1.2、1.3、11.1、11.2等）消失
   - 所有孙段落编号（如果存在，如 11.1.1、11.1.2）也消失
   - 所有重孙段落编号（如果存在，如 11.1.1.1）也消失
   - 所有内容连续显示在一个段落中
   - 只保留顶级编号（1、11等）
   - **支持任意层级的嵌套段落合并**

## 预期行为

### ✅ 正确行为
- 子段落（1.1、1.2等）的编号链接应该隐藏
- 子段落内容应该与前面内容连续显示，无换行
- 顶级段落（1、2等）之间保持段落间距
- 顶级编号保持可见

### ❌ 如果出现问题
可能的问题和检查点：

1. **段落没有合并**
   - 打开浏览器开发者工具（F12）
   - 查看 Console 是否有错误
   - 检查 body 标签是否有 `merge-paragraphs` 类
   - 检查 p 标签是否有 `sub-paragraph` 和 `top-paragraph` 类

2. **编号没有隐藏**
   - 检查 CSS 是否加载
   - 查看 Elements 面板中的样式应用情况

3. **JavaScript 错误**
   - 查看 Console 中的错误信息
   - 确认 `settings-panel-config.js` 已正确加载

## 浏览器开发者工具检查

打开开发者工具（F12），在 Console 中执行：

```javascript
// 检查body类
document.body.classList.contains('merge-paragraphs')  // 应该是 true（关闭智能分段时）

// 检查子段落数量
document.querySelectorAll('p.sub-paragraph').length  // 应该 > 0

// 检查顶级段落数量
document.querySelectorAll('p.top-paragraph').length  // 应该 > 0

// 手动触发功能
localStorage.setItem('shiji-smart-paragraph', 'false')
location.reload()
```

## 调试技巧

如果功能不正常，在 Console 中执行：

```javascript
// 查看第一个子段落
const subP = document.querySelector('p.sub-paragraph');
console.log('子段落:', subP);
console.log('display:', getComputedStyle(subP).display);  // 应该是 "inline"

// 查看第一个顶级段落
const topP = document.querySelector('p.top-paragraph');
console.log('顶级段落:', topP);
console.log('display:', getComputedStyle(topP).display);  // 应该是 "block"
```
