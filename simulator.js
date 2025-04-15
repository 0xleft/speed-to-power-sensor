var Sensor = require('./zwack-bike/lib/zwack-ble-sensor');
const ws = require('ws');

var power = 0;
var notificationInterval = 700;
var lastNotificationTime = 0;

var sensor = new Sensor({ 
  name: "LT Power 530",
  modelNumber: 'PWR-32390',
  serialNumber: '0xleft/speed-to-power'
});

const socket = new ws.WebSocket('ws://localhost:54399', {
    perMessageDeflate: false
});

socket.on('open', function open() {
    // console.log('Connected to server');
});

socket.on('message', function incoming(data) {
    try {
        var json = JSON.parse(data);
        power = json.power;
        lastNotificationTime = Date.now();
        // console.log('Received power:', power);
    } catch (e) {
        console.error('Error parsing message:', e);
    }
});

var notifyPowerCSP = function() {
  try {
    // if more than 4 seconds since last notification 0 watts
    if (Date.now() - lastNotificationTime > 4000) {
      power = 0;
    }
    sensor.notifyCSP({'watts': power});
  }
  catch( e ) {
    console.error(e);
  }
  
  setTimeout(notifyPowerCSP, notificationInterval + Math.random() * 20);
};

notifyPowerCSP();