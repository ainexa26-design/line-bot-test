from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from dotenv import load_dotenv
import os
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI
import json
from datetime import datetime

load_dotenv()

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])

creds = Credentials.from_service_account_info(
    creds_info,
    scopes=scope
)

client_sheet = gspread.authorize(creds)

sheet = client_sheet.open("LINE Bot 顧客管理").sheet1

app = Flask(__name__)

channel_secret = os.getenv("LINE_CHANNEL_SECRET")
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

handler = WebhookHandler(channel_secret)
configuration = Configuration(access_token=channel_access_token)
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)
conversation_history = {}

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print("LINE ERROR:", e)
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text
    user_id = event.source.user_id

    from datetime import datetime

    sheet.append_row([
    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    user_id,
    user_message
    ])

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    conversation_history[user_id].append({
        "role": "user",
        "content": user_message
    })
try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                 {
                     "role": "system",
                     "content": "あなたは島根県の企業向けAI受付LINE Botです。丁寧でわかりやすく、短く返答してください。問い合わせや予約相談には、必要事項を順番に聞いてください。"
                 },
            ] + conversation_history[user_id][-10:]

            )
            
        ai_message = response.choices[0].message.content

        conversation_history[user_id].append({
            "role": "assistant",
            "content": ai_message
        })
        
except Exception as e:
        print("OPENAI ERROR:", e, flush=True)
        ai_message = "エラーが出ています"

with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=ai_message)]
            )
        )

    


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=5001)
