#!/usr/bin/env python3
"""
Simple LJTick-DAC control and AIN monitor for a LabJack U3-HV.

Usage:
    python ArCSHVMonitor.py <num_channels> <set_output_HV> <dac0_voltage>

Example:
    python ArCSHVMonitor.py 1 7.0

    -> Configures AIN0 as analog input
    -> Sets LJTick-DAC DACA to the voltage corresponding to the set_output_HV and convert to DAC voltage
    -> Sets DAC0 to dac0_voltage
    -> Continuously prints AIN0 reading

Notes:
    - Assumes LJTick-DAC is connected to a U3 with:
        * SDA on FIO4
        * SCL on FIO5
      so we use dioPin = 6 for I2C.
    - AIN channels start at AIN0 and go up to AIN(num_channels - 1).
"""

"""
Need to test -5, -10, -15, -20, -22, -25, -27, -30 kV. 
Glassman Power Supply model (LX125N16), maximum voltage is -125 kV.
"""

import os
import sys
import time
import u3

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ljTickDac import LJTickDAC

def parse_args():
     if len(sys.argv) != 5:
          print("Usage: python ArCSHVMonitor.py <num_channels> <set_output_HV> <dac0_voltage> <run_seconds>")
          sys.exit(1)

     try:
          num_channels = int(sys.argv[1])
     except ValueError:
          print("Error: <num_channels> must be an integer.")
          sys.exit(1)

     try:
          set_output_HV = float(sys.argv[2])
     except ValueError:
          print("Error: <set_output_HV> must be a number (in volts).")
          sys.exit(1)
     
     try:
          dac0_voltage = float(sys.argv[3])
     except ValueError:
          print("Error: <dac0_voltage> must be a number (in volts).")
          sys.exit(1)

     if num_channels <= 0 or num_channels > 4:
          print("Error: <num_channels> must be between 1 and 4.")
          sys.exit(1)
     
     try:
          run_seconds = float(sys.argv[4])  # new argument
     except ValueError:
          print("Error: <run_seconds> must be a number (in seconds).")
          sys.exit(1)

     return num_channels, set_output_HV, dac0_voltage, run_seconds


def convertToDACAVoltage(HVVoltage):
     TotalVoltage = -125.0  # kV
     TotalProgrammaVoltage = 10.0  #V
     ljtick_daca_voltage = abs(TotalProgrammaVoltage / TotalVoltage) * abs(HVVoltage)
     return ljtick_daca_voltage


def main():
     num_channels, set_output_HV, dac0_voltage, run_seconds = parse_args()

     ljtick_daca_voltage = convertToDACAVoltage(set_output_HV)
     print(f"Setting LJTick-DAC DACA to {ljtick_daca_voltage:.5f} V for HV output of {set_output_HV} V")
     # Open the U3
     dev = u3.U3()

     try:
          dev.getCalibrationData()

          # ---- Configure analog inputs ----
          # FIO/EIO analog bitmask: (2**num_channels - 1) sets AIN0..AIN(num_channels-1)
          FIOEIOAnalog = (2 ** num_channels) - 1
          fios = FIOEIOAnalog & 0xFF     # lower 8 bits -> FIO
          eios = FIOEIOAnalog // 256     # remaining bits -> EIO

          dev.configIO(FIOAnalog=fios, EIOAnalog=eios)

          # ---- Set up LJTick-DAC (assumes on FIO4/FIO5, so dioPin=6) ----
          dioPin = 6
          tdac = LJTickDAC(dev, dioPin)

          # Set DACA to desired voltage, DACB to 0.0 V (unused)
          tdac.update(ljtick_daca_voltage, 0.0)
          print(f"DACA (LJTick-DAC output A) set to {ljtick_daca_voltage:.5f} V")

          # Set DAC1 to desired voltage.
          dev.getFeedback(u3.PortDirWrite(Direction=[0, 0, 0], WriteMask=[0, 0, 15]))

          feedbackArguments = []
          full_scale = 5.0    

          dac_value = int(dac0_voltage / full_scale * 255)
          dac_value2 = int(5.0 / full_scale * 255)

          feedbackArguments.append(u3.DAC0_8(Value=dac_value))  #125
          feedbackArguments.append(u3.DAC1_8(Value=dac_value2)) #125

          print(f"DAC0 set to {dac0_voltage:.5f}V")
          feedbackArguments.append(u3.PortStateRead())
          dev.getFeedback(feedbackArguments)
          
          #volt = dev.getAIN(3)
          #print(f"AIN2 = {volt:.5f} V")
          
          # ---- Monitor AIN channels ----
          channels = {
               "V-MONITOR": 0,
               "REFERENCE": 1,
               "TEST": 2,
          }

          print(f"Monitoring V-MONITOR and REFERENCE (Ctrl+C to stop) and saving to file 'monitoring_data_voltage{set_output_HV}.csv'")
          # clear the file if it exists
          saveDir = f"data-{time.strftime('%Y%m%d')}"
          os.makedirs(saveDir, exist_ok=True)
          open(f"{saveDir}/monitoring_data_voltage{set_output_HV}.csv", "w").close()
          with open(f"{saveDir}/monitoring_data_voltage{set_output_HV}.csv", "a") as file:  # Open file in append mode
               print("HV-Interlock\tV-Program\t", end="\t")
               file.write("HV-Interlock\tV-Program\t")
               for name, ch in channels.items():
                    if name != "TEST":
                         file.write(f"{name}\t")
                         print(f"{name}\t", end="")
                    else:
                         file.write(f"{name}\n")
                         print(f"{name}\n", end="")
               #i=0
               #while True:
               start = time.time()
               i = 0
               try:
                    while time.time() - start < run_seconds:
                         readings = []
                         readings.append(f"{dac0_voltage:.5f}")
                         readings.append(f"{ljtick_daca_voltage:.5f}")
                         for name, ch in channels.items():
                              v = dev.getAIN(ch)
                              # To-do: use the reading value from AIN1 channel to calibrate AIN0 channel. 
                              readings.append(f"{v:.5f}")
                         print("\t".join(readings) + "\t" + str(i))
                         file.write("\t".join(readings) + "\n")
                         time.sleep(0.5)
                         i+=1
                    file.close()
               except KeyboardInterrupt:
                    print("\nStopping monitor.")
                    file.close()
               finally:       
                    dev.close()

     except KeyboardInterrupt:
          print("\nStopping monitor.")
     finally:
          dev.close()


if __name__ == "__main__":
    main()
