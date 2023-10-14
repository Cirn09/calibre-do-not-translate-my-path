# Calibre 不要翻译我的文件路径 | Calibre: Do not translate my file paths

如题所示，让你的 Calibre 不要把中文路径翻译成拼音。

As the title suggests, this is a guide on how to prevent Calibre from translating Chinese file paths into Pinyin or other Latin transliteration.

Github Action 每日北京时间 13：00 自动更新。

Auto check update and release at 05:00 UTC+0 every day using Github Action.

## 使用方法 | Usage

### Windows & Linux

1. 根据平台和 Calibre 版本下载 [Release](https://github.com/Cirn09/calibre-do-not-translate-my-path/releases/latest)，覆盖原本 Calibre 文件。
2. 没了

<br/>

1. Download the [Release](https://github.com/Cirn09/calibre-do-not-translate-my-path/releases/latest) for your platform and replace the original Calibre files.
2. Enjoy.

### macOS

1. 解压下载的包，逐层点击进入底层路径，找到 `python-lib.bypy.frozen` 文件。
2. 打开 `Finder`，进入“应用程序” (/Applications)，右键点击“Calibre——显示包内容”，进入 `Contents/Frameworks/plugins` (对应的完整路径是 `/Applications/calibre.app/Contents/Frameworks/plugins` )。将第 1 步下载包里的 `python-lib.bypy.frozen`，拷贝覆盖过来、关闭 `Finder` 窗口，正常打开 `Calibre` 即可。

<br/>
 
1. Unzip downloaded file and get `python-lib.bypy.frozen` in the subdirectory.
2. Open `Finder`, right-click `Calibre` in `/Applications`, choose  `Show package content`. Copy downloaded `python-lib.bypy.frozen` to `Contents/Frameworks/plugins`. Close `Finder` and now enjoy your new `Calibre`.

### Older macOS

a. 官方最后一个支持旧版 macOS 的版本：[v5.44.0](https://download.calibre-ebook.com/5.44.0/calibre-5.44.0.dmg)，以及对应的补丁：[v5.44.0](https://github.com/Cirn09/calibre-do-not-translate-my-path/releases/download/v5.44.0/patch-mac-5.44.0.zip)

b. 实测可运行的版本：[v6.11.0](https://download.calibre-ebook.com/6.11.0/calibre-6.11.0.dmg)，以及对应的补丁：[v6.11.0](https://github.com/Cirn09/calibre-do-not-translate-my-path/releases/download/v6.11.0/patch-mac-6.11.0.zip)

<br/>

a. latest offical support: [v5.44.0](https://download.calibre-ebook.com/5.44.0/calibre-5.44.0.dmg), and patch: [v5.44.0](https://github.com/Cirn09/calibre-do-not-translate-my-path/releases/download/v5.44.0/patch-mac-5.44.0.zip)

b. Actually compatible: [v6.11.0](https://download.calibre-ebook.com/6.11.0/calibre-6.11.0.dmg), and patch: [v6.11.0](https://github.com/Cirn09/calibre-do-not-translate-my-path/releases/download/v6.11.0/patch-mac-6.11.0.zip)

### Additional

如果你已经创建了书库，希望将已有的书库改成非英文路径：

If you have already created a library and want to change the existing library to a non-English path:

0. 备份你的书库（可选，建议）
1. 打开书库，按下 Ctrl+A 选中所有书籍
2. 右键 - 编辑元数据 - 批量编辑元数据 - “查找替换”页
3. 查找模式：正则表达式，查找的字段：`title`，搜索：`$`，替换为：`__DELME__`
4. 点击“应用”，等待 Calibre 完成（点击前注意看一下下面的替换预阅，新书名应当是原书名+`__DELME__`）
5. 查找模式：字符匹配，查找的字段：`title`，搜索：`__DELME__`，“替换为”保持为空（
5. 点击“确定”，等待 Calibre 完成（点击前注意看一下下面的替换预阅，此时的新书名应当是原本的书名）

<br/>

0. Backup your library (optional, but recommended).
1. Open the library and press Ctrl+A to select all books.
2. Right-click and choose "Edit metadata," then select "Bulk metadata edit," and go to the "Search and Replace" page.
3. Use regular expressions as the search mode and search for "title" by entering `$` in the search field. Replace it with `__DELME__`.
4. Click "Apply" and wait for Calibre to finish.
5. Use character matching as the search mode and search for "title" by entering `__DELME__` in the search field. Leave the "Replace with" field empty.
6. Click "OK" and wait for Calibre to finish.

PS: English version is translated by ChatGPT. If you find any mistakes, feel free to open an issue or PR.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Cirn09/calibre-do-not-translate-my-path&type=Date)](https://star-history.com/#Cirn09/calibre-do-not-translate-my-path&Date)

## 原理 | Principle

后序写篇博客，在写了在写了.jpg

I will write a blog post about it later.

## 参考 | References

[snomiao/calibre-utf8-path](https://github.com/snomiao/calibre-utf8-path)
