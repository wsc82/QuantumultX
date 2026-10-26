# Quantumult X

个人使用的 Quantumult X 配置。根目录的 `wsc82.conf` 是可直接下载的配置文件，`Ruleset/` 存放本仓库自带的远程规则。

## 配置文件

在 Quantumult X 中通过「配置文件 → 下载」导入以下地址：

```
https://raw.githubusercontent.com/wsc82/QuantumultX/main/wsc82.conf
```

配置里没有节点订阅，也没有 MITM 证书和口令。导入后需要自己添加节点订阅，并在 Quantumult X 里生成证书、按提示安装并信任。

## 规则

`Global.list` 与 `Domestic.list` 来自 [wsc82/Surge](https://github.com/wsc82/Surge)。

`Ruleset/Catchall.list` 只给 Quantumult X 用，而且必须放在 `[filter_remote]` 的最后一条，以 `force-policy=Final`、`opt-parser=false` 加载。它用一条 `host-keyword, ., Final` 把前面规则集没有命中的域名全部交给 Final，不再做本地 DNS 查询，避免 DNS 泄漏。

```
https://raw.githubusercontent.com/wsc82/QuantumultX/main/Ruleset/Catchall.list
```
