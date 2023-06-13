# 地球实时卫星云图壁纸
**获取"风云4A"或“风云4B”的实时卫星云图，重绘图片，根据当前屏幕分辨率，生成桌面壁纸**

软件的的GUI窗口，见下图：

![Snipaste_2023-06-13_12-42-36](https://github.com/xu-liyan/current_earth_wallpaper/assets/43141587/28082493-6670-41d5-a0ac-75bccb0401bc)

## 功能
**1. 选择图像源**
* 可以选择 **“风云4A”** 或者 **“风云4B”** 作为图像来源
* 风云4A的云图中，中国大陆地区位于图像正上方，卫星云图分辨率不太高，整体色调偏红
* 风云4B的云图中，中国大陆地区位于图像左上方，卫星云图分辨率较高，整体色调观感比风云4A好
* 风云4A卫星云图的大小不超过 ***1MB***，风云4B卫星云图的大小最大可达 ***20MB***，根据自己的网络环境选择合适的图像源

**2、选择壁纸比例**  
* **铺满屏幕：** 原始图片缩放至屏幕分辨率，裁剪后调整至屏幕高度大小
* **原始大小：** 原始图片缩放至屏幕分辨率，裁剪后，保持图片 ‘原始大小’
* **黄金比例：** 原始图片缩放至屏幕分辨率，裁剪后，保持图片纵横比，高度调整至屏幕高度的 ‘0.618倍’
* **更小尺寸：** 原始图片缩放至屏幕分辨率，裁剪后，保持图片纵横比，高度调整至屏幕高度的 ‘0.45倍’

**3、选择图像保存位置**  
* 获取的原始图片和生成的壁纸图片都会保存在此文件夹
* 文件夹图片最大保存数量为96张，超过之后从最旧的文件开始依次删除，最终保留96张图片

**4、图像获取频率** 
* 每获取一次图像，壁纸也更新一次，单位为分钟
* 风云4A卫星图像的官方更新频率为60分钟，如果图像源为“FY4A”，图像获取频率建议≥60分钟
* 风云4B卫星图像的官方更新频率为15分钟，如果图像源为“FY4B”，图像获取频率建议≥15分钟

## 提示
* 点击“开始”按钮，程序按照设定的频率自动更换壁纸
* 点击“退出”按钮，弹出确认窗口，点击“确定”完全退出程序
* 点击右下角的“设为开机自启”，程序会在系统启动时自动打开，并自动开始更新壁纸，不需要手动点击“开始”。如需取消，再次点击此按钮。
* 关闭程序GUI窗口，程序默认在后台继续运行，可以在状态栏的托盘区域看到程序图标。点击托盘中的程序图标，可以恢复GUI窗口，在图标上右键会弹出菜单，可以选择显示窗口或完全退出程序

# 鸣谢
* 此项目核心框架和GUI界面的代码由 [**ChatGPT**](https://chat.openai.com/chat) 生成（ChatGPT确实强大，但生成的代码也存在不少问题，大家使用时需仔细斟酌）
* 此项目的想法来自于 [**wenkechen**](https://github.com/wenkechen) 的项目 [**MineEarth**](https://github.com/wenkechen/MineEarth) 。几年前曾使用过这款程序，但程序中存在一些问题，作者长期未更新，且图像源只有“向日葵8号”。个人比较想要风云卫星的图像，遂，自己开了这个项目。
* 图像处理的代码，其中一部分参考了 [**Jiale685**](https://blog.csdn.net/L141210113/article/details/102642277?spm=1001.2014.3001.5506) 的项目
