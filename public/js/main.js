document.addEventListener('DOMContentLoaded', () => {
    const statusMessage = document.getElementById('statusMessage');
    const totalAttacks = document.getElementById('totalAttacks');
    const averageResponseTime = document.getElementById('averageResponseTime');
    const blockedIPCount = document.getElementById('blockedIPCount');
    const attackList = document.getElementById('attackList');
    const alertList = document.getElementById('alertList');
    const blockedList = document.getElementById('blockedList');

    // Function to fetch bot status
    async function fetchBotStatus() {
        try {
            const response = await fetch('/status');
            const data = await response.json();
            statusMessage.textContent = data.status || 'Unknown';
        } catch (error) {
            console.error('Error fetching bot status:', error);
            statusMessage.textContent = 'Error';
        }
    }

    // Function to fetch ongoing attacks
    async function fetchOngoingAttacks() {
        try {
            const response = await fetch('/ongoing-attacks');
            const data = await response.json();
            attackList.innerHTML = data.attacks.map(attack =>
                `<li>IP: ${attack.ip}, Location: ${attack.location}, Start Time: ${new Date(attack.startTime).toLocaleString()}</li>`
            ).join('');
        } catch (error) {
            console.error('Error fetching ongoing attacks:', error);
            attackList.innerHTML = '<li>Error fetching attacks</li>';
        }
    }

    // Function to fetch recent alerts
    async function fetchRecentAlerts() {
        try {
            const response = await fetch('/recent-alerts');
            const data = await response.json();
            alertList.innerHTML = data.alerts.map(alert =>
                `<li>${alert.message}, Timestamp: ${new Date(alert.timestamp).toLocaleString()}</li>`
            ).join('');
        } catch (error) {
            console.error('Error fetching recent alerts:', error);
            alertList.innerHTML = '<li>Error fetching alerts</li>';
        }
    }

    // Function to fetch blocked IPs
    async function fetchBlockedIPs() {
        try {
            const response = await fetch('/blocked-ips');
            const data = await response.json();
            blockedList.innerHTML = data.blockedIPs.map(ip =>
                `<li>IP: ${ip}</li>`
            ).join('');
        } catch (error) {
            console.error('Error fetching blocked IPs:', error);
            blockedList.innerHTML = '<li>Error fetching blocked IPs</li>';
        }
    }

    // Function to fetch network statistics
    async function fetchNetworkStats() {
        try {
            const response = await fetch('/network-stats');
            const data = await response.json();
            totalAttacks.textContent = data.totalAttacks;
            averageResponseTime.textContent = `${data.averageResponseTime} ms`;
            blockedIPCount.textContent = data.blockedIPCount;
        } catch (error) {
            console.error('Error fetching network statistics:', error);
            totalAttacks.textContent = 'Error';
            averageResponseTime.textContent = 'Error';
            blockedIPCount.textContent = 'Error';
        }
    }

    // Initial data fetch
    fetchBotStatus();
    fetchOngoingAttacks();
    fetchRecentAlerts();
    fetchBlockedIPs();
    fetchNetworkStats();

    // Refresh data every 60 seconds
    setInterval(() => {
        fetchBotStatus();
        fetchOngoingAttacks();
        fetchRecentAlerts();
        fetchBlockedIPs();
        fetchNetworkStats();
    }, 60000);
});
