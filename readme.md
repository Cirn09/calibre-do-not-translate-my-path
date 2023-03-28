# Calibre 不要翻译我的文件路径 | Calibre: Do not translate my file paths

如题所示，让你的 Calibre 不要把中文路径翻译成拼音。

As the title suggests, this is a guide on how to prevent Calibre from translating Chinese file paths into Pinyin.

## 使用方法 | Usage

1. 根据平台下载 Release，覆盖原本 Calibre 文件。
2. 没了

<br/>

1. Download the Release for your platform and replace the original Calibre files.
2. Enjoy.


如果你已经创建了书库，希望将已有的书库改成非英文路径：

If you have already created a library and want to change the existing library to a non-English path:

0. 备份你的书库（可选，建议）
1. 打开书库，按下 Ctrl+A 选中所有书籍
2. 右键 - 编辑元数据 - 批量编辑元数据 - “查找替换”页
3. 查找模式：正则表达式，查找的字段：title，搜索：`$`，替换为：`__DELME__`
4. 点击“应用”，等待 Calibre 完成（点击前注意看一下下面的替换预阅，新书名应当是原书名+`__DELME__`）
5. 查找模式：字符匹配，查找的字段：title，搜索：`__DELME__`，“替换为”保持为空（
5. 点击“确定”，等待 Calibre 完成（点击前注意看一下下面的替换预阅，此时的新书名应当是原本的书名）

<br/>

0. Backup your library (optional, but recommended).
1. Open the library and press Ctrl+A to select all books.
2. Right-click and choose "Edit metadata," then select "Bulk metadata edit," and go to the "Search and Replace" page.
3. Use regular expressions as the search mode and search for "title" by entering $ in the search field. Replace it with __DELME__.
4. Click "Apply" and wait for Calibre to finish.
5. Use character matching as the search mode and search for "title" by entering __DELME__ in the search field. Leave the "Replace with" field empty.
6. Click "OK" and wait for Calibre to finish.

PS: English version is translated by ChatGPT. If you find any mistakes, feel free to open an issue or PR.


## 原理 | Principle
## 

后序写篇博客，在写了在写了.jpg

I will write a blog post about it later.

## 参考 | References

[snomiao/calibre-utf8-path](https://github.com/snomiao/calibre-utf8-path)