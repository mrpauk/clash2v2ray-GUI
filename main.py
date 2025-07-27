#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import yaml
import base64
import json
import sys
import os
from urllib.parse import quote, urlencode
from typing import List, Dict, Any
import tkinter as tk
from tkinter import ttk, messagebox
import pyperclip

class ClashToV2ray:
    """Clash config to v2rayN link converter"""

    def __init__(self, input_file: str):
        """
        Initialize the converter

        Args:
            input_file (str): Path to the Clash config file
        """
        self.input_file = input_file
        self.proxies = []

    def load_yaml(self) -> None:
        """
        Load and parse the YAML config

        Raises:
            FileNotFoundError: If the config file does not exist
            yaml.YAMLError: If there's an error parsing the YAML
        """
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if 'proxies' in config:
                    self.proxies = config['proxies']
                else:
                    raise ValueError("Missing 'proxies' section in config")
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {self.input_file}")
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"YAML parse error: {str(e)}")

    def generate_vmess_link(self, proxy: Dict[str, Any]) -> str:
        """
        Generate VMess node link
        """
        vmess_config = {
            "v": "2",
            "ps": proxy.get('name', 'Unknown'),
            "add": proxy['server'],
            "port": str(proxy['port']),
            "id": proxy['uuid'],
            "aid": str(proxy.get('alterId', 0)),
            "net": proxy.get('network', 'tcp'),
            "type": proxy.get('type', 'none'),
            "host": proxy.get('ws-headers', {}).get('Host', ''),
            "path": proxy.get('ws-path', ''),
            "tls": "tls" if proxy.get('tls', False) else ""
        }

        json_str = json.dumps(vmess_config)
        return f"vmess://{base64.b64encode(json_str.encode()).decode()}"

    def generate_ss_link(self, proxy: Dict[str, Any]) -> str:
        """
        Generate Shadowsocks node link
        """
        method = proxy['cipher']
        password = proxy['password']
        server = proxy['server']
        port = proxy['port']
        name = quote(proxy.get('name', 'Unknown'))

        ss_config = f"{method}:{password}@{server}:{port}"
        base64_str = base64.b64encode(ss_config.encode()).decode()
        return f"ss://{base64_str}#{name}"

    def generate_trojan_link(self, proxy: Dict[str, Any]) -> str:
        """
        Generate Trojan node link
        """
        password = proxy['password']
        server = proxy['server']
        port = proxy['port']
        name = quote(proxy.get('name', 'Unknown'))

        return f"trojan://{password}@{server}:{port}#{name}"

    def generate_hysteria2_link(self, proxy: Dict[str, Any]) -> str:
        """
        Generate Hysteria2 node link
        """
        server = proxy['server']
        password = proxy['password']

        # port priority: port > ports
        port = proxy.get('port') or proxy.get('ports')
        if isinstance(port, str) and '-' in port:
            port = port.split('-')[0]
        port = str(port) if port else '443'

        params = {
            "sni": proxy.get("sni", ""),
            "name": quote(proxy.get("name", "Unknown")),
            "up": str(proxy.get("up_mbps", "")),
            "down": str(proxy.get("down_mbps", ""))
        }
        params = {k: v for k, v in params.items() if v}
        query_string = urlencode(params)

        return f"hysteria2://{password}@{server}:{port}?{query_string}" if query_string else f"hysteria2://{password}@{server}:{port}"

    def convert(self) -> List[str]:
        """
        Convert all proxies to v2rayN-compatible links
        """
        links = []
        for proxy in self.proxies:
            try:
                if proxy['type'] == 'vmess':
                    links.append(self.generate_vmess_link(proxy))
                elif proxy['type'] == 'ss':
                    links.append(self.generate_ss_link(proxy))
                elif proxy['type'] == 'trojan':
                    links.append(self.generate_trojan_link(proxy))
                elif proxy['type'] == 'hysteria2':
                    links.append(self.generate_hysteria2_link(proxy))
            except KeyError as e:
                print(f"Warning: Missing field {str(e)} in proxy {proxy.get('name', 'Unknown')}")
                continue
            except Exception as e:
                print(f"Warning: Error processing proxy {proxy.get('name', 'Unknown')}: {str(e)}")
                continue
        return links

def main():
    if len(sys.argv) != 2:
        print("Usage: python clash_to_v2ray.py <clash_config_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = os.path.splitext(input_file)[0] + '_v2ray_links.txt'

    try:
        converter = ClashToV2ray(input_file)
        converter.load_yaml()
        links = converter.convert()

        if not links:
            print("Warning: No nodes converted")
            sys.exit(1)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(links))

        print(f"Done! Converted {len(links)} nodes")
        print(f"Saved to: {output_file}")

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

def create_gui():
    def paste_yaml():
        try:
            yaml_content = pyperclip.paste()
            yaml_input.delete('1.0', tk.END)
            yaml_input.insert('1.0', yaml_content)
        except Exception as e:
            messagebox.showerror("Error", f"Paste failed: {str(e)}")

    def convert_yaml():
        try:
            yaml_content = yaml_input.get('1.0', tk.END)
            temp_file = 'temp_config.yaml'
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(yaml_content)

            converter = ClashToV2ray(temp_file)
            converter.load_yaml()
            links = converter.convert()

            os.remove(temp_file)

            output_text.delete('1.0', tk.END)
            output_text.insert('1.0', '\n'.join(links))

        except Exception as e:
            messagebox.showerror("Error", f"Conversion failed: {str(e)}")

    def copy_output():
        try:
            output_content = output_text.get('1.0', tk.END).strip()
            if output_content:
                pyperclip.copy(output_content)
                messagebox.showinfo("Success", "Copied to clipboard!")
            else:
                messagebox.showwarning("Warning", "Nothing to copy!")
        except Exception as e:
            messagebox.showerror("Error", f"Copy failed: {str(e)}")

    root = tk.Tk()
    root.title("Clash Config Converter")
    root.geometry("800x600")

    style = ttk.Style()
    style.configure('TButton', padding=5)
    style.configure('TFrame', padding=5)

    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    input_label = ttk.Label(main_frame, text="YAML Config:")
    input_label.pack(anchor='w')

    yaml_input = tk.Text(main_frame, height=10, wrap=tk.WORD)
    yaml_input.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=(0, 10))

    paste_btn = ttk.Button(button_frame, text="Paste YAML", command=paste_yaml)
    paste_btn.pack(side=tk.LEFT, padx=5)

    convert_btn = ttk.Button(button_frame, text="Convert", command=convert_yaml)
    convert_btn.pack(side=tk.LEFT, padx=5)

    exit_btn = ttk.Button(button_frame, text="Exit", command=root.quit)
    exit_btn.pack(side=tk.RIGHT, padx=5)

    output_label = ttk.Label(main_frame, text="Converted Links:")
    output_label.pack(anchor='w')

    output_text = tk.Text(main_frame, height=10, wrap=tk.WORD)
    output_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    copy_btn = ttk.Button(main_frame, text="Copy Output", command=copy_output)
    copy_btn.pack(pady=(0, 10))

    return root

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main()
    else:
        root = create_gui()
        root.mainloop()
