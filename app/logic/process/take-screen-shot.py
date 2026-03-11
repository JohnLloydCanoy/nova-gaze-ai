# This is a function where we take a screen shot of the user's screen and save it to a file. We will use the pyautogui library to take the screen shot and save it to a file. We will also use the screenshot to be submitted to the Nova client for analysis. This is a crucial part of the app as it allows us to capture the user's screen and provide insights based on the visual data. We will also briefly hide the app window to ensure we capture a clean screenshot of the desktop without our own interface in it. this function will be called when the user submits a chat message, allowing us to provide context-aware responses based on the current state of the user's screen. 
import os
import time
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QBuffer, QIODevice
import pyautogui
from app.aws_nova.client import NovaAIClient


