require('dotenv').config();
const { Client, GatewayIntentBits, Events, EmbedBuilder } = require('discord.js');
const express = require('express');
const bodyParser = require('body-parser');
const winston = require('winston');
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

const ongoingAttacks = {};
const recentAlerts = []; // Store recent alerts

// Set up logging
const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
    ),
    transports: [
        new winston.transports.Console(),
        new winston.transports.File({ filename: 'combined.log' })
    ]
});

// API endpoint for DDoS alerts
app.post('/ddos-alert', (req, res) => {
    const { type, ip, location, startTime, endTime } = req.body;

    // Validate request data
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
        ongoingAttacks[ip] = { startTime, location };
        embed = new EmbedBuilder()
            .setTitle('🚨 **DDoS Attack Started** 🚨')
            .setDescription(`**IP:** ${ip}\n**Location:** ${location}\n**Start Time:** ${new Date(startTime).toLocaleString()}`)
            .setColor('#ff0000')
            .setThumbnail('http://localhost:3000/assets/alert-thumbnail.png') // Use local thumbnail
            .setFooter({ text: '⚠️ Immediate action required! ⚠️' })
            .setTimestamp();
        logger.info('DDoS attack started', { ip, location, startTime });
    } else if (type === 'end') {
        if (ongoingAttacks[ip]) {
            const attack = ongoingAttacks[ip];
            delete ongoingAttacks[ip];
            const endDate = new Date(endTime);
            const durationMs = endDate - new Date(attack.startTime);
            const durationFormatted = `${Math.floor(durationMs / (1000 * 60))} minutes ${Math.floor((durationMs % (1000 * 60)) / 1000)} seconds`;

            embed = new EmbedBuilder()
                .setTitle('✅ **DDoS Attack Ended** ✅')
                .setDescription(`**IP:** ${ip}\n**Location:** ${attack.location}\n**Start Time:** ${new Date(attack.startTime).toLocaleString()}\n**End Time:** ${endDate.toLocaleString()}\n**Duration:** ${durationFormatted}`)
                .setColor('#00ff00')
                .setThumbnail('http://localhost:3000/assets/alert-thumbnail.png') // Use local thumbnail
                .setFooter({ text: '🔍 The attack has ended. Monitor for any further issues.' })
                .setTimestamp();
            logger.info('DDoS attack ended', { ip, location: attack.location, startTime: attack.startTime, endTime, duration: durationFormatted });
        } else {
            embed = new EmbedBuilder()
                .setTitle('⚠️ **DDoS Attack Ended** ⚠️')
                .setDescription(`**IP:** ${ip} (no start record found)`)
                .setColor('#ff0000')
                .setThumbnail('http://localhost:3000/assets/alert-thumbnail.png') // Use local thumbnail
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
    // Keep only the latest 10 alerts
    if (recentAlerts.length > 10) recentAlerts.shift();

    channel.send({ embeds: [embed] });
    res.send('Alert received');
});

// API endpoints for dashboard
app.get('/status', (req, res) => {
    res.json({ status: client.user ? 'Online' : 'Offline' });
});

app.get('/ongoing-attacks', (req, res) => {
    res.json({ attacks: Object.entries(ongoingAttacks).map(([ip, details]) => ({ ip, ...details })) });
});

app.get('/recent-alerts', (req, res) => {
    res.json({ alerts: recentAlerts });
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
