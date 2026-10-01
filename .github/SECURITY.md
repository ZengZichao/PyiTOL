# Security Policy / 安全策略

## Supported Versions / 支持的版本

Security fixes are only applied to the latest release on PyPI.
安全修复只针对 PyPI 上的最新发布版本。

| Version | Supported |
| ------- | --------- |
| latest release (see [CHANGELOG.md](CHANGELOG.md)) | ✅ |
| older releases | ❌ |

## Reporting a Vulnerability / 报告漏洞

**请勿在公开 issue 中报告安全漏洞。**
**Please do not report security vulnerabilities through public GitHub issues.**

Preferred channels (任选其一，优先推荐第一种)：

1. **GitHub Private Vulnerability Reporting**（已启用）：
   仓库页 → Security → Report a vulnerability，全程私密。
2. **Email**: [zengzichao@sjtu.edu.cn](mailto:zengzichao@sjtu.edu.cn)，
   邮件标题请注明 `[PyiTOL security]`。

We aim to acknowledge reports within 7 days and will keep you informed of
the fix progress. Please include a description, reproduction steps, and the
affected version / commit if possible.

我们会在 7 天内确认收到报告，并同步修复进展。报告时请尽量附上：
漏洞描述、复现步骤、受影响的版本或 commit。

## Scope / 范围

Of particular interest:
- CLI/模板文件解析路径（Newick/Nexus/CSV 等不可信输入的处理）；
- API client 的凭据处理（iTOL API key 的读取、存储与传输）；
- 任何导致数据丢失、凭据泄露或向第三方服务器意外发送用户数据的行为。

Out of scope: issues in iTOL web service itself (report to
[iTOL](https://itol.embl.de/) maintainers).
