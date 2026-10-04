# Charles 5.2.1 简体中文启动补丁

此补丁参考 [CharlesZH](https://github.com/cuiqingandroid/CharlesZH) 的字节码汉化思路，并按 Charles 5.2.1 的字符串资源和类结构重新制作。本包不直接替换或修改 Charles 安装文件。

## 启动

1. 将压缩包解压到可写目录。
2. 保存 Charles 当前会话并完全退出 Charles。
3. 双击 `Launch-Charles-zhCN.command`。
4. 启动器会确认 Charles 版本和 JAR 指纹，在本目录生成所需的类覆盖文件，再以简体中文启动官方应用。

平常从 Dock 或“应用程序”目录启动 Charles 时仍是原版英文界面。使用本启动器会为这一次启动增加 Java 模块补丁和中文语言设置。

## 覆盖范围

已处理的范围包括：文件、编辑、视图、代理、工具、窗口和帮助菜单；主窗口工具栏、请求列表字段和常用动作；`Charles > Settings…` 的界面、查看器、启动、警告等页面；代理菜单中的记录、SSL 代理（含证书页和位置编辑器）、macOS 代理自动配置确认框、代理设置、限速、断点、代理转发、端口转发、DNS、访问控制、外部代理、外部 DNS 与网页界面等页面和规则编辑器。

其他已处理页面和弹窗包括：高亮规则与条件、序列、配置文件、设置导入/导出、Protobuf 缓存和注册表、证书导入与安全存储、根证书导出、自动保存、镜像、远程/本地映射、DNS 欺骗、请求改写及其规则编辑器、拦截/允许列表。也翻译了日志窗口操作、相关表格列名、部分错误和确认提示。HTTP、SSL、GET/POST 等通用技术缩写、字体名称、字体选项中的 `Default` 与 Gist 品牌名保留原文。

这不是完整的官方本地化，不能保证 Charles 的每个页面、系统控件和所有提示都已汉化。最左侧 `Charles` 应用菜单（About Charles、Settings…、Services、Hide、Quit 等）由 macOS/JDK 原生菜单提供，在当前补丁中仍显示英文；点击“授予权限”后出现的 macOS Helper 授权界面及其系统控件仍由 macOS/原生组件提供，可能显示英文。Charles 的内嵌帮助页面、macOS 文件选择器，以及未逐项核对的少见界面也可能显示英文。

此补丁只适配 Charles 5.2.1。遇到其他版本或不同 JAR 指纹时，构建脚本会停止，不会写入 Charles.app。Charles 更新后需要重新适配补丁。

这是社区汉化补丁，不是 Charles 官方发布或背书的版本。

## 回退

直接从 Dock 或“应用程序”目录正常启动 Charles 即可使用原版。删除本目录即可移除补丁；补丁不会更改 Charles.app、原签名、证书或偏好设置。

## 实现说明

5.2.1 使用 `ResourceBundle` 加载 `com.charlesproxy.strings`。本包提供 `strings_zh.properties`，并通过 `JAVA_TOOL_OPTIONS` 把 Java 的 `--patch-module` 参数交给 Charles 内嵌 JVM；少数硬编码的菜单和提示文字通过改写对应 class 文件的常量池覆盖。类文件只在启动本包时从本机安装复制并改写，补丁不包含 Charles 安装包。
