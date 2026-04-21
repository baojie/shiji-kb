/**
 * 在 h1 / h2 / h3、正文 <p>、<blockquote>、列表项 <li> 上插入汉语拼音（带声调）。
 * 使用 <ruby> 标注实现拼音和汉字的精确对齐。
 * 支持特殊读音词表，优先匹配特殊读音。
 * 依赖：pinyin-pro（优先本地，降级CDN）。
 */
(function () {
  const polyCache = new Map();
  let specialPronunciations = null;  // 特殊读音词表

  function isHan(ch) {
    return /[\u4e00-\u9fff]/.test(ch);
  }

  function isPolyphonicCached(pinyinFn, ch) {
    if (polyCache.has(ch)) {
      return polyCache.get(ch);
    }
    let v = false;
    if (/^[\u4e00-\u9fff]$/.test(ch)) {
      try {
        const arr = pinyinFn(ch, {
          type: "array",
          multiple: true,
          toneType: "symbol",
        });
        if (Array.isArray(arr) && arr.length > 1) {
          v = true;
        } else if (Array.isArray(arr) && arr.length === 1) {
          const s = String(arr[0] || "");
          v = s.includes("|") || s.includes("｜");
        }
      } catch (_) {
        v = false;
      }
    }
    polyCache.set(ch, v);
    return v;
  }

  /**
   * 加载特殊读音词表
   */
  async function loadSpecialPronunciations() {
    try {
      const response = await fetch('../data/special-pronunciation.json');
      const data = await response.json();
      // 按文本长度降序排序，优先匹配较长的词
      specialPronunciations = data.entries.sort((a, b) => b.text.length - a.text.length);
      console.log('[heading-pinyin] 特殊读音词表已加载:', specialPronunciations.length, '条');
    } catch (e) {
      console.warn('[heading-pinyin] 特殊读音词表加载失败，将使用标准读音:', e);
      specialPronunciations = [];
    }
  }

  /**
   * 使用正则模式匹配特殊读音
   * @param {string} text - 完整文本
   * @param {number} startIndex - 开始位置
   * @param {Function} pinyinFn - 拼音函数
   * @returns {Object|null} 匹配结果 {text, pinyin, length, note} 或 null
   */
  function matchPattern(text, startIndex, pinyinFn) {
    const substr = text.substring(startIndex);

    // 模式1: 数词 + [余/馀] + 骑 (量词用法，读jì)
    // 例如: 十骑、百骑、千骑、万骑、数十骑、十余骑
    const qiPattern = /^([0-9一二三四五六七八九十百千万数]+[余馀]?)骑/;
    const qiMatch = substr.match(qiPattern);
    if (qiMatch) {
      const fullText = qiMatch[0];  // 例如: "十骑"
      const numText = qiMatch[1];   // 例如: "十"

      try {
        // 获取数词部分的拼音
        const numPinyin = pinyinFn(numText, { type: 'array', toneType: 'symbol' });

        return {
          text: fullText,
          pinyin: [...numPinyin, 'jì'],
          length: fullText.length,
          note: '量词用法：数词+骑，读jì（去声）'
        };
      } catch (e) {
        console.warn('[heading-pinyin] 模式匹配失败:', e);
      }
    }

    // 模式2: 数词 + [余/馀] + 乘 (量词用法，读shèng)
    // 例如: 千乘、万乘、百乘
    const chengPattern = /^([0-9一二三四五六七八九十百千万数]+[余馀]?)乘/;
    const chengMatch = substr.match(chengPattern);
    if (chengMatch) {
      const fullText = chengMatch[0];
      const numText = chengMatch[1];

      try {
        const numPinyin = pinyinFn(numText, { type: 'array', toneType: 'symbol' });

        return {
          text: fullText,
          pinyin: [...numPinyin, 'shèng'],
          length: fullText.length,
          note: '量词用法：数词+乘，读shèng（去声）'
        };
      } catch (e) {
        console.warn('[heading-pinyin] 模式匹配失败:', e);
      }
    }

    return null;
  }

  /**
   * 检查从指定位置开始是否匹配特殊读音词
   * @param {string} text - 完整文本
   * @param {number} startIndex - 开始位置
   * @param {Function} pinyinFn - 拼音函数（用于模式匹配）
   * @returns {Object|null} 匹配结果 {text, pinyin, length, note} 或 null
   */
  function matchSpecialPronunciation(text, startIndex, pinyinFn) {
    if (!specialPronunciations) {
      console.warn('[heading-pinyin] specialPronunciations 未加载');
      return null;
    }

    // 优先尝试正则模式匹配
    if (pinyinFn) {
      const patternMatch = matchPattern(text, startIndex, pinyinFn);
      if (patternMatch) {
        console.log('[heading-pinyin] 模式匹配成功:', patternMatch.text, '->', patternMatch.pinyin.join(' '));
        return patternMatch;
      }
    }

    // 然后尝试词表精确匹配
    for (let entry of specialPronunciations) {
      const len = entry.text.length;
      if (startIndex + len <= text.length) {
        const substr = text.substring(startIndex, startIndex + len);
        if (substr === entry.text) {
          console.log('[heading-pinyin] 匹配到特殊读音:', entry.text, '->', entry.pinyin.join(' '));
          return {
            text: entry.text,
            pinyin: entry.pinyin,
            length: len,
            note: entry.note
          };
        }
      }
    }
    return null;
  }

  /**
   * 递归遍历DOM节点，为汉字添加 <ruby> 拼音标注
   * @param {Node} node - 要处理的节点
   * @param {Function} pinyinFn - 拼音函数
   * @param {boolean} inEntity - 是否在专名链接内
   * @returns {Node} 处理后的节点
   */
  function addRubyAnnotation(node, pinyinFn, inEntity) {
    // 文本节点：添加 ruby 标注
    if (node.nodeType === Node.TEXT_NODE) {
      const text = node.textContent;
      if (!text || !text.trim()) {
        return node;
      }

      const frag = document.createDocumentFragment();
      let currentText = "";
      let i = 0;

      while (i < text.length) {
        const ch = text[i];

        if (isHan(ch)) {
          // 先添加之前的非汉字文本
          if (currentText) {
            frag.appendChild(document.createTextNode(currentText));
            currentText = "";
          }

          // 尝试匹配特殊读音词（包括正则模式）
          const specialMatch = matchSpecialPronunciation(text, i, pinyinFn);

          if (specialMatch) {
            // 找到特殊读音词，为整个词创建ruby标注
            for (let j = 0; j < specialMatch.length; j++) {
              const wordChar = specialMatch.text[j];
              const wordPinyin = specialMatch.pinyin[j];

              const ruby = document.createElement("ruby");
              const span = document.createElement("span");
              span.className = "hanzi";
              span.textContent = wordChar;

              const rt = document.createElement("rt");
              rt.className = "pinyin-rt pinyin-special";
              rt.textContent = wordPinyin;
              rt.title = specialMatch.note || "特殊读音";

              ruby.appendChild(span);
              ruby.appendChild(rt);
              frag.appendChild(ruby);
            }
            i += specialMatch.length;
          } else {
            // 使用标准读音
            try {
              const pinyin = pinyinFn(ch, {
                toneType: "symbol",
              });
              const ruby = document.createElement("ruby");
              const span = document.createElement("span");
              span.className = "hanzi";
              span.textContent = ch;

              const rt = document.createElement("rt");
              rt.className = "pinyin-rt";

              const poly = isPolyphonicCached(pinyinFn, ch);
              if (inEntity || poly) {
                rt.classList.add("pinyin-emphasis");
                if (inEntity && poly) {
                  rt.title = "专名（图谱标注）· 多音字";
                } else if (inEntity) {
                  rt.title = "专名（知识图谱标注）";
                } else {
                  rt.title = "多音字（另有读音）";
                }
              }
              rt.textContent = pinyin;

              ruby.appendChild(span);
              ruby.appendChild(rt);
              frag.appendChild(ruby);
            } catch (_) {
              frag.appendChild(document.createTextNode(ch));
            }
            i++;
          }
        } else {
          currentText += ch;
          i++;
        }
      }

      // 添加剩余的非汉字文本
      if (currentText) {
        frag.appendChild(document.createTextNode(currentText));
      }

      return frag;
    }

    // 元素节点：递归处理子节点
    if (node.nodeType === Node.ELEMENT_NODE) {
      // 跳过这些元素
      if (node.matches && (
        node.matches("a.para-num") ||
        node.matches("a.original-text-link") ||
        node.matches("script") ||
        node.matches("style")
      )) {
        return node.cloneNode(true);
      }

      // 检查是否是专名链接
      const isEntity = node.matches && node.matches("a.entity-link");
      const newInEntity = inEntity || isEntity;

      const clone = node.cloneNode(false);
      Array.from(node.childNodes).forEach(function (child) {
        const processed = addRubyAnnotation(child, pinyinFn, newInEntity);
        if (processed.nodeType === Node.DOCUMENT_FRAGMENT_NODE) {
          Array.from(processed.childNodes).forEach(function (n) {
            clone.appendChild(n);
          });
        } else {
          clone.appendChild(processed);
        }
      });

      return clone;
    }

    return node.cloneNode(true);
  }

  /**
   * 为元素添加拼音注释（原地修改）
   * @param {Element} el - 要处理的元素
   * @param {Function} pinyinFn - 拼音函数
   */
  function addPinyinToElement(el, pinyinFn) {
    if (el.dataset.pinyinAdded) {
      return;
    }

    // 检查是否有汉字
    const text = el.textContent || "";
    if (!/[\u4e00-\u9fff]/.test(text)) {
      return;
    }

    // 创建新内容
    const newContent = document.createDocumentFragment();
    Array.from(el.childNodes).forEach(function (child) {
      const processed = addRubyAnnotation(child, pinyinFn, false);
      if (processed.nodeType === Node.DOCUMENT_FRAGMENT_NODE) {
        Array.from(processed.childNodes).forEach(function (n) {
          newContent.appendChild(n);
        });
      } else {
        newContent.appendChild(processed);
      }
    });

    // 替换元素内容
    el.innerHTML = "";
    el.appendChild(newContent);
    el.dataset.pinyinAdded = "true";
  }

  async function init() {
    // 先加载特殊读音词表
    await loadSpecialPronunciations();

    // 加载拼音库（优先本地，降级CDN）
    let pinyinFn;
    const urls = [
      "../libs/pinyin-pro.min.js",  // 本地版本（优先）
      "https://cdn.jsdelivr.net/npm/pinyin-pro@3.28.0/+esm",
      "https://cdn.jsdelivr.net/npm/pinyin-pro@3.21.0/+esm",
      "https://esm.sh/pinyin-pro@3.28.0",
    ];
    let lastErr;
    for (let u = 0; u < urls.length; u++) {
      try {
        const mod = await import(urls[u]);
        pinyinFn = mod.pinyin;
        if (typeof pinyinFn === "function") {
          console.log(`[heading-pinyin] 拼音库已加载: ${urls[u]}`);
          break;
        }
      } catch (e) {
        lastErr = e;
        console.debug(`[heading-pinyin] 尝试加载 ${urls[u]} 失败，继续尝试下一个URL`);
      }
    }
    if (typeof pinyinFn !== "function") {
      console.warn("[heading-pinyin] 无法加载拼音库（请检查网络）:", lastErr);
      return;
    }

    // 注意：不再处理 h1/h2/h3 标题以及 settings-panel 等 UI 容器，
    // 拼音仅作用于文章正文（p / blockquote / li）。

    // 收集需要处理的正文元素
    const flowElements = [];

    // 非正文容器：导航、设置面板、页眉页脚等 UI 区域不注拼音
    const EXCLUDE_SELECTOR = "nav, #settings-panel, #settings-toggle, header, footer, aside, .settings-panel, .panel, .toolbar";

    function collectFlowElement(el) {
      if (el.closest(EXCLUDE_SELECTOR)) {
        return;
      }
      if (el.dataset.pinyinAdded) {
        return;
      }
      const text = el.textContent || "";
      if (!text.trim() || !/[\u4e00-\u9fff]/.test(text)) {
        return;
      }
      flowElements.push(el);
    }

    document.querySelectorAll("body p").forEach(collectFlowElement);
    document.querySelectorAll("body blockquote").forEach(collectFlowElement);
    document.querySelectorAll("body li").forEach(collectFlowElement);

    // 分帧处理正文元素
    let index = 0;
    function processChunk(deadline) {
      const t0 = performance.now();
      while (index < flowElements.length) {
        if (deadline && deadline.timeRemaining() < 8 && index > 0) {
          break;
        }
        if (!deadline && performance.now() - t0 > 16) {
          break;
        }
        addPinyinToElement(flowElements[index++], pinyinFn);
      }
      if (index < flowElements.length) {
        if (typeof requestIdleCallback === "function") {
          requestIdleCallback(processChunk, { timeout: 2800 });
        } else {
          setTimeout(function () {
            processChunk(null);
          }, 0);
        }
      }
    }

    if (flowElements.length) {
      if (typeof requestIdleCallback === "function") {
        requestIdleCallback(processChunk, { timeout: 2800 });
      } else {
        processChunk(null);
      }
    }
  }

  // ========================================================================
  // Hash 锚点修正：等所有异步渲染（拼音注、三家注、繁简、白话等）停下来后，
  // 重新 scrollIntoView 到初始 hash。相当于"自动刷新一下"的效果。
  // 用 MutationObserver 监测 body 子树变化，debounce 600ms 视为稳定。
  // ========================================================================
  const initialHash = window.location.hash;
  let userScrolled = false;
  function markUserScrolled() { userScrolled = true; }
  window.addEventListener("wheel", markUserScrolled, { passive: true, once: true });
  window.addEventListener("touchmove", markUserScrolled, { passive: true, once: true });
  window.addEventListener("keydown", function (e) {
    const keys = ["ArrowUp", "ArrowDown", "PageUp", "PageDown", "Home", "End", " ", "Spacebar"];
    if (keys.indexOf(e.key) !== -1) userScrolled = true;
  }, { once: true });

  function scrollToInitialHash() {
    if (userScrolled) return;
    if (!initialHash || initialHash.length <= 1) return;
    // 用户若已通过点击链接跳到别处，不要把他拽回初始锚点
    if (window.location.hash !== initialHash) return;
    try {
      const id = decodeURIComponent(initialHash.slice(1));
      const target = document.getElementById(id);
      if (target) {
        const before = Math.round(window.scrollY);
        // 用 instant 强制瞬间定位，避免与 CSS scroll-behavior: smooth 配合时
        // 出现一段多余的滚动动画
        target.scrollIntoView({ behavior: "instant", block: "start" });
        const after = Math.round(window.scrollY);
        console.log(`[hash-scroll-fix] ${id}: scrollY ${before} → ${after}`);
      } else {
        console.warn(`[hash-scroll-fix] 找不到目标元素: ${id}`);
      }
    } catch (e) {
      console.warn("[hash-scroll-fix] 重定位失败:", e);
    }
  }

  function installHashScrollFix() {
    if (!initialHash || initialHash.length <= 1) return;
    if (!document.body || typeof MutationObserver === "undefined") {
      // 降级：简单延时后对齐一次
      setTimeout(scrollToInitialHash, 1500);
      return;
    }

    // 多次对齐策略：观察窗口内，每次 DOM 静默 DEBOUNCE_MS 就再对齐一次。
    // 这样即使白话翻译/三家注等异步 fetch 在拼音处理之后才注入内容，
    // 也能被捕获并重新对齐。
    const DEBOUNCE_MS = 500;    // DOM 静默多久视为"稳定一次"
    const MAX_WAIT_MS = 10000;  // 观察总时长上限
    let debounceTimer = null;
    let stopped = false;

    function stop() {
      if (stopped) return;
      stopped = true;
      observer.disconnect();
      clearTimeout(debounceTimer);
    }

    function tick() {
      if (stopped) return;
      if (userScrolled) { stop(); return; }
      scrollToInitialHash();
    }

    const observer = new MutationObserver(function () {
      if (stopped) return;
      if (userScrolled) { stop(); return; }
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(tick, DEBOUNCE_MS);
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true,
    });

    // 启动时也排一次：万一页面本身就没什么变化，也能对齐
    debounceTimer = setTimeout(tick, DEBOUNCE_MS);
    // 到上限后停止监听（最后再对齐一次）
    setTimeout(function () {
      if (!stopped) { tick(); stop(); }
    }, MAX_WAIT_MS);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      init();
      installHashScrollFix();
    });
  } else {
    init();
    installHashScrollFix();
  }
})();
