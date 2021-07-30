var Discord = require('discord.io');
var logger = require('winston');
var auth = require('./auth.json');

require('dotenv').config();
// const http = require('http');
// port = 8080

// const server = http.createServer((req, res) => {
// // Set the response HTTP header with HTTP status and Content type
// res.writeHead(200, {'Content-Type': 'text/plain'});
// // Send the response body "Hello World"
// res.end('Just for testing purposes\n');
// });

// console.log(process.env);

// server.listen(port, () => {
// console.log('Hello world listening on port', port);
// });

// Configure logger settings
logger.remove(logger.transports.Console);
logger.add(new logger.transports.Console, {
    colorize: true
});

logger.level = 'debug';
// Initialize Discord Bot
var bot = new Discord.Client({
   token: process.env.token,
   autorun: true
});

bot.on('ready', function (evt) {
    logger.info('Connected');
    logger.info('Logged in as: ');
    logger.info(bot.username + ' - (' + bot.id + ')');
});

bot.on('message', function (user, userID, channelID, message, evt) {
    // Our bot needs to know if it will execute a command
    // It will listen for messages that will start with `!`
    if (message.substring(0, 1) == '!') {
        var args = message.substring(1).split(' ');
        var cmd = args[0];
       
        args = args.splice(1);
        switch(cmd) {
            // !ping
            case 'pog':
                bot.sendMessage({
                    to: channelID,
                    message: "How's the progress over here?"
                });
            break;
            // Just add any case commands if you want to..
         }
     }
});