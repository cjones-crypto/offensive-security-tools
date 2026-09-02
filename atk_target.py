#!/usr/bin/env python3
import os
import json
import argparse
from pathlib import Path

CONFIG_PATH = Path.home() / ".atk_targets.json"


def load_config():
    if not CONFIG_PATH.exists():
        return {"current": None, "targets": {}}
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)


def cmd_set(args):
    config = load_config()
    name = args.name if args.name else "default"
    ip = args.ip

    config["targets"][name] = ip
    config["current"] = name
    save_config(config)

    print(f"[+] Target '{name}' set to: {ip}")


def cmd_show(args):
    config = load_config()
    current = config.get("current")
    if not current:
        print("[!] No current target set.")
        return

    ip = config["targets"].get(current)
    print(ip)


def cmd_info(args):
    config = load_config()
    current = config.get("current")
    if not current:
        print("[!] No current target set.")
        return

    ip = config["targets"].get(current)
    print(f"[*] Current profile: {current}")
    print(f"[*] Current target IP: {ip}")


def cmd_list(args):
    config = load_config()
    targets = config.get("targets", {})
    if not targets:
        print("[!] No targets saved.")
        return

    current = config.get("current")
    for name, ip in targets.items():
        marker = "*" if name == current else " "
        print(f"{marker} {name}: {ip}")


def cmd_switch(args):
    config = load_config()
    name = args.name

    if name not in config.get("targets", {}):
        print(f"[!] No such target profile: {name}")
        return

    config["current"] = name
    save_config(config)
    print(f"[+] Switched current target to '{name}' ({config['targets'][name]})")


def cmd_clear(args):
    config = load_config()
    config["current"] = None
    save_config(config)
    print("[+] Cleared current target.")

def cmd_clear_all(args):
    config = {"current": None, "targets": {}}
    save_config(config)
    print("[+] Cleared ALL stored targets.")

def cmd_export(args):
    config = load_config()
    current = config.get("current")
    if not current:
        print("[!] No current target set.")
        return

    ip = config["targets"].get(current)
    if args.format == "env":
        print(f'export TARGET="{ip}"')
    else:
        print(ip)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="atk_target",
        description="TechTactix Auto Target Manager - persistent pentest target profiles",
    )

    sub = parser.add_subparsers(dest="command")

    # set
    p_set = sub.add_parser("set", help="Set target IP (optionally with profile name)")
    p_set.add_argument("ip", help="Target IP or hostname")
    p_set.add_argument("-n", "--name", help="Profile name (default: 'default')")
    p_set.set_defaults(func=cmd_set)

    # show
    p_show = sub.add_parser("show", help="Show current target IP only")
    p_show.set_defaults(func=cmd_show)

    # info
    p_info = sub.add_parser("info", help="Show current target profile and IP")
    p_info.set_defaults(func=cmd_info)

    # list
    p_list = sub.add_parser("list", help="List all saved targets")
    p_list.set_defaults(func=cmd_list)

    # switch
    p_switch = sub.add_parser("switch", help="Switch current target profile")
    p_switch.add_argument("name", help="Profile name to switch to")
    p_switch.set_defaults(func=cmd_switch)

    # clear
    p_clear = sub.add_parser("clear", help="Clear current target")
    p_clear.set_defaults(func=cmd_clear)

    # clear-all
    p_clear_all = sub.add_parser("clear-all", help="Clear ALL stored targets")
    p_clear_all.set_defaults(func=cmd_clear_all)

    # export
    p_export = sub.add_parser("export", help="Export current target (env or raw)")
    p_export.add_argument(
        "-f",
        "--format",
        choices=["env", "raw"],
        default="raw",
        help="Export format: env (export TARGET=...) or raw (IP only)",
    )
    p_export.set_defaults(func=cmd_export)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
