import os
import requests
import urllib3
from datetime import datetime  # Added for timestamping

# Suppress "Unverified HTTPS request" warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
PROXMOX_URL = os.environ.get("PROXMOX_URL", "").rstrip('/')
PROXMOX_USER = os.environ.get("PROXMOX_USER", "").strip()
PROXMOX_TOKEN = os.environ.get("PROXMOX_TOKEN", "").strip()

def get_stats():
    auth_header = f"PVEAPIToken={PROXMOX_USER}!{PROXMOX_TOKEN}"
    headers = {
        "Authorization": auth_header,
        "User-Agent": "GitHub-Action-Proxmox-Stats",
        "Accept": "application/json"
    }
    
    try:
        r = requests.get(f"{PROXMOX_URL}/api2/json/cluster/resources", headers=headers, verify=False, timeout=20)
        if r.status_code != 200:
            print(f"!!! API ERROR: {r.status_code} !!!")
            return None
        
        return r.json()['data']
    except Exception as e:
        print(f"Failed to fetch data: {e}")
        return None

def generate_svg(data):
    # Get current time in UTC
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    if data is None:
        stats = {"cpu": "ERR", "mem": "ERR", "lxc": "0", "vms": "0", "status": "Offline"}
    else:
        nodes = [x for x in data if x['type'] == 'node']
        lxcs = [x for x in data if x['type'] == 'lxc' and x['status'] == 'running']
        vms = [x for x in data if x['type'] == 'qemu' and x['status'] == 'running']

        if not nodes:
            stats = {"cpu": "0%", "mem": "0%", "lxc": "0", "vms": "0", "status": "Offline"}
        else:
            cpu = sum(n.get('cpu', 0) for n in nodes) / len(nodes) * 100
            mem = sum(n.get('mem', 0) for n in nodes)
            maxmem = sum(n.get('maxmem', 0) for n in nodes)
            
            mem_p = (mem / maxmem) * 100 if maxmem > 0 else 0
            mem_gb = mem / (1024**3)
            maxmem_gb = maxmem / (1024**3)

            stats = {
                "cpu": f"{cpu:.1f}%",
                "mem": f"{mem_p:.1f}% ({mem_gb:.0f}/{maxmem_gb:.0f}G)",
                "lxc": str(len(lxcs)),
                "vms": str(len(vms)),
                "status": "Online"
            }

    color = "#39FF14" if stats['status'] == "Online" else "#ff3333"
    
    # SVG Construction - Slightly increased height (to 200) for the timestamp
    svg = f"""<svg width="450" height="200" viewBox="0 0 450 200" xmlns="http://www.w3.org/2000/svg">
      <style>
        .bg {{ fill: #0d1117; stroke: #30363d; stroke-width: 1px; rx: 10px; }}
        .txt {{ font-family: 'Segoe UI', Ubuntu, sans-serif; }}
        .title {{ font-weight: 600; font-size: 18px; fill: #39FF14; }}
        .lbl {{ font-weight: 400; font-size: 14px; fill: #8b949e; }}
        .val {{ font-weight: 600; font-size: 14px; fill: #e6edf3; }}
        .ts {{ font-size: 10px; fill: #484f58; }} /* Subtle style for timestamp */
        .dot {{ fill: {color}; }}
        .line {{ stroke: #30363d; stroke-width: 1px; }}
      </style>
      
      <rect x="0.5" y="0.5" width="449" height="199" class="bg" />
      
      <text x="25" y="35" class="txt title">PROXMOX CLUSTER</text>
      <circle cx="410" cy="30" r="5" class="dot">
        <animate attributeName="opacity" values="1;0.5;1" dur="2s" repeatCount="indefinite"/>
      </circle>
      <text x="395" y="35" class="txt val" text-anchor="end">{stats['status']}</text>
      
      <line x1="0" y1="55" x2="450" y2="55" class="line" />

      <text x="25" y="90" class="txt lbl">CPU LOAD</text>
      <text x="25" y="115" class="txt val" font-size="20">{stats['cpu']}</text>
      
      <text x="200" y="90" class="txt lbl">MEMORY</text>
      <text x="200" y="115" class="txt val" font-size="20">{stats['mem']}</text>
      
      <text x="25" y="150" class="txt lbl">LXC: <tspan class="val">{stats['lxc']}</tspan></text>
      <text x="200" y="150" class="txt lbl">VMs: <tspan class="val">{stats['vms']}</tspan></text>

      <text x="425" y="180" class="txt ts" text-anchor="end">Last Updated: {now}</text>
    </svg>"""
    
    with open("proxmox_stats.svg", "w") as f:
        f.write(svg)

if __name__ == "__main__":
    data = get_stats()
    generate_svg(data)
