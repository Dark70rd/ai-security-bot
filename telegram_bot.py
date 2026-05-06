import os
import time
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")
WORKFLOW_FILE = os.getenv("WORKFLOW_FILE", "security-scan.yml")

if not all([TELEGRAM_TOKEN, GITHUB_TOKEN, REPO_OWNER, REPO_NAME]):
    raise ValueError("Missing environment variables!")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def trigger_github_scan(url):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    payload = {"ref": "main", "inputs": {"target_url": url}}
    url_endpoint = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/{WORKFLOW_FILE}/dispatches"
    
    logger.info(f"Triggering scan for {url}...")
    resp = requests.post(url_endpoint, json=payload, headers=headers)
    
    if resp.status_code == 204:
        return fetch_latest_run_id(headers)
    else:
        logger.error(f"Trigger failed: {resp.text}")
        return None

def fetch_latest_run_id(headers):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        runs = resp.json().get("workflow_runs", [])
        if runs:
            return runs[0]["id"]
    return None

def wait_for_run(run_id, headers):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs/{run_id}"
    logger.info(f"Waiting for run {run_id}...")
    for _ in range(40):
        time.sleep(15)
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200: return None
        data = resp.json()
        if data["status"] == "completed": return data["conclusion"]
    return "timeout"

def download_artifact(run_id, headers):
    list_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs/{run_id}/artifacts"
    resp = requests.get(list_url, headers=headers)
    if resp.status_code != 200: return None
    artifacts = resp.json().get("artifacts", [])
    if not artifacts: return None
    download_url = artifacts[0]["archive_download_url"]
    dl_resp = requests.get(download_url, headers=headers)
    return dl_resp.content if dl_resp.status_code == 200 else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛡️ **AI Security Scanner**\n\nSend: `/scan <url>`")

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: `/scan <url>`")
        return
    url = context.args[0]
    if not url.startswith("http"):
        await update.message.reply_text("❌ Invalid URL")
        return
    
    await update.message.reply_text(f"🚀 Scanning {url}... (3-5 mins)")
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    run_id = trigger_github_scan(url)
    
    if not run_id:
        await update.message.reply_text("❌ Failed to start scan.")
        return

    conclusion = wait_for_run(run_id, headers)
    
    if conclusion == "success":
        await update.message.reply_text("✅ Scan Complete! Downloading report...")
        report_zip = download_artifact(run_id, headers)
        if report_zip:
            with open("report.zip", "wb") as f: f.write(report_zip)
            await update.message.reply_document(document=open("report.zip", "rb"), caption="📄 Report")
            os.remove("report.zip")
        else:
            await update.message.reply_text("❌ Could not download report.")
    else:
        await update.message.reply_text(f"❌ Scan failed: {conclusion}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan_command))
    app.run_polling()

if __name__ == "__main__":
    main()
