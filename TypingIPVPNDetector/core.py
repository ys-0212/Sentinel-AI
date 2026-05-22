# core.py - Raw wrapper for TypingIPVPNDetector
# Provides raw input/output functions without Streamlit dependency

import os
import sqlite3
import numpy as np
import requests
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

# Load environment variables
# Get the directory where this file is located
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_ENV_PATH = os.path.join(_CURRENT_DIR, ".env")
load_dotenv(_ENV_PATH)

_DB_PATH = os.path.join(_CURRENT_DIR, "local.db")


class BehaviorAnalyzer:
    """Analyzes user login behavior for anomalies."""
    
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
    
    def extract_features(self, session_data: dict) -> np.ndarray:
        """Extract feature vector from session data."""
        features = [
            session_data.get("typing_speed", 0),
            session_data.get("mouse_movements", 0),
            int(session_data.get("vpn_detected", False)),
            session_data.get("form_completion_time", 0),
            hash(session_data.get("location", "")) % 1000,
            hash(session_data.get("device_fingerprint", "")) % 1000,
            (100 - session_data.get("typing_dna_confidence", 100)) / 100.0
        ]
        return np.array(features).reshape(1, -1)
    
    def analyze(self, current_data: dict, historical_data: list) -> dict:
        """
        Analyze current session against historical behavior.
        
        Args:
            current_data: Current session data dict
            historical_data: List of historical session dicts
            
        Returns:
            dict with is_anomaly, risk_score, reasons
        """
        reasons = []
        
        if not historical_data:
            return {
                "is_anomaly": False,
                "risk_score": 0.5,
                "reasons": ["New user - establishing baseline behavior."]
            }
        
        current_features = self.extract_features(current_data)
        historical_features = np.vstack([
            self.extract_features(h) for h in historical_data
        ])
        
        similarity = cosine_similarity(current_features, historical_features)
        risk_score = float(1 - np.mean(similarity))
        risk_score = max(0, min(1, risk_score))
        
        is_anomaly = risk_score > self.threshold
        
        # Check specific risk factors
        if current_data.get("typing_dna_confidence", 100) < 70:
            reasons.append(f"Low typing biometrics confidence: {current_data['typing_dna_confidence']}%")
        
        common_locations = {r.get("location") for r in historical_data}
        if current_data.get("location") not in common_locations:
            reasons.append(f"New location detected: {current_data.get('location')}")
        
        if current_data.get("vpn_detected"):
            reasons.append("VPN or Proxy usage detected.")
        
        common_fingerprints = {r.get("device_fingerprint") for r in historical_data}
        if current_data.get("device_fingerprint") not in common_fingerprints:
            reasons.append("New device fingerprint detected.")
        
        if is_anomaly and not reasons:
            reasons.append("General behavior pattern deviates from historical norms.")
        
        return {
            "is_anomaly": is_anomaly,
            "risk_score": risk_score,
            "reasons": reasons
        }


class IPAnalyzer:
    """Analyzes IP address for VPN/proxy and geolocation."""
    
    def __init__(self):
        self.ipstack_key = os.getenv("IPSTACK_KEY")
        self.ipqualityscore_key = os.getenv("IPQUALITYSCORE_KEY")
    
    def get_geolocation(self, ip_address: str) -> dict:
        """Get geolocation data for an IP address."""
        if not self.ipstack_key:
            return {"error": "IPSTACK_KEY not configured"}
        
        try:
            url = f"http://api.ipstack.com/{ip_address}?access_key={self.ipstack_key}"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_fraud_score(self, ip_address: str) -> dict:
        """Get fraud/VPN detection data for an IP address."""
        if not self.ipqualityscore_key:
            return {"error": "IPQUALITYSCORE_KEY not configured"}
        
        try:
            url = f"https://ipqualityscore.com/api/json/ip/{self.ipqualityscore_key}/{ip_address}"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_ip(self, ip_address: str) -> dict:
        """
        Complete IP analysis including geolocation and fraud detection.
        
        Returns:
            dict with location, vpn_detected, proxy_detected, fraud_score, etc.
        """
        geo_data = self.get_geolocation(ip_address)
        fraud_data = self.get_fraud_score(ip_address)
        
        location = "Unknown"
        if "city" in geo_data and "country_name" in geo_data:
            location = f"{geo_data.get('city', 'Unknown')}, {geo_data.get('country_name', 'Unknown')}"
        
        return {
            "ip_address": ip_address,
            "location": location,
            "vpn_detected": fraud_data.get("vpn", False),
            "proxy_detected": fraud_data.get("proxy", False),
            "fraud_score": fraud_data.get("fraud_score", 0),
            "geolocation_data": geo_data,
            "fraud_data": fraud_data
        }


def analyze_login_behavior(session_data: dict, historical_data: list = None) -> dict:
    """
    Analyze login behavior for anomalies.
    
    Args:
        session_data: Current session data with keys:
            - typing_speed: int (words per minute)
            - mouse_movements: int
            - location: str
            - ip_address: str
            - vpn_detected: bool
            - device_fingerprint: str
            - form_completion_time: int (seconds)
            - typing_dna_confidence: int (0-100)
        historical_data: Optional list of previous session dicts
        
    Returns:
        dict with is_anomaly, risk_score, reasons
    """
    analyzer = BehaviorAnalyzer()
    return analyzer.analyze(session_data, historical_data or [])


def analyze_ip_address(ip_address: str) -> dict:
    """
    Analyze an IP address for VPN/proxy usage and geolocation.
    
    Args:
        ip_address: The IP address to analyze
        
    Returns:
        dict with location, vpn_detected, proxy_detected, fraud_score, etc.
    """
    analyzer = IPAnalyzer()
    return analyzer.analyze_ip(ip_address)


# Test function
if __name__ == "__main__":
    import json
    
    # Test behavior analysis
    current_session = {
        "typing_speed": 45,
        "mouse_movements": 200,
        "location": "Mumbai, India",
        "ip_address": "8.8.8.8",
        "vpn_detected": False,
        "device_fingerprint": "abc123",
        "form_completion_time": 30,
        "typing_dna_confidence": 85
    }
    
    historical = [
        {
            "typing_speed": 50,
            "mouse_movements": 180,
            "location": "Mumbai, India",
            "ip_address": "8.8.8.8",
            "vpn_detected": False,
            "device_fingerprint": "abc123",
            "form_completion_time": 25,
            "typing_dna_confidence": 90
        }
    ]
    
    result = analyze_login_behavior(current_session, historical)
    print("Behavior Analysis:")
    print(json.dumps(result, indent=2))
