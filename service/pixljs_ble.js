// Disable logging events to screen
Bluetooth.setConsole(1);

messages = ["Waiting for sound events.."];

function updateScreen() {
  g.clear();
  y=0;
  // Display date
  var t = new Date(); // get the current date and time
  var time = t.toString().replace(/\d\d:.*/,"")+t.getHours()+":"+("0"+t.getMinutes()).substr(-2)+":"+("0"+t.getSeconds()).substr(-2);
  g.drawString(time, 0, y);
  y += g.stringMetrics(time).height;
  while(messages.length > 0) {
    text = messages.shift();
    g.drawString(text, 0, y);
    y += g.stringMetrics(text).height;
    if(y > g.getHeight()) {
      break;
    }
  }
  g.flip();
}

backlight = 0;

setWatch(function() {
  backlight=backlight == 0 ? 1 : 0;
  LED.write(backlight);
}, BTN, {edge:"rising", debounce:50, repeat:true});

// Update screen text
updateScreen();
