# AI Fitness Coach

This is a Streamlit web application that uses your webcam to count exercise repetitions and provide real-time form feedback.

## Setup

1.  Create a project folder for the application.

2.  Save the files
     Save the Python code as `app.py` in your project folder.
     Save this `README.md` file in the same folder.
     Save the `requirements.txt` file.
     Save the `packages.txt` file (this is for deployment).

3.  Create a `requirements.txt` file in the same folder with the following content
    ```
    streamlit
    opencv-python-headless
    mediapipe
    numpy
    streamlit-webrtc
    av
    ```

4.  Create a Python virtual environment (recommended)
    ```
    python -m venv venv
    source venvbinactivate  # On Windows, use `venvScriptsactivate`
    ```

5.  Install the required libraries
    ```
    pip install -r requirements.txt
    ```

## How to Run (Locally)

1.  Make sure your virtual environment is activated.
2.  Open your terminal and navigate to the project folder.
3.  Run the following command
    ```
    streamlit run app.py
    ```
4.  Streamlit will open a new tab in your web browser.
5.  Allow the browser to access your webcam.
6.  Select your desired exercise from the sidebar and start working out!

## How to Deploy (to the Web)

The easiest and fastest way to deploy this app is using the free Streamlit Community Cloud.

1.  Get a GitHub Account If you don't have one, sign up for a free account at [GitHub](httpsgithub.com).

2.  Create a New Repository
     On GitHub, create a new public repository (e.g., `ai-fitness-coach`).

3.  Upload Your Files
     Upload all three of your project files to this new repository
        1.  `app.py`
        2.  `requirements.txt`
        3.  `packages.txt` (This file tells Streamlit to install the system libraries needed for OpenCV and WebRTC to work).

4.  Deploy on Streamlit Cloud
     Go to [share.streamlit.io](httpsshare.streamlit.io) and sign in with your GitHub account.
     Click the New app button.
     Select the repository you just created.
     Streamlit will automatically detect the `app.py` file.
     Click the Deploy! button.

That's it! Streamlit will handle everything. It will install the Python packages from `requirements.txt`, the system libraries from `packages.txt`, and launch your app at a public URL (e.g., `your-name-ai-fitness-coach-app-py-12345.streamlit.app`).