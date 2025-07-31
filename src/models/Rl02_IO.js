const net = require('net');

class Rl02_IO {
    constructor() {
        this.RELAY_COUNT = 16;
        this.RELAY_BEGIN_COMMAND = '<RL_BEGIN>';
        this.RELAY_END_COMMAND = '</RL_END>';
        this.RELAY_COMMANDS = [
            '<RL0>', '<RL1>', '<RL2>', '<RL3>', '<RL4>', '<RL5>', '<RL6>', '<RL7>',
            '<RL8>', '<RL9>', '<RL10>', '<RL11>', '<RL12>', '<RL13>', '<RL14>', '<RL15>'
        ];
    }

    triggerRelays(ip, port, relayNumber, duration) {
        return new Promise((resolve, reject) => {
            const client = new net.Socket();

            client.connect(port, ip, () => {
                let commandsToSend = [this.RELAY_BEGIN_COMMAND];

                if (relayNumber !== undefined) {
                    if (relayNumber < 0 || relayNumber >= this.RELAY_COUNT) {
                        return reject(new Error("Invalid relay number"));
                    }
                    const command = this.RELAY_COMMANDS[relayNumber] + duration.toString() + this.RELAY_COMMANDS[relayNumber].replace('<', '</');
                    commandsToSend.push(command);
                } else {
                    for (let i = 0; i < this.RELAY_COUNT; i++) {
                        const command = this.RELAY_COMMANDS[i] + duration.toString() + this.RELAY_COMMANDS[i].replace('<', '</');
                        commandsToSend.push(command);
                    }
                }

                commandsToSend.push(this.RELAY_END_COMMAND);

                const dataToSend = commandsToSend.join('');
                client.write(dataToSend, 'ascii', () => {
                    console.log(`RL-02 ASCII command sent: ${dataToSend}`);
                });
            });

            client.on('data', (data) => {
                console.log(`Received data: ${data.toString()}`);
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

module.exports = Rl02_IO;