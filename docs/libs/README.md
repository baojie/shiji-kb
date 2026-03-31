# 第三方JavaScript库

本目录存放项目使用的第三方JavaScript库的本地副本。

## 为什么本地化？

### ✅ 优势

1. **离线可用**：无需互联网连接即可使用所有功能
2. **加载速度**：本地文件加载比CDN更快（特别是在国内网络环境）
3. **稳定性**：不受CDN服务中断影响
4. **隐私保护**：避免向第三方CDN发送请求
5. **版本锁定**：确保使用的库版本不会意外更新

### ⚠️ 注意事项

- 需要定期检查库更新（安全补丁等）
- 增加了仓库体积（但对于1MB左右的文件可以接受）

## 当前库清单

| 库名称 | 版本 | 大小 | 用途 | 更新日期 |
|--------|------|------|------|----------|
| OpenCC.js | 1.0.5 | 1.1MB | 繁简转换 | 2026-03-31 |

## 加载机制

项目使用智能降级策略：

```
优先尝试本地版本
    ↓ 成功
使用本地文件
    ↓ 失败
降级到CDN
    ↓ 成功
使用CDN版本
    ↓ 失败
报错（必需库）或跳过（可选库）
```

详见 [`docs/js/shiji-imports.js`](../js/shiji-imports.js)

## 更新库

### 手动更新

```bash
# OpenCC.js
cd docs/libs
curl -L -o opencc.min.js https://cdn.jsdelivr.net/npm/opencc-js@1.0.5/dist/umd/full.min.js
```

### 验证完整性

下载后应验证文件完整性（使用SHA256）：

```bash
sha256sum opencc.min.js
```

## CDN后备

即使本地文件存在，系统仍然配置了CDN后备URL：

- **OpenCC.js**: https://cdn.jsdelivr.net/npm/opencc-js@1.0.5/dist/umd/full.min.js

这确保了在本地文件损坏或缺失时，系统仍能正常工作。

## 未来扩展

当需要添加新的第三方库时：

1. 下载库文件到本目录
2. 更新此README的库清单表格
3. 在 [`shiji-imports.js`](../js/shiji-imports.js) 的 `DEPENDENCIES.libs` 数组中添加配置
4. 测试本地加载和CDN降级

## 许可证

所有第三方库遵循其原始许可证：

- **OpenCC.js**: Apache License 2.0
  - 项目地址: https://github.com/nk2028/opencc-js
  - 许可证: https://github.com/nk2028/opencc-js/blob/master/LICENSE
