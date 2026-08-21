# PyiTOL 发布操作手册

本手册覆盖完整的「GitHub 发布 + PyPI 发布」流程。当前仓库已具备：
- 初始 commit `c8220f1`，已打本地 tag `v1.0.0`（`setuptools_scm` 据此推导版本 `1.0.0`）；
- `.github/workflows/publish.yml`：打 `v*` tag 自动构建并发布到 PyPI（Trusted Publishing / OIDC，无需令牌）；
- 全仓链接已统一为占位符 `https://github.com/ZengZichao/PyiTOL`。

> ⚠️ **最重要的时序原则**：`publish.yml` 在「推送 `v*` tag」时自动发布到 PyPI。因此 **tag 必须放到所有验证都通过之后再推送**，绝不能一开始就 `git push --tags`。

---

## 0. 发布前置检查（必须完成）

### 0.1 替换 `OWNER` 占位符
全仓有 6 个文件含 `github.com/ZengZichao/PyiTOL`（pyproject.toml、README.md、README_CN.md、CITATION.cff、mkdocs.yml、CONTRIBUTING.md）。把 `<owner>` 换成你的真实 GitHub 用户名或组织名（例如 `zengzichao`）：

```bash
cd /path/to/PyiTOL
OWNER=zengzichao   # ← 改成你的真实 GitHub 用户名 / 组织名
grep -rl 'github.com/ZengZichao/PyiTOL' --exclude-dir=.git --exclude-dir=.venv --exclude-dir='*.egg-info' . \
  | xargs sed -i '' "s#github.com/ZengZichao/PyiTOL#github.com/$OWNER/pyitol#g"
# 复查：应无输出
grep -rn 'github.com/ZengZichao/PyiTOL' --exclude-dir=.git --exclude-dir=.venv --exclude-dir='*.egg-info' .
```

### 0.2 处理 `/discussions` 链接
README / README_CN 中若含 `…/discussions` 链接，需在仓库 **Settings → General → Features** 勾选 **Discussions**，否则会 404。若不想启用，直接删除该链接。

### 0.3 本地干净构建验证
```bash
rm -rf build dist src/pyitol.egg-info src/pyitol/_version.py
python -m build
twine check dist/*        # 校验 sdist / wheel 元数据是否合法
```
若 `twine` / `build` 未安装：`pip install build twine`。

---

## 1. 路径 A：私有验证 → 改公开（推荐）

### 1.1 在 GitHub 新建**私有**仓库
- 仓库名 `pyitol`，**不要**勾选 Initialize with README / .gitignore / License（本地已有完整历史）。
- 记下仓库 URL：`https://github.com/<owner>/pyitol.git`

### 1.2 推送 `main`（先**不要**推送 tag）
```bash
git branch -M main
git remote add origin https://github.com/<owner>/pyitol.git
git push -u origin main          # 只推 main，不推 tag
```

### 1.3 私有阶段验证
- 打开仓库 **Actions** 页，确认 CI（`ci.yml`）通过。
- 本地跑功能自检：
  ```bash
  pip install -e ".[dev]"
  pyitol self-test
  pytest tests/ -m "not integration"
  ```
- 此时仓库仍是 Private，外界看不到，可安心检查代码、密钥、日志等。

### 1.4 在 PyPI 配置 Trusted Publisher（一次性）
1. 注册 / 登录 https://pypi.org
2. **Account settings → Publishing → Add a new trusted publisher**：
   - PyPI project name: `pyitol`
   - Owner: `<owner>`（与 0.1 一致）
   - Repository name: `pyitol`
   - Workflow name: `publish.yml`
   - Environment name: 留空或填 `pypi`
3. 保存。**此时仓库即使是 Private 也能发布**，Trusted Publisher 不限制可见性——所以下面步骤 1.5 改公开之前，只要你不 push tag，就不会误发。

### 1.5 改为公开
仓库 **Settings → General → Danger Zone → Change repository visibility → Make public**。
历史、tag、`v1.0.0` 全部保留，零搬运。

### 1.6 正式发布（最后一步：推送 tag）
```bash
git push origin --tags        # 推送 v1.0.0 → 触发 publish.yml → 发布到 PyPI
```
- 在 **Actions** 页观察 `Publish to PyPI` 是否成功。
- 成功后仓库会多出一次 Release（GitHub 自动为 tag 创建）。

---

## 2. TestPyPI 演练（强烈建议在正式发布前做一次）

PyPI 没有「私有」概念，但可用 **TestPyPI**（`test.pypi.org`）演练发布，确认 sdist/wheel 能正常上传、元数据无误。

```bash
# 1) 注册 TestPyPI 账号，并生成 API token（Account settings → API tokens）
# 2) 本地构建并上传到 TestPyPI
rm -rf build dist
python -m build
twine upload --repository testpypi dist/*     # 按提示输入 TestPyPI 的 username(__token__)/password(token)
```
- 演练验证的是「打包 + 上传」链路；正式发布仍走 1.6 的 GitHub Actions（Trusted Publishing）。
- 可选：也可在 TestPyPI 后台配 Trusted Publisher，用 `git tag -a v0.0.0-test ...` 走 Actions 演练，但本地 `twine` 更简单。

---

## 3. 发布后验证

- PyPI 页面：https://pypi.org/project/pyitol/ 应显示 `1.0.0`。
- 安装验证：
  ```bash
  python -m venv /tmp/verify
  /tmp/verify/bin/pip install pyitol
  /tmp/verify/bin/pyitol --help
  ```
- GitHub Release 页：`https://github.com/<owner>/pyitol/releases` 出现 `v1.0.0`。

---

## 4. Zenodo DOI（论文引用）

### 4.1 一次性配置（网页操作）
1. 登录 https://zenodo.org（建议直接用 GitHub 账号登录）。
2. **Settings → GitHub → Connect GitHub account**（或 Sync now），同步仓库列表。
3. 找到 `<owner>/pyitol`，点击开关 **Enable**。
4. 仓库根目录已含 `.zenodo.json`（标题 / 作者 / ORCID / license / 关键词，Zenodo 归档时自动读取），无需额外设置。

### 4.2 触发与验证
- 每次发布 GitHub **Release** 时，Zenodo 自动抓取仓库快照并生成 DOI（约 1 分钟内，可在 Zenodo 记录页看到）。
- ⚠️ Zenodo 只响应 **Release**，不响应 tag 推送。而 GitHub 推 tag 不会自动建 Release，需显式创建：
  ```bash
  gh release create v1.0.0 --generate-notes
  ```
- ⚠️ 钩子必须**先启用、后建 Release**，否则该 Release 不会自动归档。
- 查询 DOI：
  ```bash
  curl -s "https://zenodo.org/api/records?q=pyitol" | jq '.hits.hits[].doi'
  ```

### 4.3 DOI 语义
- **版本 DOI**（每个 Release 一个）：`10.5281/zenodo.<id>`，指向该次快照。
- **概念 DOI**（整个软件系列，不随版本变化）：`10.5281/zenodo.<conceptid>`，始终解析到最新版本。
- v1.0.0 首发记录：版本 DOI `10.5281/zenodo.22043046`，概念 DOI `10.5281/zenodo.22043045`。
- v1.0.1 记录：版本 DOI `10.5281/zenodo.22046669`（元数据修复补丁，代码逻辑与 v1.0.0 一致）。
- **论文引用决定**：Bioinformatics 投稿论文引用 **最新版本 DOI**（`10.5281/zenodo.22046669`，v1.0.1；正文摘要与参考文献 [33]）；一般性引用可选用概念 DOI。

---

## 5. 故障排查 / 回滚

- **误发错版本**：PyPI 不允许覆盖同一版本号，只能发新的 `patch` 版本（如 `v1.0.1`）。无法删除已发版本，**发布前务必演练**。
- **publish.yml 失败**：多在 Actions 日志看原因。常见：Trusted Publisher 的 owner/repo/workflow 任一不匹配 → 核对 1.4。
- **版本号不对（出现 `0.2.3.dev0` 之类）**：说明 `setuptools_scm` 没拿到 tag。确认 `git push origin --tags` 已执行，且 Actions checkout 用了 `fetch-depth: 0`（publish.yml 已配置）。
- **想重发同版本**：删本地+远程旧 tag 后重打：
  ```bash
  git tag -d v1.0.0 && git push origin :refs/tags/v1.0.0
  git tag -a v1.0.0 -m "Release v1.0.0" && git push origin v1.0.0
  ```

---

## 附录：备选路径 B（镜像到公开仓库）

若你希望代码先在另一个独立私有仓库验证、再整体迁移（而非改可见性），用 `git push --mirror` 一次性搬运分支+tag（**切勿 Download ZIP**，会丢 `.git` 历史和 tag，导致版本号错乱）：

```bash
git remote add public https://github.com/<owner>/pyitol.git
git push --mirror public
```
之后同样执行 1.4（把公开仓库登记为 Trusted Publisher）→ 1.6 触发发布。

> 路径 A（改可见性）更省事、零搬运，推荐优先使用。
