/* MediaWiki 风格 hook 系统。
 *
 * 每个 hook 有多个 handler。 run(value, ...rest) 依次调用:
 *   - handler 可 return 新值来改变 value (filter 模式)
 *   - handler 可 return undefined 来保持 value 不变 (action 模式)
 *   - 任何 handler 可 return null 作为特殊约定 (如 onRoute 表示"已自行处理")
 */

export class Hook {
  constructor(name) {
    this.name = name;
    this.handlers = [];
  }

  add(fn) {
    this.handlers.push(fn);
    return this;
  }

  async run(value, ...rest) {
    let cur = value;
    for (const fn of this.handlers) {
      const r = await fn(cur, ...rest);
      if (r !== undefined) cur = r;
    }
    return cur;
  }
}

export function createHooks(names) {
  const hooks = {};
  for (const n of names) hooks[n] = new Hook(n);
  return hooks;
}
