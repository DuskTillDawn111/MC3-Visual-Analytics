# 历史源码包

四个历史源码包及原始校验文件存放于 [GitHub Releases：2026 年 10 月归档](https://github.com/DuskTillDawn111/MC3-Visual-Analytics/releases/tag/archive-2026-10)。日常开发与部署使用 [main 分支](https://github.com/DuskTillDawn111/MC3-Visual-Analytics)及[项目运行说明](../README.md)。

| 包日期 | 源码 ZIP | SHA-256 校验文件 |
| --- | --- | --- |
| 2026-10-22 | [下载 ZIP](https://github.com/DuskTillDawn111/MC3-Visual-Analytics/releases/download/archive-2026-10/MC3-Visual-Analytics-20261022.zip) | [下载校验文件](https://github.com/DuskTillDawn111/MC3-Visual-Analytics/releases/download/archive-2026-10/MC3-Visual-Analytics-20261022.sha256) |
| 2026-10-23 | [下载 ZIP](https://github.com/DuskTillDawn111/MC3-Visual-Analytics/releases/download/archive-2026-10/MC3-Visual-Analytics-20261023.zip) | [下载校验文件](https://github.com/DuskTillDawn111/MC3-Visual-Analytics/releases/download/archive-2026-10/MC3-Visual-Analytics-20261023.zip.sha256) |
| 2026-10-28 | [下载 ZIP](https://github.com/DuskTillDawn111/MC3-Visual-Analytics/releases/download/archive-2026-10/MC3-Visual-Analytics-20261028.zip) | [下载校验文件](https://github.com/DuskTillDawn111/MC3-Visual-Analytics/releases/download/archive-2026-10/MC3-Visual-Analytics-20261028.zip.sha256) |
| 2026-10-29 | [下载 ZIP](https://github.com/DuskTillDawn111/MC3-Visual-Analytics/releases/download/archive-2026-10/MC3-Visual-Analytics-20261029.zip) | [下载校验文件](https://github.com/DuskTillDawn111/MC3-Visual-Analytics/releases/download/archive-2026-10/MC3-Visual-Analytics-20261029.zip.sha256) |

## 校验值

```text
0a4e9d0987dca6fc1ab159901d0181a81dfae86c16eb6ea4cdf031f6f6640191  MC3-Visual-Analytics-20261022.zip
7bcb509a24aec77021a9936b793a06d54f8c6f1b5498d3e1d44e4acc2f69eeed  MC3-Visual-Analytics-20261023.zip
e80a1c1209015deff9a2f3726c241bbcc35ada1a840c8a359478b340434fb2b3  MC3-Visual-Analytics-20261028.zip
035514abcad90413cb85ff5c54a896a512c0c9c67e8a6e547fefb1dab56ebd33  MC3-Visual-Analytics-20261029.zip
```

下载后，在 PowerShell 7 中计算文件哈希，并与对应校验文件或上表比对：

```powershell
Get-FileHash -LiteralPath '.\MC3-Visual-Analytics-20261029.zip' -Algorithm SHA256
```

归档标签关联首次导入项目的提交 `f2c30a1`。各日期的历史内容保存在上表 ZIP 附件中；GitHub 自动生成的 Source code 下载对应标签的仓库快照。

后续发布继续通过 GitHub Releases 上传版本包和校验文件，源码目录维护本索引。
