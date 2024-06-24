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
// int a1 = 1.009249522e-03, b1 = 2.378405444e-04, c1 = 2.019202697e-07;

float thermistor_weights[][3] = {
  {0.0008434273696  , 0.0002436094515 , 0.0000003223882922},
  {0.001091204241   , 0.0001997684378 , 0.0000005369500176},
  {0  , 0 , 0},
  {0.001045840827   , 0.000206591803  , 0.0000005158437112},
  {0.0007579208701  , 0.0002591593187 , 0.000000279688439},
  {0.001102046277   , 0.0001972515643 , 0.0000005438952928},
  {0.001037763124   , 0.0002063370812 , 0.0000005202162387},
  {0.0008060470394  , 0.0002485429529 , 0.0000003265959052},
  {0.000704627576   , 0.0002663986983 , 0.0000002548193916},
  {0.00109654994    , 0.0001968387117 , 0.0000005561124484},
  {0.0009407654513  , 0.000227085796  , 0.0000004071260977},
  {0.0006104314491  , 0.0002872445309 , 0.0000001205302717}
};

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
  for(int i = 0; i < 12; i ++){
    Serial.print(i);
    Serial.print(",");
    Serial.print(readMux(i));
    Serial.print(", ");
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

  // === Calculate ===
  Vo = analogRead(pin_adc0);
  R2 = R1 * (1023.0 / Vo - 1.0); //pull down
  logR2 = log(R2);
  T = (1.0 / (thermistor_weights[channel][0] + thermistor_weights[channel][1]*logR2 + thermistor_weights[channel][2]*logR2*logR2*logR2));
  T = T - 273.15;
  T = (T * 9.0)/ 5.0 + 32.0;
  T = T*100;
  return T;

}
