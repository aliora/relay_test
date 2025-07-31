class RelayControl {
    constructor(brand) {
        this.brand = brand;

        if (this.brand === 'rl-02') {
            const RL02_IO = require('./models/Rl02_IO');
            this.relayInstance = new RL02_IO();
        } else if (this.brand === 'rn-62') {
            const RN62_IO = require('./models/Rn62_IO');
            this.relayInstance = new RN62_IO();
        } else if (this.brand === 'jetson-embed') {
            console.log("here");
            const JetsonEmbed = require('./models/Jetson_Embed');
            this.relayInstance = new JetsonEmbed();
        } else {
            throw new Error("Unsupported brand for relay control");
        }
    }

    triggerRelays(ip, port, relayNumber, duration) {
        return this.relayInstance.triggerRelays(ip, port, relayNumber, duration);
    }
}

module.exports = RelayControl;
