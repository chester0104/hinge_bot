import pyautogui
import time
import signal
import sys
import random
from pynput import mouse

pyautogui.FAILSAFE = False

class HingeSwiper:
    def __init__(self):
        self.running = True
        self.setup_signal_handler()
        self.click_type = None
    
    def setup_signal_handler(self):
        def signal_handler(sig, frame):
            print("\nReceived interrupt signal, shutting down...")
            self.running = False
            # sys.exit(0) # This can be abrupt, let the loop terminate gracefully
        
        signal.signal(signal.SIGINT, signal_handler)
    
    def on_click(self, x, y, button, pressed):
        if pressed:
            if button == mouse.Button.left:
                self.click_type = 'left'
            elif button == mouse.Button.right:
                self.click_type = 'right'
            elif button == mouse.Button.middle:
                print("\nMiddle-click detected, stopping script...")
                self.running = False
            return False  # Stop listener

    def perform_like_sequence(self):
        """Performs the clicks to like a profile."""
        # Double-click where the cursor was during scrolling
        time.sleep(0.1)
        pyautogui.click(518, 1410, clicks=2, interval=0.1)
        time.sleep(0.5)
        
        # Click to send like
        pyautogui.click(610, 1722)
        time.sleep(0.8)
    
    def run_automation(self):
        print("Hinge Semi-Auto Swiper")
        print("=" * 50)
        print("Controls: LEFT=Pass | RIGHT=Like | MIDDLE=Quit")
        print("Screen area: (8,178) to (988, 2238)\n")
        
        like_count = 0
        profile_count = 0
        
        while self.running:
            try:
                profile_count += 1
                print(f"\n═══ Profile #{profile_count} ═══")
                
                self.click_type = None
                scroll_count = 0

                listener = mouse.Listener(on_click=self.on_click)
                listener.start()
                
                # Move mouse over the profile to make scrolling active
                pyautogui.moveTo(518, 1410)
                
                while not self.click_type and self.running:
                    if scroll_count < 55:
                        scroll_amount = -random.randint(1000, 5000) # Negative for scrolling down
                        pyautogui.moveTo(518, 1410)
                        pyautogui.scroll(scroll_amount, x=518, y=1410)
                        scroll_count += 1
                        print(f"\rScrolling: {scroll_count}/55", end='', flush=True)
                    else:
                        if scroll_count == 55:
                            print(f"\rScrolling: Complete - Waiting for input...", end='', flush=True)
                            scroll_count += 1 # To prevent this message from repeating
                        time.sleep(0.1)

                if not self.running:
                    listener.stop()
                    break
                
                listener.join()
                print() # for new line after scroll progress

                if self.click_type == 'right':
                    like_count += 1
                    self.perform_like_sequence()
                    print(f"✓ Liked (Total: {like_count})")

                elif self.click_type == 'left':
                    time.sleep(0.2)
                    pyautogui.click(138, 1925, clicks=2, interval=0.1)
                    print("✗ Passed")
                
                # Very short delay before next profile
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\nProgram interrupted by user")
                break
            except Exception as e:
                print(f"Error in automation loop: {e}")
                time.sleep(1)  # Short error recovery delay
        
        print("\nSemi-Auto swiper stopped")

def main():
    bot = HingeSwiper()
    bot.run_automation()

if __name__ == "__main__":
    main()