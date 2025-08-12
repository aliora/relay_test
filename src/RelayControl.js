class RelayControl {
    constructor(brand) {
        this.brand = brand;

        // Brand kontrolü olmadan doğrudan model yükle
        const brandMap = {
            'rl-02': './models/Rl02_IO',
            'rn-62': './models/Rn62_IO',
            'jetson-embed': './models/Jetson_Embed',
            'MSR-CH340': './models/MSR_CH340'
        };
        const modelPath = brandMap[this.brand];
        if (!modelPath) {
            throw new Error("Unsupported brand for relay control");
        }
        const ModelClass = require(modelPath);
        this.relayInstance = new ModelClass();
    }

    triggerRelays(ip, port, relayNumber, duration) {
        return this.relayInstance.triggerRelays(ip, port, relayNumber, duration);
    }
}

module.exports = RelayControl;
