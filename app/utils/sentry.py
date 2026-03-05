import psutil
import time
import os
import winsound

# Thresholds tuned for TUF F15
CPU_LOAD_THRESHOLD = 80.0  
FREQ_THRESHOLD = 4400      
STREAK_REQUIRED = 3        # Must be high for 3 checks (6 seconds) before beeping

def monitor_vitals():
    print(f"--- Thermal Sentry Active [User: {os.getlogin()}] ---")
    streak = 0
    
    try:
        while True:
            cpu_load = psutil.cpu_percent(interval=1)
            cpu_freq = psutil.cpu_freq().current
            
            status = f"Load: {cpu_load}% | Freq: {cpu_freq:.0f}MHz"
            print(f"{status} | Streak: {streak}  ", end="\r")

            # Check if thresholds are exceeded
            if cpu_load > CPU_LOAD_THRESHOLD or cpu_freq > FREQ_THRESHOLD:
                streak += 1
            else:
                streak = 0

            # Alert after sustained high load
            if streak >= STREAK_REQUIRED:
                print(f"\n🔥 SUSTAINED HIGH LOAD: {status}")
                print("👉 ACTION: ACTIVATE AFMAT FAN NOW")
                winsound.Beep(1000, 1000) # Longer beep for urgent action
                streak = 0 # Reset after alert
                
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nSentry deactivated.")

if __name__ == "__main__":
    monitor_vitals()