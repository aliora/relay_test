const net = require('net');

class JetsonEmbed {
    constructor() {
        this.BINARY_COMMANDS = {
            '1': '1',
            '2': '2',
            '3': '3',
            '4': '4',
            '5': '5'
        };
    }

    triggerRelays(ip, port, relayNumber = null) {
        return new Promise((resolve, reject) => {
            const client = new net.Socket();

            client.connect(port, ip, () => {
                let commandToSend;

                if (relayNumber !== null) {
                    if (!this.BINARY_COMMANDS[relayNumber]) {
                        console.error("Invalid relay number");
                        return reject(new Error("Invalid relay number"));
                    }
                    commandToSend = this.BINARY_COMMANDS[relayNumber];
                } else {
                    console.error("No relay number provided");
                    return reject(new Error("No relay number provided"));
                }

                // Komutu gönder
                client.write(commandToSend, () => {
                    console.log(`Relay command sent: ${commandToSend}`);
                });
            });

            client.on('data', (data) => {
                console.log(`Received data: ${data.toString()}`);
                client.end();
                resolve(true);
            });

            client.on('error', (err) => {
                console.error(`Connection error: ${err.message}`);
                reject(false);
            });

            client.on('end', () => {
                console.log('Connection ended');
            });
        });
    }
}

module.exports = JetsonEmbed;
