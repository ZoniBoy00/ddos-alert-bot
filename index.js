require('dotenv').config();
const { Client, GatewayIntentBits, Events, EmbedBuilder } = require('discord.js');
const express = require('express');
const bodyParser = require('body-parser');
const winston = require('winston');
const fs = require('fs');
const path = require('path');

const app = express();
const port = process.env.API_PORT || 3000;

// Set up Discord client
const client = new Client({ 
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent
    ] 
});

// Serve static files from the public directory
app.use(express.static(path.join(__dirname, 'public')));

// Body parser middleware
app.use(bodyParser.json());

// Define file paths
const logsDir = path.resolve(__dirname, 'logs');
const ongoingAttacksPath = path.resolve(logsDir, 'ongoingAttacks.json');
const blockedIPsPath = path.resolve(logsDir, 'blockedIPs.json');

// Ensure logs directory exists
if (!fs.existsSync(logsDir)) {
    fs.mkdirSync(logsDir, { recursive: true });
}

// Helper functions for file operations
const readJSONFile = (filePath) => {
    try {
        if (fs.existsSync(filePath)) {
            const data = fs.readFileSync(filePath, 'utf-8');
            return JSON.parse(data);
        }
        return [];
    } catch (error) {
        console.error(`Error reading JSON file at ${filePath}:`, error);
        return [];
    }
};

const writeJSONFile = (filePath, data) => {
    try {
        fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
    } catch (error) {
        console.error(`Error writing JSON file at ${filePath}:`, error);
    }
};

// Initialize file data
let ongoingAttacks = readJSONFile(ongoingAttacksPath);
let blockedIPs = readJSONFile(blockedIPsPath);
let recentAlerts = [];

// Set up logging
const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
    ),
    transports: [
        new winston.transports.Console(),
        new winston.transports.File({ filename: path.join(logsDir, 'combined.log') })
    ]
});

// Check resolved paths
console.log('Logs directory:', logsDir);
console.log('Ongoing attacks path:', ongoingAttacksPath);
console.log('Blocked IPs path:', blockedIPsPath);

// API endpoint for DDoS alerts
app.post('/ddos-alert', (req, res) => {
    const { type, ip, location, startTime, endTime } = req.body;

    if (!type || !ip || !location || !startTime) {
        logger.error('Invalid request data', { type, ip, location, startTime, endTime });
        return res.status(400).send('Type, IP, location, and startTime are required');
    }

    const channel = client.channels.cache.get(process.env.CHANNEL_ID);
    if (!channel) {
        logger.error('Discord channel not found', { CHANNEL_ID: process.env.CHANNEL_ID });
        return res.status(500).send('Discord channel not found');
    }

    let embed;
    if (type === 'start') {
        ongoingAttacks.push({ ip, location, startTime });
        writeJSONFile(ongoingAttacksPath, ongoingAttacks);
        embed = new EmbedBuilder()
            .setTitle('🚨 **DDoS Attack Started** 🚨')
            .setDescription(`**IP:** ${ip}\n**Location:** ${location}\n**Start Time:** ${new Date(startTime).toLocaleString()}`)
            .setColor('#ff0000')
            .setThumbnail('http://localhost:3000/assets/alert-thumbnail.png')
            .setFooter({ text: '⚠️ Immediate action required! ⚠️' })
            .setTimestamp();
        logger.info('DDoS attack started', { ip, location, startTime });
    } else if (type === 'end') {
        const index = ongoingAttacks.findIndex(attack => attack.ip === ip);
        if (index !== -1) {
            const attack = ongoingAttacks[index];
            ongoingAttacks.splice(index, 1);
            writeJSONFile(ongoingAttacksPath, ongoingAttacks);
            const endDate = new Date(endTime);
            const durationMs = endDate - new Date(attack.startTime);
            const durationFormatted = `${Math.floor(durationMs / (1000 * 60))} minutes ${Math.floor((durationMs % (1000 * 60)) / 1000)} seconds`;

            embed = new EmbedBuilder()
                .setTitle('✅ **DDoS Attack Ended** ✅')
                .setDescription(`**IP:** ${ip}\n**Location:** ${attack.location}\n**Start Time:** ${new Date(attack.startTime).toLocaleString()}\n**End Time:** ${endDate.toLocaleString()}\n**Duration:** ${durationFormatted}`)
                .setColor('#00ff00')
                .setThumbnail('http://localhost:3000/assets/alert-thumbnail.png')
                .setFooter({ text: '🔍 The attack has ended. Monitor for any further issues.' })
                .setTimestamp();
            logger.info('DDoS attack ended', { ip, location: attack.location, startTime: attack.startTime, endTime, duration: durationFormatted });
        } else {
            embed = new EmbedBuilder()
                .setTitle('⚠️ **DDoS Attack Ended** ⚠️')
                .setDescription(`**IP:** ${ip} (no start record found)`)
                .setColor('#ff0000')
                .setThumbnail('http://localhost:3000/assets/alert-thumbnail.png')
                .setFooter({ text: '🚨 No start record found for this IP. Investigate further.' })
                .setTimestamp();
            logger.warn('DDoS attack end received with no start record', { ip, endTime });
        }
    } else {
        logger.error('Invalid type received', { type });
        return res.status(400).send('Invalid type. Use "start" or "end".');
    }

    // Add to recent alerts
    const alert = {
        message: type === 'start' ? 
            `DDoS attack started from IP ${ip} at ${new Date(startTime).toLocaleString()}` :
            `DDoS attack ended from IP ${ip} at ${new Date(endTime).toLocaleString()}`,
        timestamp: new Date().toISOString()
    };
    recentAlerts.push(alert);
    if (recentAlerts.length > 10) recentAlerts.shift();

    channel.send({ embeds: [embed] });
    res.send('Alert received');
});

// API endpoint for IP block notifications
app.post('/ip-blocked', (req, res) => {
    const { ip, timestamp } = req.body;

    if (!ip || !timestamp) {
        logger.error('IP address and timestamp required for blocking notification');
        return res.status(400).send('IP address and timestamp are required');
    }

    // Add IP to the blocked list
    if (!blockedIPs.includes(ip)) {
        blockedIPs.push(ip);
        writeJSONFile(blockedIPsPath, blockedIPs);
    }

    const channel = client.channels.cache.get(process.env.CHANNEL_ID);
    if (!channel) {
        logger.error('Discord channel not found', { CHANNEL_ID: process.env.CHANNEL_ID });
        return res.status(500).send('Discord channel not found');
    }

    const embed = new EmbedBuilder()
        .setTitle('🚫 **IP Blocked** 🚫')
        .setDescription(`**IP:** ${ip}\n**Status:** Blocked\n**Timestamp:** ${new Date(timestamp).toLocaleString()}`)
        .setColor('#ff0000')
        .setThumbnail('http://localhost:3000/assets/alert-thumbnail.png')
        .setFooter({ text: '⚠️ Action taken due to suspicious activity. ⚠️' })
        .setTimestamp();

    channel.send({ embeds: [embed] });
    res.send('IP block notification sent');
});

// API endpoints for dashboard
app.get('/status', (req, res) => {
    res.json({ status: client.user ? 'Online' : 'Offline' });
});

app.get('/ongoing-attacks', (req, res) => {
    res.json({ attacks: ongoingAttacks });
});

app.get('/recent-alerts', (req, res) => {
    res.json({ alerts: recentAlerts });
});

app.get('/blocked-ips', (req, res) => {
    res.json({ blockedIPs });
});

// API endpoint for network statistics
app.get('/network-stats', (req, res) => {
    // Calculate total attacks
    const totalAttacks = ongoingAttacks.length;

    // Calculate average response time
    let averageResponseTime = 'N/A';
    if (recentAlerts.length > 0) {
        const responseTimes = recentAlerts.map(alert => {
            const timestamp = new Date(alert.timestamp).getTime();
            return timestamp; // Assuming alerts have timestamps for calculation
        });
        const totalResponseTime = responseTimes.reduce((acc, curr) => acc + curr, 0);
        averageResponseTime = (totalResponseTime / responseTimes.length).toFixed(2);
    }

    // Get blocked IPs count
    const blockedIPCount = blockedIPs.length;

    // Send the statistics
    res.json({
        totalAttacks,
        averageResponseTime,
        blockedIPCount
    });
});

// Start API server
app.listen(port, () => {
    logger.info(`API server running at http://localhost:${port}`);
});

// Start Discord client
client.once(Events.ClientReady, async () => {
    logger.info(`Logged in as ${client.user.tag}`);

    // Custom status update
    setInterval(async () => {
        const statuses = [
            '🔍 Monitoring DDoS attacks',
            '📨 Handling incoming alerts',
            '🛡️ Ensuring server security',
            '🌐 Protecting our network'
        ];
        const status = statuses[Math.floor(Math.random() * statuses.length)];
        try {
            await client.user.setPresence({
                activities: [{ name: status, type: 3 }], // Type 3 = WATCHING
                status: 'online'
            });
            logger.info(`Status updated to: ${status}`);
        } catch (error) {
            logger.error('Error updating status:', error);
        }
    }, 60000); // Change status every minute
});

client.login(process.env.BOT_TOKEN);
