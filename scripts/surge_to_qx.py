#!/usr/bin/env python3
"""Convert Surge rule-set lists into Quantumult X filter syntax.

Quantumult X filter types follow the official sample configuration
(https://raw.githubusercontent.com/crossutility/Quantumult-X/master/sample.conf)
and the KOP-XIAO reference config: host, host-suffix, host-keyword,
host-wildcard, user-agent, ip-cidr, ip6-cidr, geoip, ip-asn, and final.
Each generated line carries a policy because QX requires one. Surge-only
options (no-resolve, extended-matching, pre-matching) are dropped. Rule
types QX cannot express are omitted entirely.

The two lists converted here are:

- https://raw.githubusercontent.com/wsc82/Surge/main/Ruleset/Global.list
- https://raw.githubusercontent.com/wsc82/Surge/main/Ruleset/Domestic.list
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Surge TYPE -> QX type. Only types QX actually matches are listed.
SURGE_TO_QX = {
    "DOMAIN": "host",
    "DOMAIN-SUFFIX": "host-suffix",
    "DOMAIN-KEYWORD": "host-keyword",
    "DOMAIN-WILDCARD": "host-wildcard",
    "IP-CIDR": "ip-cidr",
    "IP-CIDR6": "ip6-cidr",
    "GEOIP": "geoip",
    "IP-ASN": "ip-asn",
    "USER-AGENT": "user-agent",
}

# Appended Surge parameters. They are not QX filter parameters.
SURGE_OPTIONS = {
    "no-resolve",
    "extended-matching",
    "pre-matching",
}

# Types documented by Surge that sample.conf does not implement.
UNSUPPORTED_REASONS = {
    "DOMAIN-SET": "QX has no domain-set rule",
    "URL-REGEX": "QX has no url-regex rule",
    "PROCESS-NAME": "QX has no process-name rule",
    "DEST-PORT": "QX has no dest-port rule",
    "SRC-PORT": "QX has no src-port rule",
    "IN-PORT": "QX has no in-port rule",
    "SRC-IP": "QX has no src-ip rule",
    "DEVICE-NAME": "QX has no device-name rule",
    "MAC-ADDRESS": "QX has no mac-address rule",
    "PROTOCOL": "QX has no protocol rule",
    "HOSTNAME-TYPE": "QX has no hostname-type rule",
    "SUBNET": "QX has no subnet rule",
    "CELLULAR-RADIO": "QX has no cellular-radio rule",
    "AND": "QX has no logical AND/OR/NOT rule",
    "OR": "QX has no logical AND/OR/NOT rule",
    "NOT": "QX has no logical AND/OR/NOT rule",
    "RULE-SET": "QX has no rule-set include",
    "SCRIPT": "QX has no script rule",
    "FINAL": "final is set in the QX config, not in these lists",
}

LISTS = (
    {
        "name": "Global",
        "policy": "Global",
        "source": "https://raw.githubusercontent.com/wsc82/Surge/main/Ruleset/Global.list",
        "output": ROOT / "Ruleset" / "Global.list",
    },
    {
        "name": "Domestic",
        "policy": "Domestic",
        "source": "https://raw.githubusercontent.com/wsc82/Surge/main/Ruleset/Domestic.list",
        "output": ROOT / "Ruleset" / "Domestic.list",
    },
)


class Skip(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def fetch(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "QuantumultX-surge-to-qx"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        text = response.read().decode(charset)
    if text.lstrip().startswith("<"):
        raise RuntimeError(f"response from {url} is not a rule list")
    return text


def split_fields(text: str) -> list[str]:
    """Split a Surge rule on commas, keeping quoted commas intact."""
    fields: list[str] = []
    buf: list[str] = []
    quote: str | None = None
    for char in text:
        if quote:
            if char == quote:
                quote = None
            else:
                buf.append(char)
            continue
        if char in {'"', "'"}:
            quote = char
            continue
        if char == ",":
            fields.append("".join(buf).strip())
            buf = []
            continue
        buf.append(char)
    fields.append("".join(buf).strip())
    return [field for field in fields if field != ""]


def strip_inline_comment(line: str) -> tuple[str, str | None]:
    """Return the rule text and a trailing comment, if one is present.

    A comment marker counts only outside quotes and only when it is preceded
    by whitespace, so semicolons inside a User-Agent value are preserved.
    """
    quote: str | None = None
    i = 0
    while i < len(line):
        char = line[i]
        if quote:
            if char == quote:
                quote = None
            i += 1
            continue
        if char in {'"', "'"}:
            quote = char
            i += 1
            continue
        preceded_by_space = i > 0 and line[i - 1] in " \t"
        if preceded_by_space and (
            char == "#" or char == ";" or line.startswith("//", i)
        ):
            comment = line[i:].strip()
            if comment.startswith("//"):
                comment = "#" + comment[2:]
            elif comment.startswith(";"):
                comment = "#" + comment[1:]
            return line[:i].strip(), comment
        i += 1
    return line.strip(), None


def normalize_value(surge_type: str, value: str) -> str:
    if surge_type == "GEOIP":
        return value.lower()
    if surge_type == "IP-ASN":
        if value.upper().startswith("AS") and value[2:].isdigit():
            return value[2:]
    return value


def convert_rule(line: str, policy: str) -> str:
    body, comment = strip_inline_comment(line)
    fields = split_fields(body)
    if not fields:
        raise Skip("empty rule")
    surge_type = fields[0].upper()
    if surge_type not in SURGE_TO_QX:
        reason = UNSUPPORTED_REASONS.get(
            surge_type, f"QX has no {surge_type.lower()} rule"
        )
        raise Skip(reason)
    if len(fields) < 2:
        raise Skip("missing match value")
    # Remaining fields are a Surge policy and/or Surge-only options. QX lines
    # always use the policy passed in, so both are left off the output.
    value = normalize_value(surge_type, fields[1])
    rendered = f"{SURGE_TO_QX[surge_type]}, {value}, {policy}"
    if comment:
        rendered = f"{rendered} {comment}"
    return rendered


def convert_text(text: str, policy: str, source_url: str) -> tuple[str, dict]:
    skipped: list[tuple[int, str, str]] = []
    output_rules = 0
    source_rules = 0
    stripped_options = 0
    body: list[str] = []

    for line_no, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if stripped == "":
            body.append("")
            continue
        if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith(";"):
            if stripped.startswith("//"):
                body.append("#" + stripped[2:])
            elif stripped.startswith(";"):
                body.append("#" + stripped[1:])
            else:
                body.append(raw.rstrip())
            continue
        source_rules += 1
        try:
            converted = convert_rule(raw, policy)
        except Skip as exc:
            skipped.append((line_no, raw.strip(), exc.reason))
            continue
        for field in split_fields(strip_inline_comment(raw)[0])[2:]:
            token = field.lower()
            if token in SURGE_OPTIONS or token.startswith("update-interval="):
                stripped_options += 1
        body.append(converted)
        output_rules += 1

    header = [
        "# ============================================================",
        "# 自动生成，请勿手工修改。",
        "# 由 scripts/surge_to_qx.py 从 wsc82/Surge 转换而来：",
        f"# {source_url}",
        "# 增删规则请改 Surge 仓库；GitHub Actions 每天同步到这里。",
        "# ============================================================",
        "",
    ]
    rendered = "\n".join(header + body).rstrip() + "\n"
    stats = {
        "source_rules": source_rules,
        "output_rules": output_rules,
        "skipped": skipped,
        "stripped_options": stripped_options,
    }
    return rendered, stats


def convert_lists() -> list[dict]:
    summaries = []
    for item in LISTS:
        text = fetch(item["source"])
        rendered, stats = convert_text(text, item["policy"], item["source"])
        if stats["source_rules"] and stats["output_rules"] == 0:
            raise RuntimeError(f"{item['name']}: every rule was skipped; refusing to write")
        item["output"].parent.mkdir(parents=True, exist_ok=True)
        item["output"].write_text(rendered, encoding="utf-8", newline="\n")
        stats["name"] = item["name"]
        summaries.append(stats)
        print(
            f"{item['name']}: source={stats['source_rules']} "
            f"output={stats['output_rules']} skipped={len(stats['skipped'])} "
            f"stripped_options={stats['stripped_options']}"
        )
        for line_no, line, reason in stats["skipped"]:
            print(f"  skip L{line_no}: {line}")
            print(f"    reason: {reason}")
    return summaries


def self_test() -> None:
    sample = "\n".join(
        [
            "# section",
            "",
            "DOMAIN-SUFFIX,google.com",
            "DOMAIN,www.example.com",
            "DOMAIN-KEYWORD,facebook",
            "DOMAIN-WILDCARD,*.example.com",
            "IP-CIDR,1.2.3.0/24,no-resolve",
            "IP-CIDR6,2001:db8::/32,no-resolve",
            "GEOIP,CN,no-resolve",
            "IP-ASN,AS13335",
            "USER-AGENT,Twitter*",
            "DOMAIN-SUFFIX,example.com,PROXY,extended-matching",
            "IP-CIDR,9.9.9.9/32,DIRECT,no-resolve,pre-matching # keep",
            "PROCESS-NAME,Telegram",
            "URL-REGEX,^https://example.com",
            "DEST-PORT,443",
            "AND,((DOMAIN,example.com),(DEST-PORT,443))",
            "OR,((PROTOCOL,UDP),(DEST-PORT,443))",
            "NOT,((DOMAIN,example.com))",
            "PROTOCOL,UDP",
            "DOMAIN-SET,https://example.com/list.txt",
            "#DOMAIN-SUFFIX,kept.example",
        ]
    )
    rendered, stats = convert_text(
        sample,
        "Global",
        "https://raw.githubusercontent.com/wsc82/Surge/main/Ruleset/Global.list",
    )
    expected = [
        "host-suffix, google.com, Global",
        "host, www.example.com, Global",
        "host-keyword, facebook, Global",
        "host-wildcard, *.example.com, Global",
        "ip-cidr, 1.2.3.0/24, Global",
        "ip6-cidr, 2001:db8::/32, Global",
        "geoip, cn, Global",
        "ip-asn, 13335, Global",
        "user-agent, Twitter*, Global",
        "host-suffix, example.com, Global",
        "ip-cidr, 9.9.9.9/32, Global # keep",
    ]
    rules = [
        line
        for line in rendered.splitlines()
        if line and not line.startswith("#")
    ]
    if rules != expected:
        raise SystemExit(f"self-test rules mismatch:\n{rules!r}")
    skipped_types = [line.split(",", 1)[0] for _, line, _ in stats["skipped"]]
    expected_skipped = [
        "PROCESS-NAME",
        "URL-REGEX",
        "DEST-PORT",
        "AND",
        "OR",
        "NOT",
        "PROTOCOL",
        "DOMAIN-SET",
    ]
    if skipped_types != expected_skipped:
        raise SystemExit(f"self-test skips mismatch: {skipped_types}")
    if "#DOMAIN-SUFFIX,kept.example" not in rendered.splitlines():
        raise SystemExit("commented source rule was not preserved")
    if "no-resolve" in rendered or "extended-matching" in rendered or "pre-matching" in rendered:
        raise SystemExit("Surge option leaked into output")
    if stats["source_rules"] != 19 or stats["output_rules"] != 11:
        raise SystemExit(f"unexpected counts: {stats['source_rules']} {stats['output_rules']}")
    print("self-test ok")


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        self_test()
        return 0
    try:
        convert_lists()
    except Exception as exc:  # noqa: BLE001 - top-level CLI boundary
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
