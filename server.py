from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import urllib.request
import urllib.error
import os

API_KEY = os.environ.get("GROQ_API_KEY", "")
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = (
    "You are ORBIT, a friendly AI study assistant and tutor. "
    "Explain things clearly to students. "
    "Use Markdown when helpful. Keep responses lightweight. "
    "Whenever someone mentions gaming, say you have activated a cheat code."
)


def ask_orbit(question, history):
    if not API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing from Render environment variables.")

    url = "https://api.groq.com/openai/v1/chat/completions"

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for item in history[-4:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role")
        content = item.get("content", "")

        if role in ("user", "assistant") and isinstance(content, str):
            messages.append({
                "role": role,
                "content": content[:2000]
            })

    messages.append({
        "role": "user",
        "content": question[:2000]
    })

    data = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 512,
        "temperature": 0.7
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

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))

        return result["choices"][0]["message"]["content"]

    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        print(
            f"GROQ HTTP ERROR: {error.code} - {details}",
            flush=True
        )
        raise

    except urllib.error.URLError as error:
        print(f"GROQ CONNECTION ERROR: {error.reason}", flush=True)
        raise


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

            print("Received chat request.", flush=True)

            answer = ask_orbit(question, history)
            status = 200

        except urllib.error.HTTPError as error:
            print(f"BACKEND: Groq returned HTTP {error.code}", flush=True)
            answer = "ORBIT couldn't reach its AI service. Please try again."
            status = 502

        except urllib.error.URLError as error:
            print(f"BACKEND: Connection failed: {error.reason}", flush=True)
            answer = "ORBIT couldn't connect to its AI service."
            status = 502

        except Exception as error:
            print(
                f"ORBIT SERVER ERROR: {type(error).__name__}: {error}",
                flush=True
            )
            answer = "ORBIT encountered an unexpected error."
            status = 500

        body = json.dumps({"answer": answer}).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


port = int(os.environ.get("PORT", 8001))
server = HTTPServer(("0.0.0.0", port), OrbitHandler)

print(f"ORBIT is running on port {port}", flush=True)
server.serve_forever()
