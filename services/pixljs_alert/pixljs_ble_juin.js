var user_id = '007';
var DEMO_MODE = 1;
var FORCED_TRAIN_EVENT_MINUTES_NEGATIVE_DELAY = 3;
var train_event_slots = `
6h45
7h40
8h20
8h45
9h00
9h15
9h40
10h00
10h45
11h10
11h20
12h10
12h35
13h30
13h40
14h05
14h40
15h10
15h45
16h05
16h40
17h05
17h25
17h45
18h10
18h30
19h20
19h35
20h10
20h30
21h05
21h40
`;
var disponibility = `
14/06/2023 9h00 11h45
14/06/2023 14h00 18h00
15/06/2023 9h00 11h45
15/06/2023 14h00 18h00
15/06/2023 9h00 11h45
15/06/2023 14h00 18h00
`;
var mode2_activation = '12/06/2023 14h30 15h00';

///////////////
// Actual code
// Disable logging events to screen
var PIN_BUZZER = D5; // Yellow cable pin Buzzer is connected to
var FLASH_EN_PIN = D9;
var SNOOZE_TOTAL_TIME_MS = 8 * 3600 * 1000;
var timeout_id_mode2 = 0;
var timeout_next_forced_train_event = 0;
var timeout_stop_alarm = 0;
var timeout_turn_off_screen = 0;
var timeout_buzzer = 0;
var current_active_train_slot = null;
var alarmEnabled = false;
var alarmLength = 300000;
var state_buzzer = 0;
var state_flashlight = 0;
var buzzer_buz_time_ms=250;
var buzzer_off_time_ms=20000;
var lightLongPauseOff=5000;    // Stop blinking this time in ms
var lightShortPauseOn = 10;    // led on time while blinking
var lightShortPauseOff = 100; // led off time while blinking
var lightCountSequence = 10; // Number of blink for each sequence
var snooze_time = 0;
var ignore_train_time = 0;
var next_event = null;

Bluetooth.setConsole(1);
backlight = 0;
Pixl.setLCDPower(false);

Graphics.prototype.setFontPixeloidSans = function(scale) {
  // Actual height 9 (8 - 0)
  // Generated with https://www.espruino.com/Font+Converter
  return this.setFontCustom(
    E.toString(require('heatshrink').decompress(atob('AAUfoEGgEBwEAkU/xGP8UggFkpN/6VE4EGmcgkEmscAhuJkdQiEUgFggEHwkkhEBgVCj0AikEgoxBkE4hAEBCgOAoAuBgIIB4GAwGBHwM+kGSpEj8EBgmCv4XCgUSjMUyUxgEIxEkCgPYgEMhUJh/goEB9GSpMkyOAgfiAoOSk0AiFIolCoPAgE2BYNJkZJB5AaCx+AgMQgFGGYMKhAIBoGgqCPBhUCgECgUBimQmChB5ElEAPkgEPjURg2A+EB/gsCxpHChJrBkQaCkkRiFwgF/I4UkiAaByFIAoMADQQOBh4aB4KJBoP8gFBn+QoCsBhEEBIM/wUCGIK5B/yzBXIUD/GAkEIAAKYBgf5DoMMgMf4BQEnw1B5IFBoCYBZwORpFD6BQCpklhlAgciWYsIg/yd4V+HwUndIPAjEDg0cgEHAwMwHwWfgEGmGgkEoscAjggB+DXCociyVKkyPB/2BoGAjDGBNIMMgDSBr4zBAAIHBT4MAkBJBAgIUBAYIAB8GIokUj6qCoMQxE4gEOhGEoUhD4M4kURgqPBDQOoqkqhsAgkP8olBCIORopyBg/woC3Ba4MXDQMQgkC3zOBwMBGoKhBHgLbBgPhJwM8BAMECwJ9BHwcIweADANQokih0AgeCKANQv4aBgQABIwNIKAMVhMAgRHBxEAniJBwFDMYUIC4IkC4EQiEwIgJaBgUgYgUigEMkOQagIcBk0VhWFoalBsH8YoUf8EEhUE/kYRwImBYQNAXIYACgN8d4MRj/EoQjBpH8ySLBwEEfIOguFEgElhWD8WiqEA88AjVSzNM0ssFg/xgm6qsqyFHK4NBqDZBjwQBwGg1BrCWQMB4AaDrMiDQYAFg0EwVABYMJhwFBglCsNQpEEgERRANC0GgDIUIhAECv4yBgGHwEDgfB/2Av+AawS2BAgb0Bw/AkEQfo0AokUisFEoMFoegq0JgvAisOwNQl0RgFUnUdsGQrjdBhMowDCCn1o4kafAMA+OjiVofAMD62UougnkAh9aqMWyHwCYOhiATCgH10sRAwU/kkSg/kyVIgF8oNg6FEGwP/pNkBgMggf5kuTpMgwEP9mapckwUA/1JkgTCgWC/4RBhEv/UIgODv9gwEgz/IEoQcBkUOLgP7gVgxmBj/AgfqhbYBnxkBxEsjUI/B/BJwNYkfggH5wZXB55IBxBlBCYUihTKBwUggH4xVJlGPwEB/UCwMAz+Ag/ghUGgV+gEfyEwikJ/EB/D7CCYMB4EQx+EjgTB4lCkMQuChBkESo2gGoMcyMowWDKANwomixUPEIPFimJlBrBg8UqUk0hXBnGiiMlg7rBuNFsVKDQMDwQ0B/FUlUJS4OClMYxFEEYMlpWhqFoHwMVlWloOgEYNVlVVgwjBxWhqWomkAr8AhfoSIN8wBpBkEB4JQBot8XgOSiUFgl4NYeEoJQBNYWRg8ANYdERoJrCksURoJrClGDGIOBqCRBh0JwtDkCRBnmBkGAoYsB+D8BwMPOgPEYwMEnkAjwSBpEhDQMwg0g8ODHIP4qFEkUOgEGjHIjUwsEAA='))),
    32,
    atob("AwIEBgYGBgIEBAQEAgQCBgYGBgYGBgYGBgYCAgQEBAYGBgYGBgYGBgYEBQYGCAcGBgYGBgYGBggGBgYEBgQGBAYGBgYGBgQGBgIFBQIIBgYGBgUGBAYGCAYGBgUCBQYAAAAAAAADAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADAgYGBgYCBgYIBgYEAAgGBQQGBgYGBgIGBgYGBgYGBgYGBgYGBgcGBgYGBgQEBAQGBwYGBgYGBgYGBgYGBgYGBgYGBgYGCAYGBgYGAgIEAgYGBgYGBgYEBgYGBgYGBgY="),
    9 | 65536 | scale << 8
  );
};

var qrcode = { width: 33, height : 33, buffer : atob("/ncqP8EMoRBunKlLt1Zqtduq8ZrsEzVFB/qqqv4AmFcAx2tCDD7RO4WK1gm7QyZ1ZEluYZoeBXDJjm2emoQRXWLF4utzyWSgfdrIm6TqMCJwdkfvByWXpWSK6pseOHUiGjXs390p+QBAqUV/pmprUFYBccunH6/V0njW/uhHQi8FGFKc/srjlQA=") };
var zzImage = { width : 20, height : 20, bpp : 1, buffer : atob("AAHwAB8GAGDADBwB88AffHwHh8B8GA/DAPx8D+fA/gAH8AB/wMf//D//gf/wD/4AP8A=")};
var checkImage = { width : 20, height : 20, bpp : 1, buffer : atob("AAAAAAAAAAAAAAABAAA4AAfAAPgQHwOD4Hx8A++AH/AA/gAHwAA4AAEAAAAAAAAAAAA=")};
var demoImage = { width : 20, height : 20, bpp : 1, buffer : atob("AAAAAAAAAAAAAAAAAAAAAAAOdt6UVSl1UpRFLnReAAAAAAAAAAAAAAAAAAAAAAAAAAA=")};
var button_watch = [0,0,0,0];

// force timezone to UTC+0200
E.setTimeZone(2);

fp = require("Storage").open(user_id + ".csv", 'a');

function buzzerSequence() {
    if(!alarmEnabled) {
        digitalWrite(PIN_BUZZER,0);
    } else {
        if(state_buzzer == 0) {
            analogWrite(PIN_BUZZER,0.5,{freq:800});
            timeout_buzzer = setTimeout(buzzerSequence, buzzer_buz_time_ms);
            state_buzzer += 1;
        } else if(state_buzzer == 1) {
            analogWrite(PIN_BUZZER,0.5,{freq:900});
            timeout_buzzer = setTimeout(buzzerSequence, buzzer_buz_time_ms);
            state_buzzer += 1;
        } else {
            digitalWrite(PIN_BUZZER,0);
            timeout_buzzer = setTimeout(buzzerSequence, buzzer_off_time_ms);
            state_buzzer = 0;
        }
    }
}

function flashLightSequence() {
    if(!alarmEnabled) {
        digitalWrite(FLASH_EN_PIN, 0);  // blinking off state
        state_flashlight = 0;
    } else {
        if(state_flashlight % 2 == 0 && state_flashlight < lightCountSequence * 2) {
            analogWrite(FLASH_EN_PIN,0.5,{ freq : 250000 }); // blinking on state
            setTimeout(flashLightSequence, lightShortPauseOn);
            state_flashlight += 1;
        } else if(state_flashlight % 2 != 0 && state_flashlight < lightCountSequence * 2) {
            digitalWrite(FLASH_EN_PIN, 0);  // blinking off state  // blinking off state
            setTimeout(flashLightSequence, lightShortPauseOff);
            state_flashlight += 1;
        } else {
            digitalWrite(FLASH_EN_PIN, 0);  // blinking off state
            setTimeout(flashLightSequence, lightLongPauseOff);
            state_flashlight = 0;
        }
    }
}

function Mode1Screen() {
  Pixl.setLCDPower(true);
  g.clear();
  // Display button icons
  // button 1 BTN1
  g.drawImage(zzImage, 0, 0);
  // button 2
  g.drawImage(checkImage, g.getWidth() - checkImage.width, 0);
  // Resize qrcode if qrcode size is smaller than 2x screen size
  if(qrcode.height * 2 <= g.getHeight()) {
    g.drawImage(qrcode, g.getWidth() / 2 - qrcode.width, g.getHeight() / 2 - qrcode.height, options = {scale: 2});
  } else {
    g.drawImage(qrcode, g.getWidth() / 2 - qrcode.width / 2, g.getHeight() / 2 - qrcode.height / 2);
  }
  g.flip();
  disableButtons();
  button_watch[1] = setWatch(onClickStopAlarm, BTN2, {edge:"rising", debounce:50, repeat:true});
  button_watch[0]  = setWatch(onClickSnooze, BTN1, {edge:"rising", debounce:50, repeat:true});
}

function construct_date(date_list) {
  let d = Date();
  d.setFullYear(date_list[0], date_list[1], date_list[2]);
  d.setHours(date_list[3], date_list[4], date_list[5], date_list[6]);
  return d;
}

function parse_interval(string_line) {
  let space_split = string_line.trim().split(" ");
  let date_split = space_split[0].split("/");
  let start_split = space_split[1].split("h");
  let end_split = space_split[2].split("h");
  let year = parseInt(date_split[2]);
  let month = parseInt(date_split[1]);
  let day = parseInt(date_split[0]);
  return [construct_date([year, month, day, parseInt(start_split[0]), parseInt(start_split[1]), 0, 0]),
    construct_date([year, month, day, parseInt(end_split[0]), parseInt(end_split[1]), 0, 0])
  ];
}

function parse_event(string_line) {
  let start_split = string_line.split("h");
  return construct_date([1970, 1, 1, parseInt(start_split[0]), parseInt(start_split[1]), 0, 0]);
}

var parsed_train_event_slots = train_event_slots.trim().split("\n").map(parse_event);
var parsed_disponibility = disponibility.trim().split("\n").map(parse_interval);
var parsed_activation = parse_interval(mode2_activation);

function turnOnOffScreenBacklight(newState, delay_turn_off) {
  Pixl.setLCDPower(newState);
  LED.write(newState);
  backlight = newState;
  if (timeout_turn_off_screen != 0) {
    clearTimeout(timeout_turn_off_screen);
    timeout_turn_off_screen = 0;
  }
  if (newState && delay_turn_off > 0) {
    timeout_turn_off_screen = setTimeout(turnOnOffScreenBacklight, delay_turn_off, 0);
  }
}

function buzzerDelay() {
  alarmEnabled = true;
  buzzerSequence();
  timeout_stop_alarm = setTimeout(stopAlarm, alarmLength);
}

function disableButtons() {
  for(id=0;id<4;id++) {
    if(button_watch[id] > 0) {
      clearWatch(button_watch[id]);
    }
    button_watch[id] = 0;
  }
}

function stopAlarm() {
  alarmEnabled = false;
  if(timeout_buzzer > 0) {
    clearTimeout(timeout_buzzer);
    timeout_buzzer = 0;
  }
  turnOnOffScreenBacklight(0, 0);
  disabledScreen();
}

function onClickStopAlarm() {
  stopAlarm();
  fp.write(Date().getTime()+",onClickStopAlarm,0"+"\n");
}

function onClickSnooze() {
  stopAlarm();
  snooze_time = Date() + SNOOZE_TOTAL_TIME_MS;
  fp.write(Date().getTime()+",onClickSnooze,0"+"\n");
}

function onMode1() {
  turnOnOffScreenBacklight(true, alarmLength);
  Mode1Screen();
  buzzerDelay();
  flashLightSequence();
}

function onMode2() {
  timeout_id_mode2 = 0;
  if (timeout_next_forced_train_event > 0) {
    print("Cleared forced event "+timeout_next_forced_train_event);
    clearTimeout(timeout_next_forced_train_event);
    timeout_next_forced_train_event = 0;
  }
  turnOnOffScreenBacklight(true, 25000);
  buzzerDelay();
  flashLightSequence();

}

function isUserAvailable() {
  let now = Date();
  match_disponibility = false;
  parsed_disponibility.every(interval => {
    if(interval[0] < now < interval[1]) {
      match_disponibility = true;
      return false;
    } else {
      return true;
    }
  });
  return match_disponibility;
}

function onTrainCrossing(forced) {
  let now = Date();
  if(now < snooze_time || now < ignore_train_time) {
    return 0;
  }
  print((forced ? "Forced" : "BT") + " train crossing event");
  now = Date();
  match_disponibility = isUserAvailable();
  if(match_disponibility) {
    fp.write(Date().getTime()+",onTrainCrossing,"+forced+"\n");
    if(!forced && next_event > now) {
      // ignore new trains events until next event slot
      ignore_train_time = next_event;
    }
    onMode1();
  }
  installTimeouts(!forced);
}

function getNextTrainEvent(hour, minute, skipSlot) {
  let match_time = construct_date([1970, 1, 1, hour, minute, 0, 0]);
  last_valid_event = null;
  parsed_train_event_slots.every(event => {
    if (event > match_time) {
      pass = last_valid_event == null && skipSlot;
      last_valid_event = event;
      return pass;
    }
    return true;
  });
  return last_valid_event;
}

function installTimeouts(skipNext) {
  if (timeout_next_forced_train_event > 0) {
    clearTimeout(timeout_next_forced_train_event);
    print("Cleaned next_forced_train_event " + timeout_next_forced_train_event);
    timeout_next_forced_train_event = 0;
  }
  let now = Date();
  g.setFontPixeloidSans(1);
  if (now.getFullYear() < 2023) {
    Pixl.setLCDPower(true);
    LED.write(false);
    g.clear();
    text = "Boitier non initialisé !";
    text_metrics = g.stringMetrics(text);
    g.drawString(text, g.getWidth() / 2 - text_metrics.width / 2, g.getHeight() / 2 - text_metrics.height / 2);
    g.flip();
    return;
  }
  if (timeout_id_mode2 == 0 && parsed_activation[0] > now && parsed_activation[1] < now) {
    print("Mode 2 programmed to activate on " + parsed_activation[0]);
    timeout_id_mode2 = setTimeout(onMode2, parsed_activation[0] - Date());
  }
  if (now < parsed_activation[0]) {
    let match_time = construct_date([1970, 1, 1, now.getHours(), now.getMinutes(), 0, 0]);
    next_event_start = Date(now+FORCED_TRAIN_EVENT_MINUTES_NEGATIVE_DELAY * 60000+5000);
    last_valid_event = getNextTrainEvent(next_event_start.getHours(), next_event_start.getMinutes(), skipNext);
    next_event = Date();
    if (!last_valid_event) {
      // tomorrow
      last_valid_event = train_event_slots[0];
      next_event.setHours(last_valid_event.getHours(), last_valid_event.getMinutes(), 0, 0);
      next_event.setMilliseconds(next_event.valueOf()+24*3600*1000);
    } else {
      next_event.setHours(last_valid_event.getHours(), last_valid_event.getMinutes(), 0, 0);
    }
    next_event_millis = parseInt(next_event - Date());
    let millidelay = FORCED_TRAIN_EVENT_MINUTES_NEGATIVE_DELAY * 60000;
    next_event_millis -= millidelay; // alert x minutes before next event
    if (next_event_millis > 0) {
      print("Next forced train event in " + parseInt(next_event_millis/60000) + " minutes ("+Date(next_event-FORCED_TRAIN_EVENT_MINUTES_NEGATIVE_DELAY * 60000).toString()+")");
      timeout_next_forced_train_event = setTimeout(onTrainCrossing, next_event_millis, true);
    } else {
      print("Oups next_event_millis <= 0 =>" + next_event_millis);
    }
  }
}
function leadZero(value) {
  return ("0"+value.toString()).substr(-2);
}
function disabledScreen() {
  if(!DEMO_MODE && !isUserAvailable()) {
    g.clear();
    Pixl.setLCDPower(false);
    LED.write(0);
    return 0;
  }
  Pixl.setLCDPower(true);
  LED.write(0);
  g.clear();
  // Display button icons
  if(DEMO_MODE) {
    g.drawImage(demoImage, 0, g.getHeight() - demoImage.height);
    g.setFontAlign(0.5, 1);
    g.setFontPixeloidSans(1);
    let next_event_alert = Date(next_event-FORCED_TRAIN_EVENT_MINUTES_NEGATIVE_DELAY * 60000);
    g.drawString("Next: "+leadZero(next_event_alert.getHours())+"h"+leadZero(next_event_alert.getMinutes()), g.getWidth() / 2, g.getHeight());
    g.setFontAlign(-1, -1);
  }
  if(snooze_time > 0) {
    g.drawImage(zzImage, 0, 0);
  }
  g.flip();
  // test train crossing
  disableButtons();
  button_watch[0] = setWatch(function() { if(snooze_time==0) {snooze_time = Date() + SNOOZE_TOTAL_TIME_MS;}else{snooze_time = 0;} disabledScreen();}, BTN1, {  repeat: true,  edge: 'rising'});
  if(DEMO_MODE) {
    button_watch[3] = setWatch(function() { onTrainCrossing(false);}, BTN4, {  repeat: true,  edge: 'rising'});
  }
}

installTimeouts(false);
disabledScreen();
