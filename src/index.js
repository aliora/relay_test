const RelayControl = require('./RelayControl');

const relayControl = new RelayControl('MSR-CH340');
//relayControl.triggerRelays('192.168.1.111', 9747,'1');
relayControl.triggerRelays('192.168.99.94', 9747,'1');
//relayControl.triggerRelays('100.8100.76.66.361.65.92', 9747,'1',100);sudo usermod -aG gpio $USER