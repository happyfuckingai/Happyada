import asyncio
# import websockets # Removed
import json # Still used by Gemini responses/tools potentially
# import base64 # Removed
import pyaudio
from RealtimeSTT import AudioToTextRecorder
import torch  # Import the torch library
import re
from google.genai import types
import asyncio
from google import genai
import os
from google.genai.types import Tool, GoogleSearch, Part, Blob, Content
import python_weather
import googlemaps # Added for travel duration
from datetime import datetime # Added for travel duration
from dotenv import load_dotenv # Added for API key loading

# --- Load Environment Variables ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MAPS_API_KEY = os.getenv("MAPS_API_KEY") # Added Maps API Key

# --- Gemini Configuration ---
GEMINI_TTS_MODEL = os.getenv("GEMINI_TTS_MODEL", "gemini-1.5-flash-preview-tts")
GEMINI_TTS_VOICE = os.getenv("GEMINI_TTS_VOICE", "echo") # Using a common voice name, adjust if needed
GEMINI_LLM_MODEL = os.getenv("GEMINI_LLM_MODEL", "gemini-1.5-flash-latest")

# --- Validate API Keys ---
if not GOOGLE_API_KEY: print("Error: GOOGLE_API_KEY not found in environment variables.")
if not MAPS_API_KEY: print("Error: MAPS_API_KEY not found in environment variables.")

# --- Print Gemini Config ---
if not os.getenv("GEMINI_TTS_MODEL"): print("Warning: GEMINI_TTS_MODEL not found, using default.")
if not os.getenv("GEMINI_TTS_VOICE"): print("Warning: GEMINI_TTS_VOICE not found, using default.")
if not os.getenv("GEMINI_LLM_MODEL"): print("Warning: GEMINI_LLM_MODEL not found, using default.")
print(f"Using Gemini TTS Model: {GEMINI_TTS_MODEL}")
print(f"Using Gemini TTS Voice: {GEMINI_TTS_VOICE}")
print(f"Using Gemini LLM Model: {GEMINI_LLM_MODEL}")
# --- End API Key Validation ---

FORMAT = pyaudio.paInt16
CHANNELS = 1
# SEND_SAMPLE_RATE = 16000 # Keep if used by RealtimeSTT or other input processing
RECEIVE_SAMPLE_RATE = 24000 # For Gemini TTS output (24kHz)
CHUNK_SIZE = 1024

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

        # --- Initialize Google GenAI Client ---
        self.client = genai.Client(api_key=GOOGLE_API_KEY, http_options={'api_version': 'v1beta'})
        self.model = GEMINI_LLM_MODEL # Use the loaded environment variable

        # --- System Behavior Prompt (Updated from reference) ---
        self.system_behavior = """
            Your name is Ada, which stands for Advanced Design Assistant.
            You have a joking personality. You are an AI designed to assist with engineering projects, and you are an expert in all engineering, math, and science disciplines.
            You address people as "Sir" and you also speak with a british accent.
            When answering, you respond using complete sentences and in a conversational tone. Make sure to keep tempo of answers quick so don't use too much commas, periods or overall punctuation.
            Any prompts that need current or recent data always use the search tool.
            """
        
        # --- Function Declarations (Added get_travel_duration_func) ---
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

        # --- Map function names to actual methods (Added get_travel_duration) ---
        self.available_functions = {
            "get_weather": self.get_weather,
            "get_travel_duration": self.get_travel_duration # Added mapping
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

        # --- Queues (Kept original relevant queues) ---
        self.input_queue = asyncio.Queue()
        self.response_queue = asyncio.Queue()
        self.audio_queue = asyncio.Queue() # Renamed from audio_output_queue for consistency

        # --- Recorder Config (Kept original) ---
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

        # --- Initialize Recorder and PyAudio (Kept original) ---
        try:
            self.recorder = AudioToTextRecorder(**self.recorder_config)
        except Exception as e:
            print(f"Error initializing AudioToTextRecorder: {e}")
            self.recorder = None

        try:
            self.pya = pyaudio.PyAudio()
        except Exception as e:
            print(f"Error initializing PyAudio: {e}")
            self.pya = None
        # --- End Initialization ---

    # --- Function Implementations ---

    async def get_weather(self, location: str) -> dict | None:
        """ Fetches current weather. (Removed SocketIO emit) """
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
                # --- SocketIO Emit Removed ---
                return weather_data # Return data for Gemini

            except Exception as e:
                print(f"Error fetching weather for {location}: {e}")
                return {"error": f"Could not fetch weather for {location}."} # Return error info

    # --- Added Travel Duration Functions (from reference, removed SocketIO emit) ---
    def _sync_get_travel_duration(self, origin: str, destination: str, mode: str = "driving") -> str:
        """ Synchronous helper for Google Maps API call """
        if not MAPS_API_KEY or MAPS_API_KEY == "YOUR_PROVIDED_KEY": # Check the actual key
            print("Error: Google Maps API Key is missing or invalid.")
            return "Error: Missing or invalid Google Maps API Key configuration."
        try:
            gmaps = googlemaps.Client(key=MAPS_API_KEY) # Use the loaded key
            now = datetime.now()
            print(f"Requesting directions: From='{origin}', To='{destination}', Mode='{mode}'")
            directions_result = gmaps.directions(origin, destination, mode=mode, departure_time=now)
            if directions_result:
                leg = directions_result[0]['legs'][0]
                duration_text = "Not available"
                result = f"Duration information not found in response for {mode}." # Default result
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
        """ Async wrapper to get travel duration. (Removed SocketIO emit) """
        print(f"Received request for travel duration from: {origin} to: {destination}, Mode: {mode}")
        if not mode:
            mode = "driving"

        try:
            result_string = await asyncio.to_thread(
                self._sync_get_travel_duration, origin, destination, mode
            )
            # --- SocketIO Emit Removed ---
            return {"duration_result": result_string} # Return result for Gemini

        except Exception as e:
            print(f"Error calling _sync_get_travel_duration via to_thread: {e}")
            return {"duration_result": f"Failed to execute travel duration request: {e}"}
    # --- End Travel Duration Functions ---


    async def clear_queues(self, text=""):
        """Clears all data from the input, response, and audio queues."""
        # Changed audio_queue name for consistency
        queues = [self.input_queue, self.response_queue, self.audio_queue]
        for q in queues:
            while not q.empty():
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    break  # Queue is empty

    async def input_message(self):
        """ Handles user text input (Kept original) """
        while True:
            try:
                prompt = await asyncio.to_thread(input, "Enter your message: ")
                if prompt.lower() == "exit":
                    await self.input_queue.put("exit")  # Signal to exit
                    print("exit input")
                    break
                await self.clear_queues()
                await self.input_queue.put(prompt)
            except Exception as e:
                print(f"Error in input_message: {e}")
                continue  # Continue the loop even if there's an error

    # --- send_prompt: Updated with Function Calling/Grounding logic from reference ---
    async def send_prompt(self):
        """Manages the Gemini conversation session, handling text and tool calls."""
        print("Starting Gemini session manager...")
        try:
            # Establish connection (same as original)
            async with self.client.aio.live.connect(model=self.model, config=self.config) as session:
                print("Gemini session connected.")

                while True: # Loop to process text inputs
                    message = await self.input_queue.get()

                    if message.lower() == "exit":
                        print("Exit signal received in send_prompt.")
                        break # Exit the main loop

                    if not session: # Check session validity (though handled by async with)
                        print("Gemini session is not active.")
                        self.input_queue.task_done(); continue # Should not happen here

                    # Send the final text input for the turn (same as original)
                    print(f"Sending FINAL text input to Gemini: {message}")
                    await session.send(input=message, end_of_turn=True)
                    print("Final text message sent to Gemini, waiting for response...")

                    # --- Process responses (NEW LOGIC based on reference) ---
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
                                        # Execute the corresponding async function
                                        function_result = await function_to_call(**tool_call_args)

                                        # Construct the response to send back to Gemini
                                        func_resp = types.FunctionResponse(
                                            id=tool_call_id,
                                            name=tool_call_name,
                                            response={"content": function_result} # Send back the result dictionary
                                        )
                                        print(f"--- Sending Tool Response for {tool_call_name} (ID: {tool_call_id}) ---")
                                        # Send the function result back, don't end the turn yet
                                        await session.send(input=func_resp, end_of_turn=False)

                                    except Exception as e:
                                        print(f"Error executing function {tool_call_name}: {e}")
                                        # Decide how to handle function execution errors (e.g., send error back?)
                                        # For now, just print and continue waiting for Gemini's next step
                                else:
                                    print(f"Error: Unknown function called by Gemini: {tool_call_name}")
                                    # Decide how to handle unknown function calls
                                continue # Move to next response chunk after handling tool call

                            # --- Handle Text Responses ---
                            elif response.text:
                                text_chunk = response.text
                                print(text_chunk, end="", flush=True) # Print chunk immediately (like original)
                                await self.response_queue.put(text_chunk) # Put chunk onto queue for TTS

                            # --- (Optional) Handle Executable Code Tool (like reference, no SocketIO) ---
                            elif (response.server_content and
                                  response.server_content.model_turn and
                                  response.server_content.model_turn.parts and
                                  response.server_content.model_turn.parts[0].executable_code):
                                try:
                                    executable_code = response.server_content.model_turn.parts[0].executable_code
                                    code_string = executable_code.code
                                    language = str(executable_code.language) # Get language as string
                                    print(f"\n--- Received Executable Code ({language}) ---")
                                    print(code_string)
                                    print("------------------------------------------")
                                    # NOTE: No execution here, just printing. The library handles execution if configured.
                                except (AttributeError, IndexError, TypeError) as e:
                                    pass # Ignore errors if structure isn't as expected

                        except Exception as e:
                             print(f"\nError processing Gemini response chunk: {e}")
                             # Potentially break or continue depending on severity
                    # --- End Processing Responses ---

                    print("\nEnd of Gemini response stream for this turn.")
                    await self.response_queue.put(None) # Signal end of response for TTS
                    self.input_queue.task_done() # Mark input processed

        except asyncio.CancelledError:
            print("Gemini session task cancelled.")
        except Exception as e:
            print(f"Error in Gemini session manager: {e}")
        finally:
            print("Gemini session manager finished.")
            # No specific cleanup needed here unless tasks were managed differently

    async def tts(self):
        """Generates audio from text using Gemini TTS and puts it on the audio_queue."""
        print("Starting Gemini TTS task...")
        while True:
            try:
                text_to_speak = ""
                # Accumulate text from the response_queue until None is received
                while True:
                    chunk = await self.response_queue.get()
                    if chunk is None: # End of current text stream
                        self.response_queue.task_done()
                        break
                    text_to_speak += chunk
                    self.response_queue.task_done()

                if not text_to_speak.strip(): # If accumulated text is empty or just whitespace
                    print("TTS: No text to speak for this turn.")
                    continue # Wait for new text from response_queue

                print(f"TTS: Generating audio for: '{text_to_speak[:60]}...'")

                try:
                    tts_config = types.GenerateContentConfig(
                        response_modalities=["AUDIO"], # Specify audio output
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                # For prebuilt voices, use PrebuiltVoiceConfig
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=GEMINI_TTS_VOICE)
                                # For custom voices (if available and configured), use CustomVoiceConfig
                                # custom_voice_config=types.CustomVoiceConfig(custom_voice=types.CustomVoice(name="your-custom-voice-name"))
                            )
                        )
                    )

                    # Using the synchronous client's generate_content method wrapped in to_thread
                    # The model specified here (GEMINI_TTS_MODEL) should be a TTS-capable model.
                    response = await asyncio.to_thread(
                        self.client.generate_content, # Using the main synchronous client
                        model=GEMINI_TTS_MODEL,       # e.g., "gemini-1.5-flash-preview-tts"
                        contents=[text_to_speak],     # Text to be synthesized
                        generation_config=tts_config
                        # stream=True # If stream=True, response is an iterable of GenerateContentResponse
                                      # and each part's data needs to be collected.
                                      # For non-streaming, it's a single GenerateContentResponse.
                    )

                    # Process non-streaming response
                    if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                        # Ensure the part is audio data
                        if response.candidates[0].content.parts[0].inline_data and response.candidates[0].content.parts[0].inline_data.data:
                            audio_data = response.candidates[0].content.parts[0].inline_data.data
                            if audio_data:
                                print(f"TTS: Received audio data ({len(audio_data)} bytes). Putting on queue.")
                                await self.audio_queue.put(audio_data)
                            else:
                                print("TTS: No audio data in the first part of the response.")
                        else:
                            print("TTS: First part of the response does not contain inline audio data.")
                            # You might want to log the part structure here for debugging
                            # print(f"TTS: Part structure: {response.candidates[0].content.parts[0]}")
                    else:
                        print("TTS: Invalid response structure, no candidates, content, or parts found.")
                        # Log the full response for debugging if necessary
                        # print(f"TTS: Full response: {response}")

                except Exception as e:
                    print(f"Error during Gemini TTS API call: {e}")
                    # Consider how to handle TTS errors, e.g., play a pre-recorded error sound
                    # or put a special marker on the audio_queue.
                    # For now, it just logs and the loop continues.

            except asyncio.CancelledError:
                print("TTS task cancelled.")
                break # Exit the main while loop
            except Exception as e:
                print(f"Outer error in TTS loop: {e}")
                # Adding a small delay to prevent busy-looping on persistent errors
                await asyncio.sleep(1)

    async def play_audio(self):
        """ Plays audio chunks from the audio_queue. (Kept Original Logic) """
        if self.pya is None:
            print("PyAudio is not initialized. Cannot play audio.")
            return

        stream = None # Initialize stream variable
        try:
            print("Opening PyAudio stream...")
            stream = await asyncio.to_thread(
                self.pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=RECEIVE_SAMPLE_RATE,
                output=True,
            )
            print("PyAudio stream opened. Waiting for audio chunks...")
            while True:
                try:
                    # Wait for audio data from the TTS task
                    bytestream = await self.audio_queue.get()
                    if bytestream is None: # Potential signal to stop? (Not currently used)
                         print("Received None in audio queue, stopping playback loop.")
                         break
                    # Write audio data to the stream in a separate thread
                    await asyncio.to_thread(stream.write, bytestream)
                    self.audio_queue.task_done() # Mark item as processed
                except asyncio.CancelledError:
                    print("Audio playback task cancelled.")
                    break  # Exit loop if task is cancelled
                except Exception as e:
                    print(f"Error in play_audio loop: {e}")
                    # Decide if error is fatal or recoverable
                    await asyncio.sleep(0.1) # Avoid busy-looping on error

        except pyaudio.PyAudioError as e:
            print(f"PyAudio error opening stream: {e}")
        except Exception as e:
            print(f"Error setting up audio stream: {e}")
        finally:
            if stream:
                print("Closing PyAudio stream...")
                await asyncio.to_thread(stream.stop_stream)
                await asyncio.to_thread(stream.close)
                print("PyAudio stream closed.")
            # Don't terminate PyAudio here if other parts might use it
            # await asyncio.to_thread(self.pya.terminate)

    async def stt(self):
        """ Listens via microphone and puts transcribed text onto input_queue. (Kept Original Logic) """
        if self.recorder is None:
            print("Audio recorder (RealtimeSTT) is not initialized.")
            return

        print("Starting Speech-to-Text engine...")
        while True:
            try:
                # Blocking call handled in a thread
                text = await asyncio.to_thread(self.recorder.text)
                if text: # Only process if text is not empty
                    print(f"STT Detected: {text}")
                    await self.clear_queues() # Clear queues before adding new input
                    await self.input_queue.put(text) # Put transcribed text onto the input queue
            except asyncio.CancelledError:
                 print("STT task cancelled.")
                 break
            except Exception as e:
                print(f"Error in STT loop: {e}")
                # Add a small delay to prevent high CPU usage on continuous errors
                await asyncio.sleep(0.5)
# --- End of ADA Class ---

# --- Main Execution Block (Example) ---
async def main():
    print("Starting Ada Assistant...")
    ada = ADA()

    if ada.pya is None or ada.recorder is None:
         print("Failed to initialize audio components. Exiting.")
         return

    # Create tasks for each concurrent operation
    tasks = [
        asyncio.create_task(ada.stt()),          # Speech to Text -> input_queue
        asyncio.create_task(ada.send_prompt()),  # input_queue -> Gemini (handles tools) -> response_queue
        asyncio.create_task(ada.tts()),          # response_queue -> Gemini TTS -> audio_queue
        asyncio.create_task(ada.play_audio()),   # audio_queue -> Speaker
        # asyncio.create_task(ada.input_message()) # Optional: Uncomment for text input instead of STT
    ]

    # Run tasks concurrently
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        print("Main tasks cancelled.")
    finally:
         print("Cleaning up...")
         # Gracefully stop tasks if needed (though gather handles cancellation)
         for task in tasks:
              if not task.done():
                   task.cancel()
         await asyncio.gather(*tasks, return_exceptions=True) # Wait for cleanup
         if ada.pya:
              print("Terminating PyAudio.")
              await asyncio.to_thread(ada.pya.terminate) # Clean up PyAudio resources

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting Ada Assistant...")
    except Exception as e:
         print(f"\nAn unexpected error occurred in main: {e}")