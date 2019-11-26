new (function() {
    var ext = this;
    var net = require('net')
    var {spawn} = require('child_process');
    const {dialog} = require('electron').remote
    const {BrowserWindow} = require('electron').remote

    var recvData = undefined;
    var noticed = true;
    var pyClient = undefined;
    var pyProc = undefined;
    
    var server = net.createServer(function(client) {
        pyClient = client;
        client.setEncoding('utf-8');

        client.on('data', function (data) {
            console.log('Receive client send data : ' + data + ', data size : ' + client.bytesRead);
            recvData = data.toString()
            noticed = false;
        });

        client.on('end', function () {
            console.log('Client disconnect.');
            server.getConnections(function (err, count) {
                if(!err)
                {
                    console.log("There are %d connections now. ", count);
                } else {
                    console.error(JSON.stringify(err));
                }

            });
        });

        client.on('timeout', function () {
            console.log('Client request time out. ');
        })
    });

    server.listen(function () {
        let port = server.address().port;
        console.log(port);
        pyProc = spawn("sudo", ["/usr/bin/python3", "/usr/lib/scratch2/scratch_extensions/dispatcher.py", port]);
        pyProc.stdout.on("data", function(data) { console.log(new String(data)); });
        pyProc.stderr.on("data", function(data) { console.log(new String(data)); });
        pyProc.on("error", function(data) { console.log(new String(data)); });
        
        server.on('close', function () {
            console.log('TCP server socket is closed.');
        });

        server.on('error', function (error) {
            console.error(JSON.stringify(error));
        });
    });

    ext._shutdown = function ()
    {
        if (pyProc) pyProc.kill(9);
        console.log("Killed spawn");
        server.close();
    };

    ext._getStatus = function ()
    {
        return {status: 2, msg: 'Ready'};
    };
    
    ext.getId = function() {
        if (recvData === undefined)
            return "";
        let i = recvData.indexOf(" ");
        if (i == -1) 
            return "";
        return recvData.slice(0, i);
    }
    
    ext.getAction = function() {
        if (recvData === undefined)
            return "";
        let i = recvData.indexOf(" ");
        if (i == -1) 
            return recvData;
        return recvData.slice(i + 1);
    }
    
    ext.getRawCommand = function() {
        if (recvData === undefined)
            return "";
        let tmp = recvData;
        return tmp;
    }
    
    ext.dataAvailable = function() {
        if (!noticed)
            return noticed = true;
        return false;
    }
    
    ext.sendData = function(data) {
        if (pyClient) {
            console.log(pyClient.write(`btsend;${data}`));
            console.log("btsend: " + data);
        }
    }
    
    ext.startPwm = function(gpio, freq, duty) {
        if (pyClient) {
            console.log(pyClient.write(`pwmstart;${gpio};${freq};${duty}`));
            console.log("pwmstart: " + gpio);
        }
    }
    
    ext.stopPwm = function(gpio) {
        if (pyClient) {
            console.log(pyClient.write(`pwmstop;${gpio}`));
            console.log("pwmstop: " + gpio);
        }
    }
    
    var descriptor = {
        blocks: [
            ['r', 'get id from bluetooth', 'getId'],
            ['r', 'get action from bluetooth', 'getAction'],
            ['r', 'get raw command from bluetooth', 'getRawCommand'],
            ['h', 'on bluetooth data available', 'dataAvailable'],
            [' ', 'send %s via bluetooth', 'sendData', ""],
            [' ', 'start pwm pin %m.gpios to %n Hz with duty of %n', 'startPwm', '18', 50, 5],
            [' ', 'stop pwm pin %m.gpios', 'stopPwm', '18'],
        ],
        menus: {
            gpios: ['0','1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26','27'],
        }
    };
    
    
    // Register the extension
    ScratchExtensions.register('PJ Pi', descriptor, ext);
})();
