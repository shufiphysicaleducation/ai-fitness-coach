import streamlit as st
import cv2
import numpy as np
import mediapipe as mp
import time
import threading
from streamlit_webrtc import VideoProcessorBase, webrtc_streamer, WebRtcMode, RTCConfiguration

# --- 1. Streamlit Page Configuration ---
st.set_page_config(
    page_title="AI Fitness Coach",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("AI Fitness Coach 🏋️")

# --- 2. MediaPipe and Drawing Utilities ---
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# --- 3. Helper Function to Calculate Angles (from Phase 2) ---
def calculate_angle(a, b, c):
    """Calculates the angle between three points (in degrees)."""
    a = np.array(a)  # First point
    b = np.array(b)  # Mid point
    c = np.array(c)  # End point
    
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    
    if angle > 180.0:
        angle = 360 - angle
        
    return angle

# --- 4. The Core Video Processing Class (Phases 1-4 Logic) ---
class FitnessCoachProcessor(VideoProcessorBase):
    def __init__(self):
        # --- State Management ---
        self.lock = threading.Lock()
        
        # --- App State ---
        self.exercise_type = "Push-ups"
        
        # --- Push-up State (from Phase 3) ---
        self.pushup_counter = 0
        self.pushup_state = "up"
        
        # --- Half-Squat State (from Phase 3) ---
        self.squat_counter = 0
        self.squat_state = "up"
        
        # --- Feedback (from Phase 4) ---
        self.feedback_message = "Start your exercise!"
        
    def set_exercise(self, exercise_type):
        """Safely sets the current exercise and resets counters."""
        with self.lock:
            if self.exercise_type != exercise_type:
                self.exercise_type = exercise_type
                # Reset counters when exercise changes
                self.pushup_counter = 0
                self.squat_counter = 0
                self.feedback_message = f"Starting {exercise_type}..."
    
    def get_display_stats(self):
        """Safely gets the current stats for display on the Streamlit UI."""
        with self.lock:
            if self.exercise_type == "Push-ups":
                reps = self.pushup_counter
            elif self.exercise_type == "Half-Squats":
                reps = self.squat_counter
            else:
                reps = 0
            
            feedback = self.feedback_message
            
        return reps, feedback

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        """Processes each frame from the webcam."""
        img = frame.to_ndarray(format="bgr24")
        
        # --- Phase 1: Real-time Pose Feed ---
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img.flags.writeable = False
        results = pose.process(img)
        img.flags.writeable = True
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        
        # Local state for this frame
        current_feedback = ""
        
        try:
            landmarks = results.pose_landmarks.landmark
            
            # --- Phase 2: Joint Angle Calculation ---
            # Get coordinates for relevant landmarks
            shoulder_l = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            elbow_l = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            wrist_l = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
            
            hip_l = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            knee_l = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            ankle_l = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
            
            # Calculate angles
            left_elbow_angle = calculate_angle(shoulder_l, elbow_l, wrist_l)
            left_hip_angle = calculate_angle(shoulder_l, hip_l, knee_l)
            left_knee_angle = calculate_angle(hip_l, knee_l, ankle_l)
            
            # --- Phase 3 & 4: Rep Counter and Feedback Engine ---
            with self.lock:
                current_exercise = self.exercise_type # Get thread-safe copy
            
            if current_exercise == "Push-ups":
                # Push-up logic
                if left_elbow_angle < 90 and self.pushup_state == "up":
                    self.pushup_state = "down"
                elif left_elbow_angle > 160 and self.pushup_state == "down":
                    self.pushup_state = "up"
                    self.pushup_counter += 1
                
                # Feedback logic
                if self.pushup_state == "down":
                    if left_hip_angle < 160:
                        current_feedback = "Keep your back straight!"
                    else:
                        current_feedback = "Good Form"
                        
            elif current_exercise == "Half-Squats":
                # Half-Squat logic
                if left_knee_angle < 150 and self.squat_state == "up":
                    self.squat_state = "down"
                elif left_knee_angle > 170 and self.squat_state == "down":
                    self.squat_state = "up"
                    self.squat_counter += 1
                
                # Feedback logic
                if self.squat_state == "down":
                    if left_knee_angle < 100:
                        current_feedback = "Going too deep!"
                    elif left_hip_angle < 160:
                        current_feedback = "Keep your chest up!"
                    else:
                        current_feedback = "Good Form"
            
            # Update shared feedback message
            if current_feedback:
                with self.lock:
                    self.feedback_message = current_feedback
            
        except Exception as e:
            # Handle cases where no landmarks are detected
            pass
            
        # --- Render UI on Video Frame ---
        
        # 1. Draw Pose Landmarks (Phase 1)
        mp_drawing.draw_landmarks(img, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                  mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                                  mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2))
        
        # 2. Get stats for display
        display_reps, display_feedback = self.get_display_stats()
        
        # 3. Status Box for Reps (Phase 3)
        cv2.rectangle(img, (0, 0), (225, 73), (245, 117, 16), -1)
        cv2.putText(img, 'REPS', (15, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.putText(img, str(display_reps), (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2, cv2.LINE_AA)
        
        # 4. Status Box for Feedback (Phase 4)
        feedback_color = (0, 255, 0) if display_feedback == "Good Form" else (0, 0, 255)
        cv2.rectangle(img, (0, 480 - 70), (640, 480), (245, 117, 16), -1)
        cv2.putText(img, 'FEEDBACK', (15, 480 - 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.putText(img, display_feedback, (10, 480 - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, feedback_color, 2, cv2.LINE_AA)

        return av.VideoFrame.from_ndarray(img, format="bgr24")

# --- 5. Streamlit UI Layout (Phase 5) ---

# Sidebar
with st.sidebar:
    st.header("Exercise Selection")
    selected_exercise = st.selectbox(
        "Choose your exercise:",
        ("Push-ups", "Half-Squats"),
        key="selected_exercise"
    )
    
    st.divider()
    
    st.header("Live Stats")
    # Placeholders for metrics that will be updated in real-time
    reps_placeholder = st.empty()
    feedback_placeholder = st.empty()
    
# Main content
st.info(f"You selected: **{selected_exercise}**. Prepare your position and start.")

# --- 6. Streamlit-WebRTC Component ---
rtc_configuration = RTCConfiguration({
    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
})

ctx = webrtc_streamer(
    key="ai-fitness-coach",
    mode=WebRtcMode.SENDRECV,
    rtc_configuration=rtc_configuration,
    video_processor_factory=FitnessCoachProcessor,
    media_stream_constraints={"video": True, "audio": False},
    async_processing=True,
)

# --- 7. Real-time Metric Update Loop ---
if ctx.video_processor:
    # Update the processor with the selected exercise
    ctx.video_processor.set_exercise(selected_exercise)
    
    # Poll the processor for the latest stats
    while ctx.state.playing:
        reps, feedback = ctx.video_processor.get_display_stats()
        
        # Update the placeholders in the sidebar
        reps_placeholder.metric("REPS", reps)
        feedback_placeholder.metric("FEEDBACK", feedback)
        
        # Small delay to prevent Streamlit from crashing
        time.sleep(0.1)
