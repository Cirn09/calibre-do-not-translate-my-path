[English](readme.md) · __简体中文__

# Calibre 不要翻译我的文件路径 v3

控制 Calibre 不要再把各种路径拉丁化，包括包括书库路径、发送到设备的文件。

# 使用方法

1. 下载 [Release](https://github.com/Cirn09/calibre-do-not-translate-my-path/releases/latest)
2. 打开 Calibre - 首选项 - [高级选项] 插件 - 从文件加载插件（右下角） - 选择下载的 zip 文件
3. 重启 Calibre
4. 享受

# 配置

可以直接在自定义插件里配置，也可以把 NoTrans 选项加进工具栏。

如果修改了书库翻译选项，希望刷新当前书库保存路径，可以使用工具栏的 NoTrans - 刷新书库。这个功能只会刷新当前书库，不会影响其他书库，也不会刷新已经发送到设备的文件（刷新之后设备文件和书库文件之间的关联还在）。

# 问题

Q: 原理？

A：https://blog.cirn09.xyz//2025/02/05/calibre-no-trans/

Q：为什么是 v3？v1 和 v2 呢？

A：v1、v2 是 patch 方案，v3 是插件方案。


Q：Release 里为什么还有 v6.x.x 和 v7.x.x？

A：那些高版本号是 patch 方案时使用的，和 Calibre 版本一一对应。


Q：Patch 版呢？

A：见 bypy-patch 分支

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Cirn09/calibre-do-not-translate-my-path&type=Date)](https://star-history.com/#Cirn09/calibre-do-not-translate-my-path&Date)
