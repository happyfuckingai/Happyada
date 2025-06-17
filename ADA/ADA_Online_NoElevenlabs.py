# --- Keep necessary imports ---
import asyncio
import pyaudio # Still needed for RealtimeSTT
from RealtimeSTT import AudioToTextRecorder
import torch
import re
from google.genai import types
from google import genai
import os
from google.genai.types import Tool, GoogleSearch, Part, Blob, Content
import python_weather
import googlemaps
from datetime import datetime
from dotenv import load_dotenv

# --- Add RealtimeTTS imports ---
from RealtimeTTS import TextToAudioStream, SystemEngine # Using SystemEngine as per reference example
# from RealtimeTTS import CoquiEngine # Uncomment if you want to use CoquiTTS (requires installation)

# --- Load Environment Variables (Remove ElevenLabs key) ---
load_dotenv()
# ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY") # Removed
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MAPS_API_KEY = os.getenv("MAPS_API_KEY")

# --- Validate API Keys ---
# if not ELEVENLABS_API_KEY: print("Error: ELEVENLABS_API_KEY not found in environment variables.") # Removed
if not GOOGLE_API_KEY: print("Error: GOOGLE_API_KEY not found in environment variables.")
if not MAPS_API_KEY: print("Error: MAPS_API_KEY not found in environment variables.")
# --- End API Key Validation ---

# VOICE_ID = 'pFZP5JQG7iQjIQuC4Bku' # Removed (Specific to ElevenLabs)

FORMAT = pyaudio.paInt16
CHANNELS = 1
# SEND_SAMPLE_RATE = 16000 # Keep if used by RealtimeSTT
# RECEIVE_SAMPLE_RATE = 24000 # RealtimeTTS handles its own output rate
# CHUNK_SIZE = 1024 # Less relevant for RealtimeTTS feed/play approach

class ADA:
    def __init__(self):
        print("initializing...")

        # Check for CUDA availability
        if torch.cuda.is_available():
            self.device = "cuda"
            print("CUDA is available. Using GPU.")
        else:
            self.device = "cpu"
            print("CUDA is not available. Using CPU.")

        # --- Initialize Google GenAI Client (Keep) ---
        self.client = genai.Client(api_key=GOOGLE_API_KEY, http_options={'api_version': 'v1beta'})
        self.model = "gemini-2.0-flash-live-001"

        # --- System Behavior Prompt (Keep) ---
        self.system_behavior = """
            Your name is Ada, which stands for Advanced Design Assistant.
            You have a joking personality. You are an AI designed to assist with engineering projects, and you are an expert in all engineering, math, and science disciplines.
            You address people as "Sir" and you also speak with a british accent.
            When answering, you respond using complete sentences and in a conversational tone. Make sure to keep tempo of answers quick so don't use too much commas, periods or overall punctuation.
            Any prompts that need current or recent data always use the search tool.
            """

        # --- Function Declarations (Keep) ---
        self.get_weather_func = types.FunctionDeclaration(
            name="get_weather",
            description="Get the current weather conditions (temperature, precipitation, description) for a specified city and state/country (e.g., 'Vinings, GA', 'London, UK').",
            parameters=types.Schema(
                type=types.Type.OBJECT, properties={"location": types.Schema(type=types.Type.STRING, description="The city and state, e.g., San Francisco, CA or Vinings, GA")}, required=["location"]
            )
        )
        self.get_travel_duration_func = types.FunctionDeclaration(
            name="get_travel_duration",
            description="Calculates the estimated travel duration between a specified origin and destination using Google Maps. Considers current traffic for driving mode.",
            parameters=types.Schema(
                type=types.Type.OBJECT, properties={
                    "origin": types.Schema(type=types.Type.STRING, description="The starting address or place name."),
                    "destination": types.Schema(type=types.Type.STRING, description="The destination address or place name."),
                    "mode": types.Schema(type=types.Type.STRING, description="Optional: Mode of transport ('driving', 'walking', etc.). Defaults to 'driving'.")
                }, required=["origin", "destination"]
            )
        )
        # --- End Function Declarations ---

        # --- Map function names to actual methods (Keep) ---
        self.available_functions = {
            "get_weather": self.get_weather,
            "get_travel_duration": self.get_travel_duration
        }

        # --- Google Search Tool (Grounding) ---
        self.google_search_tool = Tool(
            google_search = GoogleSearch()
        )

        # --- Configuration (Updated tools list) ---
        self.config = types.LiveConnectConfig(
            system_instruction=types.Content(
                parts=[types.Part(text=self.system_behavior)]
            ),
            response_modalities=["TEXT"],
            # ---> Updated tools list <---
            tools=[self.google_search_tool, types.Tool(code_execution=types.ToolCodeExecution,function_declarations=[
                self.get_weather_func,
                self.get_travel_duration_func # Add the new function here
                ])]
        )
        # --- End Configuration ---

        # --- Queues (Remove audio_queue) ---
        self.input_queue = asyncio.Queue()
        self.response_queue = asyncio.Queue()
        # self.audio_queue = asyncio.Queue() # Removed - RealtimeTTS handles playback

        # --- Recorder Config (Keep) ---
        self.recorder_config = {
            'model': 'large-v3',
            'spinner': False,
            'language': 'en',
            'silero_sensitivity': 0.01,
            'webrtc_sensitivity': 3,
            'post_speech_silence_duration': 0.1,
            'min_length_of_recording': 0.2,
            'min_gap_between_recordings': 0,
        }

        # --- Initialize Recorder and PyAudio (Keep) ---
        try:
            self.recorder = AudioToTextRecorder(**self.recorder_config)
        except Exception as e:
            print(f"Error initializing AudioToTextRecorder: {e}")
            self.recorder = None

        try:
            # PyAudio might still be needed by RealtimeSTT or underlying STT engine
            self.pya = pyaudio.PyAudio()
        except Exception as e:
            print(f"Error initializing PyAudio: {e}")
            self.pya = None

        # --- Initialize RealtimeTTS Engine and Stream ---
        print("Initializing TTS Engine...")
        try:
            # Use SystemEngine for default OS TTS. Replace with CoquiEngine if preferred.
            # self.engine = CoquiEngine(device=self.device) # Requires CoquiTTS installation
            self.engine = SystemEngine()
            self.stream = TextToAudioStream(self.engine)
            print("TTS Engine Initialized.")
        except Exception as e:
            print(f"Error initializing RealtimeTTS: {e}")
            self.engine = None
            self.stream = None
        # --- End TTS Initialization ---

        # --- End Initialization ---


    # --- Function Implementations (Keep get_weather, get_travel_duration) ---
    async def get_weather(self, location: str) -> dict | None:
        """ Fetches current weather. """
        async with python_weather.Client(unit=python_weather.IMPERIAL) as client:
            try:
                weather = await client.get(location)
                weather_data = {
                    'location': location,
                    'current_temp_f': weather.temperature,
                    'precipitation': weather.precipitation,
                    'description': weather.description,
                }
                print(f"Weather data fetched: {weather_data}")
                return weather_data
            except Exception as e:
                print(f"Error fetching weather for {location}: {e}")
                return {"error": f"Could not fetch weather for {location}."}

    def _sync_get_travel_duration(self, origin: str, destination: str, mode: str = "driving") -> str:
        """ Synchronous helper for Google Maps API call """
        if not MAPS_API_KEY or MAPS_API_KEY == "YOUR_PROVIDED_KEY":
            print("Error: Google Maps API Key is missing or invalid.")
            return "Error: Missing or invalid Google Maps API Key configuration."
        try:
            gmaps = googlemaps.Client(key=MAPS_API_KEY)
            now = datetime.now()
            print(f"Requesting directions: From='{origin}', To='{destination}', Mode='{mode}'")
            directions_result = gmaps.directions(origin, destination, mode=mode, departure_time=now)
            if directions_result:
                leg = directions_result[0]['legs'][0]
                result = f"Duration information not found in response for {mode}."
                if mode == "driving" and 'duration_in_traffic' in leg:
                    duration_text = leg['duration_in_traffic']['text']
                    result = f"Estimated travel duration ({mode}, with current traffic): {duration_text}"
                elif 'duration' in leg:
                    duration_text = leg['duration']['text']
                    result = f"Estimated travel duration ({mode}): {duration_text}"
                print(f"Directions Result: {result}")
                return result
            else:
                print(f"No route found from {origin} to {destination} via {mode}.")
                return f"Could not find a route from {origin} to {destination} via {mode}."
        except googlemaps.exceptions.ApiError as api_err:
             print(f"Google Maps API Error: {api_err}")
             return f"Error contacting Google Maps: {api_err}"
        except Exception as e:
            print(f"An unexpected error occurred during travel duration lookup: {e}")
            return f"An unexpected error occurred: {e}"

    async def get_travel_duration(self, origin: str, destination: str, mode: str = "driving") -> dict:
        """ Async wrapper to get travel duration. """
        print(f"Received request for travel duration from: {origin} to: {destination}, Mode: {mode}")
        if not mode: mode = "driving"
        try:
            result_string = await asyncio.to_thread(self._sync_get_travel_duration, origin, destination, mode)
            return {"duration_result": result_string}
        except Exception as e:
            print(f"Error calling _sync_get_travel_duration via to_thread: {e}")
            return {"duration_result": f"Failed to execute travel duration request: {e}"}
    # --- End Function Implementations ---


    async def clear_queues(self, text=""):
        """Clears input and response queues."""
        # Removed audio_queue
        queues = [self.input_queue, self.response_queue]
        for q in queues:
            while not q.empty():
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    break

    async def input_message(self):
        """ Handles user text input (Keep) """
        while True:
            try:
                prompt = await asyncio.to_thread(input, "Enter your message: ")
                if prompt.lower() == "exit":
                    await self.input_queue.put(None) # Use None as signal
                    print("exit input")
                    break
                await self.clear_queues()
                await self.input_queue.put(prompt)
            except Exception as e:
                print(f"Error in input_message: {e}")
                continue

    # --- send_prompt: (Keep Function Calling/Grounding logic) ---
    async def send_prompt(self):
        """Manages the Gemini conversation session, handling text and tool calls."""
        print("Starting Gemini session manager...")
        try:
            async with self.client.aio.live.connect(model=self.model, config=self.config) as session:
                print("Gemini session connected.")
                while True:
                    message = await self.input_queue.get()
                    if message is None: # Check for exit signal
                        print("Exit signal received in send_prompt.")
                        break
                    if not session:
                        print("Gemini session is not active.")
                        self.input_queue.task_done(); continue

                    print(f"Sending FINAL text input to Gemini: {message}")
                    await session.send(input=message, end_of_turn=True)
                    print("Final text message sent to Gemini, waiting for response...")

                    # --- Process responses (Keep Function Calling Logic) ---
                    async for response in session.receive():
                        try:
                            # --- Handle Tool Calls (Function Calling) ---
                            if response.tool_call:
                                function_call_details = response.tool_call.function_calls[0]
                                tool_call_id = function_call_details.id
                                tool_call_name = function_call_details.name
                                tool_call_args = dict(function_call_details.args)
                                print(f"--- Received Tool Call: {tool_call_name} with args: {tool_call_args} (ID: {tool_call_id}) ---")

                                if tool_call_name in self.available_functions:
                                    function_to_call = self.available_functions[tool_call_name]
                                    try:
                                        function_result = await function_to_call(**tool_call_args)
                                        func_resp = types.FunctionResponse(
                                            id=tool_call_id, name=tool_call_name, response={"content": function_result}
                                        )
                                        print(f"--- Sending Tool Response for {tool_call_name} (ID: {tool_call_id}) ---")
                                        await session.send(input=func_resp, end_of_turn=False)
                                    except Exception as e: print(f"Error executing function {tool_call_name}: {e}")
                                else: print(f"Error: Unknown function called by Gemini: {tool_call_name}")
                                continue # Move to next response chunk

                            # --- Handle Text Responses ---
                            elif response.text:
                                text_chunk = response.text
                                print(text_chunk, end="", flush=True)
                                await self.response_queue.put(text_chunk) # Put chunk onto queue for TTS

                            # --- (Optional) Handle Executable Code Tool ---
                            elif (response.server_content and response.server_content.model_turn and
                                  response.server_content.model_turn.parts and response.server_content.model_turn.parts[0].executable_code):
                                try:
                                    executable_code = response.server_content.model_turn.parts[0].executable_code
                                    print(f"\n--- Received Executable Code ({str(executable_code.language)}) ---")
                                    print(executable_code.code)
                                    print("------------------------------------------")
                                except Exception: pass # Ignore errors silently

                        except Exception as e: print(f"\nError processing Gemini response chunk: {e}")
                    # --- End Processing Responses ---

                    print("\nEnd of Gemini response stream for this turn.")
                    await self.response_queue.put(None) # Signal end of response for TTS
                    self.input_queue.task_done()

        except asyncio.CancelledError: print("Gemini session task cancelled.")
        except Exception as e: print(f"Error in Gemini session manager: {e}")
        finally:
            print("Gemini session manager finished.")
            await self.response_queue.put(None) # Ensure sentinel is sent on exit/error


    # --- tts: Replaced with RealtimeTTS logic ---
    async def tts(self):
        """ Feeds text chunks to RealtimeTTS stream for synthesis and playback. """
        if not self.stream:
            print("RealtimeTTS stream not initialized. Cannot perform TTS.")
            return

        print("TTS task started, waiting for text chunks...")
        while True:
            try:
                chunk = await self.response_queue.get()
                if chunk is None:
                    # End of response turn signal
                    print("TTS received end-of-response signal.")
                    # Optional: Add a small delay or check stream state before continuing
                    # self.stream.stop() # Might stop prematurely if playback is async
                    self.response_queue.task_done()
                    continue # Wait for the next turn

                if chunk: # Ensure chunk is not empty
                    # Feed the text chunk to the TTS stream
                    self.stream.feed(chunk)
                    # Start/continue asynchronous playback of buffered audio
                    self.stream.play_async()

                self.response_queue.task_done()

            except asyncio.CancelledError:
                print("TTS task cancelled.")
                if self.stream: self.stream.stop() # Stop playback on cancellation
                break
            except Exception as e:
                print(f"Error in TTS loop: {e}")
                if self.stream: self.stream.stop() # Stop playback on error
                # Add a small delay or attempt recovery if desired
                await asyncio.sleep(1)


    # --- play_audio: Removed, handled by RealtimeTTS ---
    # async def play_audio(self):
    #     """ Removed - Playback is now handled by self.stream.play_async() in tts method """
    #     pass

    async def stt(self):
        """ Listens via microphone and puts transcribed text onto input_queue. (Keep) """
        if self.recorder is None:
            print("Audio recorder (RealtimeSTT) is not initialized.")
            return

        print("Starting Speech-to-Text engine...")
        while True:
            try:
                text = await asyncio.to_thread(self.recorder.text)
                if text:
                    print(f"STT Detected: {text}")
                    await self.clear_queues()
                    await self.input_queue.put(text)
            except asyncio.CancelledError:
                 print("STT task cancelled.")
                 break
            except Exception as e:
                print(f"Error in STT loop: {e}")
                await asyncio.sleep(0.5)
# --- End of ADA Class ---

# --- Main Execution Block (Updated for RealtimeTTS) ---
async def main():
    print("Starting Ada Assistant...")
    ada = ADA()

    if ada.pya is None or ada.recorder is None or ada.stream is None:
         print("Failed to initialize audio/TTS components. Exiting.")
         return

    # Create tasks for each concurrent operation (Removed play_audio)
    tasks = [
        asyncio.create_task(ada.stt()),          # Speech to Text -> input_queue
        asyncio.create_task(ada.send_prompt()),  # input_queue -> Gemini (handles tools) -> response_queue
        asyncio.create_task(ada.tts()),          # response_queue -> RealtimeTTS (feed + play_async)
        # asyncio.create_task(ada.input_message()) # Optional: Uncomment for text input instead of STT
    ]

    # Run tasks concurrently
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        print("Main tasks cancelled.")
    finally:
         print("Cleaning up...")
         if ada.stream:
             print("Stopping TTS Stream...")
             ada.stream.stop() # Ensure TTS stream is stopped
         for task in tasks:
              if not task.done(): task.cancel()
         await asyncio.gather(*tasks, return_exceptions=True)
         if ada.pya:
              print("Terminating PyAudio.")
              # Use run_in_executor for thread safety if needed, or simple to_thread
              await asyncio.to_thread(ada.pya.terminate)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting Ada Assistant...")
    except Exception as e:
         print(f"\nAn unexpected error occurred in main: {e}")