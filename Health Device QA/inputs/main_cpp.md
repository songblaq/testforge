# Source: main.cpp

```
/**
 * IMU Rep Counter v0.7 — M5StickC PLUS2
 * 수정: EMA alpha 0.7, threshold 1.08/0.92, raw mag도 출력
 */
#include <M5StickCPlus2.h>
#include <Wire.h>
#include <math.h>

#define MPU6886_ADDR       0x68
#define MPU6886_PWR_MGMT_1 0x6B
#define MPU6886_ACCEL_CONFIG 0x1C
#define MPU6886_ACCEL_XOUT_H 0x3B

#define SAMPLE_MS      20
#define PEAK_TH        1.08f
#define VALLEY_TH      0.92f
#define MIN_REP_MS     400
#define MAX_REP_MS     5000
#define REST_MS        8000
#define EMA_ALPHA      0.7f

enum State { IDLE, WAIT_PEAK, WAIT_VALLEY, REST };
State state = IDLE;
int reps = 0, sets = 0;
float smag = 1.0f, rawmag = 1.0f;
float ax=0, ay=0, az=0;
unsigned long tRep=0, tAct=0, tSamp=0, tDisp=0;

void writeReg(uint8_t reg, uint8_t val) {
    Wire1.beginTransmission(MPU6886_ADDR);
    Wire1.write(reg); Wire1.write(val);
    Wire1.endTransmission();
}

void readAccel(float &x, float &y, float &z) {
    Wire1.beginTransmission(MPU6886_ADDR);
    Wire1.write(MPU6886_ACCEL_XOUT_H);
    Wire1.endTransmission(false);
    Wire1.requestFrom((uint8_t)MPU6886_ADDR, (uint8_t)6);
    int16_t rx=(Wire1.read()<<8)|Wire1.read();
    int16_t ry=(Wire1.read()<<8)|Wire1.read();
    int16_t rz=(Wire1.read()<<8)|Wire1.read();
    x=rx/16384.0f; y=ry/16384.0f; z=rz/16384.0f;
}

void setup() {
    Serial.begin(115200);
    delay(100);
    Wire1.begin(21, 22, 400000);
    delay(10);
    writeReg(MPU6886_PWR_MGMT_1, 0x80); delay(100);
    writeReg(MPU6886_PWR_MGMT_1, 0x01); delay(10);
    writeReg(MPU6886_ACCEL_CONFIG, 0x00); delay(10);
    
    auto cfg = M5.config();
    cfg.internal_imu = false;
    StickCP2.begin(cfg);
    delay(200);
    
    StickCP2.Display.setRotation(1);
    StickCP2.Display.fillScreen(TFT_BLACK);
    StickCP2.Display.setTextSize(2);
    StickCP2.Display.setTextColor(TFT_WHITE);
    StickCP2.Display.drawString("Rep Counter v0.7", 5, 10);
    StickCP2.Display.setTextSize(1);
    StickCP2.Display.drawString("BTN: Start | Shake!", 5, 35);
    
    Serial.println("=== IMU Rep Counter v0.7 ===");
    Serial.println("ms,ax,ay,az,raw_mag,smooth_mag,state,reps");
    tAct = millis();
}

void loop() {
    StickCP2.update();
    unsigned long now = millis();
    
    if (StickCP2.BtnA.wasPressed()) {
        if (state==IDLE||state==REST) {
            state=WAIT_PEAK; reps=0; sets++;
            tAct=tRep=now;
            Serial.printf("# SET %d START\n", sets);
        } else {
            state=IDLE;
            Serial.printf("# RESET reps=%d\n", reps);
        }
    }
    
    if (now-tSamp>=SAMPLE_MS) {
        tSamp=now;
        readAccel(ax,ay,az);
        rawmag = sqrtf(ax*ax+ay*ay+az*az);
        smag = EMA_ALPHA*rawmag + (1-EMA_ALPHA)*smag;
        
        unsigned long dR=now-tRep, dA=now-tAct;
        switch(state) {
        case IDLE: break;
        case WAIT_PEAK:
            if(smag>PEAK_TH){state=WAIT_VALLEY;tAct=now;}
            if(dA>REST_MS&&reps>0){state=REST;Serial.printf("# DONE reps=%d\n",reps);}
            break;
        case WAIT_VALLEY:
            if(smag<VALLEY_TH&&dR>=MIN_REP_MS){reps++;tRep=tAct=now;state=WAIT_PEAK;Serial.printf("# REP %d\n",reps);}
            if(dR>MAX_REP_MS){state=WAIT_PEAK;tAct=now;}
            break;
        case REST: break;
        }
        
        // 항상 20ms마다 raw+smooth 둘 다 출력
        Serial.printf("%lu,%.3f,%.3f,%.3f,%.3f,%.3f,%d,%d\n",
            now, ax, ay, az, rawmag, smag, state, reps);
    }
    
    if(now-tDisp>=300) {
        tDisp=now;
        StickCP2.Display.fillScreen(TFT_BLACK);
        const char* sn[]={"IDLE","PEAK?","VALLEY?","REST"};
        
        StickCP2.Display.setTextSize(1);
        StickCP2.Display.setTextColor(TFT_WHITE);
        char buf[40];
        snprintf(buf,sizeof(buf),"[%s] Set:%d",sn[state],sets);
        StickCP2.Display.drawString(buf,5,5);
        
        StickCP2.Display.setTextSize(6);
        StickCP2.Display.setTextColor(TFT_GREEN);
        snprintf(buf,sizeof(buf),"%02d",reps);
        StickCP2.Display.drawString(buf,60,25);
        
        StickCP2.Display.setTextSize(1);
        StickCP2.Display.setTextColor(TFT_YELLOW);
        snprintf(buf,sizeof(buf),"R:%.2f S:%.2f P:%.2f V:%.2f",rawmag,smag,PEAK_TH,VALLEY_TH);
        StickCP2.Display.drawString(buf,5,95);
        
        // 간단 바
        int barW = constrain((int)((smag-0.8f)*500),0,200);
        StickCP2.Display.fillRect(5,110,barW,8,TFT_CYAN);
        int pX = constrain((int)((PEAK_TH-0.8f)*500),0,200);
        int vX = constrain((int)((VALLEY_TH-0.8f)*500),0,200);
        StickCP2.Display.drawFastVLine(5+pX,108,12,TFT_RED);
        StickCP2.Display.drawFastVLine(5+vX,108,12,TFT_BLUE);
    }
}
```
