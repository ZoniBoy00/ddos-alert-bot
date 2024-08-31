import requests
import time
import psutil
import subprocess
import platform
from datetime import datetime
import argparse

# API Endpoint for DDoS Alert Bot
API_URL = 'http://localhost:3000/ddos-alert'

# Configuration settings
ALERT_IP = '1.1.1.1'  # Replace with the IP address of the attacked server
ALERT_LOCATION = 'ALERT_LOCATION' # Replace with the attacked server location
TRAFFIC_THRESHOLD = 10000000  # Threshold for high traffic detection (in bytes/sec)
PING_THRESHOLD = 100  # Ping threshold in milliseconds
PACKET_LOSS_THRESHOLD = 10  # Packet loss threshold in percentage
CHECK_INTERVAL = 15  # Time between traffic checks (in seconds), reduced for quicker checks
TRAFFIC_WINDOW = 120  # Window size for calculating average traffic (in seconds), reduced for quicker updates
CHECK_METHOD = 'all'  # Default check method: 'all', 'traffic', 'ping', 'packet_loss'

def get_current_time():
    """Return the current time in ISO 8601 format."""
    return datetime.utcnow().isoformat() + 'Z'

def send_alert(alert_type, ip, location, start_time, end_time=None):
    """
    Send a DDoS alert to the API endpoint.
    
    :param alert_type: Type of alert ('start' or 'end')
    :param ip: IP address of the attacked server
    :param location: Location of the attack
    :param start_time: Start time of the attack in ISO 8601 format
    :param end_time: End time of the attack in ISO 8601 format (optional)
    """
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
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
        print(f'DDoS alert sent successfully: {alert_type}')
    except requests.RequestException as e:
        print(f'Error sending DDoS alert: {e}')
        if response is not None:
            print(f'Response content: {response.text}')  # Print the response content for debugging

def get_network_traffic():
    """
    Get the current network traffic in bytes per second.
    Returns the network traffic measurement.
    """
    net_io = psutil.net_io_counters()
    return net_io.bytes_sent + net_io.bytes_recv

def get_ping(host):
    """
    Get the ping response time to a given host.
    Returns ping time in milliseconds.
    """
    system = platform.system()
    command = None
    
    if system == 'Windows':
        command = ['ping', '-n', '1', host]
    elif system in ['Linux', 'Darwin']:  # macOS is 'Darwin'
        command = ['ping', '-c', '1', host]
    else:
        print(f'Unsupported OS: {system}')
        return None

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=3)  # Short timeout for quicker results
        if result.returncode == 0:
            output = result.stdout
            if system == 'Windows':
                # Windows output: Reply from 192.168.1.1: bytes=32 time=12ms TTL=64
                start_index = output.find('time=')
                if start_index == -1:
                    return None
                end_index = output.find('ms', start_index)
                if end_index == -1:
                    return None
                ping_time = float(output[start_index + len('time='):end_index])
                return ping_time
            else:
                # Linux/Mac output: 64 bytes from 192.168.1.1: icmp_seq=1 ttl=64 time=12.0 ms
                start_index = output.find('time=')
                if start_index == -1:
                    return None
                end_index = output.find(' ', start_index)
                if end_index == -1:
                    end_index = output.find('ms', start_index)
                if end_index == -1:
                    return None
                ping_time = float(output[start_index + len('time='):end_index].strip())
                return ping_time
        else:
            return None
    except Exception as e:
        print(f'Error getting ping: {e}')
        return None

def get_packet_loss(host):
    """
    Get the packet loss percentage to a given host.
    Returns packet loss percentage.
    """
    try:
        system = platform.system()
        command = None

        if system == 'Windows':
            command = ['ping', '-n', '10', host]
        elif system in ['Linux', 'Darwin']:
            command = ['ping', '-c', '10', host]
        else:
            print(f'Unsupported OS: {system}')
            return None
        
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)  # Short timeout for quicker results
        if result.returncode == 0:
            output = result.stdout
            if system == 'Windows':
                # Windows output: Packets: Sent = 10, Received = 10, Lost = 0 (0% loss)
                start_index = output.find('Lost =')
                if start_index == -1:
                    return None
                end_index = output.find('(', start_index)
                if end_index == -1:
                    return None
                packet_loss = int(output[start_index + len('Lost ='):end_index].split('%')[0].strip())
                return packet_loss
            else:
                # Linux/Mac output: 10 packets transmitted, 10 received, 0% packet loss
                start_index = output.find('packet loss')
                if start_index == -1:
                    return None
                packet_loss = int(output[start_index - 5:start_index].strip())
                return packet_loss
        else:
            return None
    except Exception as e:
        print(f'Error getting packet loss: {e}')
        return None

def test_alerts():
    """
    Test sending alerts to ensure the system is working.
    """
    print('Starting test...')
    start_time = get_current_time()
    send_alert('start', ALERT_IP, ALERT_LOCATION, start_time)
    time.sleep(5)  # Shorter wait for test
    end_time = get_current_time()
    send_alert('end', ALERT_IP, ALERT_LOCATION, start_time, end_time)
    print('Test completed.')

def monitor_traffic():
    """
    Monitor network traffic, ping, and packet loss, and send alerts if thresholds are exceeded.
    """
    start_time = None
    traffic_window = []

    while True:
        # Measure traffic over a short interval
        start_measure = time.time()
        initial_bytes = get_network_traffic()
        time.sleep(CHECK_INTERVAL)  # Wait for the interval
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
        if CHECK_METHOD in ['ping', 'all']:
            ping_time = get_ping(ALERT_IP)
            print(f'Current ping time: {ping_time} ms' if ping_time is not None else 'Ping test failed')
        
        if CHECK_METHOD in ['packet_loss', 'all']:
            packet_loss = get_packet_loss(ALERT_IP)
            print(f'Current packet loss: {packet_loss}%' if packet_loss is not None else 'Packet loss test failed')

        # Determine whether to send alerts
        alert_needed = False
        if CHECK_METHOD in ['traffic', 'all'] and average_traffic > TRAFFIC_THRESHOLD:
            print('High traffic detected!')
            alert_needed = True
            if not start_time:
                start_time = get_current_time()
                send_alert('start', ALERT_IP, ALERT_LOCATION, start_time)
        if CHECK_METHOD in ['ping', 'all'] and ping_time is not None and ping_time > PING_THRESHOLD:
            print('High ping detected!')
            alert_needed = True
            if not start_time:
                start_time = get_current_time()
                send_alert('start', ALERT_IP, ALERT_LOCATION, start_time)
        if CHECK_METHOD in ['packet_loss', 'all'] and packet_loss is not None and packet_loss > PACKET_LOSS_THRESHOLD:
            print('High packet loss detected!')
            alert_needed = True
            if not start_time:
                start_time = get_current_time()
                send_alert('start', ALERT_IP, ALERT_LOCATION, start_time)

        # If traffic, ping, or packet loss is normal, end the alert
        if not alert_needed and start_time:
            end_time = get_current_time()
            print('Traffic, ping, and packet loss are normal. Sending end alert.')
            send_alert('end', ALERT_IP, ALERT_LOCATION, start_time, end_time)
            start_time = None

        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Monitor network traffic, ping, and packet loss for DDoS detection.')
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
