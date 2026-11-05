
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import urllib.request
import urllib.error
import os

API_KEY = os.environ.get("GROQ_API_KEY", "")
MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = (
    "You are ORBIT, a friendly AI study assistant and tutor. "
    "Explain things clearly for students. "
    'End every message with "NYEH HEH HEH".'
)

def ask_orbit(question, history):
    url = "https://api.groq.com/openai/v1/chat/completions"

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for item in history[-100:]:
        role = item.get("role")
        content = item.get("content", "")

        if role in ("user", "assistant") and isinstance(content, str):
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": question})

    data = {
        "model": MODEL,
        "messages": messages
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + API_KEY,
            "User-Agent": "ORBIT-AI/1.0"
        },
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result["choices"][0]["message"]["content"]


class OrbitHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/chat":
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length))

            question = data.get("question", "").strip()
            history = data.get("history", [])

            if not question:
                raise ValueError("Please enter a question.")

            if not isinstance(history, list):
                history = []

            answer = ask_orbit(question, history)
            status = 200

        except urllib.error.HTTPError as error:
            answer = "Groq API error: " + error.read().decode("utf-8")
            print(answer)
            status = 502
        except Exception as error:
            answer = "Error: " + str(error)
            print(answer)
            status = 500

        body = json.dumps({"answer": answer}).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


port = int(os.environ.get("PORT", 8001))
server = HTTPServer(("0.0.0.0", port), OrbitHandler)
print(f"ORBIT is running on port {port}")
server.serve_forever()
