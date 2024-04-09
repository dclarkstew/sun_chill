//Mux control pins
int s0 = 8;
int s1 = 9;
int s2 = 10;
int s3 = 11;

//Mux in "SIG" pin
int pin_adc0 = 0;

float Vo;
float R1 = 10000;
float logR2, R2, T;
float c1 = 1.009249522e-03, c2 = 2.378405444e-04, c3 = 2.019202697e-07;

//Variables
float RT, VR, ln, TX,  T0, VRT;

// Value of resistor
#define SERIESRESISTOR 10000 

void setup(){
  pinMode(s0, OUTPUT); 
  pinMode(s1, OUTPUT); 
  pinMode(s2, OUTPUT); 
  pinMode(s3, OUTPUT); 

  digitalWrite(s0, LOW);
  digitalWrite(s1, LOW);
  digitalWrite(s2, LOW);
  digitalWrite(s3, LOW);

  Serial.begin(9600);
}


void loop(){

  //Loop through and read all 16 values
  for(int i = 0; i < 11; i ++){
    Serial.print(i);
    Serial.print(",");
    Serial.print(readMux(i));
    Serial.print(",");
    delay(500);
  }
  // Print last value without a comma and start a new line
  Serial.print(12);
  Serial.print(",");
  Serial.println(readMux(12));

  delay(5000);
}


int readMux(int channel){
  int controlPin[] = {s0, s1, s2, s3};

  int muxChannel[12][4]={
    {0,0,0,0}, //channel 0
    {1,0,0,0}, //channel 1
    {0,1,0,0}, //channel 2
    {1,1,0,0}, //channel 3
    {0,0,1,0}, //channel 4
    {1,0,1,0}, //channel 5
    {0,1,1,0}, //channel 6
    {1,1,1,0}, //channel 7
    {0,0,0,1}, //channel 8
    {1,0,0,1}, //channel 9
    {0,1,0,1}, //channel 10
    {1,1,0,1}, //channel 11
    // {0,0,1,1}, //channel 12
    // {1,0,1,1}, //channel 13
    // {0,1,1,1}, //channel 14
    // {1,1,1,1}  //channel 15
  };

  // Digital write to set up the configuration for that channel 
  for(int i = 0; i < 4; i ++){
    digitalWrite(controlPin[i], muxChannel[channel][i]);
  }

  //read the value at the SIG pin
  // Method 3
//  VRT = analogRead(pin_adc0);         //Acquisition analog value of VRT
//  VRT  = (5.00 / 1023.00) * VRT;      //Conversion to voltage
//  VR = 5.00 - VRT;
//  RT = VRT / (VR / 10000.00);                //Resistance of RT
//
//  ln = log(RT / 10000.00);
//  TX = (1.00 / ((ln / 3435.00) + (1.00 / 298.15)));   //Temperature from thermistor
//  TX = ((TX-273.15)*1.8)+32;
//  TX = (int)(TX*100);
//  return TX;

  // Method 2 maybe the best?
  Vo = analogRead(pin_adc0);
  R2 = R1 * (1023.0 / Vo - 1.0);
  logR2 = log(R2);
  T = (1.0 / (c1 + c2*logR2 + c3*logR2*logR2*logR2));
  T = T - 273.15;
  T = (T * 9.0)/ 5.0 + 32.0;
  T = T*100;
  return T;

  // Method 1
//  int reading = analogRead(pin_adc0);
//  reading = (1023 / reading) - 1;     // (1023/ADC - 1) 
//  reading = SERIESRESISTOR / reading;  // 10K / (1023/ADC - 1)
//
//  float steinhart;
//  steinhart = reading / 10000.00;     // (R/Ro)
//  steinhart = log(steinhart);                  // ln(R/Ro)
//  steinhart /= 3435;                   // 1/B * ln(R/Ro)
//  steinhart += 1.0 / (25 + 273.15); // + (1/To)
//  steinhart = 1.0 / steinhart;                 // Invert
//  steinhart -= 273.15;
//  reading = (steinhart*9.0)/5.0 + 32.0;
//  reading *= 100;
//
//  //return the value
//  return reading;
}