__English__ · [简体中文](readme_zh.md)

# Calibre: Do Not Translate My Path v3

Control Calibre not to Latinize various paths, including library paths and files sent to devices.

# How to use

1. Download [Release](https://github.com/Cirn09/calibre-do-not-translate-my-path/releases/latest)
2. Open Calibre - Preferences - [Advanced] Plugins - Load plugin from file (bottom right) - Select the downloaded zip file
3. Restart Calibre
4. Enjoy

# Configuration

You can configure it directly in the custom plugin, or add the NoTrans option to the toolbar.

If you modify the translation options of the library and want to refresh the current library save path, you can use the NoTrans - Refresh library in the toolbar. This function will only refresh the current library, not affect other libraries, and will not refresh the files already sent to the device (the association between the device file and the library file remains after the refresh).

# Q&A

Q: How does it work?

A：https://blog.cirn09.xyz//2025/02/05/calibre-no-trans/


Q: Why v3? What about v1 and v2?

A: v1 and v2 are patch solutions, v3 is a plugin solution.


Q: Why are there still v6.x.x and v7.x.x in the Release?

A: Those high version numbers are used in the patch solution and correspond to each Calibre version.


Q: What about the patch version?

A: See the bypy-patch branch


ps: This readme translate by Github copilot auto complete.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Cirn09/calibre-do-not-translate-my-path&type=Date)](https://star-history.com/#Cirn09/calibre-do-not-translate-my-path&Date)
