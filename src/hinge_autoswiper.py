import pyautogui
import time
import signal
import sys
import random

pyautogui.FAILSAFE = False

class HingeSwiper:
    def __init__(self):
        self.running = True
        self.setup_signal_handler()
    
    def setup_signal_handler(self):
        def signal_handler(sig, frame):
            print("\nReceived interrupt signal, shutting down...")
            self.running = False
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
    
    def perform_like_action(self):
        """Always like the profile"""
        # Double-click at fixed coordinates (500, 1000)
        pic_x, pic_y = 500, 1000
        
        pyautogui.click(pic_x, pic_y, clicks=2, interval=0.25)
        time.sleep(0.5)
        
        # Send Like button coordinates
        send_like_x = 618
        send_like_y = 1720
        
        pyautogui.moveTo(send_like_x, send_like_y)
        time.sleep(0.1)
        pyautogui.click(send_like_x, send_like_y)
        time.sleep(0.8)
    
    def perform_special_action_sequence(self):
        """Performs the special sequence of actions after every 8 likes."""
        print("→ Starting special sequence...")
        
        pyautogui.click(715, 2130)
        time.sleep(1)
        
        pyautogui.click(938, 591)
        time.sleep(1)
        
        # Repeat 8 times
        for i in range(8):
            print(f"\r  Special sequence: {i + 1}/8", end='', flush=True)
            pyautogui.moveTo(850, 800)
            pyautogui.dragTo(50, 750, duration=0.5, button='left')
            time.sleep(1)
            
            pyautogui.click(622, 775)
            time.sleep(1)
            
        pyautogui.click(103, 2127)
        time.sleep(1)
        
        print("\r✓ Special sequence complete    ")
    
    def run_automation(self):
        print("Hinge Auto-Swiper")
        print("=" * 50)
        print("Screen area: (8,178) to (988, 2238) | Press Ctrl+C to stop\n")
        
        profile_count = 0
        
        while self.running:
            try:
                profile_count += 1
                
                # Wait for a short interval before liking
                wait_time = random.uniform(0.5, 1.5)
                time.sleep(wait_time)
                
                self.perform_like_action()
                print(f"✓ Profile #{profile_count} liked")
                
                # Check if it's time for the special action sequence
                if profile_count % 8 == 0:
                    self.perform_special_action_sequence()
                
                # Very short delay before next profile
                time.sleep(0.2)
                
            except KeyboardInterrupt:
                print("\nProgram interrupted by user")
                break
            except Exception as e:
                print(f"Error in automation loop: {e}")
                time.sleep(1)  # Short error recovery delay
        
        print("\nAuto-swiper stopped")

def main():
    bot = HingeSwiper()
    bot.run_automation()

if __name__ == "__main__":
    main()