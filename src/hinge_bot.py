import pyautogui
import time
import json
import requests
import signal
import sys
import os
from dotenv import load_dotenv
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageGrab
import random
import base64
import io
import pygame

load_dotenv()

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

pyautogui.FAILSAFE = False

class ScreenCapture:
    def __init__(self, x1=8, y1=178, x2=982, y2=2032):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.width = x2 - x1
        self.height = y2 - y1
    
    def capture_screen(self):
        screenshot = ImageGrab.grab(bbox=(self.x1, self.y1, self.x2, self.y2))
        return screenshot
    
    def extract_text(self):
        screenshot = self.capture_screen()
        screenshot_np = np.array(screenshot)
        
        try:
            text = pytesseract.image_to_string(screenshot_np, config='--psm 6')
            return text.strip()
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""
    
    def search_text(self, query):
        text = self.extract_text()
        return query.lower() in text.lower()
    
    def get_text_coordinates(self, query):
        if self.search_text(query):
            center_x = self.x1 + self.width // 2
            center_y = self.y1 + self.height // 2
            return (center_x, center_y)
        return None

class OpenAIClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1/chat/completions"
    
    def compress_and_encode_image(self, image_path, max_size=(512, 512), quality=85):
        """Compress image, resize, and encode to base64"""
        try:
            with Image.open(image_path) as img:
                img.thumbnail(max_size)
                
                # Use JPEG for compression
                buffer = io.BytesIO()
                img.convert("RGB").save(buffer, format="JPEG", quality=quality)
                
                return base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"Error compressing image {image_path}: {e}")
            return None
    
    def analyze_screenshots(self, screenshot_paths):
        """Analyze multiple screenshots using OpenAI Vision API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare the messages with images
        messages = [
            {
                "role": "system", 
                "content": "You are analyzing dating profile screenshots to decide like or pass. ONLY look at the girl's SOLO photos and judge based on physical attractiveness. You MUST NOT like any profiles with ugly, fat, or overly masculine girls. Ignore bio text, interests, and everything else - only focus on the girl's appearance in photos. Pay especially close attention to pictures where there is only one girl, and you MUST decide from pictures like that whether or not she is ugly or fat."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Look ONLY at the girl's SOLO photos in these screenshots. Pay especially close attention to pictures where there is only one girl, and you MUST decide from pictures like that whether or not she is ugly, fat, or overly masculine. Judge purely on physical attractiveness. Is she hot and not fat and not overly masculine? Be brutally honest about her appearance only. Keep your response concise, and YOU MUST RESPOND CONCISELY with a SHORT CRITIQUE based on the criterion mentioned with a max of 25 words. Ignore all text, bio, and interests. End your response with '[like]' if she's attractive OR if there is NO Solo photo of the girl, but '[pass]' if she's ugly, or chubby/overweight/fat, or overly masculine."
                    }
                ]
            }
        ]
        
        # Add each screenshot to the message
        for i, screenshot_path in enumerate(screenshot_paths):
            try:
                base64_image = self.compress_and_encode_image(screenshot_path)
                if not base64_image:
                    continue
                messages[1]["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                        "detail": "low"
                    }
                })
            except Exception as e:
                print(f"Error encoding image {screenshot_path}: {e}")
                continue
        
        data = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=60)
            
            if response.status_code != 200:
                print(f"API Error: {response.status_code} - {response.text}")
                return f"API Error: {response.status_code} - {response.text}"
            
            response.raise_for_status()
            
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return "Error: No response from API"
                
        except requests.exceptions.RequestException as e:
            print(f"Request exception: {e}")
            return f"API Error: {e}"
        except Exception as e:
            print(f"General exception: {e}")
            return f"Error: {e}"
    
    def send_completion(self, prompt, model="gpt-4", max_tokens=4000):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": "be very concise, funny, sarcastic, like a friend giving you advice."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return "Error: No response from API"
                
        except requests.exceptions.RequestException as e:
            return f"API Error: {e}"
        except Exception as e:
            return f"Error: {e}"

class HingeBot:
    def __init__(self):
        self.screen = ScreenCapture()
        self.openai_client = None
        self.running = True
        self.like_count = 0
        self.profile_count = 0
        self.api_calls_made = 0  # Track actual API calls for accurate token counting
        self.tokens_per_profile = 0
        self.max_profiles = 0
        self.sound_effects_enabled = False
        self.like_sound = None
        self.pass_sound = None
        
        self.setup_openai()
        self.setup_signal_handler()
        self.setup_token_limits()
        self.setup_sound_effects()
    
    def setup_signal_handler(self):
        def signal_handler(sig, frame):
            print("\n" + "=" * 50)
            print("PROGRAM INTERRUPTED BY USER")
            print("=" * 50)
            self.display_summary()
            print("=" * 50)
            self.running = False
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
    
    def setup_openai(self):
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            print("Error: OPENAI_API_KEY not found in .env file.")
            print("Please create a .env file with: OPENAI_API_KEY=your_api_key_here")
            sys.exit(1)
        
        self.openai_client = OpenAIClient(api_key)
    
    def setup_token_limits(self):
        """Ask user for tokens used today and tokens per profile, then calculate max profiles"""
        TOKEN_LIMIT = 2500000
        
        print("\n" + "=" * 50)
        print("TOKEN USAGE CONFIGURATION")
        print("=" * 50)
        print(f"OpenAI API Daily Token Limit: {TOKEN_LIMIT:,} tokens")
        
        # First ask for tokens already used today
        tokens_used_today = 0
        while True:
            try:
                tokens_used_input = input("Enter tokens already used today: ")
                tokens_used_today = int(tokens_used_input)
                
                if tokens_used_today < 0:
                    print("Error: Tokens used today cannot be negative")
                    continue
                
                if tokens_used_today >= TOKEN_LIMIT:
                    print(f"Error: Tokens used today ({tokens_used_today:,}) exceeds or equals daily limit ({TOKEN_LIMIT:,})")
                    continue
                
                break
                
            except ValueError:
                print("Error: Please enter a valid number")
            except KeyboardInterrupt:
                print("\nSetup cancelled by user")
                sys.exit(0)
        
        # Calculate remaining tokens
        remaining_tokens = TOKEN_LIMIT - tokens_used_today
        print(f"Remaining tokens available: {remaining_tokens:,}")
        
        # Then ask for tokens per profile
        while True:
            try:
                tokens_input = input("Enter estimated tokens used per profile: ")
                self.tokens_per_profile = int(tokens_input)
                
                if self.tokens_per_profile <= 0:
                    print("Error: Tokens per profile must be greater than 0")
                    continue
                
                # Calculate max profiles: ((remaining_tokens) / tokens_per_profile) - 1
                self.max_profiles = int((remaining_tokens / self.tokens_per_profile) - 1)
                
                if self.max_profiles <= 0:
                    print(f"Error: Not enough tokens remaining. With {self.tokens_per_profile:,} tokens per profile, you can't process any profiles.")
                    continue
                
                print(f"\n✓ Configuration:")
                print(f"  - Tokens used today: {tokens_used_today:,}")
                print(f"  - Remaining tokens: {remaining_tokens:,}")
                print(f"  - Tokens per profile: {self.tokens_per_profile:,}")
                print(f"  - Max profiles to process: {self.max_profiles:,}")
                print(f"  - Estimated total tokens for this session: {self.max_profiles * self.tokens_per_profile:,}")
                print("=" * 50 + "\n")
                break
                
            except ValueError:
                print("Error: Please enter a valid number")
            except KeyboardInterrupt:
                print("\nSetup cancelled by user")
                sys.exit(0)
    
    def setup_sound_effects(self):
        """Ask user if they want sound effects enabled"""
        print("\n" + "=" * 50)
        print("SOUND EFFECTS CONFIGURATION")
        print("=" * 50)
        
        while True:
            try:
                response = input("Enable sound effects? (y/n): ").strip().lower()
                
                if response == 'y' or response == 'yes':
                    pygame.mixer.init()
                    self.like_sound = pygame.mixer.Sound("sfx/ding-sound-effect_1.mp3")
                    self.pass_sound = pygame.mixer.Sound("sfx/wrong-answer-sound-effect.mp3")
                    self.sound_effects_enabled = True
                    print("✓ Sound effects enabled")
                    print("=" * 50 + "\n")
                    break
                elif response == 'n' or response == 'no':
                    self.sound_effects_enabled = False
                    print("✓ Sound effects disabled")
                    print("=" * 50 + "\n")
                    break
                else:
                    print("Error: Please enter 'y' or 'n'")
                    
            except KeyboardInterrupt:
                print("\nSetup cancelled by user")
                sys.exit(0)
    
    def scroll_profile(self, scroll_count=5):
        center_x = 25
        center_y = 1111
        
        pyautogui.moveTo(center_x, center_y)
        
        if not hasattr(self, 'screenshots_to_delete'):
            self.screenshots_to_delete = []
        
        initial_screenshot = f"initial_profile.png"
        screenshot = self.screen.capture_screen()
        screenshot.save(initial_screenshot)
        time.sleep(0.1)
        self.screenshots_to_delete.append(initial_screenshot)
        
        for session_num in range(1, scroll_count + 1):  # FIXED: Renamed variable to avoid conflicts
            pyautogui.click(center_x, center_y)
            
            pyautogui.moveTo(center_x, center_y)
            
            # scroll amount 11 times that sum to EXACTLY 10,000 units
            target_total = 10000
            num_scrolls = 11
            
            # Generate random scroll amounts that add up to exactly 10,000
            scroll_amounts = []
            remaining_total = target_total
            
            # Generate n-1 random scrolls, then calculate the final one to hit exactly 10,000
            for scroll_idx in range(num_scrolls - 1):
                min_amount = 500
                max_amount = min(1200, remaining_total - (500 * (num_scrolls - scroll_idx - 1)))
                
                if max_amount <= min_amount:
                    scroll_amount = min_amount
                else:
                    scroll_amount = random.randint(min_amount, max_amount)
                
                scroll_amounts.append(scroll_amount)
                remaining_total -= scroll_amount
            
            # Final scroll gets exactly what's needed to reach 10,000
            final_scroll = remaining_total
            scroll_amounts.append(final_scroll)
            
            # Ensure the final scroll is reasonable (between 500-1200)
            if final_scroll < 500 or final_scroll > 1200:
                # Redistribute if final scroll is unreasonable
                scroll_amounts = []
                for _ in range(num_scrolls):
                    scroll_amounts.append(target_total // num_scrolls)
                
                # Add remainder to random scrolls
                remainder = target_total % num_scrolls
                for remainder_idx in range(remainder):  # FIXED: Different variable name
                    scroll_amounts[random.randint(0, num_scrolls - 1)] += 1
            
            # Verify we hit exactly 10,000 units
            actual_total = sum(scroll_amounts)
            
            # Safety check - this should always be 10,000 now
            assert actual_total == 10000, f"ERROR: Total was {actual_total}, not 10,000!"
            
            # Perform the scrolling with randomized amounts
            for scroll_idx, scroll_amount in enumerate(scroll_amounts):
                print(f"\rScroll Session {session_num}/{scroll_count}: {scroll_idx + 1}/{num_scrolls}", end='', flush=True)
                pyautogui.scroll(-scroll_amount)
            
            print(f"\rScroll Session {session_num}/{scroll_count}: Complete ✓")
            
            # Take screenshot after scrolling - FIXED: Use session_num instead of i
            screenshot_filename = f"scroll_session_{session_num}.png"
            screenshot = self.screen.capture_screen()
            screenshot.save(screenshot_filename)
            time.sleep(0.1)
            
            self.screenshots_to_delete.append(screenshot_filename)
        
        return self.screenshots_to_delete
    
    def cleanup_screenshots(self):
        if hasattr(self, 'screenshots_to_delete'):
            for screenshot_filename in self.screenshots_to_delete:
                try:
                    os.remove(screenshot_filename)
                except Exception as e:
                    print(f"Warning: Could not delete {screenshot_filename}: {e}")
            self.screenshots_to_delete = []
    
    def decide_like_or_pass(self, screenshot_paths):
        """Use OpenAI Vision API to analyze screenshots and decide like/pass"""
        response = self.openai_client.analyze_screenshots(screenshot_paths)
        self.api_calls_made += 1  # Increment after successful API call
        print(f"AI Analysis: {response}")
        
        if "[like]" in response.lower():
            return "like"
        else:
            return "pass"
    
    def perform_like_action(self):
        # Play ding sound effect if enabled (before action)
        if self.sound_effects_enabled:
            self.like_sound.play()
        
        # Double-click the picture to open the like dialog (copied from semi-auto swiper)
        time.sleep(0.1)
        pyautogui.click(518, 1410, clicks=2, interval=0.1)
        time.sleep(0.5)
        
        # Click to send like
        pyautogui.click(610, 1722)
        time.sleep(0.8)
        
        # Increment like counter
        self.like_count += 1
        print(f"✓ Like sent (Total: {self.like_count})")
        
        # Check if it's time for the special action sequence
        if self.like_count % 8 == 0:
            self.perform_special_action_sequence()
        
        self.cleanup_screenshots()
        return self.check_for_new_profile()
    
    
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
    
    def perform_pass_action(self):
        # Play wrong answer sound effect if enabled (before action)
        if self.sound_effects_enabled:
            self.pass_sound.play()
        
        # Use exact coordinates for X button
        pass_x = 105
        pass_y = 1865
        
        pyautogui.moveTo(pass_x, pass_y)
        pyautogui.click(pass_x, pass_y)
        
        # Wait for pass action to complete
        time.sleep(1)
        
        print("✗ Passed")
        self.cleanup_screenshots()
        return self.check_for_new_profile()
    
    def check_for_new_profile(self):
        screen_text = self.screen.extract_text().lower()
        
        profile_indicators = ["age", "miles away", "years old", "looking for", "about me"]
        
        for indicator in profile_indicators:
            if indicator in screen_text:
                return True
        
        return len(screen_text.strip()) > 50
    
    def display_summary(self):
        """Display summary statistics"""
        print(f"Total profiles processed: {self.profile_count}")
        print(f"Total likes given: {self.like_count}")
        print(f"Estimated tokens used: {self.api_calls_made * self.tokens_per_profile:,}")

    
    def run_automation(self):
        print("Starting Hinge automation with screenshot-based AI analysis...")
        print("Press Ctrl+C to stop\n")
        
        while self.running:
            try:
                # Check if max profiles limit has been reached
                if self.profile_count >= self.max_profiles:
                    print("\n" + "=" * 50)
                    print("MAX PROFILES LIMIT REACHED")
                    print("=" * 50)
                    self.display_summary()
                    print("=" * 50)
                    break
                
                self.profile_count += 1
                print(f"\n═══ Profile #{self.profile_count}/{self.max_profiles} ═══")
                
                screenshot_paths = self.scroll_profile()
                
                if len(screenshot_paths) == 0:
                    print("WARNING: No screenshots captured. Passing...")
                    self.perform_pass_action()
                    continue
                
                decision = self.decide_like_or_pass(screenshot_paths)
                
                if decision == "like":
                    self.perform_like_action()
                else:
                    self.perform_pass_action()
                
            except KeyboardInterrupt:
                print("\n" + "=" * 50)
                print("PROGRAM INTERRUPTED BY USER")
                print("=" * 50)
                self.display_summary()
                print("=" * 50)
                break
            except Exception as e:
                print(f"Error in automation loop: {e}")
                self.cleanup_screenshots()  # Clean up on error
        
        print("\nAutomation stopped")

def main():
    print("Hinge Bot - AI Vision Analysis")
    print("=" * 50)
    
    if not os.path.exists(".env"):
        print("Error: .env file not found")
        print("Please create a .env file with your OpenAI API key")
        sys.exit(1)
    
    bot = HingeBot()
    bot.run_automation()

if __name__ == "__main__":
    main()