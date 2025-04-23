
import argparse
import json
import math
import os
import random
import queue
import re
import time
import nodriver as uc
import requests
import subprocess
import threading
import multiprocessing
import numpy as np
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

from bs4 import BeautifulSoup as BS
from controllers.shared import *
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def writeParkFactors():
	url = "https://www.ballparkpal.com/Park-Factors.php"
	factors = nested_dict()

if __name__ == '__main__':
	parser = argparse.ArgumentParser()

	args = parser.parse_args()