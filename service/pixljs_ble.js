// Disable logging events to screen
Bluetooth.setConsole(1);
backlight = 0;
var PIN_BUZZER = D3; // Pin Buzzer is connected to
var PIN_NEOPIXEL = D8; // Pin Addressable Led is connected to
var FLASH_EN_PIN = D4;
var alarmPos = 0;
var lightPos = 0;
var alarmTimer = 0;
var turnOffScreenTimer = 0;
var alarmStopTimer = 0;
var alarmEnabled = false;
var alarmOnTime=250;
var buzzerTimeDelay=20000;
var lightLongPauseOff=5000;    // Stop blinking this time in ms
var lightShortPauseOn = 10;    // led on time while blinking
var lightShortPauseOff = 100; // led off time while blinking
var lightCountSequence = 10; // Number of blink for each sequence

var qrcode = { width: 21, height : 21, buffer : atob("/tP8ERBuqrt1tduvrsEJB/qv4A8A8rzpbD/AzReIoqPr7IB/Q/lCEEO8unCt1Vgup0kFvx/sLgA=") };
var zzImage = { width : 20, height : 20, bpp : 1, buffer : atob("AAHwAB8GAGDADBwB88AffHwHh8B8GA/DAPx8D+fA/gAH8AB/wMf//D//gf/wD/4AP8A=")};
var checkImage = { width : 20, height : 20, bpp : 1, buffer : atob("AAAAAAAAAAAAAAABAAA4AAfAAPgQHwOD4Hx8A++AH/AA/gAHwAA4AAEAAAAAAAAAAAA=")};
var demoImage = { width : 20, height : 20, bpp : 1, buffer : atob("AAAAAAAAAAAAAAAAAAAAAAAOdt6UVSl1UpRFLnReAAAAAAAAAAAAAAAAAAAAAAAAAAA=")};

var display_refresh_timer = 0;
function makeColorArray(r,g,b) {
    c = new Uint8ClampedArray(10*3);
    for(var i=0;i<c.length;i+=3) {
     c[i] = r;
     c[i+1] = g;
     c[i+2] = b;
    }
   return c;
}
var ledState0 = makeColorArray(0, 0, 0);
var ledState1 = makeColorArray(255, 255, 255);

function buzzerSequence() {
    if(!alarmEnabled) {
        digitalWrite(PIN_BUZZER,0);
    } else {
        if(alarmPos == 0) {
            analogWrite(PIN_BUZZER,0.5,{freq:800});
            setTimeout(buzzerSequence, alarmOnTime);
            alarmPos += 1;
        } else if(alarmPos == 1) {
            analogWrite(PIN_BUZZER,0.5,{freq:900});
            setTimeout(buzzerSequence, alarmOnTime);
            alarmPos += 1;
        } else {
            digitalWrite(PIN_BUZZER,0);
            setTimeout(buzzerSequence, buzzerTimeDelay);
            alarmPos = 0;
        }
    }
}

function lightSequence() {
    if(!alarmEnabled) {
        require("neopixel").write(PIN_NEOPIXEL, ledState0);  // blinking off state
        alarmPos = 0;
    } else {
        if(alarmPos % 2 == 0 && alarmPos < lightCountSequence * 2) {
            require("neopixel").write(PIN_NEOPIXEL, ledState1); // blinking on state
            setTimeout(lightSequence, lightShortPauseOn);
            alarmPos += 1;
        } else if(alarmPos % 2 != 0 && alarmPos < lightCountSequence * 2) {
            require("neopixel").write(PIN_NEOPIXEL, ledState0);  // blinking off state
            setTimeout(lightSequence, lightShortPauseOff);
            alarmPos += 1;
        } else {
            require("neopixel").write(PIN_NEOPIXEL, ledState0);  // blinking off state
            setTimeout(lightSequence, lightLongPauseOff);
            alarmPos = 0;
        }
    }
}

function flashLightSequence() {
    if(!alarmEnabled) {
        digitalWrite(FLASH_EN_PIN, 0);  // blinking off state
        lightPos = 0;
    } else {
        if(lightPos % 2 == 0 && lightPos < lightCountSequence * 2) {
            analogWrite(FLASH_EN_PIN,0.5,{ freq : 250000 }); // blinking on state
            setTimeout(lightSequence, lightShortPauseOn);
            lightPos += 1;
        } else if(lightPos % 2 != 0 && lightPos < lightCountSequence * 2) {
            digitalWrite(FLASH_EN_PIN, 0);  // blinking off state  // blinking off state
            setTimeout(lightSequence, lightShortPauseOff);
            lightPos += 1;
        } else {
            digitalWrite(FLASH_EN_PIN, 0);  // blinking off state
            setTimeout(lightSequence, lightLongPauseOff);
            lightPos = 0;
        }
    }
}

function buzzerDelay() {
  buzzerSequence();
  alarmStopTimer = setTimeout(function() {alarmEnabled = false;}, 240000);
}

function turnOnOffScreenBacklight(newState, delay_turn_off) {
  Pixl.setLCDPower(newState);
  LED.write(newState);
  backlight = newState;
  if(turnOffScreenTimer != 0) {
    clearTimeout(turnOffScreenTimer);
    turnOffScreenTimer = 0;
  }
  if(newState) {
    turnOffScreenTimer = setTimeout(turnOnOffScreenBacklight, delay_turn_off, 0);
  }
}

function updateScreen() {
  g.clear();
  // Display button icons
  // button 1 BTN1
  g.drawImage(zzImage, 0, 0);
  // button 3
  g.drawImage(demoImage, 0, g.getHeight() - demoImage.height);
  // button 2
  g.drawImage(checkImage, g.getWidth() - checkImage.width, 0);
  y=0;
  // Display date
  var t = new Date(); // get the current date and time
  var time = t.getHours()+":"+("0"+t.getMinutes()).substr(-2)+":"+("0"+t.getSeconds()).substr(-2);
  g.drawString(time, g.getWidth() / 2 - g.stringMetrics(time).width / 2, y);
  y += g.stringMetrics(time).height;
  // Resize qrcode if qrcode size is smaller than 2x screen size
  if(qrcode.height * 2 <= g.getHeight()) {
    g.drawImage(qrcode, g.getWidth() / 2 - qrcode.width, g.getHeight() / 2 - qrcode.height, options = {scale: 2});
  } else {
    g.drawImage(qrcode, g.getWidth() / 2 - qrcode.width / 2, g.getHeight() / 2 - qrcode.height / 2);
  }
  g.flip();
}

function stopScreenRefresh() {
    if(display_refresh_timer != 0) {
        clearInterval(display_refresh_timer);
    }
}

function main() {
    stopScreenRefresh();
    display_refresh_timer = setInterval(updateScreen, 1000);
    setTimeout(stopScreenRefresh, 300000);
    updateScreen();
    // Turn on backlight
    if(!alarmEnabled) {
        turnOnOffScreenBacklight(1, 300000);
        alarmEnabled = true;
        alarmTimer = setTimeout(buzzerDelay, buzzerTimeDelay);
        lightSequence();
    }
}

// Test button
setWatch(main, BTN4, {edge:"rising", debounce:50, repeat:true});

// Stop alarm button
setWatch(function() {alarmEnabled = false;turnOnOffScreenBacklight(0, 0);}, BTN2, {edge:"rising", debounce:50, repeat:true});

// Update screen text without setting up alarm
updateScreen();
