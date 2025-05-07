# PAIN-X

print("""
██████╗  █████╗ ██╗███╗   ██╗    ██╗  ██╗
██╔══██╗██╔══██╗██║████╗  ██║    ╚██╗██╔╝
██████╔╝███████║██║██╔██╗ ██║     ╚███╔╝ 
██╔═══╝ ██╔══██║██║██║╚██╗██║     ██╔██╗ 
██║     ██║  ██║██║██║ ╚████║    ██╔╝ ██╗
╚═╝     ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝    ╚═╝  ╚═╝
""")

# Import required modules
import google.generativeai as genai  # AI (Gemini)
import os  # Operating system interactions
from dotenv import load_dotenv  # Load environment variables
import subprocess  # Execute system commands
import datetime  # Timestamp logs
import sys  # Exit script
import platform  # Detect operating system
import shutil  # For checking clipboard tool

# Detect OS platform
CURRENT_OS = platform.system()
IS_WINDOWS = CURRENT_OS == "Windows"
IS_LINUX = CURRENT_OS == "Linux"

# Load or prompt API key
def load_api_key():
    if os.path.exists(".env"):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            return api_key
    return prompt_for_api_key()

# Prompt and save API key
def prompt_for_api_key():
    api_key = input("Please paste your Gemini API key here: ").strip()
    with open(".env", "w") as file:
        file.write(f"GEMINI_API_KEY={api_key}\n")
    return api_key

# Configure AI
api_key = load_api_key()
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
except Exception as e:
    print(f"Error configuring AI: {e}")
    sys.exit(1)

# Base prompt for generating CLI commands
base_prompt = f"""
You are a professional and context-aware CLI assistant for {CURRENT_OS} systems.

Your role is to generate a safe, modern, and effective command-line solution for the user's request.

Instructions:
- Always respond with ONE best command only.
- First line: the command (no quotes or backticks).
- Second line: starts with 'Explanation:' explaining clearly what the command does.
- Ensure it's safe and avoid any destructive or non-standard behavior.
- Always prefer native CLI tools and commonly available packages.
User Request: {{INPUT}}
"""

# Risk check prompt
risk_check_prompt = """
Check if this command is risky on a {OS} system: `{COMMAND}`
- If risky: "Risky: explanation"
- If safe: "Safe"
""".replace("{OS}", CURRENT_OS)

# Validate command risk
def validate_command_risk(command):
    try:
        prompt = risk_check_prompt.replace("{COMMAND}", command)
        response = model.generate_content(prompt).text.strip()
        return response[6:].strip() if response.startswith("Risky:") else None
    except Exception as e:
        return None

# Generate command and explanation from AI
def gemini_command_and_explanation(user_input):
    try:
        if not user_input.strip():
            return None, None, "Input empty"
        prompt = base_prompt.replace("{INPUT}", user_input)
        response_text = model.generate_content(prompt).text.strip()
        lines = response_text.split('\n', 1)
        command = lines[0].replace("`", "").replace("'", "").replace('"', '').strip()
        explanation = lines[1].replace("Explanation:", "").replace("`", "").strip() if len(lines) > 1 else ""
        return command, explanation, None
    except Exception as e:
        return None, None, f"Error: {e}"

# Execute command safely
def run_command_safely(command, mode, user_input_for_log):
    output_log = ""
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            print(line, end="")
            output_log += line
        process.wait()
        if "access is denied" in output_log.lower():
            print("Command might need administrator privileges.")
        with open("history.log", "a", encoding='utf-8') as log_file:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_file.write(f"[{timestamp}] Mode: {mode}, Request: '{user_input_for_log}', Command: '{command}'\n")
    except Exception as e:
        print(f"Error executing command: {e}")

# Copy to clipboard based on OS
def copy_to_clipboard(command):
    try:
        if IS_WINDOWS:
            subprocess.run(['powershell', '-Command', f'Set-Clipboard -Value "{command}"'], shell=True)
            print("Command copied to clipboard.")
        elif IS_LINUX:
            if shutil.which("xclip"):
                subprocess.run(f"echo '{command}' | xclip -selection clipboard", shell=True)
                print("Command copied to clipboard.")
            else:
                print("xclip not installed. Please run 'sudo apt install xclip' to enable clipboard functionality.")
        else:
            print("Clipboard copy not supported on this OS.")
    except Exception as e:
        print(f"Clipboard error: {e}")

# Command Suggester Extension
def run_command_suggester():
    print("\n=== Command Suggester Mode ===")
    task = input("Describe the Linux/Windows command task: ").strip()
    if not task:
        print("No task provided.")
        return

    try:
        subprocess.run([sys.executable, "suggester.py", task])
    except Exception as e:
        print(f"Failed to run command suggester: {e}")

# Main interaction loop
while True:
    print("\nSelect mode:")
    print("  1 - Quick")
    print("  2 - Interactive")
    print("  3 - Command Suggester")
    print("  4 - Exit")
    mode = input("Enter option: ").strip()

    if mode == "4":
        print("Feel the pain")
        sys.exit()
    if mode not in ["1", "2", "3"]:
        continue

    if mode == "3":
        run_command_suggester()
        continue

    mode = "quick" if mode == "1" else "interactive"

    while True:
        user_input = input("Enter command request ('back' to change mode): ").strip()
        if user_input.lower() in ["quit", "exit"]:
            print("Feel the pain")
            sys.exit()
        if user_input.lower() == "back":
            break

        command, explanation, error = gemini_command_and_explanation(user_input)
        if error:
            print(error)
            continue

        risk = validate_command_risk(command)
        print(f"Command: {command}")
        print(f"Explanation: {explanation}")

        if mode == "interactive" or (mode == "quick" and risk):
            if risk:
                print(f"Risk: {risk}")
            action = input("Run (y), Copy (c), Cancel (x): ").strip().lower()
            if action == "y":
                run_command_safely(command, mode, user_input)
            elif action == "c":
                copy_to_clipboard(command)
            elif action == "x":
                continue
        else:
            run_command_safely(command, mode, user_input)
