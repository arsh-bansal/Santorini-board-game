# Game Implementation folder

## Steps to create an executable file.

1. Create a virtual environment (inside Game Implementation folder)

`python -m venv .venv` (Windows)

OR

`python3 -m venv .venv` (MacOS)

2. Activate virtual environment

`.\venv\Scripts\activate` (Windows)

OR

`. .venv/bin/active` (MacOS)

3. Install dependencies

`pip install -r requirements.txt`

4. Build the binary

`pyinstaller --onefile main.py`

5. Run the program (MacOS).

   - Go to System Settings
   - Select Privacy and Security from the sidebar
   - Allow the main_unix app under the security section
   - Then run `./dist/main`

6. Run the program (Windows)
   - Double click, duh.
