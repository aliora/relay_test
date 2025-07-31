const net = require('net');

class Rn62_IO {
    constructor() {
        this.BINARY_COMMANDS = {
            '1': Buffer.from([99, 3, 3, 7, 7, 9, 9, 1, 1]),
            '2': Buffer.from([99, 3, 3, 7, 7, 9, 9, 2, 1]),
        };
    }

    triggerRelays(ip, port, relayNumber) {
        return new Promise((resolve, reject) => {
            const client = new net.Socket();

            client.connect(port, ip, () => {
                let commandToSend;

                if (relayNumber !== undefined) {
                    if (!this.BINARY_COMMANDS[relayNumber]) {
                        console.error("Invalid relay number");
                        return reject(new Error("Invalid relay number"));
                    }
                    commandToSend = this.BINARY_COMMANDS[relayNumber];
                } else {
                    const commands = Object.values(this.BINARY_COMMANDS);
                    commandToSend = Buffer.concat(commands);
                }

                client.write(commandToSend, () => {
                    console.log(`RN-62 Binary command sent: ${commandToSend.toString('hex')}`);
                });
            });

            client.on('data', (data) => {
                console.log(`Received data: ${data.toString('hex')}`);
                client.end();
                resolve(true);
            });

            client.on('error', (err) => {
                reject(false);
            });

            client.on('end', () => {
            });
        });
    }
}

module.exports = Rn62_IO;
