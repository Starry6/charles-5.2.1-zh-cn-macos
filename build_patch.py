#!/usr/bin/env python3
"""Build the non-invasive Charles 5.2.1 Chinese Java module patch."""

from __future__ import annotations

import argparse
import hashlib
import plistlib
import struct
from pathlib import Path
from zipfile import ZipFile

EXPECTED_JAR_SHA256 = "e3d88ccdc495ddc37f2f120ccf4577702bbe731a5a311aa49c035716695e34f4"
DEFAULT_APP = Path("/Applications/Charles.app")

FRAME = {
    "Charles started": "Charles 已启动",
    "Debug logging": "调试日志",
    "Debug logging enabled.  Double-click to disable.": "调试日志已启用。双击可关闭。",
    "Breakpoints": "断点",
    "Memory Usage. Click to run Garbage Collection.": "内存用量。点击执行垃圾回收。",
    "Help": "帮助",
}

MENU = {
    "About Java": "关于 Java",
    "port \x01": "端口 \x01",
}

HELP_CLASSES = {
    "com/charlesproxy/gui/menus/HelpMenu$2.class": {
        "Thank you for registering Charles. We really appreciate it.\n\nPlease visit https://www.charlesproxy.com/ for more information\non Charles or if you need to purchase additional licenses.": "感谢注册 Charles！\n\n请访问 https://www.charlesproxy.com/ 了解更多信息，或购买其他许可证。",
    },
    "com/charlesproxy/gui/menus/HelpMenu$3.class": {
        "Are you sure you want to remove your Charles license from this installation of Charles?": "确定要从此 Charles 安装中移除许可证吗？",
    },
    "com/charlesproxy/gui/menus/HelpMenu$6.class": {
        "The available local network interfaces and their IP addresses are listed below.  Excluded from this list are any loopback or link local addresses.": "下方列出了可用的本地网络接口及其 IP 地址。回环地址和链路本地地址不会显示在此列表中。",
    },
    "com/charlesproxy/gui/menus/HelpMenu$8.class": {
        "The certificate file is missing or corrupt. Please reset the Charles Root SSL Certificate and try again.": "证书文件缺失或已损坏。请重置 Charles 根 SSL 证书后重试。",
    },
    "com/charlesproxy/gui/menus/HelpMenu$11.class": {
        "Configure your device to use Charles as its HTTP proxy on \x01, then browse to chls.pro/ssl to download and install the certificate.\n\nNote that on iOS 10 and later you must then go into Settings > General > About > Certificate Trust Settings and enable the Charles certificate to be trusted.": "将设备的 HTTP 代理设为 Charles（地址：\x01），然后访问 chls.pro/ssl 下载并安装证书。\n\niOS 10 及更高版本请前往“设置”>“通用”>“关于本机”>“证书信任设置”，开启对 Charles 证书的完全信任。",
    },
    "com/charlesproxy/gui/menus/HelpMenu$12.class": {
        "The password used on the keystore files Charles creates when it generates SSL certificates is:": "Charles 生成 SSL 证书时，密钥库文件使用的密码为：",
    },
    "com/charlesproxy/gui/menus/HelpMenu$13.class": {
        "Are you sure you want to reset the Charles Root Certificate for this installation of Charles?\nEach installation of Charles generates its own unique Charles Root Certificate. If you reset, you will need to install and trust this Charles installation’s new Charles Root Certificate on macOS and your devices.": "确定要重置此 Charles 安装的根证书吗？\n每个 Charles 安装都会生成唯一的根证书。重置后，你需要在 macOS 和设备上重新安装并信任新的 Charles 根证书。",
        "Reset": "重置",
        "Cancel": "取消",
    },
}

PROXY = {
    "One or more of the required proxy servers are not currently active. Please check the Proxy Settings.": "一个或多个所需的代理服务器当前未运行。请检查代理设置。",
}

EDIT_MENU = {
    "Undo": "撤销",
    "Redo": "重做",
    "Cut": "剪切",
    "Copy": "复制",
    "Paste": "粘贴",
}

SESSION_UI = {
    "Compose": "编写请求…",
    "Repeat": "重发请求",
    "Structure": "结构",
    "Sequence": "序列",
    "Focused": "关注",
    "Unencrypted": "未加密",
    "Filter": "筛选",
    "Settings": "设置",
}

SESSION_NAV = {
    "Sequence": "序列",
    "Structure": "结构",
}

SESSION_NAV_SEQUENCE = {
    "Sequence": "序列",
    "Show in Sequence": "在序列视图中显示",
}

SESSION_NAV_STRUCTURE = {
    "Structure": "结构",
    "Show in Structure": "在结构视图中显示",
}

TABLE_FIELDS = {
    "Icon": "图标",
    "Response Status": "响应状态",
    "Method": "方法",
    "Host": "主机",
    "Path": "路径",
    "Request Start Time": "请求开始时间",
    "Request Complete Time": "请求完成时间",
    "Response Start Time": "响应开始时间",
    "Response End Time": "响应结束时间",
    "Duration": "耗时",
    "DNS Duration": "DNS 耗时",
    "Connect Duration": "连接耗时",
    "SSL Handshake Duration": "SSL 握手耗时",
    "Request Duration": "请求耗时",
    "Response Duration": "响应耗时",
    "Client Address": "客户端地址",
    "Client IP": "客户端 IP",
    "Client Kept Alive": "客户端保持连接",
    "Client Port": "客户端端口",
    "Content-Type": "内容类型",
    "End": "结束时间",
    "Info": "信息",
    "Kept Alive": "保持连接",
    "Notes": "备注",
    "Protocol": "协议",
    "Remote Address": "远程地址",
    "Remote IP": "远程 IP",
    "Remote Port": "远程端口",
    "Req Bdy Size": "请求体大小",
    "Req Enc": "请求编码",
    "Req End": "请求结束",
    "Req Hdr Size": "请求头大小",
    "Req Hshk Size": "请求握手大小",
    "Req Size": "请求大小",
    "Request": "请求",
    "Request Body Size": "请求体大小",
    "Request Content Encoding": "请求内容编码",
    "Request Handshake Size": "请求握手大小",
    "Request Header Size": "请求头大小",
    "Request Size": "请求大小",
    "Resp Bdy Size": "响应体大小",
    "Resp Enc": "响应编码",
    "Resp Hdr Size": "响应头大小",
    "Resp Hshk Size": "响应握手大小",
    "Resp Size": "响应大小",
    "Resp Start": "响应开始",
    "Response": "响应",
    "Response Body Size": "响应体大小",
    "Response Content Encoding": "响应内容编码",
    "Response Handshake Size": "响应握手大小",
    "Response Header Size": "响应头大小",
    "Response Size": "响应大小",
    "Size": "大小",
    "Start": "开始时间",
    "Status": "状态",
    "Tags": "标签",
}

TOOLBAR = {
    "Structure": "结构",
    "Sequence": "序列",
    "Clear": "清空",
    "Compose": "编写请求…",
    "Repeat": "重发请求",
    "Start": "开始",
    "Stop": "停止",
    "Start ": "启动 ",
    "Stop ": "停止 ",
    "Breakpoints": "断点",
    "Throttle": "限速",
    "Proxying": "代理",
    "Disable": "禁用",
    "Enable": "启用",
    "Buy": "购买",
    "Purchase a License": "购买许可证",
    "\x01 Recording": "\x01记录",
    "\x01 SSL Proxying": "\x01 SSL 代理",
    "\x01 Throttling": "\x01限速",
    "\x01 Breakpoints": "\x01断点",
}

TOOLBAR_RECORDING = {
    "Stop": "停止",
    "Start": "开始",
    "\x01 Recording": "\x01记录",
}

TOOLBAR_SSL = {
    "Stop": "停止",
    "Start": "开始",
    "\x01 SSL Proxying": "\x01 SSL 代理",
}

TOOLBAR_THROTTLE = {
    "Stop": "停止",
    "Start": "开始",
    "\x01 Throttling": "\x01限速",
}

TOOLBAR_BREAKPOINTS = {
    "Disable Breakpoints": "禁用断点",
    "Enable Breakpoints": "启用断点",
}

TOOLBAR_PROXYING = {
    "Start ": "启动 ",
    "Stop ": "停止 ",
}

STATUS_MESSAGES = {
    "Throttling started": "已开始限速",
    "Throttling stopped": "已停止限速",
    "Full connection quality": "连接状态正常",
    "Reduced connection quality": "连接质量下降",
    "Unstable (\x01%)": "连接不稳定（\x01%）",
    "Recording started": "已开始记录",
    "Recording stopped": "已停止记录",
}

WINDOW_MENU = {
    "Enter Full Screen": "进入全屏",
    "Leave Full Screen": "退出全屏",
}

COMPOSE_DIALOG = {
    "Compose": "编写请求",
    "Cancel": "取消",
    "URL:": "请求地址：",
    "Method:": "方法：",
    "Content type:": "内容类型：",
    "Protocol version:": "协议版本：",
}

UI_SETTINGS = {
    "Show Charles icon in the menu bar": "在菜单栏显示 Charles 图标",
    "Show system tray icon": "在系统托盘显示图标",
    "Minimise to system tray": "最小化到系统托盘",
    "Show memory usage": "显示内存用量",
    "Enable global hotkeys": "启用全局快捷键",
    "Charles window always on top": "窗口始终置顶",
    "Highlight changes in the Structure view": "高亮显示结构视图中的变更",
    "Display font:": "显示字体：",
    "Display font size:": "显示字号：",
    "Highlight query params:": "高亮显示查询参数：",
    "Display Font Changes": "显示字体更改",
    "Please restart Charles to complete the application of display font changes.": "请重新启动 Charles 以完成显示字体更改。",
}

VIEWERS_SETTINGS = {
    "Viewers": "查看器",
    "Show line numbers": "显示行号",
    "Show whitespace": "显示空白字符",
    "Line wrap": "自动换行",
    "Tall": "垂直",
    "Wide": "水平",
    "Combine header and body viewers": "合并头部和正文查看器",
    "Combine request and response": "合并请求和响应",
    "Structure view layout:": "结构视图布局：",
    "Sequence view layout:": "序列视图布局：",
    "Speed:": "速度单位：",
    "bytes / second": "字节/秒",
    "bits / second": "比特/秒",
    "Time:": "时间单位：",
    "minutes and seconds": "分钟和秒",
    "milliseconds": "毫秒",
}

STARTUP_SETTINGS = {
    "Open a new session": "启动时新建会话",
    "Start throttling": "启动时启用限速",
    "Check for updates": "启动时检查更新",
}

WARNINGS_SETTINGS = {
    "Warnings": "警告",
    "Prompt to save sessions": "保存会话时提示",
    "Warn when clearing a session": "清空会话时警告",
    "Reset Warnings": "重置警告提示",
}

QUERY_PARAM_HIGHLIGHT = {
    "None": "无",
    "Greyscale": "灰度",
    "Color": "彩色",
}

SETTINGS_DIALOG = {
    "Done": "完成",
    "Cancel": "取消",
    "Help": "帮助",
    "Import": "导入",
    "Export": "导出",
    "Apply": "应用",
    "Charles Settings": "Charles 设置",
}

UNSAVED_CHANGES = {
    "Save": "保存",
    "Don't Save": "不保存",
    "Cancel": "取消",
    'There are unsaved changed to "\x01".\nDo you wish to save changes?': '会话“\x01”有未保存的更改。\n是否保存？',
    "Unsaved Changes": "未保存的更改",
}

PROXY_DIALOGS = {
    "com/charlesproxy/gui/tools/UOUV.class": {
        "Enable \x01": "启用\x01",
        "Only for selected \x01": "仅对选中的\x01",
    },
    "com/charlesproxy/gui/settings/SSLProxyingPanel.class": {
        "Include": "包含",
        "Exclude": "排除",
    },
    "com/charlesproxy/gui/lib/table/LocationsTableModel.class": {
        "Location": "位置",
    },
    "com/charlesproxy/gui/helper/LocationsTableHelper$LocationFormPanel.class": {
        "Edit Location": "编辑位置",
    },
    "com/charlesproxy/gui/helper/edfX.class": {
        "Filter": "筛选",
    },
    "com/charlesproxy/gui/helper/LlnI.class": {
        "Protocol:": "协议：",
        "Host:": "主机：",
        "Port:": "端口：",
        "Path:": "路径：",
        "Query:": "查询参数：",
    },
    "com/charlesproxy/gui/settings/qClj.class": {
        "You must create a Charles Secure Store to import private SSL Certificates into Charles.": "请先创建 Charles 安全存储区，再将私有 SSL 证书导入 Charles。",
        "The Charles Secure Store is locked, you must unlock it for Charles to access your private SSL Certificates.": "Charles 安全存储区已锁定。请先解锁，以便 Charles 访问其中的私有 SSL 证书。",
    },
    "com/charlesproxy/gui/settings/ImportCertificateHelper$ImportPemPanel.class": {
        "Certificate With Private Key": "带私钥的证书",
        "PEM Encoded Private Key": "PEM 编码的私钥",
        "PEM Encoded Certificates": "PEM 编码的证书链",
        "Cannot validate private key without certificate": "没有证书，无法验证私钥",
        "Private key does not match public key from primary certificate": "私钥与主证书中的公钥不匹配",
        "Unexpected error validating private key": "验证私钥时发生意外错误",
        "Unable to parse private key": "无法解析私钥",
        "Invalid certificate chain": "证书链无效",
        "Unexpected error validating certificate chain": "验证证书链时发生意外错误",
        "Error with private key\n\t- \x01": "私钥错误\n\t- \x01",
        "Error with certificate chain\n\t- \x01": "证书链错误\n\t- \x01",
        "You must supply a private key": "必须提供私钥",
    },
    "com/charlesproxy/gui/settings/ImportCertificateHelper$CertificatesTableModel.class": {
        "Certificate": "证书",
    },
    "com/charlesproxy/gui/settings/RootSSLCertificateSettingsPanel.class": {
        "Using automatically generated root certificate": "使用自动生成的根证书",
        "Import PEM": "导入 PEM",
        "Import P12": "导入 P12",
        "Remove": "移除",
    },
    "com/charlesproxy/gui/settings/ServerSSLCertificatesSettingsPanel.class": {
        "Import PEM": "导入 PEM",
        "Import P12": "导入 P12",
        "Remove": "移除",
    },
    "com/charlesproxy/gui/settings/ClientSSLCertificatesSettingsPanel$MyTableModel.class": {
        "Host": "主机",
        "Certificate": "证书",
    },
    "com/charlesproxy/gui/settings/ClientSSLCertificatesSettingsPanel$MyFormPanel.class": {
        "Edit Client SSL Certificate": "编辑客户端 SSL 证书",
        "No Certificate": "未选择证书",
        "No certificate selected": "尚未选择证书",
        "Import PEM": "导入 PEM",
        "Import P12": "导入 P12",
    },
    "com/charlesproxy/gui/settings/ProxySettingsPanel$AbstractIntegrationPanel.class": {
        "Enable \x01 proxy": "启用 \x01 代理",
        "Enable \x01 proxy on launch": "启用 \x01 代理（启动时启用）",
        "Use HTTP proxy": "使用 HTTP 代理",
        "Use SOCKS proxy": "使用 SOCKS 代理",
    },
    "com/charlesproxy/gui/settings/ProxySettingsPanel$OptionsPanel.class": {
        "Bypass Charles for these Hosts & Domains:": "以下主机和域名绕过 Charles：",
        "Configures the browser or OS bypass proxy settings.": "配置浏览器或操作系统的代理绕过规则。",
        "Invalid domain value '\x01'.": "无效的域名“\x01”。",
        "One or more of the bypass values you supplied included unnecessary information such as a protocol or port number.  Charles has automatically corrected these values.": "你填写的绕过规则中有一项或多项包含协议或端口号等多余信息，Charles 已自动修正。",
        "\x01 Warning": "\x01 警告",
    },
    "com/charlesproxy/gui/settings/ProxySettingsPanel$ProxiesPanel.class": {
        "Enable SOCKS proxy": "启用 SOCKS 代理",
        "Use a dynamic port": "使用动态端口",
        "Enable HTTP proxying over SOCKS": "通过 SOCKS 启用 HTTP 代理",
        "Include default HTTP ports (80, 443, 8080, 8443)": "包含默认 HTTP 端口（80、443、8080、8443）",
        "Enable transparent HTTP proxying": "启用透明 HTTP 代理",
        "Support HTTP/2": "支持 HTTP/2",
        "Restore Defaults": "恢复默认值",
        "HTTP Proxy Mode": "HTTP 代理模式",
        "SOCKS Proxy Mode": "SOCKS 代理模式",
        "HTTP Proxy": "HTTP 代理",
        "SOCKS Proxy": "SOCKS 代理",
        "Port:": "端口：",
        "Ports:": "端口：",
    },
    "com/charlesproxy/gui/settings/ProxySettingsPanel$MozillaFirefoxPanel.class": {
        "Manually choose profile path": "手动选择配置文件路径",
        "Choose…": "选择…",
    },
    "com/charlesproxy/gui/settings/DNSSettingsPanel.class": {
        "Prefer IPv6 addresses when connecting to dual-stack hosts": "连接到双栈主机时优先使用 IPv6 地址",
    },
    "com/charlesproxy/gui/settings/ACLSettingsPanel.class": {
        "This access control list determines who can use this Charles instance. The localhost (this machine) is always included. The default access control list is empty, meaning that no one can use Charles except from this computer.\n\nIf you would like to enable other machines to connect to this Charles instance enter IP addresses below, eg. 192.168.2.35 or fe80::7751:8349:cfe2:d2cc. You can also specify subnets, eg. 192.168.2.0/24 or fc00::/64.To allow anyone to access Charles enter 0.0.0.0/0 for IPv4 connections and ::/0 for IPv6.": "此访问控制列表用于指定哪些设备可以使用此 Charles 实例。本机始终允许访问。默认列表为空，表示仅允许本机使用 Charles。\n\n若要允许其他设备连接此 Charles 实例，请在下方输入 IP 地址，例如 192.168.2.35 或 fe80::7751:8349:cfe2:d2cc。也可以指定子网，例如 192.168.2.0/24 或 fc00::/64。若要允许任何设备访问，请为 IPv4 输入 0.0.0.0/0，为 IPv6 输入 ::/0。",
        "Prompt to allow unauthorized connections": "对未授权连接进行提示",
    },
    "com/charlesproxy/gui/settings/ExternalProxySettingsPanel.class": {
        "Web Proxy (HTTP)": "Web 代理（HTTP）",
        "Secure Web Proxy (HTTPS)": "安全 Web 代理（HTTPS）",
        "SOCKS Proxy": "SOCKS 代理",
        "Web Proxy Server": "Web 代理服务器",
        "Secure Web Proxy Server": "安全 Web 代理服务器",
        "SOCKS Proxy Server": "SOCKS 代理服务器",
        "Use external proxy servers": "使用外部代理服务器",
        "Select a protocol to configure:": "选择要配置的协议：",
        "Proxy server requires a password": "代理服务器需要密码",
        "Domain:": "域：",
        "Username:": "用户名：",
        "Password:": "密码：",
        "Bypass external proxies for the following hosts:": "以下主机绕过外部代理：",
        "Always bypass external proxies for localhost": "localhost 始终绕过外部代理",
        "The domain field is only required for Windows authentication (NTLM).": "仅 Windows 身份验证（NTLM）需要填写域字段。",
    },
    "com/charlesproxy/gui/settings/ExternalDNSResolverSettingsPanel.class": {
        "hosts": "主机",
        "External Resolver Address:": "外部解析器地址：",
        "The External Resolver Address must be specified in order to enable the External DNS Resolver": "启用外部 DNS 解析器前，必须指定解析器地址。",
    },
    "com/charlesproxy/gui/settings/RemoteControlSettingsPanel.class": {
        "Enable web interface": "启用网页界面",
        "Allow anonymous access": "允许匿名访问",
        "The Web Interface lets you control Charles using your web browser. You can access the Web Interface at http://control.charles/ when Charles is running. You can enable this feature and configure access control below.": "网页界面可让你通过浏览器控制 Charles。Charles 运行时，可访问 http://control.charles/ 打开网页界面。你可以在下方启用此功能并配置访问控制。",
    },
    "com/charlesproxy/gui/settings/RemoteControlSettingsPanel$RemoteControlTableModel.class": {
        "Username": "用户名",
        "Password": "密码",
    },
    "com/charlesproxy/gui/settings/RecordingSettingsPanel$LimitsPanel.class": {
        "Recording size limit (MB):": "记录大小限制（MB）：",
        "Limit recording history": "限制记录历史",
        "Max requests:": "最大请求数：",
        "Limit WebSocket transaction history": "限制 WebSocket 事务历史",
        "Max messages:": "最大消息数：",
        "A recording limit means that old requests will automatically be cleared from the session when the limit is reached. Please ensure that the limit is set high enough so that you do not unexpectedly lose data.": "达到记录上限后，旧请求会自动从会话中清除。请将上限设为足够大的数值，避免意外丢失数据。",
        "A WebSocket transaction limit means that old WebSocket messages will automatically be cleared from the transaction when the limit is reached. Please ensure that the limit is set high enough so that you do not unexpectedly lose data.": "达到 WebSocket 事务上限后，旧 WebSocket 消息会自动从事务中清除。请将上限设为足够大的数值，避免意外丢失数据。",
        "Recording Limits": "记录限制",
    },
    "com/charlesproxy/tools/breakpoints/BreakpointsTool$MySettingsPanel$BreakpointsTableModel.class": {
        "Location": "位置",
        "Breakpoint": "断点",
        "\x01Request": "\x01请求",
        "\x01Request & Response": "\x01请求和响应",
        "\x01Response": "\x01响应",
    },
    "com/charlesproxy/tools/breakpoints/BreakpointsTool$MySettingsPanel$BreakpointFormPanel.class": {
        "Edit Breakpoint": "编辑断点",
        "Request": "请求",
        "Response": "响应",
        "Please choose to break on the Request or Response or both.": "请选择在请求、响应或两者上设置断点。",
    },
    "com/charlesproxy/tools/breakpoints/ssJy.class": {"Method:": "方法："},
    "com/charlesproxy/tools/ReverseProxiesTool$MySettingsPanel$ReverseProxyFormPanel.class": {
        "Edit Reverse Proxy": "编辑反向代理",
        "Local port:": "本地端口：",
        "Remote host:": "远程主机：",
        "Remote port:": "远程端口：",
        "Rewrite redirects": "改写重定向",
        "Preserve host in header fields": "保留请求头中的 Host 字段",
        "Listen on a specific address:": "监听指定地址：",
        "Local address:": "本地地址：",
        "Remote Port": "远程端口",
        "Local Port": "本地端口",
    },
    "com/charlesproxy/tools/PortForwardingTool$MySettingsPanel$PortForwardingFormPanel.class": {
        "Edit Port Forwarding": "编辑端口转发",
        "Protocol:": "协议：",
        "Start port:": "起始端口：",
        "End port:": "结束端口：",
        "Remote host:": "远程主机：",
        "Remote port:": "远程端口：",
        "Listen on a specific address:": "监听指定地址：",
        "Local address:": "本地地址：",
        "End Port": "结束端口",
        "Remote Host": "远程主机",
        "A remote host is required": "必须填写远程主机。",
        "Remote Port": "远程端口",
        "Start Port": "起始端口",
    },
    "com/charlesproxy/gui/settings/ThrottleSettingsPanel.class": {
        "hosts": "主机",
    },
    "com/charlesproxy/gui/settings/QUqz.class": {
        "Add Preset": "添加预设",
        "Remove Preset": "删除预设",
        "Throttle preset:": "限速预设：",
        "Set the throttle configuration based on preset connection characteristics.": "根据预设的网络连接特征设置限速参数。",
        "Download": "下载",
        "Upload": "上传",
        "Bandwidth (kbps):": "带宽（kbps）：",
        "Utilisation (%):": "利用率（%）：",
        "Round-trip latency (ms):": "往返延迟（ms）：",
        "MTU (bytes):": "MTU（字节）：",
        "Reliability (%):": "可靠性（%）：",
        "Likelihood a connection will fail completely": "连接完全中断的可能性",
        "Stability (%):": "稳定性（%）：",
        "Likelihood a connection will be unstable": "连接不稳定的可能性",
        "Unstable quality range (%):": "不稳定时的连接质量范围（%）：",
        "The quality range for unstable connections": "不稳定连接的质量范围",
        "Download Bandwidth": "下载带宽",
        "Upload Bandwidth": "上传带宽",
        "Download Utilisation": "下载利用率",
        "Upload Utilisation": "上传利用率",
        "Latency": "延迟",
        "Reliability": "可靠性",
        "MTU": "MTU",
        "Stability": "稳定性",
        "Low Quality": "低质量阈值",
        "High Quality": "高质量阈值",
    },
    "com/charlesproxy/gui/settings/ThrottleSettingsPanel$ThrottleConfigurationPanel$4.class": {
        "Preset Name": "预设名称",
        "New Throttle Preset": "新建限速预设",
        "You must provide a non-empty preset name.": "预设名称不能为空。",
        "You must provide a unique preset name, '\x01' has already been used.": "预设名称必须唯一，‘\x01’已被使用。",
    },
    "com/charlesproxy/config/qCWd.class": {
        "56 kbps Modem": "56 kbps 调制解调器",
        "32 Mbps Fibre": "32 Mbps 光纤",
        "100 Mbps Fibre": "100 Mbps 光纤",
    },
}

ADDITIONAL_UI = {
    "com/charlesproxy/gui/settings/SettingsDialog.class": {
        "Apply": "应用",
    },
    "com/charlesproxy/gui/frames/LogFrame.class": {
        "Filter": "筛选",
        "Close \x01": "关闭\x01",
        "Save \x01…": "保存\x01…",
        "Clear \x01": "清除\x01",
    },
    "com/charlesproxy/gui/settings/SequenceSettingsPanel.class": {
        "Sequence": "序列",
        "Auto scroll": "自动滚动",
        "Filter uses regex": "筛选使用正则表达式",
        "Max rows:": "最大行数：",
    },
    "com/charlesproxy/gui/settings/HighlightSettingsPanel$ConditionPanel.class": {
        "Edit Condition": "编辑条件",
        "Regex": "正则表达式",
        "Case sensitive": "区分大小写",
        "Match whole value": "匹配整个值",
        "Matches": "匹配",
        "Does not match": "不匹配",
        "Type:": "类型：",
        "Name:": "名称：",
        "Value:": "值：",
    },
    "com/charlesproxy/gui/settings/HighlightSettingsPanel$CategoryPanel.class": {
        "Edit Category": "编辑类别",
        "Conditions": "条件",
        "Highlight Color": "高亮颜色",
    },
    "com/charlesproxy/gui/settings/HighlightSettingsPanel$CategoryTableModel.class": {
        "Color": "颜色",
        "Location": "位置",
        "Conditions": "条件",
    },
    "com/charlesproxy/gui/settings/HighlightSettingsPanel$ConditionTableModel.class": {
        "Field": "字段",
        "Condition": "条件",
    },
    "com/charlesproxy/gui/settings/GistIntegrationSettingsPanel.class": {
        "Open Gist after publishing": "发布后打开 Gist",
        "Secret": "私密",
        "Public": "公开",
        "Use GitHub Enterprise": "使用 GitHub Enterprise",
        "Publish as:": "发布为：",
        "Publish limit (MB):": "发布大小限制（MB）：",
        "GitHub location:": "GitHub 地址：",
        "Deauthorize": "取消授权",
        "Authorize": "授权",
        "Charles is authorized to publish to your GitHub account.": "Charles 已获准向你的 GitHub 帐户发布 Gist。",
        "You must authorize Charles to publish Gists using your GitHub account. This will open GitHub.com where you can grant Charles access to publish with your account.": "请先授权 Charles 使用你的 GitHub 帐户发布 Gist。接下来会打开 GitHub.com，你可以在那里允许 Charles 代表你发布 Gist。",
        "Please enter a valid location e.g. https://api.github.com": "请输入有效的地址，例如 https://api.github.com。",
        "Error parsing URI: \x01": "URI 解析失败：\x01",
    },
    "com/charlesproxy/gui/settings/GistIntegrationSettingsPanel$3.class": {
        "More Info": "更多信息",
        "GitHub Authorization": "GitHub 授权",
        "Paste the GitHub authorization token below.\n\nYou may revoke this access at any time from your GitHub account.": "请在下方粘贴 GitHub 授权令牌。\n\n你可以随时在 GitHub 帐户中撤销此授权。",
        "Unable to open OAuth token URI": "无法打开 OAuth 令牌 URI",
        "You need to manually generate a personal access token from your enterprise GitHub account. You can then copy and paste that token below to allow Charles to publish gists on your behalf.": "请在 GitHub Enterprise 帐户中手动生成个人访问令牌，再将令牌复制到下方，以允许 Charles 代表你发布 Gist。",
    },
    "com/charlesproxy/gui/settings/UOLV.class": {
        "GitHub Authorization": "GitHub 授权",
        "You have a saved authorisation token for your current GitHub server.  This token will not be valid for other GitHub installations.": "当前 GitHub 服务器已保存授权令牌。该令牌不能用于其他 GitHub 服务实例。",
    },
    "com/charlesproxy/gui/settings/ProfilesDialog.class": {
        "Profiles contain a complete copy of all your configuration settings.\n\nThe currently active profile is updated each time you change your current settings, when you change your active profile all your settings are reverted to the state they were in when you last used that profile.\n\nBe aware that if you import a saved configuration it will overwrite the settings for your current profile.  We recommend using import/export to backup or create a snapshot of your current configuration and profiles to maintain multiple parallel workspaces.\n": "每个配置文件都包含一份完整的配置副本。\n\n当前活动配置文件会随着设置的更改而更新。切换活动配置文件时，所有设置都会恢复为上次使用该配置文件时的状态。\n\n导入已保存的配置会覆盖当前配置文件中的设置。建议使用导入/导出备份当前配置，或为配置文件创建快照，以维护多个独立的工作环境。\n",
    },
    "com/charlesproxy/gui/settings/ProfilesDialog$ProfilesTableModel.class": {
        "Active": "活动",
        "Name": "名称",
        "Error": "错误",
        "Error restoring profile \x01": "还原配置文件失败：\x01",
        "Error renaming profile.": "重命名配置文件失败。",
        "Error creating profile \x01": "创建配置文件失败：\x01",
        "Error deleting profile \x01": "删除配置文件失败：\x01",
        "Untitled": "未命名",
        "Delete Profiles": "删除配置文件",
        "Are you sure you want to delete all selected profiles? This action cannot be undone.": "确定要删除所有选中的配置文件吗？此操作无法撤销。",
        "\x01 Note that the default profile and the currently active profile cannot be deleted.": "\x01 注意：默认配置文件和当前活动配置文件无法删除。",
    },
    "com/charlesproxy/config/export/ConfigurationImportExportSection.class": {
        "Proxy": "代理",
        "Tools": "工具",
        "Preferences": "偏好设置",
    },
    "com/charlesproxy/gui/settings/ImportExportDialog.class": {
        "Import": "导入",
        "Export": "导出",
        "import": "导入",
        "export": "导出",
        "Choose File": "选择文件",
        "\x01 XML Files": "\x01 XML 文件",
        "Charles Settings": "Charles 设置",
    },
    "com/charlesproxy/gui/settings/ImportExportDialog$MultiSelectListPanel.class": {
        "Select all": "全选",
        "Select the settings to \x01:": "选择要\x01的设置：",
    },
    "com/charlesproxy/gui/settings/AbstractImportExportSettingsPanel.class": {
        "Incorrect configuration type": "配置类型不正确",
        "The file '%s' did not contain configuration of type %s": "文件“%s”中不包含类型为 %s 的配置",
    },
    "com/charlesproxy/gui/settings/ProtobufSettingsPanel$CachingPanel.class": {
        "Cache": "缓存",
        "Cache resolved protobuf descriptors": "缓存已解析的 Protocol Buffers 描述符",
        "Cache TTL (seconds):": "缓存有效期（秒）：",
        "Cache size:": "缓存大小：",
        "Hits:": "命中次数：",
        "Misses:": "未命中次数：",
        "304s:": "304 次：",
        "Clear Cache": "清除缓存",
        "Heuristic Cache TTL": "启发式缓存有效期",
        "Please enter a non-negative number.": "请输入非负数。",
    },
    "com/charlesproxy/gui/settings/ProtobufSettingsPanel$CacheLocationsTableModel.class": {
        "Currently Cached Resources": "当前缓存的资源",
    },
    "com/charlesproxy/gui/settings/ProtobufSettingsPanel$RegistryPanel.class": {
        "Registry": "注册表",
    },
    "com/charlesproxy/gui/settings/ProtobufSettingsPanel$RegistryPanel$RegistryTableModel.class": {
        "Descriptor": "描述符",
        "Error": "错误",
        "Error adding descriptor \x01.  The most likely reason for this error is that the uploaded file is not a valid descriptor or is missing required dependencies.  You can upload any required descriptors first and then retry.": "添加描述符\x01失败。文件可能不是有效的描述符，或缺少依赖项。请先上传所需的依赖描述符，然后重试。",
        "Error deleting descriptor \x01.  The most likely reason for this error is that the descriptor you attempted to delete contains definitions required by one of the remaining descriptors.": "删除描述符\x01失败。该描述符可能包含其他现存描述符所需的定义，因此无法删除。",
    },
    "com/charlesproxy/gui/settings/ClientSSLCertificatesSettingsPanel.class": {
        "Failed to save certificates": "保存证书失败",
    },
    "com/charlesproxy/gui/settings/ImportCertificateHelper.class": {
        "Import Failed": "导入失败",
        "Certificate Loader": "证书加载器",
        "Unexpected error validating certificate": "验证证书时发生意外错误",
        "Invalid certificate chain, a certificate in the chain failed verification by the next certificate": "证书链无效：链中的某个证书未通过后续证书的验证",
        "Private key does not match public key from primary certificate": "私钥与主证书中的公钥不匹配",
        "Unlock Secure Store": "解锁安全存储区",
        "Reset Secure Store": "重置安全存储区",
        "Create Secure Store": "创建安全存储区",
    },
    "com/charlesproxy/gui/settings/ImportCertificateHelper$ImportPemPanel.class": {
        "Cannot validate private key without certificate": "没有证书，无法验证私钥",
        "Private key does not match public key from primary certificate": "私钥与主证书中的公钥不匹配",
        "Unexpected error validating private key": "验证私钥时发生意外错误",
        "Unable to parse private key": "无法解析私钥",
        "Error with private key\n\t- \x01": "私钥错误\n\t- \x01",
        "Error with certificate chain\n\t- \x01": "证书链错误\n\t- \x01",
        "You must supply a private key": "必须提供私钥",
    },
    "com/charlesproxy/gui/settings/ImportCertificateHelper$1.class": {
        "Charles Secure Store": "Charles 安全存储区",
    },
    "com/charlesproxy/gui/settings/ImportCertificateHelper$2.class": {
        "Reset Charles Secure Store": "重置 Charles 安全存储区",
        "Are you sure you want to reset the Charles Secure Store? You will need to add your certificates to Charles again.": "确定要重置 Charles 安全存储区吗？重置后需要重新向 Charles 添加证书。",
        "Reset": "重置",
        "Cancel": "取消",
    },
    "com/charlesproxy/gui/settings/ImportCertificateHelper$3.class": {
        "Charles Secure Store": "Charles 安全存储区",
    },
    "com/charlesproxy/gui/frames/RegisterFrame.class": {
        "Register": "注册",
        "Cancel": "取消",
        "Registered Name:": "注册名称：",
        "License Key:": "许可证密钥：",
        "Thank you for purchasing a license for Charles. Please enter the details from your confirmation email.": "感谢购买 Charles 许可证。请输入确认邮件中的信息。",
    },
    "com/charlesproxy/gui/menus/ExportSSLCACertificateAction.class": {
        "You cannot export the Root Certificate and key with an empty password.": "导出根证书和私钥时必须设置密码。",
    },
    "com/charlesproxy/gui/menus/ExportSSLCACertificateAction$MySettingsPanel.class": {
        "Export Certificate and Key": "导出证书和私钥",
        "Export the Charles Root Certificate and Private Key for importing into other Charles installations, so you can share the root certificate.\n\nPlease enter a password to protect the exported certificate and key.": "导出 Charles 根证书和私钥，以便导入其他 Charles 安装实例并共享根证书。\n\n请输入密码以保护导出的证书和私钥。",
    },
    "com/charlesproxy/tools/breakpoints/oaSX.class": {
        "Abort": "中止",
        "Execute": "执行",
    },
    "com/charlesproxy/tools/breakpoints/BreakpointsFrame.class": {
        "Breakpoints": "断点",
    },
    "com/charlesproxy/tools/BlacklistTool$MySettingsPanel.class": {
        "Blocking action:": "拦截操作：",
        "Drop connection": "丢弃连接",
        "Return 403 response": "返回 403 响应",
    },
    "com/charlesproxy/tools/WhitelistTool$MySettingsPanel.class": {
        "Blocking action:": "拦截操作：",
        "Drop connection": "丢弃连接",
        "Return 403 response": "返回 403 响应",
    },
    "com/charlesproxy/tools/AutoSaveTool$MySettingsPanel.class": {
        "Start on a multiple of the Save interval": "按保存间隔的整数倍启动",
        "Enable on startup": "启动时启用",
        "Choose…": "选择…",
        "Save interval:": "保存间隔：",
        "minutes": "分钟",
        "Save to:": "保存到：",
        "Save type:": "保存类型：",
        "Save Interval": "保存间隔",
        "Save To": "保存到",
        "The period must be greater than 0.": "间隔必须大于 0。",
        "You must enter a save to path.": "请输入保存路径。",
        "Save to path does not exist or is not a directory.": "保存路径不存在或不是目录。",
    },
    "com/charlesproxy/tools/AutoSaveTool.class": {
        "Auto Save": "自动保存",
        "Auto-save directory doesn't exist. Disabling auto-save.": "自动保存目录不存在，已禁用自动保存。",
        "Charles Session": "Charles 会话",
        "Comma Separated File": "逗号分隔文件",
        "Failed to auto-save session: \x01": "自动保存会话失败：\x01",
    },
    "com/charlesproxy/UOLV.class": {
        "Charles Session": "Charles 会话",
        "Comma Separated File": "逗号分隔文件",
        "JSON Session File": "JSON 会话文件",
        "XML Session File": "XML 会话文件",
        "HTTP Archive": "HTTP 归档",
    },
    "com/charlesproxy/gui/session/actions/AbstractExportAction.class": {
        "Charles Session": "Charles 会话",
        "Comma Separated File": "逗号分隔文件",
        "HTTP Trace File": "HTTP 跟踪文件",
        "XML Summary File": "XML 摘要文件",
        "XML Session File": "XML 会话文件",
        "JSON Summary File": "JSON 摘要文件",
        "JSON Session File": "JSON 会话文件",
        "HTTP Archive": "HTTP 归档",
    },
    "com/charlesproxy/tools/MirrorTool$MySettingsPanel.class": {
        "Save to:": "保存到：",
        "Choose…": "选择…",
        "Please choose a directory to save to before enabling the Mirror tool.": "启用镜像工具前，请先选择保存目录。",
        "The chosen save directory does not exist.": "所选保存目录不存在。",
        "The chosen save directory exists but is not a directory.": "所选保存路径不是目录。",
    },
    "com/charlesproxy/tools/MapTool$MapFormPanel.class": {
        "Edit Mapping": "编辑映射",
        "Map From": "映射来源",
        "Map To": "映射目标",
        "Preserve host in header fields": "保留请求头中的 Host 字段",
        "Preserve base path": "保留基础路径",
    },
    "com/charlesproxy/tools/MapTool$MySettingsPanel$MapMappingTableModel.class": {
        "From": "来源",
        "To": "目标",
    },
    "com/charlesproxy/tools/MapLocalTool$MapLocalFormPanel.class": {
        "Edit Mapping": "编辑映射",
        "Map From": "映射来源",
        "Map To": "映射目标",
        "Local path": "本地路径",
        "Choose": "选择…",
        "Case sensitive": "区分大小写",
        "Local Path": "本地路径",
        "You must choose a valid local path to map to.": "请选择有效的本地映射路径。",
    },
    "com/charlesproxy/tools/MapLocalTool$MySettingsPanel$MapLocalMappingTableModel.class": {
        "Location": "位置",
        "Local Path": "本地路径",
    },
    "com/charlesproxy/tools/DNSSpoofingTool$MySettingsPanel$DNSSpoofFormPanel.class": {
        "Edit DNS Spoof": "编辑 DNS 欺骗",
        "Host name:": "主机名：",
        "Address:": "地址：",
        "The target address can be a host name or an IP address.": "目标地址可以是主机名或 IP 地址。",
        "Host Name": "主机名",
        "A host name is required": "必须输入主机名。",
        "Address": "地址",
        "An address is required": "必须输入地址。",
        "The address \"\x01\" is not valid. It should be a valid and resolvable DNS name or an IP address.": "地址“\x01”无效。请输入可解析的有效 DNS 名称或 IP 地址。",
        "The host name \"\x01\" is not valid. It should be a valid DNS name.": "主机名“\x01”无效。请输入有效的 DNS 名称。",
    },
    "com/charlesproxy/tools/rewrite/RewriteRulePanel.class": {
        "Rewrite Action": "改写操作",
        "Request": "请求",
        "Response": "响应",
        "Name:": "名称：",
        "Regex": "正则表达式",
        "Match whole value": "匹配整个值",
        "Case sensitive": "区分大小写",
        "Replace first": "替换第一个",
        "Replace all": "全部替换",
        "Type:": "类型：",
        "Value:": "值：",
        "Where": "位置",
        "Match": "匹配",
        "Replace": "替换",
        "Enter text to match or leave blank to match all.": "输入要匹配的文本；留空则匹配全部。",
        "Enter new values or leave blank for no change. If using regex matches you may enter references to groups, eg. $1": "输入替换值；留空则不作更改。使用正则表达式时，可引用捕获组，例如 $1。",
        "Please choose the rule type": "请选择规则类型。",
        "Invalid regular expression": "正则表达式无效。",
        "Please enter a replacement status code": "请输入要替换的状态码。",
    },
    "com/charlesproxy/tools/rewrite/RewriteSetPanel.class": {
        "Rewrite Set": "改写集",
        "Rewrite Rule": "改写规则",
        "Name:": "名称：",
    },
    "com/charlesproxy/tools/rewrite/RewriteSetPanel$RewriteRulesTableModel.class": {
        "Type": "类型",
        "Action": "操作",
    },
    "com/charlesproxy/tools/rewrite/vFhG.class": {
        "Debug in Error Log": "在错误日志中调试",
    },
    "com/charlesproxy/tools/rewrite/vFhG.class": {
        "Debug in Error Log": "在错误日志中调试",
    },
    "com/charlesproxy/tools/rewrite/RewriteTool.class": {
        "Rewrite Tool": "改写工具",
        "Failed to import rewrite sets from “\x01”: \x01": "从“\x01”导入改写集失败：\x01",
        "Failed to export rewrite sets to “\x01”: \x01": "导出改写集到“\x01”失败：\x01",
    },
    "com/charlesproxy/tools/rewrite/dpAz.class": {
        "Rewrite Headers: URL rewrite made bad URL: \x01": "改写请求头时 URL 改写产生了无效 URL：\x01",
    },
    "com/charlesproxy/tools/fwEL.class": {
        "Map Local: \x01: destination doesn't exist: \x01": "本地映射：\x01：目标路径不存在：\x01",
        "Map Local: \x01: requested file doesn't exist case-sensitive so not serving: \x01": "本地映射：\x01：请求的文件不存在（区分大小写），无法提供服务：\x01",
        "Map Local: \x01: requested file doesn't exist so not serving: \x01": "本地映射：\x01：请求的文件不存在，无法提供服务：\x01",
        "Map Local: destination doesn't exist: \x01": "本地映射：目标路径不存在：\x01",
        "Map Local: requested file doesn't exist case-sensitive so not serving: \x01": "本地映射：请求的文件不存在（区分大小写），无法提供服务：\x01",
        "Map Local: requested file doesn't exist so not serving: \x01": "本地映射：请求的文件不存在，无法提供服务：\x01",
        "Push promise disabled due to matching Map Local locations.": "匹配到本地映射规则，已禁用推送承诺。",
    },
    "com/charlesproxy/tools/CNaw.class": {
        "Failed to start reverse proxy rule: \x01": "启动反向代理规则失败：\x01",
    },
    "com/charlesproxy/tools/SIFg.class": {
        "Failed to start port forwarding rule: \x01": "启动端口转发规则失败：\x01",
    },
}

# Additional hard-coded strings found while walking the menus, settings pages,
# context menus, editors, and their confirmation/file dialogs. Keep these in a
# separate map so class-file replacements stay tied to their actual owner.
AUDIT_FIXES = {
    "com/charlesproxy/gui/settings/SettingsPanel.class": {
        "Please enter a number.": "请输入数字。",
        "Please enter a valid number.": "请输入有效数字。",
        "Please enter a valid whole number.": "请输入有效整数。",
    },
    "com/charlesproxy/gui/settings/KLfM.class": {
        "Choose the Mozilla Firefox profiles directory or a specific profile": "选择 Mozilla Firefox 配置文件目录或某个配置文件",
    },
    "com/charlesproxy/gui/settings/ProxySettingsPanel$ProxiesPanel.class": {
        "HTTP Proxy Port": "HTTP 代理端口",
        "SOCKS Proxy Port": "SOCKS 代理端口",
        "SOCKS Transparent HTTP proxying ports": "SOCKS 透明 HTTP 代理端口",
    },
    "com/charlesproxy/gui/settings/RecordingSettingsPanel$LimitsPanel.class": {
        "Recording Size Limit": "记录大小限制",
        "Max Requests": "最大请求数",
        "Max WebSocket Messages": "最大 WebSocket 消息数",
        "Value must be greater than 0.": "数值必须大于 0。",
        "Value must be greater than or equal to 0.": "数值必须大于或等于 0。",
    },
    "com/charlesproxy/gui/settings/GistIntegrationSettingsPanel.class": {
        "Publish Limit": "发布大小限制",
        "GitHub Location": "GitHub 地址",
        "Please enter a non-negative number.": "请输入非负数。",
        "Please enter a location for your installation e.g. https://api.github.com": "请输入 GitHub 服务地址，例如 https://api.github.com。",
    },
    "com/charlesproxy/gui/settings/ImportCertificateHelper.class": {
        "import an SSL certificate": "导入 SSL 证书",
    },
    "com/charlesproxy/gui/settings/Tbpq.class": {"Import Failed": "导入失败"},
    "com/charlesproxy/gui/settings/TSYl.class": {"Import Failed": "导入失败"},
    "com/charlesproxy/gui/settings/XIzE.class": {
        "Unable to parse certificate chain": "无法解析证书链",
    },
    "com/charlesproxy/gui/settings/oaSX.class": {"No Certificate": "未选择证书"},
    "com/charlesproxy/gui/helper/LocationsTableHelper$LocationFormPanel.class": {
        "The port contains invalid characters.": "端口包含无效字符。",
        "The hostname contains invalid characters.": "主机名包含无效字符。",
        "The protocol contains invalid characters.": "协议包含无效字符。",
    },
    "com/charlesproxy/gui/menus/SaveSSLCACertificateAction.class": {
        "Base 64 encoded certificate": "Base64 编码证书",
        "Binary certificate": "二进制证书",
    },
    "com/charlesproxy/gui/menus/ExportSSLCACertificateAction.class": {
        "Failed to extract the Charles Root Certificate details.": "无法提取 Charles 根证书信息。",
    },
    "com/charlesproxy/gui/menus/LlnI.class": {
        "Couldn't find certifiate file.": "找不到证书文件。",
    },
    "com/charlesproxy/gui/lib/ExtendedJOptionPane.class": {
        "Don't show this again": "不再显示此提示",
    },
    "com/charlesproxy/gui/session/popups/AbstractModelNodePopupMenu.class": {
        "Enable SSL Proxying": "启用 SSL 代理",
        "Disable SSL Proxying": "停用 SSL 代理",
    },
    "com/charlesproxy/gui/session/popups/npZC.class": {
        "Enable SSL Proxying": "启用 SSL 代理",
        "Disable SSL Proxying": "停用 SSL 代理",
        "SSL Proxying: Disabled": "SSL 代理：已停用",
        "SSL Proxying: Enabled": "SSL 代理：已启用",
    },
    "com/charlesproxy/gui/session/actions/ClearSessionAction.class": {
        "Are you sure that you want to CLEAR all of the transactions from \"\x01\"?": "确定要清空会话“\x01”中的所有事务吗？",
        "Clear": "清空",
        "Cancel": "取消",
        "Clear Session": "清空会话",
    },
    "com/charlesproxy/gui/session/actions/ClearOthersAction.class": {"Clear Others": "清空其他项目"},
    "com/charlesproxy/gui/session/actions/ClearOthersSequenceAction.class": {"Clear Others": "清空其他项目"},
    "com/charlesproxy/gui/transaction/actions/ViewAsTypeMenu.class": {
        "View Request As": "请求显示为",
        "View Response As": "响应显示为",
    },
    "com/charlesproxy/gui/transaction/viewers/TransactionViewerContentTypeManager.class": {
        "Viewer Mappings": "查看器映射",
    },
    "com/charlesproxy/gui/transaction/viewers/TransactionViewerContentTypeManager$SettingsPanel$ViewerContentTypeMappingTableModel.class": {
        "Location": "位置",
        "Request Type": "请求类型",
        "Response Type": "响应类型",
    },
    "com/charlesproxy/gui/transaction/viewers/TransactionViewerContentTypeManager$ViewerContentTypeMappingFormPanel.class": {
        "Edit Viewer Mapping": "编辑查看器映射",
        "Request type": "请求类型",
        "Response type": "响应类型",
    },
    "com/charlesproxy/gui/transaction/viewers/lib/TransactionSearchPanel.class": {
        "Match Case": "区分大小写",
        "Use Regex": "使用正则表达式",
        "Text to find": "要查找的文本",
        "Find Next": "查找下一个",
        "Find Prev": "查找上一个",
    },
    "com/charlesproxy/gui/transaction/editors/json/JSONEditorPopupMenu.class": {
        "Add Top-Level": "添加顶层节点",
        "New Array": "新建数组",
        "New Primitive": "新建基本值",
        "New Object": "新建对象",
    },
    "com/charlesproxy/gui/transaction/viewers/gen/LlnI.class": {
        "Session Cookies": "会话 Cookie",
        "Set Cookie": "设置 Cookie",
    },
    "com/charlesproxy/gui/transaction/general/ivpO.class": {
        "Request Start Time": "请求开始时间",
        "Request End Time": "请求结束时间",
        "Client Address": "客户端地址",
        "Request Speed": "请求速度",
        "Response Speed": "响应速度",
        "Remote Address": "远程地址",
        "Response Start Time": "响应开始时间",
        "Response End Time": "响应结束时间",
        "Response Code": "响应代码",
        "Content-Type": "内容类型",
        "Uncompressed Body": "解压后的正文",
    },
    "com/charlesproxy/gui/transaction/general/dpAz.class": {
        "Request Speed": "请求速度",
        "Response Speed": "响应速度",
    },
    "com/charlesproxy/gui/transaction/general/npZC.class": {
        "SSL Proxying not enabled for this host. Enable in the Proxy Menu, SSL Proxying Settings": "此主机尚未启用 SSL 代理。请在“代理”菜单的“SSL 代理设置”中启用。",
        "SSL Proxying enabled for this host": "已为此主机启用 SSL 代理",
    },
    "com/charlesproxy/gui/transaction/general/VVEV.class": {
        "Server Chosen": "选定的服务器",
        "Session Resumed": "会话已恢复",
        "Session ID": "会话 ID",
        "Charles to Server": "Charles 到服务器",
        "Server Certificates": "服务器证书",
        "Charles to Client": "Charles 到客户端",
        "Client Session ID": "客户端会话 ID",
        "Client Requested": "客户端请求的项目",
        "Client Supported": "客户端支持的项目",
        "Client Certificates": "客户端证书",
        "Server Session ID": "服务器会话 ID",
    },
    "com/charlesproxy/gui/find/AdvancedFindDialog.class": {
        "Find in \x01": "查找：\x01",
        "Using glob syntax: * matches any string, ? matches any character, escape using \\": "通配符语法：* 匹配任意字符串，? 匹配任意字符；使用反斜杠进行转义。",
        "Case sensitive": "区分大小写",
        "Whole words": "全字匹配",
        "Regular expression": "正则表达式",
        "Session": "会话",
        "Selected": "所选内容",
        "Path": "路径",
        "Request Header": "请求头",
        "Request Body": "请求正文",
        "Response Header": "响应头",
        "Response Body": "响应正文",
        "Request URL": "请求 URL",
        "Scope": "范围",
        "Include": "搜索范围",
        "Find": "查找",
        "Cancel": "取消",
    },
    "com/charlesproxy/gui/find/ssJy.class": {
        "Request Header": "请求头",
        "Request Body": "请求正文",
        "Response Header": "响应头",
        "Response Body": "响应正文",
        "Request URL": "请求 URL",
    },
    "com/charlesproxy/gui/find/RbRC.class": {
        " in \x01": " 位于 \x01",
        " in current selection": "（当前选区）",
        "req header": "请求头",
        "req body": "请求正文",
        "requests": "请求",
        "resp header": "响应头",
        "headers": "请求头和响应头",
        "req body, resp header": "请求正文和响应头",
        "requests, resp header": "请求及响应头",
        "resp body": "响应正文",
        "req header, resp body": "请求头和响应正文",
        "bodies": "请求和响应正文",
        "requests, resp body": "请求及响应正文",
        "responses": "响应",
        "req header, responses": "请求头和响应",
        "req body, responses": "请求正文和响应",
        "requests, responses": "请求和响应",
        "urls": "URL",
        "urls, req header": "URL 和请求头",
        "urls, req body": "URL 和请求正文",
        "urls, requests": "URL 和请求",
        "urls, resp header": "URL 和响应头",
        "urls, headers": "URL、请求头和响应头",
        "urls, req body, resp header": "URL、请求正文和响应头",
        "urls, requests, resp header": "URL、请求及响应头",
        "urls, resp body": "URL 和响应正文",
        "urls, req header, resp body": "URL、请求头和响应正文",
        "urls, bodies": "URL、请求和响应正文",
        "urls, requests, resp body": "URL、请求及响应正文",
        "urls, responses": "URL 和响应",
        "urls, req header, responses": "URL、请求头和响应",
        "urls, req body, responses": "URL、请求正文和响应",
        "\x01 results": "\x01 条结果",
        "more than \x01 results": "超过 \x01 条结果",
    },
    "com/charlesproxy/gui/transaction/actions/AdvancedRepeatAction$MySettingsPanel.class": {
        "Show results in a new Session": "在新会话中显示结果",
    },
    "com/charlesproxy/gui/frames/ActiveConnectionsFrame$ActiveTableModel.class": {
        "Client Process": "客户端进程",
        "Connected From": "连接来源",
    },
    "com/charlesproxy/gui/RbRC.class": {
        "Charles is running low on memory. Recording has been stopped. Please clear the session to free memory and continue recording.": "Charles 内存不足，已停止记录。请清空会话以释放内存，然后继续记录。",
    },
    "com/charlesproxy/gui/ZcYD.class": {"Show Charles": "显示 Charles", "Hide Charles": "隐藏 Charles"},
    "com/charlesproxy/gui/snjf.class": {"Show Charles": "显示 Charles", "Hide Charles": "隐藏 Charles"},
    "com/charlesproxy/gui/QUqz.class": {"Show Charles": "显示 Charles", "Hide Charles": "隐藏 Charles"},
    "com/charlesproxy/gui/UQHx.class": {
        "Show Charles": "显示 Charles",
        "Hide Charles": "隐藏 Charles",
        "Windows Proxy": "Windows 代理",
        "External Proxy Servers": "外部代理服务器",
        "macOS Proxy": "macOS 代理",
        "Mozilla Firefox Proxy": "Mozilla Firefox 代理",
        "Charles Web Debugging Proxy": "Charles Web 调试代理",
    },
    "com/charlesproxy/gui/lib/table/MemoryJTable$4$2.class": {
        "New Custom Header Column": "新建自定义请求头列",
    },
    "com/charlesproxy/gui/security/DefaultInteractivePasswordAuthenticator$PasswordPromptPanel.class": {
        "Entered passwords do not match. Please try again.": "两次输入的密码不一致，请重试。",
        "Incorrect password. Please try again.": "密码错误，请重试。",
    },
    "com/charlesproxy/gui/transaction/editors/CookieEditor$EditableCookieTableModel.class": {
        "Illegal Cookie Value": "Cookie 值无效",
    },
    "com/charlesproxy/gui/transaction/editors/OZTL.class": {
        "Illegal Cookie Value '%s' - %s": "Cookie 值“%s”无效：%s",
    },
    "com/charlesproxy/gui/transaction/viewers/json/OZTL.class": {
        "Primitive Value": "基本值",
    },
    "com/charlesproxy/gui/transaction/viewers/xml/edfX.class": {"XML Text": "XML 文本"},
    "com/charlesproxy/gui/transaction/viewers/xml/OZTL.class": {"Document Type": "文档类型"},
    "com/charlesproxy/gui/transaction/viewers/multipart/edfX.class": {"File name": "文件名"},
    "com/charlesproxy/gui/transaction/actions/CopyToClipboardAction$CurlCommand.class": {
        "Copy cURL Request": "复制 cURL 请求",
        "Cannot represent unsupported content encoding": "无法表示不支持的内容编码",
    },
    "com/charlesproxy/gui/transaction/actions/CopyToClipboardAction.class": {
        "Copy To Clipboard Error": "复制到剪贴板失败",
    },
    "com/charlesproxy/gui/transaction/actions/SaveTransactionsAction.class": {
        "Save All…": "全部保存…",
        "Select a directory to save into": "选择保存目录",
        "Select": "选择",
        "Invalid directory selected. Please select a directory to save into.": "所选目录无效，请选择一个保存目录。",
        "Save All": "全部保存",
        "Duplicate Responses": "重复响应",
        "Save Last": "保存最后一个",
        "Save First": "保存第一个",
    },
    "com/charlesproxy/gui/transaction/actions/SaveWebSocketMessagesAction.class": {
        "Save WebSocket Messages…": "保存 WebSocket 消息…",
        "Select a directory to save into": "选择保存目录",
        "Select": "选择",
        "Invalid directory selected. Please select a directory to save into.": "所选目录无效，请选择一个保存目录。",
        "Save All": "全部保存",
        "Replace Existing File": "替换现有文件",
        "Replace Existing Files": "替换现有文件",
        "Replace": "替换",
        "Replace All": "全部替换",
        "Cancel": "取消",
        "No messages were found to save.": "没有找到可保存的消息。",
        "Saving files…": "正在保存文件…",
    },
    "com/charlesproxy/gui/transaction/actions/SaveBodyAction.class": {
        "Replace Existing File": "替换现有文件",
        "Replace": "替换",
        "Cancel": "取消",
        "Save Error": "保存失败",
    },
    "com/charlesproxy/gui/utils/dpAz.class": {
        "Please choose a file type and try again.": "请选择文件类型后重试。",
        "Replace Existing File": "替换现有文件",
        "Replace": "替换",
        "Cancel": "取消",
        "Save Failed": "保存失败",
    },
    "com/charlesproxy/gui/frames/LogFrame.class": {
        "Failed to close log file": "关闭日志文件失败",
        "Replace Existing File": "替换现有文件",
        "Replace": "替换",
        "Cancel": "取消",
        "Log to File": "记录到文件",
    },
    "com/charlesproxy/gui/CharlesGUIFileManager$2.class": {
        "Import Failed": "导入失败",
        "All Available": "所有可用文件",
    },
    "com/charlesproxy/gui/CharlesGUIFileManager$1.class": {
        "All Available": "所有可用文件",
        "Open Failed": "打开失败",
        "Charles could not open this file due to the following error: \x01": "Charles 无法打开此文件，错误信息：\x01",
    },
    "com/charlesproxy/gui/session/actions/AbstractExportAction.class": {
        "Legacy Charles Session File": "旧版 Charles 会话文件",
    },
    "com/charlesproxy/gui/settings/LFHo.class": {"No help is available.": "没有可用的帮助信息。"},
    "com/charlesproxy/gui/transaction/chart/WtvV.class": {
        "Export Error": "导出失败",
        "Failed to save the exported image": "无法保存导出的图像",
    },
    "com/charlesproxy/gui/transaction/editors/KLfM.class": {"XML Text": "XML 文本"},
    "com/charlesproxy/gui/transaction/editors/json/JSONTransferHandler.class": {
        "Error importing JSON data": "导入 JSON 数据失败",
        "Error exporting JSON data": "导出 JSON 数据失败",
    },
    "com/charlesproxy/gui/transaction/editors/json/edfX.class": {
        "A parent node must be an ObjectNode": "父节点必须是 ObjectNode 类型。",
        "Key values must not be empty": "键名不能为空。",
        "A parent node must be either an ObjectNode or ArrayNode": "父节点必须是 ObjectNode 或 ArrayNode 类型。",
    },
    "com/charlesproxy/gui/transaction/editors/multipart/edfX.class": {
        "Selected file is not a file.": "所选路径不是文件。",
        "Unexpected error reading content from selected file": "读取所选文件内容时发生意外错误",
        "Selected file exceeds the maximum file size of 128 MB": "所选文件超过 128 MB 的大小上限",
        "Error reading file": "读取文件失败",
    },
    "com/charlesproxy/gui/transaction/editors/UOUV.class": {
        "Missing host": "缺少主机名",
        "Missing path": "缺少路径",
        "Unexpected URI syntax exception in transaction": "事务中的 URI 语法异常",
    },
    "com/charlesproxy/gui/transaction/editors/protobuf/npZC.class": {
        "Root node must be a ContentNode": "根节点必须是 ContentNode。",
    },
    "com/charlesproxy/gui/transaction/viewers/websocket/ivpO.class": {
        "Old messages have been dropped from this record because of the configured WebSocket message limit.": "由于已达到 WebSocket 消息数上限，此记录中的旧消息已被丢弃。",
    },
    "com/charlesproxy/gui/transaction/viewers/amf/npZC.class": {
        "Header Part": "头部部分",
        "Body Part": "正文部分",
        "Must Understand": "必须理解",
    },
    "com/charlesproxy/gui/transaction/viewers/amf/edfX.class": {
        "The data is not valid AMF. Please check the Text view to see if it contains unexpected data.": "AMF 数据无效。请检查“文本”视图中是否包含异常数据。",
    },
    "com/charlesproxy/gui/transaction/viewers/amf/oaSX.class": {
        "Failed to find reference source for this node": "找不到此节点的引用来源",
    },
    "com/charlesproxy/gui/transaction/viewers/VVEV.class": {
        "Open Descriptor Registry": "打开描述符注册表",
    },
    "com/charlesproxy/gui/transaction/viewers/gen/ivpO.class": {
        "Cannot make estimates. Actual length unknown.": "无法估算，实际长度未知。",
    },
    "com/charlesproxy/gui/transaction/viewers/gen/SWcV.class": {
        "Error initialising WebP image reader": "初始化 WebP 图像读取器失败",
    },
    "com/charlesproxy/gui/transaction/viewers/gen/oaSX.class": {
        "Parse Failed": "解析失败",
    },
    "com/charlesproxy/gui/transaction/viewers/xml/UOLV.class": {
        "Response is not a SOAP Envelope": "响应不是 SOAP Envelope。",
        "Could not find SOAP Body element": "找不到 SOAP Body 元素。",
        "Request is not a SOAP Envelope": "请求不是 SOAP Envelope。",
    },
    "com/charlesproxy/gui/transaction/viewers/json/ivpO.class": {"JSON Header": "JSON 头部"},
    "com/charlesproxy/gui/transaction/viewers/json/UOUV.class": {"JSON Text": "JSON 文本"},
    "com/charlesproxy/gui/transaction/viewers/multipart/oaSX.class": {
        "Failed to decode Multipart body": "无法解码 Multipart 正文",
    },
    "com/charlesproxy/gui/transaction/viewers/protobuf/edfX.class": {"Protobuf Text": "Protobuf 文本"},
    "com/charlesproxy/gui/transaction/viewers/lib/edfX.class": {
        "Find Previous": "查找上一个",
        "Find Next": "查找下一个",
    },
    "com/charlesproxy/gui/transaction/viewers/lib/qClj.class": {
        "Failed to instrospect property": "检查属性失败",
    },
    "com/charlesproxy/gui/transaction/actions/dpAz.class": {
        "No responses were found to save.": "没有找到可保存的响应。",
        "Save All": "全部保存",
    },
    "com/charlesproxy/gui/transaction/actions/npZC.class": {"Save All": "全部保存"},
    "com/charlesproxy/gui/transaction/actions/VVEV.class": {"Save All": "全部保存"},
    "com/charlesproxy/gui/transaction/actions/WtvV.class": {
        "Replace Existing File": "替换现有文件",
        "Replace All": "全部替换",
        "Replace": "替换",
        "Cancel": "取消",
    },
    "com/charlesproxy/gui/transaction/actions/CopyURLAction.class": {"Copy URL": "复制 URL"},
    "com/charlesproxy/gui/transaction/actions/CopyURLsAction.class": {"Copy URLs": "复制 URL"},
    "com/charlesproxy/gui/transaction/actions/CopyToClipboardAction$TextComponent.class": {
        "Copy Selection": "复制选中内容",
    },
    "com/charlesproxy/gui/transaction/actions/CopyToClipboardAction$Text.class": {
        "Copy Selection": "复制选中内容",
    },
    "com/charlesproxy/gui/transaction/actions/CopyToClipboardAction$Request.class": {"Copy Request": "复制请求"},
    "com/charlesproxy/gui/transaction/actions/CopyToClipboardAction$Response.class": {"Copy Response": "复制响应"},
    "com/charlesproxy/gui/find/ivpO.class": {"No results found.": "没有找到结果。"},
    "com/charlesproxy/gui/transaction/editors/amf/UOUV.class": {
        "Failed to convert to the correct type": "无法转换为正确的类型",
    },
    "com/charlesproxy/gui/transaction/editors/amf/edfX.class": {
        "The data is not valid AMF. Please check the Text view to see if it contains unexpected data.": "AMF 数据无效。请检查“文本”视图中是否包含异常数据。",
    },
    "com/charlesproxy/gui/transaction/viewers/protobuf/npZC.class": {
        "Could not find descriptor in configuration to remove": "在配置中找不到要移除的描述符",
    },
    "com/charlesproxy/gui/transaction/viewers/protobuf/baKA.class": {
        "Doesn't appear to be a map field": "这似乎不是 map 字段",
    },
    "com/charlesproxy/gui/transaction/viewers/protobuf/AbstractProtocolBuffersViewer$ConfigLocation.class": {
        "viewer mapping": "查看器映射",
        "configured 'View As' type": "已配置的“显示为”类型",
        "Content-Type header": "Content-Type 请求头",
    },
    "com/charlesproxy/gui/transaction/actions/Base64DecodeAction.class": {
        "Failed to decode Base 64. Probably not valid Base 64 input.": "Base64 解码失败，输入内容可能不是有效的 Base64。",
    },
    "com/charlesproxy/gui/settings/ImportExportDialog$2.class": {"Charles Settings": "Charles 设置"},
    "com/charlesproxy/gui/frames/XIzE.class": {
        "Charles License": "Charles 许可证",
        "Thank you for purchasing a license for Charles. Charles will now close. Please start Charles again to continue.": "感谢购买 Charles 许可证。Charles 即将关闭，请重新启动 Charles 以继续使用。",
    },
    "com/charlesproxy/gui/utils/UIUtils.class": {"Failed to set look and feel": "设置外观样式失败"},
    "com/charlesproxy/tools/KLfM.class": {
        "Select a file or directory for the root of the mapping": "选择映射的根文件或目录",
    },
    "com/charlesproxy/tools/SIFg.class": {
        "Port Forwarding": "端口转发",
        "End port is less than start port": "结束端口小于起始端口",
        "Too many ports in start port to end port range": "起始端口到结束端口的范围过大",
    },
    "com/charlesproxy/tools/rewrite/RewriteTool.class": {
        "Rewrite Set XML Files": "改写集 XML 文件",
    },
    "com/charlesproxy/tools/rewrite/RewriteTool$MySettingsPanel.class": {
        "Rewrite Sets.xml": "改写集.xml",
        "Save editor should not have thrown an exception": "保存编辑器时发生异常",
    },
    "com/charlesproxy/tools/rewrite/RewriteRulePanel.class": {
        "New Value": "新值",
        "Match Value": "匹配值",
        "Match Header": "匹配请求头",
    },
    "com/charlesproxy/tools/rewrite/ewjy.class": {
        "Add Header": "添加请求头",
        "Modify Header": "修改请求头",
        "Remove Header": "移除请求头",
        "Host": "主机",
        "Path": "路径",
        "URL": "URL",
        "Add Query Param": "添加查询参数",
        "Modify Query Param": "修改查询参数",
        "Remove Query Param": "移除查询参数",
        "Response Status": "响应状态",
        "Body": "正文",
        "Append": "追加",
        "Remove": "移除",
        "Modify": "修改",
        "Append Query": "追加查询参数",
        "Modify Query": "修改查询参数",
        "Remove Query": "移除查询参数",
        "Status": "状态",
    },
    "com/charlesproxy/tools/rewrite/LlnI.class": {
        "Add Header": "添加请求头",
        "Remove Header": "移除请求头",
        "Host": "主机",
        "Path": "路径",
        "URL": "URL",
        "Add Query Param": "添加查询参数",
        "Remove Query Param": "移除查询参数",
        "Response Status": "响应状态",
        "Body": "正文",
        "New": "新值",
        "Replace": "替换",
    },
    "com/charlesproxy/tools/AutoSaveTool.class": {
        "JSON Summary File": "JSON 摘要文件",
        "XML Session File": "XML 会话文件",
        "HTTP Trace File": "HTTP 跟踪文件",
        "JSON Session File": "JSON 会话文件",
        "XML Summary File": "XML 摘要文件",
        "Auto-saved session.": "会话已自动保存。",
    },
    "com/charlesproxy/gui/transaction/general/ivpO.class": {
        " [Failed: \x01]": " [失败：\x01]",
    },
    "com/charlesproxy/gui/transaction/editors/amf/UOUV.class": {
        "An error occurred updating the value: \x01": "更新值时发生错误：\x01",
        "The value is not in the correct format: \x01": "值的格式不正确：\x01",
    },
    "com/charlesproxy/gui/transaction/editors/amf/edfX.class": {
        "Failed to serialize AMF tree: \x01": "序列化 AMF 树失败：\x01",
    },
    "com/charlesproxy/gui/transaction/editors/VVEV.class": {
        "Failed to parse headers: \x01": "解析请求头失败：\x01",
    },
    "com/charlesproxy/gui/transaction/editors/json/JSONTransferHandler.class": {
        "Error inserting content: \x01": "插入内容失败：\x01",
    },
    "com/charlesproxy/gui/transaction/editors/json/edfX.class": {
        "An error occurred updating the value: \x01": "更新值时发生错误：\x01",
        "An error occurred changing the name: \x01": "修改名称时发生错误：\x01",
    },
    "com/charlesproxy/gui/transaction/editors/multipart/oaSX.class": {
        "Failed to decode Multipart body: \x01": "解码 Multipart 正文失败：\x01",
    },
    "com/charlesproxy/gui/transaction/editors/protobuf/npZC.class": {
        "Failed to serialize protocol buffers message: \x01": "序列化 Protocol Buffers 消息失败：\x01",
    },
    "com/charlesproxy/gui/transaction/editors/protobuf/oaSX.class": {
        "Failed to parse and serialise Protobuf message: \x01": "解析并序列化 Protobuf 消息失败：\x01",
    },
    "com/charlesproxy/gui/transaction/editors/protobuf/edfX.class": {
        "An error occurred updating the key value: \x01": "更新键值时发生错误：\x01",
        "An error occurred updating the value: \x01": "更新值时发生错误：\x01",
    },
    "com/charlesproxy/gui/transaction/viewers/amf/edfX.class": {
        "Failed to parse AMF: \x01": "解析 AMF 失败：\x01",
    },
    "com/charlesproxy/gui/transaction/viewers/gen/OZTL.class": {
        "SWFBodyViewer failed to parse SWF: \x01: \x01": "SWF 正文查看器解析 SWF 失败：\x01：\x01",
        "\x01 records": "\x01 条记录",
    },
    "com/charlesproxy/gui/transaction/viewers/gen/SWcV.class": {
        "Error initialising WebP image reader: \x01": "初始化 WebP 图像读取器失败：\x01",
    },
    "com/charlesproxy/gui/transaction/viewers/xml/npZC.class": {
        "Failed to Parse XML Document\nReason: \x01\nLine: \x01 Column: \x01": "解析 XML 文档失败\n原因：\x01\n行：\x01 列：\x01",
    },
    "com/charlesproxy/gui/transaction/viewers/json/WtvV.class": {
        "Failed to parse JSON: \x01": "解析 JSON 失败：\x01",
    },
    "com/charlesproxy/gui/transaction/viewers/lib/edfX.class": {
        "Failed to parse data (\x01)": "解析数据失败（\x01）",
        "Data is incomplete (\x01 of \x01). Please check the recording limits in the Recording Settings.": "数据不完整（\x01 / \x01）。请检查“代理”>“记录设置”中的记录限制。",
        "Please wait… Downloaded \x01 of \x01.": "请稍候…已下载 \x01 / \x01。",
    },
    "com/charlesproxy/gui/transaction/viewers/protobuf/AbstractProtocolBuffersViewer.class": {
        "Viewer settings have been customised for this \x01.": "此 \x01 的查看器设置已自定义。",
        "We cannot parse JSON encoded messages to protobuf (even partially) without the correct message type: \x01": "缺少正确的消息类型，无法将 JSON 编码的消息解析为 Protobuf（即使是部分解析）：\x01",
    },
    "com/charlesproxy/gui/transaction/actions/AdvancedRepeatAction$MySettingsPanel.class": {
        "Invalid input: \x01": "输入无效：\x01",
        "Negative value: \x01": "数值不能为负：\x01",
    },
    "com/charlesproxy/gui/transaction/actions/SaveBodyAction.class": {
        "A file named \"\x01\" already exists.": "名为“\x01”的文件已存在。",
    },
    "com/charlesproxy/gui/transaction/actions/WtvV.class": {
        "A file named \"\x01\" already exists.": "名为“\x01”的文件已存在。",
    },
    "com/charlesproxy/gui/transaction/actions/SaveWebSocketMessagesAction.class": {
        "A file named \"\x01\" already exists.": "名为“\x01”的文件已存在。",
    },
    "com/charlesproxy/gui/transaction/actions/SaveTransactionsAction.class": {
        "Multiple responses for the same file exist.\"\x01\" already exists.": "多个响应对应同一文件。“\x01”已存在。",
    },
    "com/charlesproxy/gui/settings/SettingsPanel.class": {
        "Please enter a number larger than or equal to \x01": "请输入大于或等于 \x01 的数值",
        "Please enter a number smaller than or equal to \x01": "请输入小于或等于 \x01 的数值",
    },
    "com/charlesproxy/gui/settings/ProxySettingsPanel$ProxiesPanel.class": {
        "Please check the list of ports, one of them is invalid:\n\x01": "请检查端口列表，其中一个端口无效：\n\x01",
    },
    "com/charlesproxy/gui/frames/LogFrame.class": {
        "A file named \"\x01\" already exists.": "名为“\x01”的文件已存在。",
        "Could not open log file: \x01": "无法打开日志文件：\x01",
        "Could not write log file: \x01": "无法写入日志文件：\x01",
    },
    "com/charlesproxy/gui/utils/dpAz.class": {
        "A file named \"\x01\" already exists.": "名为“\x01”的文件已存在。",
    },
    "com/charlesproxy/gui/frames/xWwR.class": {"\x01 proxy to \x01:\x01": "\x01 代理至 \x01：\x01"},
    "com/charlesproxy/gui/CharlesFrame.class": {
        "Failed to find required image: \x01": "找不到所需图像：\x01",
    },
    "com/charlesproxy/gui/lib/table/MemoryJTable.class": {
        "Unexpected error moving \x01 columns to postions: \x01": "移动 \x01 列时发生意外错误：\x01",
    },
    "com/charlesproxy/gui/menus/HelpMenu$10.class": {"Script not found or not executable: \x01": "找不到脚本或脚本不可执行：\x01"},
    "com/charlesproxy/gui/session/SessionFrame.class": {"Session \x01": "会话 \x01"},
    "com/charlesproxy/gui/session/AbstractSessionFrame.class": {
        "Cannot determine session file type from file name: \x01": "无法根据文件名确定会话文件类型：\x01",
    },
    "com/charlesproxy/gui/session/actions/edfX.class": {"Unknown export type: \x01": "未知的导出类型：\x01"},
    "com/charlesproxy/tools/UOLV.class": {"Blocked \x01 - returned error response": "已拦截 \x01 - 已返回错误响应"},
    "com/charlesproxy/tools/fwEL.class": {"Mapped to local file: \x01": "已映射到本地文件：\x01"},
    "com/charlesproxy/tools/QUqz.class": {
        "Not allowed \x01 - connection dropped": "未允许 \x01 - 连接已丢弃",
        "Not allowed \x01 - returned error response": "未允许 \x01 - 已返回错误响应",
    },
    "com/charlesproxy/tools/yDHk.class": {"Invalid new port in: \x01": "以下规则中的新端口无效：\x01"},
    "com/charlesproxy/tools/SuMZ.class": {"Mirror failed for \"\x01\": \x01": "镜像“\x01”失败：\x01"},
    "com/charlesproxy/tools/EQdO.class": {"Partial response Content-Range header malformed: \x01": "部分响应中的 Content-Range 请求头格式错误：\x01"},
    "com/charlesproxy/validator/gui/ValidatorSessionFrame.class": {
        "\x01 (\x01 invalid)": "\x01（\x01 项无效）",
        "\x01 (\x01 invalid, \x01% complete)": "\x01（\x01 项无效，已完成 \x01%）",
    },
    "com/charlesproxy/gui/find/Dosw.class": {"\x01 (1 match)": "\x01（1 项匹配）"},
    "com/charlesproxy/gui/transaction/chart/ChartJTable.class": {
        "\x01 more transactions.  Generated by Charles Proxy": "另有 \x01 个事务。由 Charles Proxy 生成",
    },
}

# Maps whose original entries share a Java class with later audit findings.
# They are applied after AUDIT_FIXES so all literals on the same class survive.
AUDIT_FIXES_EXTRA = {
    "com/charlesproxy/gui/transaction/general/ivpO.class": {
        "Request Start Time": "请求开始时间",
        "Request End Time": "请求结束时间",
        "Client Address": "客户端地址",
        "Request Speed": "请求速度",
        "Response Speed": "响应速度",
        "Remote Address": "远程地址",
        "Response Start Time": "响应开始时间",
        "Response End Time": "响应结束时间",
        "Response Code": "响应代码",
        "Content-Type": "内容类型",
        "Uncompressed Body": "解压后的正文",
    },
    "com/charlesproxy/gui/transaction/editors/amf/UOUV.class": {
        "Failed to convert to the correct type": "无法转换为正确的类型",
    },
    "com/charlesproxy/gui/transaction/editors/amf/edfX.class": {
        "The data is not valid AMF. Please check the Text view to see if it contains unexpected data.": "AMF 数据无效。请检查“文本”视图中是否包含异常数据。",
    },
    "com/charlesproxy/gui/transaction/editors/json/JSONTransferHandler.class": {
        "Error importing JSON data": "导入 JSON 数据失败",
        "Error exporting JSON data": "导出 JSON 数据失败",
    },
    "com/charlesproxy/gui/transaction/editors/json/edfX.class": {
        "A parent node must be an ObjectNode": "父节点必须是 ObjectNode 类型。",
        "Key values must not be empty": "键名不能为空。",
        "A parent node must be either an ObjectNode or ArrayNode": "父节点必须是 ObjectNode 或 ArrayNode 类型。",
    },
    "com/charlesproxy/gui/transaction/editors/protobuf/npZC.class": {
        "Root node must be a ContentNode": "根节点必须是 ContentNode。",
    },
    "com/charlesproxy/gui/transaction/viewers/amf/edfX.class": {
        "The data is not valid AMF. Please check the Text view to see if it contains unexpected data.": "AMF 数据无效。请检查“文本”视图中是否包含异常数据。",
    },
    "com/charlesproxy/gui/transaction/viewers/gen/SWcV.class": {
        "Error initialising WebP image reader": "初始化 WebP 图像读取器失败",
    },
    "com/charlesproxy/gui/transaction/viewers/lib/edfX.class": {
        "Find Previous": "查找上一个",
        "Find Next": "查找下一个",
    },
    "com/charlesproxy/gui/transaction/actions/AdvancedRepeatAction$MySettingsPanel.class": {
        "Show results in a new Session": "在新会话中显示结果",
    },
    "com/charlesproxy/gui/transaction/actions/SaveBodyAction.class": {
        "Replace Existing File": "替换现有文件",
        "Replace": "替换",
        "Cancel": "取消",
        "Save Error": "保存失败",
    },
    "com/charlesproxy/gui/transaction/actions/WtvV.class": {
        "Replace Existing File": "替换现有文件",
        "Replace All": "全部替换",
        "Replace": "替换",
        "Cancel": "取消",
    },
    "com/charlesproxy/gui/transaction/actions/SaveWebSocketMessagesAction.class": {
        "Save WebSocket Messages…": "保存 WebSocket 消息…",
        "Select a directory to save into": "选择保存目录",
        "Select": "选择",
        "Invalid directory selected. Please select a directory to save into.": "所选目录无效，请选择一个保存目录。",
        "Save All": "全部保存",
        "Replace Existing File": "替换现有文件",
        "Replace Existing Files": "替换现有文件",
        "Replace": "替换",
        "Replace All": "全部替换",
        "Cancel": "取消",
        "No messages were found to save.": "没有找到可保存的消息。",
        "Saving files…": "正在保存文件…",
    },
    "com/charlesproxy/gui/transaction/actions/SaveTransactionsAction.class": {
        "Save All…": "全部保存…",
        "Select a directory to save into": "选择保存目录",
        "Select": "选择",
        "Invalid directory selected. Please select a directory to save into.": "所选目录无效，请选择一个保存目录。",
        "Save All": "全部保存",
        "Duplicate Responses": "重复响应",
        "Save Last": "保存最后一个",
        "Save First": "保存第一个",
    },
    "com/charlesproxy/gui/settings/SettingsPanel.class": {
        "Please enter a number.": "请输入数字。",
        "Please enter a valid number.": "请输入有效数字。",
        "Please enter a valid whole number.": "请输入有效整数。",
    },
    "com/charlesproxy/gui/settings/ProxySettingsPanel$ProxiesPanel.class": {
        "HTTP Proxy Port": "HTTP 代理端口",
        "SOCKS Proxy Port": "SOCKS 代理端口",
        "SOCKS Transparent HTTP proxying ports": "SOCKS 透明 HTTP 代理端口",
    },
    "com/charlesproxy/gui/frames/LogFrame.class": {
        "Failed to close log file": "关闭日志文件失败",
        "Replace Existing File": "替换现有文件",
        "Replace": "替换",
        "Cancel": "取消",
        "Log to File": "记录到文件",
    },
    "com/charlesproxy/gui/utils/dpAz.class": {
        "Please choose a file type and try again.": "请选择文件类型后重试。",
        "Replace Existing File": "替换现有文件",
        "Replace": "替换",
        "Cancel": "取消",
        "Save Failed": "保存失败",
    },
}


def patch_constant_pool(data: bytes, replacements: dict[str, str]) -> tuple[bytes, set[str]]:
    if data[:4] != b"\xca\xfe\xba\xbe":
        raise ValueError("not a Java class file")
    class_file_attribute_names = {
        "AnnotationDefault", "BootstrapMethods", "Code", "ConstantValue",
        "Deprecated", "EnclosingMethod", "Exceptions", "InnerClasses",
        "LineNumberTable", "LocalVariableTable", "LocalVariableTypeTable",
        "MethodParameters", "Module", "ModuleMainClass", "ModulePackages",
        "NestHost", "NestMembers", "PermittedSubclasses", "Record",
        "RuntimeInvisibleAnnotations", "RuntimeInvisibleParameterAnnotations",
        "RuntimeInvisibleTypeAnnotations", "RuntimeVisibleAnnotations",
        "RuntimeVisibleParameterAnnotations", "RuntimeVisibleTypeAnnotations",
        "Signature", "SourceDebugExtension", "SourceFile", "StackMapTable",
        "Synthetic",
    }
    conflicts = class_file_attribute_names.intersection(replacements)
    if conflicts:
        raise ValueError(f"refusing to replace class-file attribute name(s): {sorted(conflicts)}")
    count = struct.unpack_from(">H", data, 8)[0]
    replacements_bytes = {
        old.encode("utf-8"): (old, new.encode("utf-8"))
        for old, new in replacements.items()
    }
    out = bytearray(data[:10])
    seen: set[str] = set()
    pos = 10
    index = 1
    while index < count:
        tag = data[pos]
        out.append(tag)
        pos += 1
        if tag == 1:
            size = struct.unpack_from(">H", data, pos)[0]
            pos += 2
            raw = data[pos : pos + size]
            pos += size
            found = replacements_bytes.get(raw)
            if found is None:
                encoded = raw
            else:
                original, encoded = found
                if len(encoded) > 65535:
                    raise ValueError("replacement string exceeds class-file limit")
                out.extend(struct.pack(">H", len(encoded)))
                out.extend(encoded)
                seen.add(original)
                index += 1
                continue
            out.extend(struct.pack(">H", size))
            out.extend(encoded)
        elif tag in (3, 4):
            out.extend(data[pos : pos + 4])
            pos += 4
        elif tag in (5, 6):
            out.extend(data[pos : pos + 8])
            pos += 8
            index += 1
        elif tag in (7, 8, 16, 19, 20):
            out.extend(data[pos : pos + 2])
            pos += 2
        elif tag in (9, 10, 11, 12, 17, 18):
            out.extend(data[pos : pos + 4])
            pos += 4
        elif tag == 15:
            out.extend(data[pos : pos + 3])
            pos += 3
        else:
            raise ValueError(f"unsupported constant-pool tag {tag}")
        index += 1
    out.extend(data[pos:])
    return bytes(out), seen


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", type=Path, default=DEFAULT_APP, help="Charles.app path")
    args = parser.parse_args()

    info_path = args.app / "Contents/Info.plist"
    jar_path = args.app / "Contents/Java/charles.jar"
    if not info_path.is_file() or not jar_path.is_file():
        raise SystemExit(f"Charles.app or charles.jar not found: {args.app}")
    info = plistlib.loads(info_path.read_bytes())
    version = info.get("CFBundleShortVersionString")
    if version != "5.2.1":
        raise SystemExit(f"This patch targets Charles 5.2.1; found {version!r}")
    jar_hash = hashlib.sha256(jar_path.read_bytes()).hexdigest()
    if jar_hash != EXPECTED_JAR_SHA256:
        raise SystemExit("charles.jar does not match the inspected 5.2.1 build; refusing to patch it")

    target_dir = Path(__file__).resolve().parent / "patch"
    targets: dict[str, dict[str, str]] = {
        "com/charlesproxy/gui/CharlesFrame.class": FRAME,
        "com/charlesproxy/gui/menus/HelpMenu.class": MENU,
        "com/charlesproxy/gui/menus/HelpMenu$5.class": {"Java Version": "Java 版本"},
        "com/charlesproxy/gui/menus/ProxyMenu.class": PROXY,
        "com/charlesproxy/gui/menus/EditMenu.class": EDIT_MENU,
        "com/charlesproxy/gui/session/AbstractSessionFrame.class": SESSION_UI,
        "com/charlesproxy/gui/session/qClj.class": SESSION_NAV,
        "com/charlesproxy/gui/transaction/actions/SwitchSequenceNavigatorAction.class": SESSION_NAV_SEQUENCE,
        "com/charlesproxy/gui/transaction/actions/SwitchStructureNavigatorAction.class": SESSION_NAV_STRUCTURE,
        "com/charlesproxy/gui/session/tables/TransactionField.class": TABLE_FIELDS,
        "com/charlesproxy/gui/gbNU.class": TOOLBAR,
        "com/charlesproxy/gui/qJQT.class": TOOLBAR_RECORDING,
        "com/charlesproxy/gui/WqPB.class": TOOLBAR_SSL,
        "com/charlesproxy/gui/TSYl.class": TOOLBAR_THROTTLE,
        "com/charlesproxy/gui/OmOM.class": TOOLBAR_BREAKPOINTS,
        "com/charlesproxy/gui/inLa.class": TOOLBAR_PROXYING,
        "com/charlesproxy/gui/SWcV.class": STATUS_MESSAGES,
        "com/charlesproxy/macos/UOUV.class": WINDOW_MENU,
        "com/charlesproxy/gui/session/actions/ComposeDialog.class": COMPOSE_DIALOG,
        "com/charlesproxy/gui/settings/UISettingsPanel.class": UI_SETTINGS,
        "com/charlesproxy/gui/settings/ViewersSettingsPanel.class": VIEWERS_SETTINGS,
        "com/charlesproxy/gui/settings/StartupSettingsPanel.class": STARTUP_SETTINGS,
        "com/charlesproxy/gui/settings/PromptsSettingsPanel.class": WARNINGS_SETTINGS,
        "com/charlesproxy/config/UserInterfaceConfiguration$QueryParamHighlightStyle.class": QUERY_PARAM_HIGHLIGHT,
        "com/charlesproxy/gui/settings/SettingsDialog.class": SETTINGS_DIALOG,
        "com/charlesproxy/gui/lib/qClj.class": UNSAVED_CHANGES,
    }
    targets.update(HELP_CLASSES)
    for name, replacements in PROXY_DIALOGS.items():
        targets.setdefault(name, {}).update(replacements)
    for name, replacements in ADDITIONAL_UI.items():
        targets.setdefault(name, {}).update(replacements)
    for name, replacements in AUDIT_FIXES.items():
        targets.setdefault(name, {}).update(replacements)
    for name, replacements in AUDIT_FIXES_EXTRA.items():
        targets.setdefault(name, {}).update(replacements)
    target_dir.mkdir(parents=True, exist_ok=True)
    # Remove obsolete generated overrides too, while preserving properties files.
    for stale in target_dir.rglob("*.class"):
        stale.unlink()
    changed = 0
    missing: list[str] = []
    with ZipFile(jar_path) as jar:
        for name, replacements in targets.items():
            try:
                original = jar.read(name)
            except KeyError:
                missing.append(f"class missing: {name}")
                continue
            updated, seen = patch_constant_pool(original, replacements)
            unmatched = set(replacements) - seen
            if unmatched:
                details = ", ".join(repr(value) for value in sorted(unmatched))
                raise SystemExit(f"translation string(s) not found in {name}: {details}")
            if not seen:
                continue
            output = target_dir / name
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(updated)
            changed += 1
            print(f"patched {name}: {len(seen)} string(s)")
    if missing:
        raise SystemExit("\n".join(missing))
    if changed < 5:
        raise SystemExit(f"only {changed} classes changed; refusing to publish an incomplete patch")
    print(f"Built {changed} class overrides in {target_dir}")


if __name__ == "__main__":
    main()
