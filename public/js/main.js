document.addEventListener('DOMContentLoaded', () => {
    const statusMessage = document.getElementById('statusMessage');
    const attackList = document.getElementById('attackList');
    const alertList = document.getElementById('alertList');

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

    // Initial data fetch
    fetchBotStatus();
    fetchOngoingAttacks();
    fetchRecentAlerts();
});
