// Initialize the Pixl.js display
g.clear();
Bluetooth.setConsole(1);
LED.write(false);

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


// Variables to track the slider position
var sliderValue = 5;
var sliderWidth = 100;
var sliderHeight = 10;
var sliderYPosition = 40;
var knobHeight = 15;
var countdown = 30;
var answerTime = 1;
var intervalId1 = 0;
var intervalId2 = 0;

// Function to handle button press
function handleButtonPress(e) {
  if (e === BTN2 && sliderValue < 10 && answerTime == 1) {
    // Increment slider value on Button 1 press
    sliderValue++;
    drawSlider();
  } else if (e === BTN1 && sliderValue > 0 && answerTime == 1) {
    // Decrement slider value on Button 2 press
    sliderValue--;
    drawSlider();
  } else if (e === BTN3) {
    drawNextMessage();
  }
}

function drawNextMessage() {
  clearInterval(intervalId2);
  answerTime = 0;
  // Clear the display
  g.clear();
  g.setFontAlign(0.5, 0.5);
  x = g.getWidth() / 2; // Calculate the center x-coordinate
  y = g.getHeight() / 2; // Calculate the center y-coordinate
  g.setFontPixeloidSans(1);
  g.drawString(
    "Merci pour\n votre réponse. \n Attendez le \n prochain passage !", x, y);
  g.flip();
  sliderValue = 5;
  setTimeout(function() {
    drawSlider();
    answerTime = 1;
    intervalId2 = setInterval(drawSlider, 1000);
  }, 10000); // 30,000 milliseconds = 30 seconds
}

function drawExitMessage() {
  answerTime = 0;
  // Clear the display
  g.clear();
  g.setFontAlign(0.5, 0.5);
  x = g.getWidth() / 2; // Calculate the center x-coordinate
  y = g.getHeight() / 2; // Calculate the center y-coordinate
  g.setFontPixeloidSans(1);
  g.drawString("Merci pour\n vos réponses. \n A demain !", x, y);
  g.flip();
  sliderValue = 5;
  setTimeout(function() {
    answerTime = 1;
    countdown = 30;
    intervalId = setInterval(updateCountdown, 1000);
    intervalId2 = setInterval(drawSlider, 1000);
  }, 10000); // 30,000 milliseconds = 30 seconds
  // Update the display
}
// Function to draw the slider
function drawSlider() {
  // Clear the display
  g.clear();
  // Draw the slider track
  g.drawRect(sliderXPosition, sliderYPosition, sliderXPosition + sliderWidth,
    sliderYPosition + sliderHeight);
  var sliderXPosition = (g.getWidth() - sliderWidth) / 2;
  // Calculate the position of the slider knob
  var knobX = Math.round(sliderValue / 10 * sliderWidth) + sliderXPosition;
  // Calculate the position of the slider knob vertically
  var knobY = sliderYPosition;
  // Draw the slider knob as a triple vertical line
  var knobYPosition = knobY - (knobHeight - sliderHeight) / 2;
  g.drawLine(knobX, knobYPosition, knobX, knobYPosition + knobHeight);
  g.drawLine(knobX + 1, knobYPosition, knobX + 1, knobYPosition + knobHeight);
  g.drawLine(knobX - 1, knobYPosition, knobX - 1, knobYPosition + knobHeight);
  g.drawLine(knobX + 2, knobYPosition, knobX + 2, knobYPosition + knobHeight);
  g.drawLine(knobX - 2, knobYPosition, knobX - 2, knobYPosition + knobHeight);
  g.setFontAlign(-1, -1);
  g.setFontPixeloidSans(2);
  g.drawString("-", 0, 0);
  f_metrics = g.stringMetrics("+");
  g.drawString("+", g.getWidth() - f_metrics.width, 0);
  g.setFontPixeloidSans(1);
  g.setFontAlign(0.5, 0.5);
  var x = g.getWidth() / 2; // Calculate the center x-coordinate
  var y = 13 + 15 / 2; // Calculate the center y-coordinate
  g.drawString(sliderValue, x, y);
  g.setFontAlign(0.0, -1);
  x = g.getWidth() / 2; // Calculate the center x-coordinate
  g.drawString("Gêne au passage", x, 0);
  g.setFontAlign(0.0, 0.0);
  x = g.getWidth() - 30; // Calculate the center x-coordinate
  y = 60; // Calculate the center y-coordinate
  g.drawString("Suivant > ", x, y);
  g.setFontAlign(0.5, 0.5);
  x = g.getWidth() / 2; // Calculate the center x-coordinate
  y = 33; // Calculate the center y-coordinate
  if (sliderValue < 2) {
    g.drawString("Pas du tout Gênant", x, y);
  } else if (sliderValue > 7) {
    g.drawString("Extrêment Gênant", x, y);
  } else {
    g.drawString("Assez Gênant", x, y);
  }
  // Start the countdown timer
  g.setFontAlign(0.5, 0.5); // Center text horizontally and vertically
  g.drawString(countdown, 20, 60);
  // Update the display
  g.flip();
}
// Function to update and display the countdown timer
function updateCountdown() {
  if(answerTime != 1) {
    return 0;
  }
  if (countdown > 0) {
    countdown--; // Decrease the countdown value by 1 second
    drawSlider();
  } else {
    clearInterval(intervalId);
    drawExitMessage(); // Stop the interval
  }
}
var intervalId = setInterval(updateCountdown, 1000);

// Attach the button press event listener
setWatch(function() {
  handleButtonPress(BTN1);
}, BTN1, {
  repeat: true,
  edge: 'rising'
});
setWatch(function() {
  handleButtonPress(BTN2);
}, BTN2, {
  repeat: true,
  edge: 'rising'
});
setWatch(function() {
  handleButtonPress(BTN3);
}, BTN3, {
  repeat: true,
  edge: 'rising'
});
