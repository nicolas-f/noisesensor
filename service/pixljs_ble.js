// Disable logging events to screen
Bluetooth.setConsole(1);

messages = ["Waiting for sound events.."];

function updateScreen() {
  g.clear();
  //g.setFont("Vector", 9);
  y=0;
  while(messages.length > 0) {
    text = messages.shift();
    g.drawString(text, 0, y);
    y += g.stringMetrics(text).height;
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
