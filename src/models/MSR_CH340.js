const http = require('http');

class JetsonEmbed {
    constructor() {
        this.ENDPOINT_PATH = '/trigger';
    }

    triggerRelays(ip, port, relayNumber = null) {
        return new Promise((resolve, reject) => {
            // POST verisi - relay number ile
            const postData = JSON.stringify({
                relayNumber: relayNumber
            });

            // HTTP istek seçenekleri
            const options = {
                hostname: ip,
                port: port,
                path: this.ENDPOINT_PATH,
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(postData)
                }
            };

            const req = http.request(options, (res) => {
                let data = '';

                res.on('data', (chunk) => {
                    data += chunk;
                });

                res.on('end', () => {
                    try {
                        const response = JSON.parse(data);
                        console.log(`HTTP Response: ${JSON.stringify(response)}`);
                        
                        if (res.statusCode === 200) {
                            resolve(response);
                        } else {
                            reject(new Error(`HTTP ${res.statusCode}: ${response.message}`));
                        }
                    } catch (error) {
                        reject(new Error(`JSON parse error: ${error.message}`));
                    }
                });
            });

            req.on('error', (error) => {
                console.error(`HTTP Request error: ${error.message}`);
                reject(error);
            });

            req.setTimeout(30000, () => {
                req.destroy();
                reject(new Error('Request timeout'));
            });

            // POST verisini gönder
            req.write(postData);
            req.end();

            console.log(`HTTP POST request sent to http://${ip}:${port}${this.ENDPOINT_PATH}`);
        });
    }
}

module.exports = JetsonEmbed;