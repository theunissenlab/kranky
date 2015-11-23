
#define FASTADC 1
#define DOTIMER 0
// defines for setting and clearing register bits
#ifndef cbi
#define cbi(sfr, bit) (_SFR_BYTE(sfr) &= ~_BV(bit))
#endif
#ifndef sbi
#define sbi(sfr, bit) (_SFR_BYTE(sfr) |= _BV(bit))
#endif



byte output_pins[8] = {7,8,9,10,11,12,13};
byte analog_pin = 0;
byte analogval = 0;
#if DOTIMER
long count = 0;
long timercount = 100000;
long lasttime=0; 
#endif

void setup()
{
#if FASTADC
  // set prescale to 16
  cbi(ADCSRA,ADPS2) ;
  sbi(ADCSRA,ADPS1) ;
  sbi(ADCSRA,ADPS0) ;
#endif
#if DOTIMER
  Serial.begin(19200);
#endif
  // set portB (output pins) to output and low
  for (int i = 0; i < sizeof(output_pins); i++) {
    pinMode(output_pins[i], OUTPUT);
    digitalWrite(output_pins[i], 0);
  }
}


void loop(){
#if DOTIMER
  count = count + 1;
  if (count >= timercount)
  {
    Serial.println((millis()-lasttime)*1000/timercount);
    Serial.println(analogval);
    for (int i = 0; i < 8; i++){
          Serial.print(bitRead(analogval,i));
        }
    Serial.println();
    lasttime = millis();
    count = 0; 
  }
#endif

//  analogval = analogRead(analog_pin)>>6;
// analogval = B00100001;

  PORTB = analogval<<2;
  




}

