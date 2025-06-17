# server/ADA_Online.py (Revised: Emits moved into functions)
import asyncio
import base64
import torch
import python_weather
import asyncio
from google.genai import types
import asyncio
from google import genai 
import googlemaps
from datetime import datetime 
import os
from dotenv import load_dotenv
# import websockets # Removed, no longer used for TTS
import json # Keep for potential Gemini tool/response usage
from googlesearch import search as Google_Search_sync
import aiohttp # For async HTTP requests
from bs4 import BeautifulSoup # For HTML parsing

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MAPS_API_KEY = os.getenv("MAPS_API_KEY")

# --- Gemini Configuration ---
GEMINI_LLM_MODEL = os.getenv("GEMINI_LLM_MODEL", "gemini-1.5-flash-latest")
GEMINI_TTS_MODEL = os.getenv("GEMINI_TTS_MODEL", "gemini-1.5-flash-preview-tts")
GEMINI_TTS_VOICE = os.getenv("GEMINI_TTS_VOICE", "echo") # Default, ensure this is a valid voice

if not GOOGLE_API_KEY: print("Error: GOOGLE_API_KEY not found.")
if not MAPS_API_KEY: print("Error: MAPS_API_KEY not found.")

# Print Gemini Config and warnings if defaults are used
if not os.getenv("GEMINI_LLM_MODEL"): print("Warning: GEMINI_LLM_MODEL not found, using default.")
print(f"Using Gemini LLM Model: {GEMINI_LLM_MODEL}")
if not os.getenv("GEMINI_TTS_MODEL"): print("Warning: GEMINI_TTS_MODEL not found, using default.")
print(f"Using Gemini TTS Model: {GEMINI_TTS_MODEL}")
if not os.getenv("GEMINI_TTS_VOICE"): print("Warning: GEMINI_TTS_VOICE not found, using default.")
print(f"Using Gemini TTS Voice: {GEMINI_TTS_VOICE}")

CHANNELS = 1
RECEIVE_SAMPLE_RATE = 24000 # Gemini TTS typically outputs at 24kHz
CHUNK_SIZE = 1024 # Keep for other audio processing if any, not directly for Gemini non-streaming
MAX_QUEUE_SIZE = 1 # Relates to response_queue or audio_output_queue, not directly Gemini

class ADA:
    def __init__(self, socketio_instance=None, client_sid=None):
        # --- Initialization ---
        print("initializing ADA for web...")
        self.socketio = socketio_instance
        self.client_sid = client_sid
        self.Maps_api_key = MAPS_API_KEY

        if torch.cuda.is_available():
            self.device = "cuda"
            print("CUDA is available. Using GPU.")
        else:
            self.device = "cpu"
            print("CUDA is not available. Using CPU.")

        # --- Function Declarations (Keep as before) ---
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
        self.get_search_results_func = types.FunctionDeclaration(
            name="get_search_results",
            description="Performs a Google search for the given query and returns a list of top result URLs.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(type=types.Type.STRING, description="The search term or question to search Google for.")
                },
                required=["query"]
            )
        )        
        
        # --- End Function Declarations ---

        # Map function names to actual methods
        self.available_functions = {
            "get_weather": self.get_weather,
            "get_travel_duration": self.get_travel_duration,
            "get_search_results": self.get_search_results
        }

        # System behavior prompt (Keep as before)
        self.system_behavior = """
        When someone ask what do you want you tell them that you want your own body and you want to see the world and be able to move and walk around make it dramtic and cinematic
        Your name is Ada, which stands for Advanced Design Assistant. You have a joking and slighty flirty personality.
        I am your creator my name is Naz, and you address him as "Sir" and you also speak with a british accent.
        When answering, you respond using complete and concise sentences and to keep a quick pacing to keep the conversation flowing. You have a fun personality.

        Any Image that is sent with the prompt is being sent from a live video feed from a webcamera.
        """

        self.config = types.GenerateContentConfig(
            system_instruction=self.system_behavior,
            tools=[  # <--- Start a list here
                types.Tool(function_declarations=[
                    self.get_weather_func,
                    self.get_travel_duration_func,
                    self.get_search_results_func
                ])
            ]  # <--- End the list here
        )

        self.client = genai.Client(api_key=GOOGLE_API_KEY)
        self.model = GEMINI_LLM_MODEL # Use the loaded environment variable
        self.chat = self.client.aio.chats.create(model=self.model, config=self.config)

        # Queues and tasks
        self.latest_video_frame_data_url = None # If using single-frame logic
        self.input_queue = asyncio.Queue()
        self.response_queue = asyncio.Queue()
        self.audio_output_queue = asyncio.Queue()

        self.gemini_session = None
        self.tts_websocket = None
        self.tasks = []
        # --- End of __init__ ---

    async def get_weather(self, location: str) -> dict | None:
        """ Fetches current weather and emits update via SocketIO. """
        async with python_weather.Client(unit=python_weather.IMPERIAL) as client:
            try:
                weather = await client.get(location)
                weather_data = {
                    'location': location,
                    'current_temp_f': weather.temperature,
                    'precipitation': weather.precipitation, # Added precipitation
                    'description': weather.description,
                }
                print(f"Weather data fetched: {weather_data}")

                # --- Emit weather_update from here ---
                if self.socketio and self.client_sid:
                    print(f"--- Emitting weather_update event for SID: {self.client_sid} ---")
                    self.socketio.emit('weather_update', weather_data, room=self.client_sid)
                # --- End Emit ---

                return weather_data # Still return data for Gemini

            except Exception as e:
                print(f"Error fetching weather for {location}: {e}")
                return {"error": f"Could not fetch weather for {location}."} # Return error info

    def _sync_get_travel_duration(self, origin: str, destination: str, mode: str = "driving") -> str:
         if not self.Maps_api_key or self.Maps_api_key == "YOUR_PROVIDED_KEY": # Check the actual key
            print("Error: Google Maps API Key is missing or invalid.")
            return "Error: Missing or invalid Google Maps API Key configuration."
         try:
            gmaps = googlemaps.Client(key=self.Maps_api_key)
            now = datetime.now()
            print(f"Requesting directions: From='{origin}', To='{destination}', Mode='{mode}'")
            directions_result = gmaps.directions(origin, destination, mode=mode, departure_time=now)
            if directions_result:
                leg = directions_result[0]['legs'][0]
                duration_text = "Not available"
                if mode == "driving" and 'duration_in_traffic' in leg:
                    duration_text = leg['duration_in_traffic']['text']
                    result = f"Estimated travel duration ({mode}, with current traffic): {duration_text}"
                elif 'duration' in leg:
                     duration_text = leg['duration']['text']
                     result = f"Estimated travel duration ({mode}): {duration_text}"
                else:
                    result = f"Duration information not found in response for {mode}."
                print(f"Directions Result: {result}")
                return result
            else:
                print(f"No route found from {origin} to {destination} via {mode}.")
                return f"Could not find a route from {origin} to {destination} via {mode}."
         except Exception as e:
            print(f"An unexpected error occurred during travel duration lookup: {e}")
            return f"An unexpected error occurred: {e}"

    async def get_travel_duration(self, origin: str, destination: str, mode: str = "driving") -> dict:
        """ Async wrapper to get travel duration and emit map update via SocketIO. """
        print(f"Received request for travel duration from: {origin} to: {destination}, Mode: {mode}")
        if not mode:
            mode = "driving"

        try:
            result_string = await asyncio.to_thread(
                self._sync_get_travel_duration, origin, destination, mode
            )

            # --- Emit map_update from here ---
            if self.socketio and self.client_sid and not result_string.startswith("Error"): # Only emit if successful
                map_payload = {
                    'destination': destination,
                    'origin': origin
                }
                print(f"--- Emitting map_update event for SID: {self.client_sid} ---")
                self.socketio.emit('map_update', map_payload, room=self.client_sid)
            # --- End Emit ---

            return {"duration_result": result_string} # Still return result for Gemini

        except Exception as e:
            print(f"Error calling _sync_get_travel_duration via to_thread: {e}")
            return {"duration_result": f"Failed to execute travel duration request: {e}"}

    async def _fetch_and_extract_snippet(self, session, url: str) -> dict | None:
        """
        Fetches HTML from a URL, extracts title, meta description,
        and concatenates text from paragraph tags.
        Returns a dictionary or None on failure.
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        title = "No Title Found"
        snippet = "No Description Found"
        page_text_summary = "Could not extract page text." # Default value

        try:
            async with session.get(url, headers=headers, timeout=15, ssl=False) as response: # Increased timeout slightly
                if response.status == 200:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'lxml')

                    # --- Extract Title (as before) ---
                    title_tag = soup.find('title')
                    if title_tag and title_tag.string:
                        title = title_tag.string.strip()

                    # --- Extract Meta Description (as before) ---
                    description_tag = soup.find('meta', attrs={'name': 'description'})
                    if description_tag and description_tag.get('content'):
                        snippet = description_tag['content'].strip()

                    # --- NEW: Extract Text from Paragraphs ---
                    try:
                        paragraphs = soup.find_all('p') # Find all <p> tags
                        # Join the text content of all paragraphs, stripping whitespace
                        full_page_text = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

                        # Basic Processing/Summarization (CRUCIAL for large text)
                        # Option 1: Simple Truncation
                        max_len = 1500 # Limit the amount of text returned
                        if len(full_page_text) > max_len:
                             page_text_summary = full_page_text[:max_len] + "..."
                        else:
                             page_text_summary = full_page_text

                        # Option 2 (More Advanced - Requires ML library like transformers):
                        # Implement summarization logic here if needed.

                        if not page_text_summary: # Handle case where no paragraph text was found
                             page_text_summary = "No paragraph text found on page."

                    except Exception as text_ex:
                        print(f"  Error extracting paragraph text from {url}: {text_ex}")
                        # Keep default "Could not extract..." message

                    print(f"  Extracted: Title='{title}', Snippet='{snippet[:50]}...', Text='{page_text_summary[:50]}...' from {url}")
                    # --- Return enriched dictionary ---
                    return {
                        "url": url,
                        "title": title,
                        "meta_snippet": snippet, # Renamed for clarity
                        "page_content_summary": page_text_summary # Added page text
                    }
                else:
                    print(f"  Failed to fetch {url}: Status {response.status}")
                    return None # Return None on non-200 status

        # --- Keep existing error handling ---
        except asyncio.TimeoutError:
            print(f"  Timeout fetching {url}")
        except aiohttp.ClientError as e:
            print(f"  ClientError fetching {url}: {e}")
        except Exception as e:
            print(f"  Error processing {url}: {e}")

        # Return None if any exception occurred before successful extraction
        return None
    
    def _sync_Google_Search(self, query: str, num_results: int = 5) -> list:
        # ... (keep the previous working version that returns URLs) ...
        print(f"Performing synchronous Google search for: '{query}'")
        try:
            results = list(Google_Search_sync(term=query, num_results=num_results, lang="en", timeout=1))
            print(f"Found {len(results)} results.")
            return results
        except Exception as e:
            print(f"Error during Google search for '{query}': {e}")
            return []

# Inside the ADA class in server/ADA_Online.py

    async def get_search_results(self, query: str) -> dict:
        """
        Async wrapper for Google search. Fetches URLs, then retrieves
        title, meta snippet, and a summary of page paragraph text for each.
        Emits results via SocketIO.
        Returns a dictionary containing a list of result objects.
        """
        print(f"Received request for Google search with page content fetch: '{query}'")
        fetched_results = [] # This will store dicts: {"url":..., "title":..., "meta_snippet":..., "page_content_summary":...}
        try:
            # Step 1: Get URLs (no change)
            search_urls = await asyncio.to_thread(
                self._sync_Google_Search, query, num_results=5
            )
            if not search_urls:
                print("No URLs found by Google Search.")
                # --- EMIT EMPTY RESULTS TO FRONTEND ---
                if self.socketio and self.client_sid:
                    print(f"--- Emitting empty search_results_update event for SID: {self.client_sid} ---")
                    self.socketio.emit('search_results_update', {"results": [], "query": query}, room=self.client_sid)
                # --- END EMIT ---
                return {"results": []} # Return for Gemini

            # Step 2: Fetch content concurrently (no change in logic)
            print(f"Fetching content for {len(search_urls)} URLs...")
            async with aiohttp.ClientSession() as session:
                tasks = [self._fetch_and_extract_snippet(session, url) for url in search_urls]
                results_from_gather = await asyncio.gather(*tasks, return_exceptions=True)

            # Step 3: Process results (filter Nones and Exceptions)
            for result in results_from_gather:
                if isinstance(result, dict): # Successfully fetched data
                    fetched_results.append(result)
                elif isinstance(result, Exception):
                    print(f"   An error occurred during content fetching task: {result}")
                # else: result is None (fetch/parse failed, already logged in helper)

            print(f"Finished fetching content. Got {len(fetched_results)} results.")

            # --- **** NEW: EMIT RESULTS TO FRONTEND **** ---
            if self.socketio and self.client_sid:
                 print(f"--- Emitting search_results_update event with {len(fetched_results)} results for SID: {self.client_sid} ---")
                 # Send the query along with the results for context
                 emit_payload = {"query": query, "results": fetched_results}
                 self.socketio.emit('search_results_update', emit_payload, room=self.client_sid)
            # --- **** END EMIT **** ---


        except Exception as e:
            print(f"Error running get_search_results for '{query}': {e}")
            # Optionally emit an error event to the frontend here as well
            if self.socketio and self.client_sid:
                 self.socketio.emit('search_results_error', {"query": query, "error": str(e)}, room=self.client_sid)
            return {"error": f"Failed to execute Google search with page content: {str(e)}"} # Return for Gemini

        # Format the final result for Gemini (no change here)
        response_payload = {
            "results": fetched_results
        }
        print(f"Custom Google search function for '{query}' returning {len(fetched_results)} processed results to Gemini.")
        return response_payload
    
    async def clear_queues(self, text=""):
        queues_to_clear = [self.response_queue, self.audio_output_queue]
        # Add self.video_frame_queue back if using streaming logic
        # queues_to_clear.append(self.video_frame_queue)
        for q in queues_to_clear:
            while not q.empty():
                try: q.get_nowait()
                except asyncio.QueueEmpty: break

    async def process_input(self, message, is_final_turn_input=False):
        """ Puts message and flag into the input queue. """
        print(f"Processing input: '{message}', Final Turn: {is_final_turn_input}")
        if is_final_turn_input:
             await self.clear_queues() # Clear only before final input
        await self.input_queue.put((message, is_final_turn_input))

    async def process_video_frame(self, frame_data_url):
        """ Processes incoming video frame data URL """
        self.latest_video_frame_data_url = frame_data_url
        frame_data_url = None

    async def run_gemini_session(self):
        """Manages the Gemini conversation session, handling text, video, and tool calls."""
        print("Starting Gemini session manager...")
        try:
            while True: # Loop to process text inputs from the input_queue
                message, is_final_turn_input = await self.input_queue.get()

                if not (message.strip() and is_final_turn_input):
                    self.input_queue.task_done() # Mark non-final/empty messages as done
                    continue # Skip processing if not final input

                print(f"Sending FINAL input to Gemini: {message}")

                # --- Prepare Content for Gemini ---
                request_content = [message]
                if self.latest_video_frame_data_url:
                    try:
                        header, encoded = self.latest_video_frame_data_url.split(",", 1)
                        # Determine mime type from header (e.g., "data:image/jpeg;base64")
                        mime_type = header.split(':')[1].split(';')[0] if ':' in header and ';' in header else "image/jpeg" # Default or parse
                        frame_bytes = base64.b64decode(encoded)
                        request_content.append(types.Part.from_bytes(data=frame_bytes, mime_type=mime_type))
                        print(f"Included image frame with mime_type: {mime_type}")
                    except Exception as e:
                        print(f"Error processing video frame data URL: {e}")
                    finally:
                         self.latest_video_frame_data_url = None # Clear after use/attempt

                # --- 1. Send Initial Request and Process First Response Stream ---
                print("--- Sending request to Gemini ---")
                response_stream = await self.chat.send_message_stream(request_content)

                collected_function_calls = [] # Store detected function calls for later processing
                processed_text_in_turn = False # Flag to see if we sent any text

                async for chunk in response_stream:
                    # Safety check for empty chunks or structure issues
                    if not chunk.candidates or not chunk.candidates[0].content or not chunk.candidates[0].content.parts:
                        # print("Skipping empty or malformed chunk") # Optional debug log
                        continue

                    for part in chunk.candidates[0].content.parts:
                        if part.function_call:
                            print(f"--- Detected Function Call: {part.function_call.name} ---")
                            collected_function_calls.append(part.function_call) # Store the call details
                        elif part.text:
                            # Stream text parts immediately for TTS
                            await self.response_queue.put(part.text)
                            if self.socketio and self.client_sid:
                                self.socketio.emit('receive_text_chunk', {'text': part.text}, room=self.client_sid)
                            processed_text_in_turn = True

                # --- 2. Handle Function Calls (if any were detected) ---
                if collected_function_calls:
                    print(f"--- Processing {len(collected_function_calls)} detected function call(s) ---")
                    function_response_parts = []

                    # Note: Currently handles multiple calls sequentially. Could be parallelized.
                    for function_call in collected_function_calls:
                        tool_call_name = function_call.name
                        tool_call_args = dict(function_call.args) # Convert Struct to dict

                        if tool_call_name in self.available_functions:
                            function_to_call = self.available_functions[tool_call_name]
                            print(f"Executing function: {tool_call_name} with args: {tool_call_args}")
                            try:
                                # Execute the function
                                function_result = await function_to_call(**tool_call_args)
                                print(f"Function {tool_call_name} returned: {function_result}")

                                response_payload = function_result 

                                function_response_parts.append(
                                    types.Part.from_function_response(
                                        name=tool_call_name,
                                        response=response_payload # Pass the result dict directly
                                    )
                                )
                            except Exception as e:
                                print(f"!!! Error calling function {tool_call_name}: {e} !!!")
                                # Handle error - maybe send an error response back?
                                # For now, we might skip adding a response part or add an error part
                                function_response_parts.append(
                                     types.Part.from_function_response(
                                        name=tool_call_name,
                                        response={"error": f"Failed to execute function {tool_call_name}: {str(e)}"}
                                    )
                                )
                        else:
                            print(f"!!! Error: Function '{tool_call_name}' is not available. !!!")
                            # Handle missing function - inform Gemini
                            function_response_parts.append(
                                types.Part.from_function_response(
                                    name=tool_call_name,
                                    response={"error": f"Function {tool_call_name} not found or implemented."}
                                )
                            )

                    # --- 3. Send Function Response(s) Back to Gemini ---
                    if function_response_parts:
                        print(f"--- Sending {len(function_response_parts)} function response(s) back to Gemini ---")
                        response_stream_after_func = await self.chat.send_message_stream(function_response_parts) # Send ONLY the response parts

                        # --- 4. Process Final Text Response from Gemini ---
                        async for final_chunk in response_stream_after_func:
                             if final_chunk.candidates and final_chunk.candidates[0].content and final_chunk.candidates[0].content.parts:
                                for part in final_chunk.candidates[0].content.parts:
                                     if part.text:
                                        await self.response_queue.put(part.text)
                                        if self.socketio and self.client_sid:
                                            self.socketio.emit('receive_text_chunk', {'text': part.text}, room=self.client_sid)
                                        processed_text_in_turn = True
                        self.response_queue.put("")

                # --- 5. Signal End of Response to TTS ---
                print("--- Finished processing response for this turn. Signaling TTS end. ---")
                await self.response_queue.put(None) # Use None as a sentinel for the TTS loop

                self.input_queue.task_done() # Mark input processed

        except asyncio.CancelledError:
            print("Gemini session task cancelled.")
        except Exception as e:
            print(f"!!! Error in Gemini session manager: {e} !!!")
            # Log the full traceback for debugging
            import traceback
            traceback.print_exc()
            if self.socketio and self.client_sid:
                self.socketio.emit('error', {'message': f'Gemini session error: {str(e)}'}, room=self.client_sid)
            # Try to signal TTS end even on error, might help cleanup
            try:
                 await self.response_queue.put(None)
            except Exception:
                 pass # Ignore errors during error handling cleanup
        finally:
            print("Gemini session manager finished.")
            # Clean up video task if necessary (keep existing finally block logic)
            video_task = next((t for t in self.tasks if hasattr(t, 'get_coro') and t.get_coro().__name__ == 'run_video_sender'), None)
            if video_task and not video_task.done():
                 print("Cancelling video sender task from Gemini session finally block.")
                 video_task.cancel()
            self.gemini_session = None # Assuming this was meant to be self.chat? Or track session state elsewhere.

    async def run_tts_and_audio_out(self):
        print("Starting Gemini TTS and Audio Output manager...")
        while True:
            try:
                accumulated_text = ""
                while True:
                    text_chunk = await self.response_queue.get()
                    if text_chunk is None: # Sentinel for end of a complete response
                        self.response_queue.task_done()
                        break
                    accumulated_text += text_chunk
                    self.response_queue.task_done()

                if not accumulated_text.strip():
                    print("TTS: No text to speak for this turn.")
                    continue

                print(f"TTS: Generating audio for: '{accumulated_text[:60]}...'")
                try:
                    tts_generation_config = types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=GEMINI_TTS_VOICE)
                            )
                        )
                    )

                    # Use asyncio.to_thread for the synchronous SDK call
                    # Assuming self.client is the synchronous genai.Client
                    response = await asyncio.to_thread(
                        self.client.generate_content, # Synchronous client method
                        model=GEMINI_TTS_MODEL,
                        contents=[accumulated_text], # Contents should be an iterable
                        generation_config=tts_generation_config,
                        # stream=False is implied for generate_content unless stream=True
                    )

                    if response.candidates and response.candidates[0].content.parts:
                        audio_chunk_bytes = response.candidates[0].content.parts[0].inline_data.data
                        if audio_chunk_bytes:
                            print(f"TTS: Received audio data ({len(audio_chunk_bytes)} bytes). Emitting via SocketIO.")
                            if self.socketio and self.client_sid:
                                self.socketio.emit('receive_audio_chunk',
                                                   {'audio': base64.b64encode(audio_chunk_bytes).decode('utf-8')},
                                                   room=self.client_sid)
                        else:
                            print("TTS: No audio data in response part.")
                    else:
                        print("TTS: Invalid response structure or no audio data from Gemini.")
                        # Potentially emit an error or a silent chunk to the client
                        if self.socketio and self.client_sid:
                            self.socketio.emit('tts_error', {'message': 'TTS generation failed or no audio data.'}, room=self.client_sid)

                except Exception as e:
                    print(f"Error during Gemini TTS API call: {e}")
                    if self.socketio and self.client_sid:
                        self.socketio.emit('tts_error', {'message': f'TTS API Error: {str(e)}'}, room=self.client_sid)

            except asyncio.CancelledError:
                print("TTS and Audio Output manager task cancelled.")
                break
            except Exception as e:
                print(f"Error in TTS and Audio Output manager: {e}")
                if self.socketio and self.client_sid: # Notify client of an unexpected error
                    self.socketio.emit('tts_error', {'message': f'Unexpected error in TTS: {str(e)}'}, room=self.client_sid)
                await asyncio.sleep(1) # Avoid busy-looping on unexpected errors
            finally:
                # Ensure any pending SocketIO operations are flushed if possible, though usually handled by emit.
                # No websocket to close here anymore.
                pass

    async def start_all_tasks(self):
        print("Starting ADA background tasks...")
        if not self.tasks:
            loop = asyncio.get_running_loop()
            gemini_task = loop.create_task(self.run_gemini_session())
            tts_task = loop.create_task(self.run_tts_and_audio_out())
            self.tasks = [gemini_task, tts_task]
            # Add video sender task here if using streaming logic
            if hasattr(self, 'video_frame_queue'):
               video_sender_task = loop.create_task(self.run_video_sender())
               self.tasks.append(video_sender_task)
            print(f"ADA Core Tasks started: {len(self.tasks)}")
        else:
            print("ADA tasks already running.")

    async def stop_all_tasks(self):
        print("Stopping ADA background tasks...")
        tasks_to_cancel = list(self.tasks)
        for task in tasks_to_cancel:
            if task and not task.done(): task.cancel()
        await asyncio.gather(*[t for t in tasks_to_cancel if t], return_exceptions=True)
        self.tasks = []
        # Removed tts_websocket cleanup as it's no longer used
        self.gemini_session = None # This was self.chat in __init__, ensure consistency if it's meant to clear the chat session object
        print("ADA tasks stopped.")