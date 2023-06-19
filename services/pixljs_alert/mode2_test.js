// Initialize the Pixl.js display
g.clear();
Bluetooth.setConsole(1);
LED.write(false);

function leadZero(value) {
  return ("0"+value.toString()).substr(-2);
}

const bitmap_font = E.toString(require('heatshrink').decompress(atob('AAUfoEGgEBwEAkU/xGP8UggFkpN/6VE4EGmcgkEmscAhuJkdQiEUgFggEHwkkhEBgVCj0AikEgoxBkE4hAEBCgOAoAuBgIIB4GAwGBHwM+kGSpEj8EBgmCv4XCgUSjMUyUxgEIxEkCgPYgEMhUJh/goEB9GSpMkyOAgfiAoOSk0AiFIolCoPAgE2BYNJkZJB5AaCx+AgMQgFGGYMKhAIBoGgqCPBhUCgECgUBimQmChB5ElEAPkgEPjURg2A+EB/gsCxpHChJrBkQaCkkRiFwgF/I4UkiAaByFIAoMADQQOBh4aB4KJBoP8gFBn+QoCsBhEEBIM/wUCGIK5B/yzBXIUD/GAkEIAAKYBgf5DoMMgMf4BQEnw1B5IFBoCYBZwORpFD6BQCpklhlAgciWYsIg/yd4V+HwUndIPAjEDg0cgEHAwMwHwWfgEGmGgkEoscAjggB+DXCociyVKkyPB/2BoGAjDGBNIMMgDSBr4zBAAIHBT4MAkBJBAgIUBAYIAB8GIokUj6qCoMQxE4gEOhGEoUhD4M4kURgqPBDQOoqkqhsAgkP8olBCIORopyBg/woC3Ba4MXDQMQgkC3zOBwMBGoKhBHgLbBgPhJwM8BAMECwJ9BHwcIweADANQokih0AgeCKANQv4aBgQABIwNIKAMVhMAgRHBxEAniJBwFDMYUIC4IkC4EQiEwIgJaBgUgYgUigEMkOQagIcBk0VhWFoalBsH8YoUf8EEhUE/kYRwImBYQNAXIYACgN8d4MRj/EoQjBpH8ySLBwEEfIOguFEgElhWD8WiqEA88AjVSzNM0ssFg/xgm6qsqyFHK4NBqDZBjwQBwGg1BrCWQMB4AaDrMiDQYAFg0EwVABYMJhwFBglCsNQpEEgERRANC0GgDIUIhAECv4yBgGHwEDgfB/2Av+AawS2BAgb0Bw/AkEQfo0AokUisFEoMFoegq0JgvAisOwNQl0RgFUnUdsGQrjdBhMowDCCn1o4kafAMA+OjiVofAMD62UougnkAh9aqMWyHwCYOhiATCgH10sRAwU/kkSg/kyVIgF8oNg6FEGwP/pNkBgMggf5kuTpMgwEP9mapckwUA/1JkgTCgWC/4RBhEv/UIgODv9gwEgz/IEoQcBkUOLgP7gVgxmBj/AgfqhbYBnxkBxEsjUI/B/BJwNYkfggH5wZXB55IBxBlBCYUihTKBwUggH4xVJlGPwEB/UCwMAz+Ag/ghUGgV+gEfyEwikJ/EB/D7CCYMB4EQx+EjgTB4lCkMQuChBkESo2gGoMcyMowWDKANwomixUPEIPFimJlBrBg8UqUk0hXBnGiiMlg7rBuNFsVKDQMDwQ0B/FUlUJS4OClMYxFEEYMlpWhqFoHwMVlWloOgEYNVlVVgwjBxWhqWomkAr8AhfoSIN8wBpBkEB4JQBot8XgOSiUFgl4NYeEoJQBNYWRg8ANYdERoJrCksURoJrClGDGIOBqCRBh0JwtDkCRBnmBkGAoYsB+D8BwMPOgPEYwMEnkAjwSBpEhDQMwg0g8ODHIP4qFEkUOgEGjHIjUwsEAA=')));
const police_heights = atob("AwIEBgYGBgIEBAQEAgQCBgYGBgYGBgYGBgYCAgQEBAYGBgYGBgYGBgYEBQYGCAcGBgYGBgYGBggGBgYEBgQGBAYGBgYGBgQGBgIFBQIIBgYGBgUGBAYGCAYGBgUCBQYAAAAAAAADAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADAgYGBgYCBgYIBgYEAAgGBQQGBgYGBgIGBgYGBgYGBgYGBgYGBgcGBgYGBgQEBAQGBwYGBgYGBgYGBgYGBgYGBgYGBgYGCAYGBgYGAgIEAgYGBgYGBgYEBgYGBgYGBgY=");

Graphics.prototype.setFontPixeloidSans = function(scale) {
  // Actual height 9 (8 - 0)
  // Generated with https://www.espruino.com/Font+Converter
  return this.setFontCustom(
    bitmap_font,
    32,
    police_heights,
    9 | 65536 | scale << 8
  );
};


// Variables to track the slider position
var sliderValue = 5;
var time_end_question = Date() + 15 * 60 * 1000;
var idRefreshInterval = 0;
var button_watch = [0,0,0,0];

function disableButtons() {
  for(id=0;id<4;id++) {
    if(button_watch[id] > 0) {
      clearWatch(button_watch[id]);
    }
    button_watch[id] = 0;
  }
}

function screenQuestion() {
  if(idRefreshInterval > 0) {
    clearInterval(idRefreshInterval);
    idRefreshInterval = 0;
  }
  idRefreshInterval = setInterval(refreshCountdown, 1000);
  answerTime = 1;
  drawSlider();
  disableButtons();
  // Attach the button press event listener
  button_watch[0]=setWatch(e => {sliderValue=Math.max(0,sliderValue-1);drawSlider();}, BTN1, {repeat: true, edge: 'rising'}, BTN1);
  button_watch[1]=setWatch(e => {sliderValue=Math.min(10,sliderValue+1);drawSlider();}, BTN2, {repeat: true, edge: 'rising'}, BTN2);
  button_watch[2]=setWatch(e => {clearInterval(idRefreshInterval);idRefreshInterval=0; disableButtons();drawNextMessage();}, BTN3, {repeat: true, edge: 'rising'}, BTN3);
}

function drawNextMessage() {
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
  setTimeout(screenQuestion, 10000); // 30,000 milliseconds = 30 seconds
}

function drawExitMessage() {
  // Clear the display
  g.clear();
  g.setFontAlign(0.5, 0.5);
  x = g.getWidth() / 2; // Calculate the center x-coordinate
  y = g.getHeight() / 2; // Calculate the center y-coordinate
  g.setFontPixeloidSans(1);
  g.drawString("Merci pour\n vos réponses. \n A demain !", x, y);
  g.flip();
  sliderValue = 5;
  time_end_question = Date() + 15 * 60 * 1000;
  setTimeout(screenQuestion, 10000); // 30,000 milliseconds = 30 seconds
  // Update the display
}
// Function to draw the slider
function drawSlider() {
  let sliderWidth = 100;
  let sliderHeight = 10;
  let knobHeight = 15;
  let sliderYPosition = 40;
  // Clear the display
  g.clear();
  // Draw the slider track
  var sliderXPosition = (g.getWidth() - sliderWidth) / 2;
  g.drawRect(sliderXPosition, sliderYPosition, sliderXPosition + sliderWidth,
    sliderYPosition + sliderHeight);
  // Calculate the position of the slider knob
  var knobX = Math.round(sliderValue / 10 * sliderWidth) + sliderXPosition;
  // Calculate the position of the slider knob vertically
  var knobY = sliderYPosition;
  // Draw the slider knob as a triple vertical line
  var knobYPosition = knobY - (knobHeight - sliderHeight) / 2;
  g.fillRect(knobX-2, knobYPosition, knobX+2, knobYPosition + knobHeight);
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
  let timeRemaining = parseInt((time_end_question-Date())/1000);
  g.drawString(parseInt(timeRemaining / 60)+"m"+leadZero(timeRemaining % 60), 20, 60);
  // Update the display
  g.flip();
}
// Function to update and display the countdown timer
function refreshCountdown() {
  if (Date() < time_end_question) {
    drawSlider();
  } else {
    // Stop the interval
    clearInterval(idRefreshInterval);
    idRefreshInterval = 0;
    drawExitMessage();
  }
}

screenQuestion();
