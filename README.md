# Quantumult X

个人使用的 Quantumult X 配置。根目录的 `wsc82.conf` 是可直接下载的配置文件，`Ruleset/` 存放本仓库自带的远程规则。

## 配置文件

在 Quantumult X 中通过「配置文件 → 下载」导入以下地址：

```
https://raw.githubusercontent.com/wsc82/QuantumultX/main/wsc82.conf
```

配置里没有节点订阅，也没有 MITM 证书和口令。导入后需要自己添加节点订阅，并在 Quantumult X 里生成证书、按提示安装并信任。

## 规则

`Ruleset/ApplePush.list`、`Ruleset/YouTube.list`、`Ruleset/Telegram.list`、`Ruleset/AI.list`、`Ruleset/Global.list` 与 `Ruleset/Domestic.list` 是 Quantumult X 分流规则。六份列表由 `scripts/surge_to_qx.py` 从 [wsc82/Surge](https://github.com/wsc82/Surge) 的同名规则每天自动转换，也可以在 Actions 里手动触发。请不要直接改这六份文件；增删规则请到 Surge 仓库修改，下次同步会带过来。

`ApplePush.list` 是 Apple 推送服务（APNs）域名与官方 IP 段

```
https://raw.githubusercontent.com/wsc82/QuantumultX/main/Ruleset/ApplePush.list
```

`YouTube.list` 是 YouTube 视频、图片、短链和 App 接口

```
https://raw.githubusercontent.com/wsc82/QuantumultX/main/Ruleset/YouTube.list
```

`Telegram.list` 是 Telegram 域名与官方 IP 段

```
https://raw.githubusercontent.com/wsc82/QuantumultX/main/Ruleset/Telegram.list
```

`AI.list` 是 AI 服务与 X（Twitter）的域名和 IP

```
https://raw.githubusercontent.com/wsc82/QuantumultX/main/Ruleset/AI.list
```

`Global.list` 是境外网站与服务的代理合集

```
https://raw.githubusercontent.com/wsc82/QuantumultX/main/Ruleset/Global.list
```

`Domestic.list` 是国内网站、国内 CDN 与 Apple 服务

```
https://raw.githubusercontent.com/wsc82/QuantumultX/main/Ruleset/Domestic.list
```

`Ruleset/Catchall.list` 只给 Quantumult X 用，而且必须放在 `[filter_remote]` 的最后一条，以 `force-policy=Final`、`opt-parser=false` 加载。它用一条 `host-keyword, ., Final` 把前面规则集没有命中的域名全部交给 Final，不再做本地 DNS 查询，避免 DNS 泄漏。

```
https://raw.githubusercontent.com/wsc82/QuantumultX/main/Ruleset/Catchall.list
```

ApplePush、YouTube、Telegram、AI 是专用规则，要写在 Global 前面，否则 Global 里的同名域名会先命中。参数和 `wsc82.conf` 里现有的 `[filter_remote]` 一致。Catchall 仍然是最后一条。

```
[filter_remote]
https://raw.githubusercontent.com/wsc82/QuantumultX/main/Ruleset/ApplePush.list, tag=ApplePush, force-policy=ApplePush, update-interval=172800, opt-parser=false, enabled=true
https://raw.githubusercontent.com/wsc82/QuantumultX/main/Ruleset/YouTube.list, tag=YouTube, force-policy=YouTube, update-interval=172800, opt-parser=false, enabled=true
https://raw.githubusercontent.com/wsc82/QuantumultX/main/Ruleset/Telegram.list, tag=Telegram, force-policy=Telegram, update-interval=172800, opt-parser=false, enabled=true
https://raw.githubusercontent.com/wsc82/QuantumultX/main/Ruleset/AI.list, tag=AI, force-policy=AI, update-interval=172800, opt-parser=false, enabled=true
https://raw.githubusercontent.com/wsc82/QuantumultX/main/Ruleset/Global.list, tag=Global, force-policy=TOP, update-interval=172800, opt-parser=false, enabled=true
https://raw.githubusercontent.com/wsc82/QuantumultX/main/Ruleset/Domestic.list, tag=Domestic, force-policy=direct, update-interval=172800, opt-parser=false, enabled=true
https://raw.githubusercontent.com/wsc82/QuantumultX/main/Ruleset/Catchall.list, tag=Catchall, force-policy=Final, update-interval=172800, opt-parser=false, enabled=true
```
