import requests
import time
import psutil
import subprocess
import platform
from datetime import datetime
from collections import defaultdict, deque
import argparse

# API Endpoints
API_URL_ALERT = 'http://localhost:3000/ddos-alert'
API_URL_IP_BLOCKED = 'http://localhost:3000/ip-blocked'
API_URL_NETWORK_STATS = 'http://localhost:3000/network-stats'

# Configuration settings
ALERT_IP = '1.1.1.1'  # Replace with the IP address of the attacked server
ALERT_LOCATION = 'ALERT_LOCATION'  # Replace with the attacked server location
TRAFFIC_THRESHOLD = 10000000  # Threshold for high traffic detection (in bytes/sec)
PING_THRESHOLD = 100  # Ping threshold in milliseconds
PACKET_LOSS_THRESHOLD = 10  # Packet loss threshold in percentage
CHECK_INTERVAL = 15  # Time between traffic checks (in seconds)
TRAFFIC_WINDOW = 120  # Window size for calculating average traffic (in seconds)
CHECK_METHOD = 'all'  # Default check method: 'all', 'traffic', 'ping', 'packet_loss'

# Firewall Configuration
BLOCK_DURATION = 3600  # Block IP for 1 hour (in seconds)
THRESHOLD_CONNECTIONS = 100  # Max allowed connections from a single IP
SUSPICIOUS_CONNECTIONS_THRESHOLD = 10  # Suspicious connections from different IPs within a short interval
DETECTION_WINDOW = 60  # Time window in seconds for detection of suspicious activities

# Tracking data
blocked_ips = defaultdict(float)
suspicious_ips = defaultdict(lambda: deque(maxlen=SUSPICIOUS_CONNECTIONS_THRESHOLD))

def get_current_time():
    """Return the current time in ISO 8601 format."""
    return datetime.utcnow().isoformat() + 'Z'

def send_alert(alert_type, ip, location, start_time, end_time=None):
    """Send a DDoS alert to the API endpoint."""
    if alert_type not in ['start', 'end']:
        print(f'Invalid alert type: {alert_type}')
        return

    payload = {
        'type': alert_type,
        'ip': ip,
        'location': location,
        'startTime': start_time,
    }
    if end_time:
        payload['endTime'] = end_time

    try:
        response = requests.post(API_URL_ALERT, json=payload)
        response.raise_for_status()
        print(f'DDoS alert sent successfully: {alert_type}')
    except requests.RequestException as e:
        print(f'Error sending DDoS alert: {e}')

def notify_ip_blocked(ip):
    """Notify about blocked IP."""
    payload = {'ip': ip}
    try:
        response = requests.post(API_URL_IP_BLOCKED, json=payload)
        response.raise_for_status()
        print(f'IP block notification sent successfully for {ip}')
    except requests.RequestException as e:
        print(f'Error sending IP block notification: {e}')

def manage_ip(ip, action):
    """Block or unblock the specified IP using the appropriate firewall command for the OS."""
    system = platform.system()
    try:
        if system == 'Windows':
            if action == 'block':
                subprocess.run(['netsh', 'advfirewall', 'firewall', 'add', 'rule', f'name=Block_{ip}', 'dir=in', 'action=block', 'remoteip='+ip], check=True)
            elif action == 'unblock':
                subprocess.run(['netsh', 'advfirewall', 'firewall', 'delete', 'rule', f'name=Block_{ip}'], check=True)
            else:
                print("Unsupported action for Windows.")
                return

        elif system == 'Linux':
            if action == 'block':
                subprocess.run(['iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP'], check=True)
            elif action == 'unblock':
                subprocess.run(['iptables', '-D', 'INPUT', '-s', ip, '-j', 'DROP'], check=True)
            else:
                print("Unsupported action for Linux.")
                return

        elif system == 'Darwin':  # macOS
            if action == 'block':
                subprocess.run(['sudo', 'pfctl', '-t', 'blocked_ips', '-T', 'add', ip], check=True)
            elif action == 'unblock':
                subprocess.run(['sudo', 'pfctl', '-t', 'blocked_ips', '-T', 'delete', ip], check=True)
            else:
                print("Unsupported action for macOS.")
                return

        else:
            print(f'Unsupported OS for IP management: {system}')
            return

        if action == 'block':
            blocked_ips[ip] = time.time() + BLOCK_DURATION
            print(f"IP {ip} blocked.")
            notify_ip_blocked(ip)
        elif action == 'unblock':
            blocked_ips.pop(ip, None)
            print(f"IP {ip} unblocked.")

    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def monitor_connections():
    """Monitor active connections and block suspicious IPs."""
    while True:
        result = subprocess.run(['netstat', '-ntu'], capture_output=True, text=True)
        lines = result.stdout.splitlines()

        ip_connections = defaultdict(int)
        for line in lines:
            parts = line.split()
            if len(parts) > 4:
                ip = parts[4].split(':')[0]
                ip_connections[ip] += 1

        for ip, connections in ip_connections.items():
            if connections > THRESHOLD_CONNECTIONS and ip not in blocked_ips:
                print(f"Alert: {connections} connections from {ip} detected!")
                manage_ip(ip, 'block')
            elif ip in blocked_ips and time.time() > blocked_ips[ip]:
                manage_ip(ip, 'unblock')

            # Track suspicious IPs to avoid false positives
            suspicious_ips[ip].append(time.time())
            if len(suspicious_ips[ip]) >= SUSPICIOUS_CONNECTIONS_THRESHOLD:
                time_diff = suspicious_ips[ip][-1] - suspicious_ips[ip][0]
                if time_diff < DETECTION_WINDOW and ip not in blocked_ips:
                    print(f"Suspicious behavior detected from {ip} over {time_diff} seconds!")
                    manage_ip(ip, 'block')
                elif time.time() > blocked_ips.get(ip, 0):
                    manage_ip(ip, 'unblock')

        time.sleep(CHECK_INTERVAL)

def get_network_traffic():
    """Get the current network traffic in bytes."""
    net_io = psutil.net_io_counters()
    return net_io.bytes_sent + net_io.bytes_recv

def get_ping(host):
    """Get the ping response time to a given host."""
    system = platform.system()
    command = None

    if system == 'Windows':
        command = ['ping', '-n', '1', host]
    elif system in ['Linux', 'Darwin']:
        command = ['ping', '-c', '1', host]
    else:
        print(f'Unsupported OS: {system}')
        return None

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            output = result.stdout
            if system == 'Windows':
                start_index = output.find('time=')
                if start_index == -1:
                    return None
                end_index = output.find('ms', start_index)
                if end_index == -1:
                    return None
                ping_time = float(output[start_index + len('time='):end_index])
            else:  # Linux/macOS
                start_index = output.find('time=')
                if start_index == -1:
                    return None
                end_index = output.find(' ms', start_index)
                if end_index == -1:
                    return None
                ping_time = float(output[start_index + len('time='):end_index])
            return ping_time
        return None
    except subprocess.TimeoutExpired:
        print('Ping command timed out.')
        return None
    except Exception as e:
        print(f'Error getting ping: {e}')
        return None

def get_packet_loss(host):
    """Get the packet loss percentage to a given host."""
    system = platform.system()
    command = None

    if system == 'Windows':
        command = ['ping', '-n', '10', host]
    elif system in ['Linux', 'Darwin']:
        command = ['ping', '-c', '10', host]
    else:
        print(f'Unsupported OS: {system}')
        return None

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            output = result.stdout
            if system == 'Windows':
                start_index = output.find('Lost = ')
                if start_index == -1:
                    return None
                end_index = output.find(' ', start_index + len('Lost = '))
                if end_index == -1:
                    return None
                packet_loss = int(output[start_index + len('Lost = '):end_index])
            else:  # Linux/macOS
                start_index = output.find('packet loss')
                if start_index == -1:
                    return None
                loss_str = output[start_index:].split(',')[0]
                packet_loss = int(loss_str.split()[0].strip('%'))
            return packet_loss
        return None
    except subprocess.TimeoutExpired:
        print('Packet loss command timed out.')
        return None
    except Exception as e:
        print(f'Error getting packet loss: {e}')
        return None

def get_network_stats():
    """Fetch network statistics from the API."""
    try:
        response = requests.get(API_URL_NETWORK_STATS)
        response.raise_for_status()
        stats = response.json()
        return stats
    except requests.RequestException as e:
        print(f'Error fetching network statistics: {e}')
        return None

def test_alerts():
    """Test sending alerts to ensure the system is working."""
    print('Starting test...')
    start_time = get_current_time()
    send_alert('start', ALERT_IP, ALERT_LOCATION, start_time)
    time.sleep(5)
    end_time = get_current_time()
    send_alert('end', ALERT_IP, ALERT_LOCATION, start_time, end_time)
    print('Test completed.')

def monitor_traffic():
    """Monitor network traffic, ping, and packet loss, and send alerts if thresholds are exceeded."""
    start_time = None
    traffic_window = []

    while True:
        # Measure traffic over a short interval
        start_measure = time.time()
        initial_bytes = get_network_traffic()
        time.sleep(CHECK_INTERVAL)
        final_bytes = get_network_traffic()
        interval_traffic = final_bytes - initial_bytes

        # Append to window and maintain window size
        traffic_window.append(interval_traffic)
        if len(traffic_window) > TRAFFIC_WINDOW:
            traffic_window.pop(0)

        average_traffic = sum(traffic_window) / len(traffic_window)
        print(f'Network traffic measured over {CHECK_INTERVAL} seconds: {interval_traffic} bytes')
        print(f'Average traffic over {TRAFFIC_WINDOW} intervals: {average_traffic} bytes/sec')

        # Check ping and packet loss
        ping_time = get_ping(ALERT_IP) if CHECK_METHOD in ['ping', 'all'] else None
        packet_loss = get_packet_loss(ALERT_IP) if CHECK_METHOD in ['packet_loss', 'all'] else None

        print(f'Current ping time: {ping_time} ms' if ping_time is not None else 'Ping test failed')
        print(f'Current packet loss: {packet_loss}%' if packet_loss is not None else 'Packet loss test failed')

        # Determine whether to send alerts
        alert_needed = False
        if CHECK_METHOD in ['traffic', 'all'] and average_traffic > TRAFFIC_THRESHOLD:
            print('High traffic detected!')
            alert_needed = True
        if CHECK_METHOD in ['ping', 'all'] and ping_time is not None and ping_time > PING_THRESHOLD:
            print('High ping detected!')
            alert_needed = True
        if CHECK_METHOD in ['packet_loss', 'all'] and packet_loss is not None and packet_loss > PACKET_LOSS_THRESHOLD:
            print('High packet loss detected!')
            alert_needed = True

        # Send start alert if needed
        if alert_needed and not start_time:
            start_time = get_current_time()
            send_alert('start', ALERT_IP, ALERT_LOCATION, start_time)

        # Send end alert if conditions are normal
        if not alert_needed and start_time:
            end_time = get_current_time()
            print('Traffic, ping, and packet loss are normal. Sending end alert.')
            send_alert('end', ALERT_IP, ALERT_LOCATION, start_time, end_time)
            start_time = None

        # Monitor and block suspicious IPs
        monitor_connections()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Monitor network traffic, ping, and packet loss for DDoS detection and IP blocking.')
    parser.add_argument('--check-method', choices=['all', 'traffic', 'ping', 'packet_loss'], default='all', help='Method(s) to use for checking (default: all)')
    parser.add_argument('--test', action='store_true', help='Run a test to send alerts')
    args = parser.parse_args()

    CHECK_METHOD = args.check_method

    if args.test:
        test_alerts()
    else:
        try:
            monitor_traffic()
        except KeyboardInterrupt:
            print("Monitoring stopped by user.")
