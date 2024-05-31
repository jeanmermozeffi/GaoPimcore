import requests
import os
import re
import time
from datetime import datetime
import unidecode
import uuid

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException

import pandas as pd
from pandas.errors import EmptyDataError
import numpy as np


class Largus:
    def __init__(self):
        pass