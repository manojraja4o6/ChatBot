from flask import Flask, request, jsonify, send_from_directory
import math
import pyttsx3
import threading
import queue

app = Flask(__name__)

# Initialize Text-to-Speech engine
tts_engine = pyttsx3.init()

# Queue for handling TTS requests
tts_queue = queue.Queue()

# Predefined keyword-response pairs
keyword_responses = {
    "hi": "Hello! How can I assist you today?",
    "hello": "Hi there! What can I do for you?",
    "hey": "Hey! Need help with something?",
    "how are you": "I'm just a bot, but I'm here to help!",
    "your name": "I'm your friendly Math Chatbot!",
    "bye": "Goodbye! Have a great day!",
    "thanks": "You're welcome!",
    "thank you": "Happy to help!",
    "calculate": "Sure! Please provide the mathematical expression.",
    "solve": "I'm ready to solve. What’s the problem?",
    "help": "You can ask me math queries like 'solve 2+2' or say 'hi' to chat with me.",
}

# TTS worker function
def tts_worker():
    while True:
        text = tts_queue.get()
        if text is None:  # Stop signal
            break
        try:
            tts_engine.say(text)
            tts_engine.runAndWait()
        except Exception as e:
            print(f"TTS Error: {e}")
        tts_queue.task_done()

# Start TTS worker thread
tts_thread = threading.Thread(target=tts_worker, daemon=True)
tts_thread.start()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '').strip().lower()
    if not user_input:
        return jsonify({"response": "Please enter a valid input."})

    response = None

    # Keyword-based response matching
    for keyword, reply in keyword_responses.items():
        if keyword in user_input:
            response = reply
            break

    # Handle mathematical queries if no keyword response matched
    if not response:
        try:
            # Preprocess input to allow Python-safe evaluation
            user_input = user_input.replace('^', '**')  # Replace ^ with ** for exponentiation

            # Safe evaluation context with only math functions and constants
            allowed_names = {
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "log": math.log,  # Natural logarithm
                "sqrt": math.sqrt,
                "exp": math.exp,
                "pi": math.pi,
                "e": math.e,
                "pow": pow,
                "abs": abs,
                "round": round,
                "ceil": math.ceil,
                "floor": math.floor
            }

            # Evaluate the mathematical expression
            result = eval(user_input, {"__builtins__": None}, allowed_names)
            response = f"The result is: {result}"

        except ZeroDivisionError:
            response = "Error: Division by zero is not allowed."
        except (SyntaxError, NameError):
            response = "Error: Invalid expression. Please check your input."
        except Exception as e:
            response = f"Error: Unable to compute ({str(e)})."

    # Add response to TTS queue
    tts_queue.put(response)

    return jsonify({"response": response})

@app.route('/shutdown', methods=['POST'])
def shutdown():
    # Signal the TTS worker to exit and wait for it to finish
    tts_queue.put(None)
    tts_thread.join()
    return "Server shutting down."

if __name__ == '__main__':
    try:
        app.run(debug=True)
    except KeyboardInterrupt:
        # Gracefully stop TTS thread on exit
        tts_queue.put(None)
        tts_thread.join()
