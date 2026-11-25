import os
import sys
import socket
import ipaddress
import requests
from concurrent.futures import ThreadPoolExecutor

G = "\033[92m"
C = "\033[96m"
R = "\033[91m"
Y = "\033[93m"
W = "\033[97m"
RESET = "\033[0m"

REPORT = []
COMMON_PORTS = [22, 53, 80, 443, 445, 8080, 8443]


def banner():
    os.system("clear")
    print(G + """
╔══════════════════════════════════╗
║       DREAM CYBER SUITE          ║
║            VERSION 4.0           ║
║          NEON EDITION            ║
╚══════════════════════════════════╝
""" + RESET)


def save_report():
    if not REPORT:
        print(Y + "No report available." + RESET)
        return
    with open("dream_report.txt", "a", encoding="utf-8") as f:
        f.write("\n".join(REPORT) + "\n")
        f.write("=" * 40 + "\n")
    print(G + "[+] Report saved: dream_report.txt" + RESET)


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.0.2.1", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return None


def public_ip():
    print(C + "\n[ PUBLIC IP LOOKUP ]" + RESET)
    try:
        ip = requests.get("https://api.ipify.org", timeout=10).text.strip()
        print(G + "[+] Public IP: " + W + ip + RESET)
        lookup_public_ip(ip)
    except requests.RequestException as e:
        print(R + "[!] Network error: " + str(e) + RESET)


def lookup_public_ip(ip):
    try:
        address = ipaddress.ip_address(ip)
        if not address.is_global:
            print(Y + "[!] Public IP required." + RESET)
            return

        data = requests.get("https://ipwho.is/" + ip, timeout=12).json()
        if not data.get("success"):
            print(R + "[!] Lookup failed." + RESET)
            return

        conn = data.get("connection") or {}
        timezone = data.get("timezone") or {}
        fields = {
            "IP": data.get("ip"),
            "Country": data.get("country"),
            "Region": data.get("region"),
            "City": data.get("city"),
            "ISP": conn.get("isp"),
            "Organization": conn.get("org"),
            "Timezone": timezone.get("id"),
            "Latitude": data.get("latitude"),
            "Longitude": data.get("longitude"),
        }

        for key, value in fields.items():
            print(C + f"[+] {key}: " + W + str(value) + RESET)
            REPORT.append(f"{key}: {value}")

        lat, lon = data.get("latitude"), data.get("longitude")
        if lat is not None and lon is not None:
            maps = f"https://www.google.com/maps?q={lat},{lon}"
            print(G + "\n[+] Google Maps: " + W + maps + RESET)
            REPORT.append("Google Maps: " + maps)

        print(Y + "\n[!] IP location is approximate, not GPS." + RESET)
    except (requests.RequestException, ValueError, KeyError) as e:
        print(R + "[!] Lookup error: " + str(e) + RESET)


def private_ip():
    print(C + "\n[ PRIVATE IP INFORMATION ]" + RESET)
    ip = get_local_ip()
    if ip:
        network = ipaddress.ip_network(ip + "/24", strict=False)
        print(G + "[+] Your Local IP: " + W + ip + RESET)
        print(G + "[+] Detected /24 network: " + W + str(network) + RESET)
        REPORT.append("Local IP: " + ip)
    else:
        print(R + "[!] Could not detect local IP. Connect to Wi-Fi/LAN." + RESET)


def valid_local_target(ip):
    try:
        target = ipaddress.ip_address(ip)
        local = get_local_ip()
        if not target.is_private or target.version != 4 or not local:
            return False
        network = ipaddress.ip_network(local + "/24", strict=False)
        return target in network
    except ValueError:
        return False


def check_host(ip):
    open_ports = []
    for port in COMMON_PORTS:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.35)
                if sock.connect_ex((str(ip), port)) == 0:
                    open_ports.append(port)
        except OSError:
            pass
    return (str(ip), open_ports) if open_ports else None


def private_lookup():
    print(C + "\n[ PRIVATE IP CHECK ]" + RESET)
    ip = input("Enter Private IP: ").strip()
    if not valid_local_target(ip):
        print(R + "[!] Enter an IP in your own local /24 network." + RESET)
        return

    print(G + "[+] Valid private IP: " + W + ip + RESET)
    result = check_host(ip)
    if result:
        host, ports = result
        print(G + "[+] Responding TCP ports: " + W + str(ports) + RESET)
        REPORT.append(f"{host}: Open TCP ports {ports}")
    else:
        print(Y + "[!] No tested TCP ports responded." + RESET)
        print(Y + "Device may still be online; this is not proof it is offline." + RESET)


def network_scanner():
    print(C + "\n[ LOCAL NETWORK SCANNER ]" + RESET)
    local = get_local_ip()
    if not local:
        print(R + "[!] Connect to Wi-Fi/LAN first." + RESET)
        return

    network = ipaddress.ip_network(local + "/24", strict=False)
    print(G + "[+] Your network: " + W + str(network) + RESET)
    print(Y + "[!] Scans only your own detected local /24 network." + RESET)

    if input("Continue? (yes/no): ").strip().lower() != "yes":
        return

    print(C + "\n[+] Checking common TCP ports..." + RESET)
    targets = [ip for ip in network.hosts() if str(ip) != local]
    found = 0

    with ThreadPoolExecutor(max_workers=40) as executor:
        for result in executor.map(check_host, targets):
            if result:
                host, ports = result
                found += 1
                line = f"IP: {host} | Open TCP ports: {ports}"
                print(G + "[+] " + line + RESET)
                REPORT.append(line)

    print(Y + f"\n[+] Devices responding on tested ports: {found}" + RESET)
    print(Y + "Devices with all tested ports closed/filtered may not appear." + RESET)


def menu():
    while True:
        banner()
        print(C + """
[1] Public IP Lookup
[2] Private IP Information
[3] Private IP Scanner
[4] Local Network Scanner
[5] Save Scan Report
[6] Exit
""" + RESET)

        choice = input(G + "DREAM >> " + RESET).strip()
        if choice == "1":
            public_ip()
        elif choice == "2":
            private_ip()
        elif choice == "3":
            private_lookup()
        elif choice == "4":
            network_scanner()
        elif choice == "5":
            save_report()
        elif choice == "6":
            print(G + "\nThanks for using DREAM CYBER SUITE!" + RESET)
            sys.exit(0)
        else:
            print(R + "[!] Invalid option." + RESET)

        input(W + "\nPress Enter to continue..." + RESET)


if __name__ == "__main__":
    menu()
