from __future__ import annotations
from typing import Any, Dict, Union
from io import BytesIO
import json, re
from pypdf import PdfReader
from openai import OpenAI

import os, sys, traceback, shutil
from datetime import datetime

import streamlit as st
import pandas as pd
from io import BytesIO
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from datetime import datetime
import re 