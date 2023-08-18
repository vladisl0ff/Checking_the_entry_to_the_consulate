# Checking the entry to the consulate
This project is a Python-based Telegram bot designed to help users monitor available appointment slots at the Russian Embassy located in Belgrade, Serbia. The bot leverages the aiogram framework to interact with the Telegram Bot API. Its primary function is to periodically check the availability of appointment slots for consular services at the specified embassy and notify users when slots become available.

# Features:
### 1. User Registration:
* When users initiate a conversation with the bot using the "/start" command, they are guided through the registration process.
* Users are prompted to provide the URL of the Russian Embassy's appointment booking page and a time interval for checking.

### 2. Automated Availability Checks and Notifications:

* The bot continuously monitors the provided URL for available appointment slots at the Russian Embassy in Belgrade.
* It performs regular checks at the specified time intervals and sends notifications to users via Telegram messages if slots become available.

### 3. User Interaction and Control:

* Users can start and stop the automated checking process using predefined keyboard buttons.
* Users can also change their registered URL and time interval settings through interaction with the bot.

### 4. Captcha Handling:

* The bot includes mechanisms to handle captcha challenges on the appointment booking page.
* It captures and processes captcha images, extracts digits using optical character recognition (OCR), and submits the captcha response.

### 5. Persistent Data Storage:

* User registration data, including URL and time interval preferences, are stored in a database.
* The Finite State Machine (FSM) provided by aiogram is used to manage user states during the registration process.

# Dependencies:
* `aiogram`: A Python framework for interacting with the Telegram Bot API.
* `validators`: A library for validating URLs.
* `easyocr`: Optical character recognition library for extracting digits from captcha images.
* `selenium`: Web automation library for browser control.
* `PIL`: Python Imaging Library for image manipulation.
* `aiogram.contrib`: Components and middleware from aiogram for extended functionality.

# Usage:
* Users start interacting with the bot by sending the "/start" command.
* The bot guides users through the registration process, including providing the URL of the Russian Embassy's appointment booking page and a desired time interval.
* The bot periodically checks the specified URL for available appointment slots, sending notifications to users through Telegram messages.
* Users can modify their settings, start/stop checks, and interact with the bot using predefined keyboard buttons.

It's important to note that this project requires access to the Telegram Bot API and integration with an actual Telegram bot token. Additionally, since the bot interacts with web content, updates may be required to accommodate changes in the structure of the embassy's appointment booking page.

Feel free to explore the code and adapt it according to your needs. If you have any questions or need further assistance, feel free to ask!
