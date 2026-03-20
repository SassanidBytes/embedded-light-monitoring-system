#include <Wire.h>
#include <OPT4048.h>

OPT4048 opt4048;
#define OPT4048_ADDRESS 0x44

String currentMode = "RGB";

void setup() {
  Serial.begin(115200);
  opt4048.begin(OPT4048_ADDRESS);
  
  
  OPT4048_ConfigA config;
  config.OpMode = 0x03; 
  opt4048.writeConfig(config);
}

void loop() {
  
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.startsWith("MODE:")) {
      currentMode = cmd.substring(5);
      currentMode.trim();
    }
  }

  OPT4048_RGB rgb;
  OPT4048_XYZ xyz;
  float lux, x, y, cct;
  OPT4048_ErrorCode err = getSensorData(rgb, xyz, lux, x, y, cct);
  
  if (err == NO_ERROR) {
    if (currentMode == "RGB") {
      int r = (int)(rgb.R * 255);
      int g = (int)(rgb.G * 255);
      int b = (int)(rgb.B * 255);
      


      Serial.print("RGB:");
      Serial.print(r);
      Serial.print(",");
      Serial.print(g);
      Serial.print(",");
      Serial.print(b);
      Serial.println();
    } else if (currentMode == "LUX") {
      



      Serial.print("LUX:");
      Serial.println(lux, 2);
    } else if (currentMode == "CIE") {
      


      Serial.print("CIE:");
      Serial.print(x, 4);
      Serial.print(",");
      Serial.print(y, 4);
      Serial.print(",");
      Serial.print(cct, 0);
      Serial.println();
    }
  }
  delay(100); 
}

OPT4048_ErrorCode getSensorData(OPT4048_RGB& rgb, OPT4048_XYZ& xyz, float& lux, float& x, float& y, float& cct) {
  OPT4048_RESULT channelData[4];
  OPT4048_ErrorCode err = opt4048.readAllChannels(channelData);
  
  if (err == NO_ERROR) {
    OPT4048_ADC adc = opt4048.ConvertRAWtoADC(channelData);
    xyz = opt4048.ConvertADCtoXYZ(adc);
    lux = xyz.Y;  
    rgb = opt4048.ConvertXYZtoRGB(xyz);

    float sum = xyz.X + xyz.Y + xyz.Z;
    if (sum > 0) {
      x = xyz.X / sum;
      y = xyz.Y / sum;
    } else {
      x = 0.0;
      y = 0.0;
    }

    
    float n = (x - 0.3320) / (y - 0.1858);
    cct = -449 * n*n*n + 3525 * n*n - 6823.3 * n + 5520.33;
    if (cct < 0) cct = 0; 

  }
  return err;
}