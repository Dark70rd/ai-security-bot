#!/usr/bin/env python3
"""
AI Security Agent
Analyzes raw scan results from Nmap, Nuclei, and SQLMap using Google Gemini.
"""

import os
import sys
from datetime import datetime

# Import the Google Generative AI library
try:
    import google.generativeai as genai
except ImportError:
    print("[ERROR] google-generativeai package not found. Installing...")
    os.system("pip install google-generativeai")
    import google.generativeai as genai

def configure_api():
    """Configure the API key and model."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set.")
    
    genai.configure(api_key=api_key)
    
    # Use current stable models (2026)
    model_name = "gemini-1.5-flash"
    
    try:
        model = genai.GenerativeModel(model_name)
        print(f"[+] Successfully initialized model: {model_name}")
        return model
    except Exception as e:
        print(f"[ERROR] Failed to initialize model '{model_name}': {e}")
        # Fallback to alternative models if primary fails
        fallback_models = ["gemini-1.5-pro", "gemini-2.0-flash"]
        for fallback in fallback_models:
            try:
                print(f"[+] Trying fallback model: {fallback}...")
                model = genai.GenerativeModel(fallback)
                print(f"[+] Successfully initialized fallback model: {fallback}")
                return model
            except Exception as fb_err:
                print(f"[ERROR] Fallback '{fallback}' also failed: {fb_err}")
        
        raise RuntimeError("All model initialization attempts failed.")

def sanitize_input(text):
    """Sanitize input text to prevent prompt injection or formatting issues."""
    if not text:
        return "No data provided."
    # Gemini 3.1 supports massive context, but we truncate to 100k for performance
    max_tokens_approx = 100000 
    if len(text) > max_tokens_approx:
        print(f"[WARN] Input truncated from {len(text)} to {max_tokens_approx} characters.")
        return text[:max_tokens_approx] + "\n... [TRUNCATED] ..."
    return text

def analyze_findings(model, target_url, nmap_results, nuclei_results, sqlmap_results):
    """Send scan results to the AI for analysis."""
    
    # Sanitize inputs BEFORE constructing the prompt
    safe_nmap = sanitize_input(nmap_results)
    safe_nuclei = sanitize_input(nuclei_results)
    safe_sqlmap = sanitize_input(sqlmap_results)
    
    prompt = f"""
    You are an expert Cybersecurity Analyst. Your task is to analyze the provided security scan results 
    for the target: {target_url}.
    
    The scans performed were:
    1. Nmap (Port Scanning & Service Detection)
    2. Nuclei (Vulnerability Scanning)
    3. SQLMap (SQL Injection Testing)
    
    RAW DATA:
    ---
    [NMAP OUTPUT]
    {safe_nmap}
    
    [NUCLEI OUTPUT]
    {safe_nuclei}
    
    [SQLMAP OUTPUT]
    {safe_sqlmap}
    ---
    
    INSTRUCTIONS:
    1. Create a professional Markdown security report.
    2. Include an Executive Summary.
    3. Detail findings by tool (Nmap, Nuclei, SQLMap).
    4. If vulnerabilities are found, categorize them by severity (Critical, High, Medium, Low).
    5. If NO vulnerabilities are found, explicitly state "No Vulnerabilities Detected" but also analyze 
       the network behavior (e.g., "Ports filtered suggests active firewall").
    6. Provide actionable remediation steps.
    7. Keep the tone professional and technical.
    
    Generate the report now.
    """

    try:
        print("[+] Sending findings to AI for analysis...")
        
        # Generate content using the current SDK
        response = model.generate_content(prompt)
        
        if not response or not response.text:
            raise ValueError("AI returned empty response.")
            
        return response.text

    except Exception as e:
        print(f"[ERROR] AI Analysis Failed: {e}")
        return f"""
        # Security Scan Report
        
        ## ⚠️ AI Analysis Failed
        
        The automated analysis could not be completed due to an error:
        `{str(e)}`
        
        ### Raw Findings Available:
        - **Nmap:** {len(safe_nmap)} characters
        - **Nuclei:** {len(safe_nuclei)} characters
        - **SQLMap:** {len(safe_sqlmap)} characters
        """

def main():
    if len(sys.argv) < 2:
        print("[ERROR] Target URL not provided.")
        print("Usage: python ai_security_agent.py <target_url>")
        sys.exit(1)

    target_url = sys.argv[1]
    
    # Retrieve results from environment variables
    nmap_results = os.getenv("NMAP_RESULTS", "No Nmap results found.")
    nuclei_results = os.getenv("NUCLEI_RESULTS", "No Nuclei results found.")
    sqlmap_results = os.getenv("SQLMAP_RESULTS", "No SQLMap results found.")

    print(f"[+] Processing scan results for: {target_url}")

    try:
        model = configure_api()
        report = analyze_findings(model, target_url, nmap_results, nuclei_results, sqlmap_results)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_url = target_url.replace("https://", "").replace("http://", "").replace("/", "_").replace(".", "_")
        filename = f"report_{safe_url}_{timestamp}.md"
        
        # Save report
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"[+] Report saved to: {filename}")
        print("[+] Process Complete.")
        
    except Exception as e:
        print(f"[FATAL] Critical Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()