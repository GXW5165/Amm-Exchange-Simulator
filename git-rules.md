# Git 协作流程说明

本项目采用简单、稳定的 Git 协作方式：**一个主分支 `master` + 临时修改分支 + Pull Request 合并 + 重要版本打 tag**。

本文件用于说明项目成员在后续修改、提交、合并代码时应遵守的基本流程。

---

## 1. 分支设计

本项目只保留一个长期主分支：

```text
master
```

`master` 表示当前最新的、完整的、相对稳定的项目版本。

其他分支都是临时分支，用于完成某一次具体修改。修改完成并合并后，应及时删除。

推荐使用以下三类临时分支：

```text
update/xxx    功能修改、界面修改、一般改进
fix/xxx       bug 修复
docs/xxx      文档修改
```

示例：

```text
update/add-fee-display
update/improve-swap-ui
fix/liquidity-calculation
docs/update-readme
```

不建议长期保留 `dev`、`test`、`release` 等复杂分支。当前项目已经基本成型，后续主要是小规模修改和版本更新，简单分支结构更清晰。

---

## 2. 基本原则

所有成员都应遵守以下原则：

1. `master` 永远保存最新完整版本。
2. 不直接在 `master` 上修改和提交。
3. 每次修改前，先从最新 `master` 新建临时分支。
4. 每个临时分支只做一件相对明确的事情。
5. 修改完成后，通过 Pull Request 合并回 `master`。
6. 合并后删除临时分支。
7. 重要完整版本使用 tag 保存，例如 `v1.0`、`v1.1`。
8. AI 工具生成的代码必须人工检查后才能提交和合并。

---

## 3. 开始一次修改前的流程

每次开始修改前，都要先同步最新的 `master`。

```bash
git checkout master
git pull origin master
```

然后从 `master` 新建一个临时分支。

例如，要修改手续费显示功能：

```bash
git checkout -b update/add-fee-display
```

此时本地分支结构可以理解为：

```text
master
  └── update/add-fee-display
```

`update/add-fee-display` 一开始和 `master` 完全一样，之后只在这个分支上进行本次修改。

---

## 4. 修改并提交代码

在临时分支上完成代码修改后，先查看改动状态：

```bash
git status
```

查看具体修改内容：

```bash
git diff
```

确认无误后提交：

```bash
git add .
git commit -m "update: add fee display"
```

提交信息建议简洁明确，说明本次提交做了什么。

推荐格式：

```text
update: 修改某个功能
fix: 修复某个问题
docs: 修改文档
```

---

## 5. 推送临时分支到 GitHub

本地提交完成后，将临时分支推送到远程仓库：

```bash
git push -u origin update/add-fee-display
```

如果是其他分支名，把命令中的分支名替换掉即可。

---

## 6. 创建 Pull Request

推送分支后，在 GitHub 仓库页面创建 Pull Request。

方向应为：

```text
临时分支 → master
```

例如：

```text
update/add-fee-display → master
```

Pull Request 中应说明：

```text
1. 本次修改了什么功能
2. 修改了哪些主要文件
3. 是否已经本地运行或测试
4. 是否可能影响其他模块
```

---

## 7. 合并是什么意思

合并不是简单地用某个开发者的版本覆盖 `master`。

Git 会比较：

```text
1. 两个分支共同出发时的旧 master
2. 当前 master
3. 要合并的临时分支
```

然后把临时分支中的修改加入 `master`。

如果不同开发者修改的是不同文件，通常会自动合并。如果修改的是同一个文件的同一段代码，Git 会提示冲突，需要人工解决，不会悄悄覆盖。

---

## 8. 如果别人已经先合并了修改怎么办

如果你在开发期间，别人已经把自己的 PR 合并进了 `master`，那么你在合并自己的 PR 前，最好先把最新 `master` 同步到自己的分支：

```bash
git checkout update/my-change
git fetch origin
git merge origin/master
```

如果没有冲突，可以继续推送：

```bash
git push
```

如果有冲突，需要先解决冲突，再提交：

```bash
git add .
git commit -m "fix: resolve merge conflict"
git push
```

---

## 9. 合并 PR 后其他人要做什么

当某个 PR 合并进 `master` 后，其他开发者需要更新本地 `master`：

```bash
git checkout master
git pull origin master
```

这样本地项目就会更新为最新完整版本。

如果还要继续开发，应该从这个最新 `master` 新建新的临时分支：

```bash
git checkout -b update/next-change
```

---

## 10. 合并后删除临时分支

Pull Request 合并后，临时分支通常就没有继续保留的必要了。

删除远程分支：

```bash
git push origin --delete update/add-fee-display
```

删除本地分支：

```bash
git checkout master
git pull origin master
git branch -d update/add-fee-display
```

---

## 11. 推荐的 Pull Request 合并方式

GitHub 上常见合并方式有三种：

```text
Create a merge commit
Squash and merge
Rebase and merge
```

本项目推荐优先使用：

```text
Squash and merge
```

它可以把一个临时分支里的多个零散提交压缩成一个清晰的提交，再放入 `master`，使主分支历史更干净。

---

## 12. 使用 tag 保存重要版本

分支用于开发，tag 用于保存已经完成的重要版本。

例如：

```text
v1.0 初始完整版本
v1.1 增加手续费显示
v1.2 修复流动性计算
```

创建 tag：

```bash
git checkout master
git pull origin master
git tag -a v1.1 -m "Add fee display"
git push origin v1.1
```

查看所有 tag：

```bash
git tag
```

切换到某个历史版本查看：

```bash
git checkout v1.1
```

---

## 13. AI 工具修改代码的处理规则

如果使用 Claude、Copilot 或其他 AI 工具修改代码，不要直接把 AI 生成的内容推到 `master`。

推荐做法：

```bash
git checkout master
git pull origin master
git checkout -b update/ai-assisted-change
```

AI 修改完成后，必须人工检查：

```bash
git diff
git status
```

重点检查：

```text
1. 是否删除了原有重要代码
2. 是否修改了无关文件
3. 是否引入了错误逻辑
4. 是否改变了项目结构
5. 是否留下 Generated with Claude / Co-authored-by 等不需要的提交信息
```

确认无误后再提交、推送、开 PR。

---

## 14. 不应该做的操作

除非明确知道后果，否则不要执行：

```bash
git push --force origin master
```

原因：可能覆盖远程 `master` 历史，导致其他人的代码丢失。

不要直接在 `master` 上提交：

```bash
git checkout master
git add .
git commit -m "update something"
git push origin master
```

正确做法是先新建临时分支。

也不要在一个分支里混合多个无关修改。如果修改内容不相关，应拆成多个分支和多个 PR。

---

## 15. 常用命令汇总

查看当前分支：

```bash
git branch
```

查看远程分支：

```bash
git branch -r
```

同步远程信息：

```bash
git fetch -p
```

切换到主分支：

```bash
git checkout master
```

拉取最新主分支：

```bash
git pull origin master
```

新建并切换分支：

```bash
git checkout -b update/branch-name
```

查看修改状态：

```bash
git status
```

查看修改内容：

```bash
git diff
```

提交修改：

```bash
git add .
git commit -m "update: message"
```

推送新分支：

```bash
git push -u origin update/branch-name
```

把最新 master 合并到当前分支：

```bash
git fetch origin
git merge origin/master
```

删除远程分支：

```bash
git push origin --delete update/branch-name
```

删除本地分支：

```bash
git branch -d update/branch-name
```

创建版本 tag：

```bash
git tag -a v1.1 -m "Version description"
git push origin v1.1
```

---

## 16. 一句话总结

本项目的协作方式是：

```text
master 保存最新完整版本；
每次修改从 master 新建临时分支；
修改完成后通过 Pull Request 合并回 master；
Git 会自动合并不同位置的修改；
如果同一段代码被多人修改，会提示冲突并要求人工解决；
合并后其他人 git pull，就能拿到新的完整版本；
重要阶段使用 tag 保存版本。
```

::: 
