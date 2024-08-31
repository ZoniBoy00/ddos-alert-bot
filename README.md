# DDoS Alert Bot

A bot to monitor and manage DDoS attacks with a web dashboard.

## Overview

The DDoS Alert Bot is designed to monitor and manage DDoS attacks by sending alerts to a Discord channel and providing a web dashboard for monitoring ongoing attacks and recent alerts. It utilizes the Discord.js library to interact with Discord and Express.js to serve a web interface.

## Features

- **Discord Integration**: Sends DDoS attack alerts and statuses to a specified Discord channel.
- **Web Dashboard**: Provides real-time updates on ongoing attacks and recent alerts through a web-based interface.
- **Logging**: Uses Winston for logging and tracking events.

## Installation

### Prerequisites

Ensure you have Node.js and npm installed. You can download Node.js from [nodejs.org](https://nodejs.org/).

### Clone the Repository

```bash
git clone https://github.com/ZoniBoy00/ddos-alert-bot.git
cd ddos-alert-bot
```

### Install Dependencies

```bash
npm install
```

### Configuration

Create a .env file in the root directory of the project with the following content:

```dotenv
BOT_TOKEN=your_discord_bot_token
CHANNEL_ID=your_discord_channel_id
API_PORT=3000
```

- `BOT_TOKEN`: Your Discord bot token.
- `CHANNEL_ID`: The ID of the Discord channel where alerts will be sent.
- `API_PORT`: (Optional) The port on which the API server will run. Default is 3000.

## Usage

### Starting the Bot

To start the bot and the web server, run:

```bash
npm start
```

The bot will log in to Discord and start listening for incoming alerts. The web server will be available on [http://localhost:3000](http://localhost:3000).

### API Endpoints

- **POST /ddos-alert**: Receives DDoS alerts and sends them to the Discord channel.

  **Body Parameters:**
  - `type`: start or end (indicates the start or end of an attack)
  - `ip`: IP address of the attacked server
  - `location`: Location of the attack
  - `startTime`: Start time of the attack (ISO 8601 format)
  - `endTime`: End time of the attack (ISO 8601 format, optional if type is start)

- **GET /status**: Returns the bot's status (Online/Offline).

- **GET /ongoing-attacks**: Returns a list of ongoing attacks with their details.

- **GET /recent-alerts**: Returns a list of recent alerts (currently not implemented).

### Web Dashboard

The web dashboard is accessible at [http://localhost:3000](http://localhost:3000). It includes:

- **Bot Status**: Shows whether the bot is online or offline.
- **Ongoing Attacks**: Displays current ongoing attacks.
- **Recent Alerts**: Lists recent alerts (if implemented).

## Integrating with FiveM Servers, VPS Servers, or Domains

To integrate the DDoS Alert Bot with FiveM servers, VPS servers, or domains for receiving notifications, follow these steps:

### FiveM Server

- **Create a Webhook Endpoint**: Set up a webhook endpoint on your server that can send HTTP POST requests to your DDoS Alert Bot's /ddos-alert endpoint. The webhook should trigger an alert when it detects a DDoS attack.
- **Configure Webhook**: In your FiveM server configuration or scripts, configure the webhook to send the required data (IP, location, start time, etc.) to your DDoS Alert Bot.

#### Example FiveM Lua Script

Here's a basic example of a Lua script for FiveM that sends a POST request to the DDoS Alert Bot when an attack is detected:

```lua
-- FiveM Lua Script Example

local webhookURL = 'http://localhost:3000/ddos-alert' -- Replace with your DDoS Alert Bot URL

-- Function to send alert
function sendDdosAlert(type, ip, location, startTime, endTime)
    local data = {
        type = type,
        ip = ip,
        location = location,
        startTime = startTime,
        endTime = endTime
    }

    PerformHttpRequest(webhookURL, function(errorCode, responseText, headers)
        if errorCode == 200 then
            print("DDoS alert sent successfully.")
        else
            print("Failed to send DDoS alert: " .. errorCode)
        end
    end, 'POST', json.encode(data), { ['Content-Type'] = 'application/json' })
end

-- Example usage
-- sendDdosAlert('start', '192.168.1.1', 'New York, USA', '2024-08-31T12:00:00Z')
-- sendDdosAlert('end', '192.168.1.1', 'New York, USA', '2024-08-31T14:00:00Z', '2024-08-31T14:00:00Z')
```

### VPS Server

- **Monitor Network Traffic**: Set up monitoring tools or scripts on your VPS that can detect unusual traffic patterns indicative of a DDoS attack.
- **Send Alerts**: Configure these monitoring tools to send HTTP POST requests to your DDoS Alert Bot's /ddos-alert endpoint with the relevant attack details.

### Domain Monitoring

- **Use a Domain Monitoring Service**: Utilize domain monitoring services that can detect DDoS attacks or other threats to your domain.
- **Configure Alerts**: Configure the monitoring service to send HTTP POST requests to your DDoS Alert Bot's /ddos-alert endpoint when it detects a potential DDoS attack.

### Example Alert Payload

Here's an example of how the payload should look when sending a DDoS alert to the /ddos-alert endpoint:

```json
{
  "type": "start",
  "ip": "192.168.1.1",
  "location": "New York, USA",
  "startTime": "2024-08-31T12:00:00Z"
}
```

For an attack end alert:

```json
{
  "type": "end",
  "ip": "192.168.1.1",
  "endTime": "2024-08-31T14:00:00Z"
}
```

## Contributing

Feel free to submit issues and pull requests. Contributions are welcome!

- Fork the repository
- Create a new branch (git checkout -b feature-branch)
- Make your changes
- Commit your changes (git commit -am 'Add new feature')
- Push to the branch (git push origin feature-branch)
- Create a new Pull Request

## License

This project is licensed under the [MIT License.](https://github.com/ZoniBoy00/ddos-alert-bot/blob/main/LICENSE)
