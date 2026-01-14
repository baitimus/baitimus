import os
import requests
import urllib3

# Suppress "Unverified HTTPS request" warnings for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION (Loaded from Secrets) ---
PROXMOX_URL = os.environ["PROXMOX_URL"]   # e.g., https://proxmox.example.com:8006
PROXMOX_USER = os.environ["PROXMOX_USER"]  # e.g., root@pam
PROXMOX_TOKEN = os.environ["PROXMOX_TOKEN"] # e.g., github=uuid-secret

def get_stats():
    # The API expects: "PVEAPIToken=USER@REALM!TOKENID=UUID"
    # We construct this from our two secrets.
    headers = {"Authorization": f"PVEAPIToken={PROXMOX_USER}!{PROXMOX_TOKEN}"}
    
    try:
        # verify=False is needed if you don't have a valid public SSL cert
        r = requests.get(f"{PROXMOX_URL}/api2/json/cluster/resources", headers=headers, verify=False, timeout=10)
        r.raise_for_status()
        data = r.json()['data']
    except Exception as e:
        print(f"Connection Error: {e}")
        return None

    nodes = [x for x in data if x['type'] == 'node']
    lxcs = [x for x in data if x['type'] == 'lxc' and x['status'] == 'running']
    vms = [x for x in data if x['type'] == 'qemu' and x['status'] == 'running']

    # Aggregating Cluster Stats
    if not nodes:
        return None

    cpu_usage = sum(n.get('cpu', 0) for n in nodes) / len(nodes) * 100
    mem_used = sum(n.get('mem', 0) for n in nodes)
    mem_total = sum(n.get('maxmem', 0) for n in nodes)
    mem_percent = (mem_used / mem_total) * 100
    
    # Formatting bytes to GB
    mem_used_gb = mem_used / (1024**3)
    mem_total_gb = mem_total / (1024**3)

    return {
        "cpu": f"{cpu_usage:.1f}%",
        "mem": f"{mem_percent:.1f}% ({mem_used_gb:.0f}/{mem_total_gb:.0f} GB)",
        "lxc": len(lxcs),
        "vms": len(vms),
        "status": "ONLINE"
    }

def generate_svg(stats):
    # Fallback values if stats are missing
    if not stats:
        stats = {"cpu": "N/A", "mem": "N/A", "lxc": "-", "vms": "-", "status": "UNREACHABLE"}

    # Colors: Green #39FF14, Dark BG #0d1117, Dim Text #8b949e
    # Status color changes based on availability
    status_color = "#39FF14" if stats['status'] == "ONLINE" else "#ff3333"

    svg = f"""
    <svg width="450" height="180" viewBox="0 0 450 180" xmlns="http://www.w3.org/2000/svg">
      <style>
        .bg {{ fill: #0d1117; stroke: #30363d; stroke-width: 1px; rx: 10px; }}
        .title {{ font: 600 18px 'Segoe UI', Ubuntu, sans-serif; fill: #39FF14; }}
        .label {{ font: 400 14px 'Segoe UI', Ubuntu, sans-serif; fill: #8b949e; }}
        .val {{ font: 600 14px 'Segoe UI', Ubuntu, sans-serif; fill: #e6edf3; }}
        .status-dot {{ fill: {status_color}; }}
        .line {{ stroke: #30363d; stroke-width: 1px; }}
      </style>
      
      <rect x="0.5" y="0.5" width="449" height="179" class="bg" />
      
      <text x="25" y="35" class="title">PROXMOX CLUSTER</text>
      <circle cx="410" cy="30" r="5" class="status-dot">
        <animate attributeName="opacity" values="1;0.5;1" dur="2s" repeatCount="indefinite"/>
      </circle>
      <text x="350" y="35" class="val" text-anchor="end">{stats['status']}</text>
      
      <line x1="0" y1="55" x2="450" y2="55" class="line" />

      <text x="25" y="90" class="label">CPU LOAD</text>
      <text x="25" y="115" class="val" font-size="20">{stats['cpu']}</text>
      
      <text x="25" y="150" class="label">ACTIVE LXC</text>
      <text x="110" y="150" class="val">{stats['lxc']}</text>

      <text x="200" y="90" class="label">MEMORY USAGE</text>
      <text x="200" y="115" class="val" font-size="20">{stats['mem']}</text>
      
      <text x="200" y="150" class="label">ACTIVE VMS</text>
      <text x="290" y="150" class="val">{stats['vms']}</text>

    </svg>
    """
    
    with open("proxmox_stats.svg", "w") as f:
        f.write(svg)

if __name__ == "__main__":
    data = get_stats()
    generate_svg(data)
