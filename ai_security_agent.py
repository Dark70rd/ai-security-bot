#!/usr/bin/env python3
"""
AI Security Agent
Analyzes raw scan results from Nmap, Nuclei, and SQLMap using Google Gemini.
"""

import os
import sys
from datetime import datetime

# Import the Google Generative AI library (using new google-genai package)
try:
    import google.genai as genai
except ImportError:
    try:
        # Fallback to deprecated library if new one not available
        import google.generativeai as genai
    except ImportError:
        print("[ERROR] google-genai package not found. Installing...")
        os.system("pip install google-genai")
        import google.genai as genai

# Import OpenAI as alternative
try:
    import openai
except ImportError:
    print("[WARN] OpenAI package not available. Only Google Gemini will be used.")
    openai = None

def configure_api():
    """Configure the API key and model."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set.")
    
    genai.configure(api_key=api_key)
    
    # Use current stable models (May 2026)
    # gemini-1.5-flash does NOT exist - use gemini-2.0-flash instead
    model_name = "gemini-2.0-flash"
    
    try:
        model = genai.GenerativeModel(model_name)
        print(f"[+] Successfully initialized model: {model_name}")
        return model
    except Exception as e:
        print(f"[ERROR] Failed to initialize model '{model_name}': {e}")
        # Fallback to alternative models if primary fails
        fallback_models = ["gemini-2.0-pro", "gemini-1.5-pro"]
        for fallback in fallback_models:
            try:
                print(f"[+] Trying fallback model: {fallback}...")
                model = genai.GenerativeModel(fallback)
                print(f"[+] Successfully initialized fallback model: {fallback}")
                return model
            except Exception as fb_err:
                print(f"[ERROR] Fallback '{fallback}' also failed: {fb_err}")
        
        raise RuntimeError("All model initialization attempts failed.")

def analyze_with_openai(target_url, nmap_results, nuclei_results, sqlmap_results):
    """Fallback analysis using OpenAI when Google quota is exceeded."""

    if not openai:
        print("[ERROR] OpenAI library not available")
        return None

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("[WARN] OPENAI_API_KEY not set, skipping OpenAI fallback")
        return None

    try:
        client = openai.OpenAI(api_key=openai_key)

        prompt = f"""You are a cybersecurity analyst. Analyze these security scan results for {target_url}.

SCAN RESULTS:
==========
NMAP PORT SCAN:
{nmap_results}

NUCLEI VULNERABILITY SCAN:
{nuclei_results}

SQLMAP INJECTION TEST:
{sqlmap_results}
==========

Create a professional security report with:
1. Executive Summary (2-3 sentences)
2. Key Findings by severity (Critical/High/Medium/Low)
3. Network Analysis (port status, firewall detection)
4. Recommendations

Be concise but thorough. Focus on actionable insights."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.3
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"[ERROR] OpenAI fallback failed: {e}")
        return None

def generate_fallback_report(target_url, nmap_results, nuclei_results, sqlmap_results):
    """Generate a basic security report when AI analysis is unavailable."""

    # Basic analysis functions
    def analyze_nmap(output):
        findings = []
        if "filtered" in output.lower():
            findings.append("🔥 **Firewall Detected** - Ports are being filtered, indicating active network protection")
        if "open" in output.lower():
            findings.append("⚠️ **Open Ports Found** - Review port exposure and running services")
        if "80/tcp" in output or "443/tcp" in output:
            findings.append("ℹ️ **Web Services Detected** - HTTP/HTTPS ports are accessible")
        return findings

    def analyze_nuclei(output):
        findings = []
        if "no results found" in output.lower() or len(output.strip()) < 50:
            findings.append("✅ **No Critical Vulnerabilities** - Nuclei scan completed with no findings")
        else:
            findings.append("⚠️ **Potential Vulnerabilities** - Review Nuclei output for specific issues")
        return findings

    def analyze_sqlmap(output):
        findings = []
        if "no injection" in output.lower() or "not injectable" in output.lower():
            findings.append("✅ **No SQL Injection** - SQLMap found no injection vulnerabilities")
        elif "injectable" in output.lower():
            findings.append("🔥 **SQL Injection Risk** - Potential SQL injection vulnerabilities detected")
        else:
            findings.append("⚠️ **SQL Injection Test Completed** - Review output for injection attempts")
        return findings

    # Generate report
    report = f"""# Security Scan Report - {target_url}

## ⚠️ AI Analysis Unavailable (Quota Exceeded)

Due to API quota limitations, automated AI analysis is currently unavailable. Below is a basic automated analysis of the scan results.

## Executive Summary

Automated security scan completed for {target_url}. Manual review of raw scan data is recommended for comprehensive analysis.

## Scan Results Analysis

### 🔍 Network Analysis (Nmap)
{chr(10).join(f"- {finding}" for finding in analyze_nmap(nmap_results))}

### 🛡️ Vulnerability Assessment (Nuclei)
{chr(10).join(f"- {finding}" for finding in analyze_nuclei(nuclei_results))}

### 💉 SQL Injection Testing (SQLMap)
{chr(10).join(f"- {finding}" for finding in analyze_sqlmap(sqlmap_results))}

## Recommendations

1. **Review Raw Data** - Examine the complete scan outputs below for detailed findings
2. **Manual Verification** - Perform manual testing to validate automated results
3. **Quota Management** - Consider upgrading your Google Gemini API plan for unlimited analysis
4. **Alternative AI Services** - Consider using OpenAI, Anthropic, or other AI providers

## Raw Scan Data

### Nmap Results
```
{nmap_results}
```

### Nuclei Results
```
{nuclei_results}
```

### SQLMap Results
```
{sqlmap_results}
```

---
*Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Analysis: Basic automated parsing (AI quota exceeded)*
"""

    return report

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
    """Send scan results to the AI for analysis with quota management."""

    # Sanitize inputs BEFORE constructing the prompt
    safe_nmap = sanitize_input(nmap_results)
    safe_nuclei = sanitize_input(nuclei_results)
    safe_sqlmap = sanitize_input(sqlmap_results)

    # Create a more structured and concise prompt
    prompt = f"""You are a cybersecurity analyst. Analyze these security scan results for {target_url}.

SCAN RESULTS:
==========
NMAP PORT SCAN:
{safe_nmap}

NUCLEI VULNERABILITY SCAN:
{safe_nuclei}

SQLMAP INJECTION TEST:
{safe_sqlmap}
==========

Create a professional security report with:
1. Executive Summary (2-3 sentences)
2. Key Findings by severity (Critical/High/Medium/Low)
3. Network Analysis (port status, firewall detection)
4. Recommendations

Be concise but thorough. Focus on actionable insights."""

    # Try AI analysis with quota management
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"[+] Attempting AI analysis (attempt {attempt + 1}/{max_retries})...")

            # Generate content using the current SDK
            response = model.generate_content(prompt)

            if not response or not response.text:
                raise ValueError("AI returned empty response.")

            return response.text

        except Exception as e:
            error_msg = str(e).lower()

            # Check for quota exceeded errors
            if "quota" in error_msg or "429" in error_msg or "rate limit" in error_msg:
                if attempt < max_retries - 1:
                    wait_time = 30 * (attempt + 1)  # Progressive backoff: 30s, 60s, 90s
                    print(f"[WARN] Quota exceeded. Retrying in {wait_time} seconds...")
                    import time
                    time.sleep(wait_time)
                    continue
                else:
                    print("[WARN] Google quota exceeded after retries. Trying OpenAI fallback...")
                    openai_result = analyze_with_openai(target_url, safe_nmap, safe_nuclei, safe_sqlmap)
                    if openai_result:
                        print("[+] OpenAI fallback successful!")
                        return openai_result
                    else:
                        print("[ERROR] OpenAI fallback also failed. Using basic analysis.")
                        return generate_fallback_report(target_url, safe_nmap, safe_nuclei, safe_sqlmap)
            else:
                # Other errors - try OpenAI fallback immediately
                print(f"[ERROR] Google AI failed: {e}")
                print("[WARN] Trying OpenAI fallback...")
                openai_result = analyze_with_openai(target_url, safe_nmap, safe_nuclei, safe_sqlmap)
                if openai_result:
                    print("[+] OpenAI fallback successful!")
                    return openai_result
                else:
                    print("[ERROR] OpenAI fallback failed. Using basic analysis.")
                    return generate_fallback_report(target_url, safe_nmap, safe_nuclei, safe_sqlmap)

    # This should never be reached, but just in case
    return generate_fallback_report(target_url, safe_nmap, safe_nuclei, safe_sqlmap)

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