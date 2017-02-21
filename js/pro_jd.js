"use strict";
var page = require('webpage').create(),
    system = require('system'),
    address;

page.settings.loadImages = false;
//page.settings.userAgent = 'Mozilla/5.0 (Linux; Android 5.1.1; Nexus 6 Build/LYZ28E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Mobile Safari/537.36';
page.settings.resourceTimeout = 10000;

if (system.args.length === 1) {
    console.log('Usage: pro_jd.js <some URL>');
    phantom.exit(1);
} else {
    address = system.args[1];

    page.onResourceRequested = function (req) {
        var url = req.url;
        var re = /^http(.*)skuIds=J_(\d+)$/;
        if (re.test(url)) {
            console.log(url);
        }
    };

    page.open(address, function (status) {
        if (status !== 'success') {
            console.log('error');
        }
        phantom.exit();
    });
}
