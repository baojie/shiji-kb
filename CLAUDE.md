# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

《史记》知识库：用AI Agent将《史记》130篇转化为结构化知识图谱。

## 项目约定

- 不要自动 commit。只在用户明确要求时才执行 git commit。
- 反思流程全自动。每章的 Agent 反思循环不需要用户逐步确认，直接执行完整流程。
- 对话和输出以中文为主。
- 当用户在对话中明确要求自动确认时，后续操作不再逐步询问，自动执行。
- commit时只提交用户已暂存（git add）的文件，不得擅自 `git add -A` 或 `git add .` 添加未暂存的文件。
- commit message不要自动加版本号（如v3.1），版本号由用户决定。

## Git提交消息规范

- **只在用户明确要求时才commit**
- **只提交缓存区（staged）内容**，提交消息只描述缓存区中的变更，不包括未暂存文件
- 首行：一句话总结（不超过50字），说明做了什么
- 空行后按目录/模块分组列出具体变更
- 每组用 `模块名:` 开头，下面用 `- ` 列出具体项
- 区分"新增"、"更新"、"修复"、"删除"

示例格式：
```
首行总结（做了什么）

模块A:
- 新增 xxx
- 更新 yyy

模块B:
- 修复 zzz
```

