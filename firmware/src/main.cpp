#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <Update.h>
#include <ArduinoJson.h>
#include <FastLED.h>
#include "secrets.h"

#define LED_PIN 5
#define LED_COUNT 40
#define LED_TYPE WS2812B
#define COLOR_ORDER GRB
#define BATTERY_ADC A13

CRGB leds[LED_COUNT];
WebServer server(80);
String currentState = "idle";
int currentProgress = 0;
uint8_t currentBrightness = 96;
CRGB currentColor = CRGB(43,108,255);

CRGB parseHex(String s){
  if(s.startsWith("#")) s.remove(0,1);
  long v=strtol(s.c_str(),nullptr,16);
  return CRGB((v>>16)&255,(v>>8)&255,v&255);
}

void render(){
  FastLED.setBrightness(currentBrightness);
  fill_solid(leds, LED_COUNT, CRGB::Black);
  if(currentState=="printing" || currentState=="test"){
    int n = constrain((currentProgress * LED_COUNT + 99) / 100, 0, LED_COUNT);
    for(int i=0;i<n;i++) leds[i]=currentColor;
  } else if(currentState=="paused") {
    fill_solid(leds, LED_COUNT, ((millis()/500)%2)?CRGB::Orange:CRGB::Black);
  } else if(currentState=="error" || currentState=="cancelled") {
    fill_solid(leds, LED_COUNT, ((millis()/250)%2)?CRGB::Red:CRGB::Black);
  } else {
    fill_solid(leds, LED_COUNT, currentColor);
  }
  FastLED.show();
}

int batteryPercent(){
  // Prototype hook: calibrate divider/ADC for final PCB. Return -1 when unavailable.
  return -1;
}

void handleStatus(){
  if(!server.hasArg("plain")){ server.send(400,"application/json","{\"error\":\"json required\"}"); return; }
  JsonDocument d; auto err=deserializeJson(d,server.arg("plain"));
  if(err){ server.send(400,"application/json","{\"error\":\"bad json\"}"); return; }
  currentState = String((const char*)d["state"] | "unknown");
  currentProgress = constrain((int)(d["progress"] | 0),0,100);
  currentBrightness = constrain((int)(d["brightness"] | 96),1,255);
  currentColor = parseHex(String((const char*)d["color"] | "#64748b"));
  render();
  server.send(200,"application/json","{\"ok\":true}");
}

void handleInfo(){
  JsonDocument d; d["name"]=DEVICE_NAME; d["firmware"]="0.1.0"; d["ip"]=WiFi.localIP().toString(); d["rssi"]=WiFi.RSSI();
  int bp=batteryPercent(); if(bp>=0)d["battery"]=bp;
  String out; serializeJson(d,out); server.send(200,"application/json",out);
}

void handleFirmware(){
  bool ok=!Update.hasError();
  server.sendHeader("Connection","close");
  server.send(ok?200:500,"text/plain",ok?"OK":"FAIL");
  delay(250); if(ok) ESP.restart();
}

void setup(){
  Serial.begin(115200);
  FastLED.addLeds<LED_TYPE,LED_PIN,COLOR_ORDER>(leds,LED_COUNT);
  FastLED.setCorrection(TypicalLEDStrip); render();
  WiFi.mode(WIFI_STA); WiFi.setHostname(DEVICE_NAME); WiFi.begin(WIFI_SSID,WIFI_PASSWORD);
  unsigned long start=millis(); while(WiFi.status()!=WL_CONNECTED && millis()-start<20000){delay(250);}
  server.on("/api/status",HTTP_POST,handleStatus);
  server.on("/api/info",HTTP_GET,handleInfo);
  server.on("/api/firmware",HTTP_POST,handleFirmware,[]{
    HTTPUpload& u=server.upload();
    if(u.status==UPLOAD_FILE_START){Update.begin(UPDATE_SIZE_UNKNOWN);}
    else if(u.status==UPLOAD_FILE_WRITE){Update.write(u.buf,u.currentSize);}
    else if(u.status==UPLOAD_FILE_END){Update.end(true);}
  });
  server.on("/",HTTP_GET,[]{server.send(200,"text/plain","RS3D Status Bar online");});
  server.begin();
}

void loop(){server.handleClient(); if(currentState=="paused"||currentState=="error"||currentState=="cancelled")render(); delay(10);}
