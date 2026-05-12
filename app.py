from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

app = Flask(__name__)

channel_secret = os.getenv("LINE_CHANNEL_SECRET")
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

handler = WebhookHandler(channel_secret)
configuration = Configuration(access_token=channel_access_token)
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

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

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
    {
        "role": "system",
        "content": "あなたは島根県の企業向けAI受付LINE Botです。丁寧でわかりやすく、短く返答してください。問い合わせや予約相談には、必要事項を順番に聞いてください。"
    },
    {
        "role": "user",
        "content": user_message
    }
]
        )
        ai_message = response.choices[0].message.content
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