import os
import requests
import urllib3

# Suppress "Unverified HTTPS request" warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
# Strip trailing slashes to prevent "https://domain.com//api2" errors
PROXMOX_URL = os.environ["PROXMOX_URL"].rstrip('/')
PROXMOX_USER = os.environ["PROXMOX_USER"].strip()
PROXMOX_TOKEN = os.environ["PROXMOX_TOKEN"].strip()

def get_stats():
    # Construct the Authorization Header
    # Expected format: PVEAPIToken=user@realm!token_name=uuid
    auth_header = f"PVEAPIToken={PROXMOX_USER}!{PROXMOX_TOKEN}"
    
    # FAKE A BROWSER (Crucial for bypassing WAF/Cloudflare)
    headers = {
        "Authorization": auth_header,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    print(f"Connecting to: {PROXMOX_URL}/api2/json/cluster/resources")
    # Debug: Print secret lengths to check for hidden spaces (Safe to show in logs)
    print(f"Debug - User Length: {len(PROXMOX_USER)} (Expected ~16)")
    print(f"Debug - Token Length: {len(PROXMOX_TOKEN)} (Expected ~47)")

    try:
        r = requests.get(f"{PROXMOX_URL}/api2/json/cluster/resources", headers=headers, verify=False, timeout=15)
        
        # IF IT FAILS: Print the actual response text so we see WHY
        if r.status_code != 200:
            print(f"!!! API ERROR: {r.status_code} !!!")
            print(f"Response Body: {r.text[:500]}") # Print first 500 chars of error
        
        r.raise_for_status()
        data = r.json()['data']
        return data

    except Exception as e:
        print(f"Failed to fetch data: {e}")
        return None

def generate_svg(data):
    # If data is None (connection failed), use dummy data so script doesn't crash
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

    # Generate the SVG
    color = "#39FF14" if stats['status'] == "Online" else "#ff3333"
    svg = f"""<svg width="450" height="180" viewBox="0 0 450 180" xmlns="http://www.w3.org/2000/svg">
      <style>
        .bg {{ fill: #0d1117; stroke: #30363d; stroke-width: 1px; rx: 10px; }}
        .txt {{ font-family: 'Segoe UI', Ubuntu, sans-serif; }}
        .title {{ font-weight: 600; font-size: 18px; fill: #39FF14; }}
        .lbl {{ font-weight: 400; font-size: 14px; fill: #8b949e; }}
        .val {{ font-weight: 600; font-size: 14px; fill: #e6edf3; }}
        .dot {{ fill: {color}; }}
      </style>
      <rect x="0.5" y="0.5" width="449" height="179" class="bg" />
      <text x="25" y="35" class="txt title">PROXMOX CLUSTER</text>
      <circle cx="410" cy="30" r="5" class="dot" />
      <text x="395" y="35" class="txt val" text-anchor="end">{stats['status']}</text>
      <line x1="0" y1="55" x2="450" y2="55" stroke="#30363d" />
      <text x="25" y="90" class="txt lbl">CPU LOAD</text>
      <text x="25" y="115" class="txt val" font-size="20">{stats['cpu']}</text>
      <text x="200" y="90" class="txt lbl">MEMORY</text>
      <text x="200" y="115" class="txt val" font-size="20">{stats['mem']}</text>
      <text x="25" y="150" class="txt lbl">LXC: <tspan class="val">{stats['lxc']}</tspan></text>
      <text x="200" y="150" class="txt lbl">VMs: <tspan class="val">{stats['vms']}</tspan></text>
    </svg>"""
    
    with open("proxmox_stats.svg", "w") as f:
        f.write(svg)

if __name__ == "__main__":
    data = get_stats()
    generate_svg(data)
