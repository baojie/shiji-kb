# GitHub Pages 配置指南

## 如何启用 GitHub Pages

1. **推送代码到 GitHub**
   ```bash
   git add docs/
   git commit -m "Add GitHub Pages files"
   git push origin main
   ```

2. **在 GitHub 仓库中配置 Pages**
   - 打开你的 GitHub 仓库页面
   - 点击 **Settings**（设置）
   - 在左侧菜单找到 **Pages**
   - 在 "Build and deployment" 部分：
     - **Source**: 选择 "Deploy from a branch"
     - **Branch**: 选择 `main`
     - **Folder**: 选择 `/docs`
   - 点击 **Save**（保存）

3. **等待部署**
   - GitHub 会自动构建和部署你的网站
   - 通常需要 1-2 分钟
   - 部署完成后，页面上会显示网站 URL

4. **访问你的网站**
   - URL 格式：`https://[你的用户名].github.io/[仓库名]/`
   - 例如：`https://username.github.io/shiji-kb/`

## 文件说明

- **docs/.nojekyll**: 告诉 GitHub Pages 不使用 Jekyll 处理文件
- **docs/index.html**: 主页，包含章节目录
- **docs/css/**: CSS 样式文件
- **docs/chapters/**: 所有章节的 HTML 文件

## 更新内容

当你更新了章节内容后：

1. 重新生成 HTML 文件
2. 复制到 `docs/chapters/` 目录
3. 提交并推送到 GitHub：
   ```bash
   git add docs/chapters/
   git commit -m "Update chapter content"
   git push
   ```

GitHub Pages 会自动重新部署。

## 本地测试

在推送到 GitHub 之前，建议先本地测试：

```bash
cd docs
python3 -m http.server 8000
```

然后访问 `http://localhost:8000` 查看效果。

## 故障排除

### CSS 样式没有加载
- 检查浏览器控制台是否有 404 错误
- 确认 CSS 路径是相对路径（`../css/shiji-styles.css`）
- 确保 `docs/.nojekyll` 文件存在

### 页面显示 404
- 确认已经在 GitHub Settings 中正确配置了 Pages
- 等待几分钟让 GitHub 完成部署
- 检查 GitHub Actions 标签页查看部署状态

### 中文显示乱码
- 确认 HTML 文件编码为 UTF-8
- 检查 HTML 头部是否有 `<meta charset="UTF-8">`
