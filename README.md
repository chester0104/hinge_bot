# hinge_bot
An automated dating profile evaluator that uses OpenAI's Vision API (4o-mini) to analyze Hinge profiles through screenshots and make like/pass decisions based on visual analysis.

## Features
AI Vision Analysis: Captures multiple screenshots while scrolling through profiles and sends them to GPT-4o-mini for evaluation
Automated Actions: Automatically likes or passes profiles based on AI decisions
Token Management: Built-in token usage tracking and limits to manage OpenAI API costs
Sound Effects: Optional audio feedback for likes/passes
Special Sequences: Handles Hinge's UI quirks (refreshes after every 8 likes)

## How It Works
Scrolls through each profile in randomized patterns
Captures 6 screenshots at different scroll positions
Sends screenshots to OpenAI Vision API for analysis
Executes like/pass action based on AI response
Cleans up temporary screenshot files
Tracks token usage to stay within daily limits

## Requirements
Python 3.x
OpenAI API key
Tesseract OCR
Libraries: pyautogui, opencv-python, pytesseract, pygame, Pillow, requests, python-dotenv

## Setup
Create a .env file with your OpenAI API key:
OPENAI_API_KEY=your_key_here

Run the bot and configure token limits when prompted.

Please use responsibly and in accordance with Hinge's TOS.
