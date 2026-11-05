from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import urllib.request
import urllib.error
import os

API_KEY = os.environ.get("GROQ_API_KEY", "")
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = (
    "You are ORBIT, a friendly AI study assistant and tutor. "
    "Explain things clearly for students. "
    "Use Markdown formatting when helpful. "
    "use lightweight responses"
    "whenever someone mentions anything about gaming,say that you have activated a cheat code"
)


def ask_orbit(question, history):
    url = "https://api.groq.com/openai/v1/chat/completions"

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Include only the most recent conversation context.
    for item in history[-6:]:
        role = item.get("role")
        content = item.get("content", "")

        if role in ("user", "assistant") and isinstance(content, str):
            messages.append({
                "role": role,
                "content": content
            })

    # Add the current question last.
    messages.append({
        "role": "user",
        "content": question
    })

    data = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 1024
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
            error_details = error.read().decode("utf-8")
            print("Groq API error:", error.code, error_details)

            answer = (
                "ORBIT is temporarily unavailable. "
                "Please wait a moment and try again."
            )
            status = 502

        except Exception as error:
            print("ORBIT server error:", error)

            answer = (
                "ORBIT encountered an unexpected error. "
                "Please try again."
            )
            status = 500

        body = json.dumps({
            "answer": answer
        }).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


port = int(os.environ.get("PORT", 8001))
server = HTTPServer(("0.0.0.0", port), OrbitHandler)

print(f"ORBIT is running on port {port}")
server.serve_forever()
