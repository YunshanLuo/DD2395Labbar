#!/usr/bin/env python3


def _rule_present(res, rules):
    for key in rules:
        if key in res:
            return True
    return False


def _substitutes_forever(text, rules, cap=1000):
    res = text
    while _rule_present(res, rules):
        for key in rules:
            res = res.replace(key, rules[key])
        if len(res) > cap:
            return True
    return False


def filter_text(text):
    rules = {}
    for line in text.split("\n"):
        if line.startswith("#"):
            parts = line[1:].split("=")
            key = parts[0].strip()
            val = parts[1].strip()
            rules[key] = val

    for val in rules.values():
        if _substitutes_forever(val, rules):
            return False
    return True
