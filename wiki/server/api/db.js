/* 语义数据存储层. v0 = JSON 文件 (lazy load, 启动后缓存在内存).
 *
 * 接口窄, 以后换 SQLite 不改 handler:
 *   db.getEntity(id)           → object | null
 *   db.listEntityIds()         → string[]
 *   db.meta()                  → { generated, count, ... }
 */

'use strict';

const fs = require('fs');
const path = require('path');

const DEFAULT_PATH = path.resolve(__dirname, '../../data/semantic.json');

class JsonDb {
  constructor(filePath = DEFAULT_PATH) {
    this.filePath = filePath;
    this._data = null;
  }

  _load() {
    if (this._data !== null) return this._data;
    if (!fs.existsSync(this.filePath)) {
      console.warn(`[db] 数据文件缺失: ${this.filePath} (跑 seed.js)`);
      this._data = { entities: {}, generated: null };
      return this._data;
    }
    try {
      this._data = JSON.parse(fs.readFileSync(this.filePath, 'utf8'));
    } catch (e) {
      console.error(`[db] ${this.filePath} 解析失败:`, e.message);
      this._data = { entities: {}, generated: null };
    }
    return this._data;
  }

  getEntity(id) {
    const d = this._load();
    return (d.entities && d.entities[id]) || null;
  }

  listEntityIds() {
    const d = this._load();
    return Object.keys(d.entities || {});
  }

  meta() {
    const d = this._load();
    return {
      count: Object.keys(d.entities || {}).length,
      generated: d.generated || null,
      path: this.filePath,
    };
  }
}

// 单例, handler 直接 require
const db = new JsonDb();

module.exports = { db, JsonDb };
