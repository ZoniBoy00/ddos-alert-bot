# DDoS Monitoring Script

A Python script to monitor network traffic, ping, and packet loss for DDoS detection and send alerts to a specified API endpoint.

## Overview

This Python script monitors network traffic, ping response time, and packet loss. It sends alerts to an API endpoint when thresholds are exceeded. The script can run continuously to monitor network conditions and trigger alerts if DDoS attack patterns are detected.

## Features

- **Network Traffic Monitoring**: Measures network traffic in bytes per second.
- **Ping Monitoring**: Measures ping response time to a given host.
- **Packet Loss Monitoring**: Measures packet loss percentage to a given host.
- **Customizable Thresholds**: Allows configuration of thresholds for traffic, ping, and packet loss.
- **Alerts**: Sends alerts to a specified API endpoint when thresholds are exceeded.

## Installation

### Prerequisites

Ensure you have Python 3.6 or higher installed. You can download Python from [python.org](https://www.python.org/).

### Clone the Repository

```bash
git clone https://github.com/ZoniBoy00/ddos-alert-bot.git
cd ddos-alert-bot
```

### Install Dependencies

Install the required Python packages using pip:

```bash
pip install requests psutil
```

### Configuration

Modify the script's configuration section to set up your IP address, alert location, and thresholds. The configuration settings can be found in the script itself:

```python
ALERT_IP = '1.1.1.1'  # Replace with the IP address of the attacked server
ALERT_LOCATION = 'ALERT_LOACTION' # Replace with the attacked server location
TRAFFIC_THRESHOLD = 10000000  # Threshold for high traffic detection (in bytes/sec)
PING_THRESHOLD = 100  # Ping threshold in milliseconds
PACKET_LOSS_THRESHOLD = 10  # Packet loss threshold in percentage
CHECK_INTERVAL = 15  # Time between traffic checks (in seconds)
TRAFFIC_WINDOW = 120  # Window size for calculating average traffic (in seconds)
CHECK_METHOD = 'all'  # Default check method: 'all', 'traffic', 'ping', 'packet_loss'
```

**Important:** Proper configuration is crucial to avoid false alerts. Ensure you adjust the thresholds based on your network's normal traffic patterns and expected performance. 

For example:
- **Traffic Threshold**: Set this value based on your network's typical traffic levels to avoid false positives from regular traffic spikes.
- **Ping and Packet Loss Thresholds**: Choose thresholds that are appropriate for your network's latency and packet loss under normal conditions.

## Usage

### Running the Script

To start monitoring network traffic, ping, and packet loss, run:

```bash
python monitor.py
```

### Command-Line Arguments

- `--check-method`: Specifies the method(s) to use for checking. Options are `all`, `traffic`, `ping`, or `packet_loss`. Default is `all`.
- `--test`: Runs a test to send alerts. This will simulate a DDoS alert and should be used for testing purposes.

Example:

```bash
python monitor.py --check-method all
python monitor.py --test
```

## Avoiding False Alerts

1. **Understand Normal Traffic Patterns**: Monitor your network's typical traffic patterns and adjust the traffic threshold accordingly. If your network experiences regular spikes, set the threshold higher to avoid false positives.
2. **Fine-Tune Ping and Packet Loss Thresholds**: Set the ping and packet loss thresholds based on your network's normal performance. Adjust these values if you notice frequent false alerts during routine network usage.
3. **Test Configuration**: Use the `--test` flag to simulate alerts and ensure the script behaves as expected. This helps in tuning the thresholds and understanding the alert system.
