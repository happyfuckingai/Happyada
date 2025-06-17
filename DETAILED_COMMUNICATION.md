# Detaljerad Förklaring: Hur ADA:s Webbapplikation (`ada_app`) Fungerar

Denna fil beskriver i detalj hur ADA:s webbapplikation är uppbyggd och hur de olika komponenterna kommunicerar med varandra för att skapa en realtidsinteraktiv upplevelse.

ADA:s webbapplikation är byggd för realtidsinteraktion, vilket innebär att den kan lyssna, tänka och svara nästan omedelbart. Detta uppnås genom en kombination av en frontend (webbgränssnittet i din webbläsare) och en backend (en server som körs på din dator), som kommunicerar sömlöst.

## 1. Startpunkt: Användaren och Frontend (Webbgränssnittet i din webbläsare)

När du öppnar ADA i din webbläsare startar processen:

*   **`index.html`**: Detta är den grundläggande HTML-filen som laddas först. Den fungerar som en tom duk där React-applikationen sedan byggs upp.
*   **`main.jsx`**: Denna fil är startpunkten för React-applikationen. Den tar kontroll över `index.html` och börjar rendera de olika delarna av gränssnittet.
*   **`App.jsx`**: Detta är hjärtat i frontend. `App.jsx` hanterar det övergripande tillståndet för applikationen (t.ex. om mikrofonen är på, vilka meddelanden som visas, om videoflödet är aktivt). Den etablerar också den viktiga **Socket.IO-anslutningen** till backend-servern.
*   **`InputArea.jsx`**: Detta är komponenten där du som användare interagerar. Här kan du skriva dina meddelanden i ett textfält eller klicka på mikrofonknappen för att prata. Här finns också knappen för att starta/stoppa videoflödet (webbkamera/skärmdelning).
*   **`VideoFeed.jsx`**: Denna komponent hanterar visning av video från din webbkamera eller din skärm. Den fångar videoströmmen och förbereder den för att skickas till backend.
*   **`ChatBox.jsx`**: Visar konversationen mellan dig och ADA.
*   **`StatusDisplay.jsx`**: Visar meddelanden om ADA:s aktuella status (t.ex. "Lyssnar...", "Tänker...").
*   **`AiVisualizer.jsx`**: En visuell indikator som ändrar utseende beroende på om ADA lyssnar, talar eller är inaktiv.
*   **Widget-komponenter** (t.ex. `WeatherWidget.jsx`, `MapWidget.jsx`, `SearchResultsWidget.jsx`, `CodeExecutionWidget.jsx`): Dessa komponenter visas dynamiskt när ADA behöver presentera specifik information (t.ex. väderprognoser, kartor, sökresultat eller kod).

## 2. Kommunikation Frontend -> Backend (via Socket.IO)

När du interagerar med frontend skickas information till backend-servern:

*   **Anslutning:** Så snart `App.jsx` laddas, försöker den ansluta till backend-servern (vanligtvis `http://localhost:5000`) med hjälp av **Socket.IO**. Detta skapar en **beständig, dubbelriktad kommunikationskanal (WebSocket)**.
*   **Textinmatning:**
    1.  Du skriver ett meddelande i `InputArea` och trycker "Send" eller Enter.
    2.  `InputArea.jsx` skickar texten till `App.jsx` via en funktion (`onSendText` prop).
    3.  `App.jsx` tar emot texten och skickar den omedelbart till backend-servern via Socket.IO-eventet `"send_text_message"`.
*   **Röstinmatning (Speech-to-Text - STT):**
    1.  Du klickar på mikrofonknappen i `InputArea`.
    2.  `App.jsx` använder webbläsarens inbyggda **Web Speech API** för att lyssna på din mikrofon.
    3.  När du talar, transkriberar Web Speech API din röst till text i realtid.
    4.  När du slutar tala (eller efter en kort paus), skickar `App.jsx` den färdiga transkriberade texten till backend-servern via Socket.IO-eventet `"send_transcribed_text"`.
*   **Video/Skärminmatning (Multimodal Input):**
    1.  Du klickar på "Show Video" och väljer "Webcam" eller "Screen Share" i `VideoFeed`.
    2.  `VideoFeed.jsx` använder webbläsarens API:er (`navigator.mediaDevices.getUserMedia()` för kamera, `navigator.mediaDevices.getDisplayMedia()` för skärm) för att fånga en videoström.
    3.  Komponenten ritar kontinuerligt (t.ex. varje sekund) en bild från videoströmmen till en dold HTML `<canvas>`.
    4.  Bilden från `<canvas>` konverteras till en Base64-kodad JPEG-bild (en textsträng som representerar bilden).
    5.  Denna Base64-bild skickas till backend-servern via Socket.IO-eventet `"send_video_frame"`.
    6.  När du stänger videoflödet skickas eventet `"video_feed_stopped"` till backend.

## 3. Backend-bearbetning (Python Flask/Socket.IO Server)

Backend-servern är skriven i Python och använder Flask för webbserverfunktioner och Flask-SocketIO för realtidskommunikation.

*   **`app.py`**: Detta är huvudfilen för backend-servern. Den fungerar som en "router" som tar emot alla inkommande Socket.IO-event från frontend. Den skapar också en instans av `ADA_Online`-klassen.
*   **`ADA_Online.py`**: Denna fil innehåller den faktiska AI-logiken och integrationen med externa tjänster. Det är här ADA:s "tänkande" sker.
*   **Mottagande av data i `app.py`:**
    *   När `app.py` tar emot `"send_text_message"` eller `"send_transcribed_text"`:
        *   Den skickar texten vidare till `ADA_Online.py` för att bearbetas av AI-modellen.
    *   När `app.py` tar emot `"send_video_frame"`:
        *   Den avkodar den Base64-kodade bilden tillbaka till ett bildformat som Python kan hantera.
        *   Den skickar bilden (tillsammans med eventuell textkontext) till `ADA_Online.py` för att skickas till Google Gemini Live API (om konfigurerat för multimodal input).
*   **AI-bearbetning i `ADA_Online.py`:**
    1.  `ADA_Online.py` tar emot texten och/eller bilden.
    2.  Den skickar denna input till **Google Gemini API** (en kraftfull AI-modell som körs i Googles moln).
    3.  **Funktionsanrop (Tool Calling):** Gemini-modellen analyserar din fråga och den visuella informationen. Om den bedömer att den behöver hjälp av ett externt verktyg för att svara (t.ex. om du frågar om vädret eller vill söka på internet), "anropar" den en specifik funktion.
        *   `ADA_Online.py` har fördefinierade Python-funktioner (t.ex. `get_weather`, `get_travel_duration`, `get_search_results`) som motsvarar dessa verktyg.
        *   `ADA_Online.py` exekverar den anropade Python-funktionen. Dessa funktioner gör i sin tur egna API-anrop till externa tjänster (t.ex. `python-weather` för väder, `googlemaps` för kartor, `googlesearch-python` för webbsökning).
        *   Resultatet från det externa verktyget (t.ex. väderdata, restid, sökresultat) skickas sedan tillbaka till Gemini-modellen.
    4.  **Generering av svar:** Gemini-modellen använder all information (din ursprungliga fråga, video, och eventuella verktygsresultat) för att formulera ett textbaserat svar.

## 4. Kommunikation Backend -> Frontend (via Socket.IO)

När backend har bearbetat din input och genererat ett svar, skickas det tillbaka till frontend:

*   **Text-svar:**
    1.  `ADA_Online.py` skickar Gemini:s text-svar tillbaka till `app.py` i små, hanterbara "bitar" (chunks).
    2.  `app.py` skickar dessa textbitar till frontend via Socket.IO-eventet `"receive_text_chunk"`.
*   **Röst-svar (Text-to-Speech - TTS):**
    1.  Samtidigt som texten skickas till frontend, skickar `ADA_Online.py` även text-svaret till **ElevenLabs TTS API** (en molntjänst för röstsyntes) via en separat WebSocket-anslutning.
    2.  ElevenLabs genererar ljudbitar (i PCM-format) och strömmar tillbaka dem till `ADA_Online.py`.
    3.  `ADA_Online.py` tar emot dessa ljudbitar, Base64-kodar dem, och skickar dem till frontend via Socket.IO-eventet `"receive_audio_chunk"`.
*   **Verktygsresultat:**
    *   När ett verktyg har körts och genererat ett resultat (t.ex. väderdata, kartdata, sökresultat), skickar `app.py` dessa data via dedikerade Socket.IO-event (t.ex. `"weather_update"`, `"map_update"`, `"search_results_update"`, `"executable_code_received"`) till frontend.
*   **Statusuppdateringar:** Backend skickar kontinuerligt statusmeddelanden (t.ex. "Thinking...", "Ready.") via `"status"` eventet för att hålla dig informerad om vad ADA gör.

## 5. Åter till Frontend (Webbgränssnittet) för visning och uppspelning

`App.jsx` i frontend lyssnar på alla dessa inkommande Socket.IO-event:

*   **Text:** När `"receive_text_chunk"` tas emot, läggs textbitarna ihop och visas i `ChatBox.jsx`, vilket bygger upp ADA:s svar i realtid.
*   **Ljud:** När `"receive_audio_chunk"` tas emot:
    *   Ljudbitarna läggs i en kö.
    *   `App.jsx` använder webbläsarens **Web Audio API** för att spela upp ljudbitarna i ordning, vilket skapar ADA:s röstsvar.
    *   `AiVisualizer.jsx` uppdaterar sin status (t.ex. till "Speaking") baserat på om ljud spelas upp.
*   **Verktygsresultat:** När `"weather_update"`, `"map_update"`, `"search_results_update"` etc. tas emot, uppdateras tillståndet i `App.jsx`. Detta gör att respektive widget-komponent (`WeatherWidget.jsx`, `MapWidget.jsx`, `SearchResultsWidget.jsx`) visas med den nya datan.
*   **Status:** `StatusDisplay.jsx` uppdateras med de senaste statusmeddelandena från backend.

## Hur det "bara lirar och fungerar"

Nyckeln till att allt "bara lirar och fungerar" är den **realtidskommunikation** som möjliggörs av **WebSockets (Socket.IO)**. Istället för att frontend hela tiden måste fråga backend om det finns något nytt, kan backend "pusha" information till frontend så fort den blir tillgänglig. Detta skapar en flytande och responsiv upplevelse.

*   **Asynkronitet:** Både frontend (med Reacts `useEffect` och `useCallback` hooks, samt Web Audio API) och backend (med `asyncio` i Python) är designade för att hantera uppgifter asynkront. Det betyder att de kan utföra flera saker samtidigt utan att blockera varandra, vilket är avgörande för realtidsinteraktion (t.ex. att lyssna på mikrofonen, skicka data, ta emot svar och spela upp ljud samtidigt).
*   **Modulär design:** Projektet är uppdelat i små, specialiserade komponenter (t.ex. `InputArea`, `ChatBox`, `VideoFeed`, `ADA_Online`). Varje komponent har en tydlig uppgift, och de kommunicerar med varandra via väldefinierade gränssnitt (props i React, eventer i Socket.IO). Detta gör systemet lättare att förstå, underhålla och utöka.
*   **API-integrationer:** Genom att använda API:er (Application Programming Interfaces) kan ADA koppla ihop sig med kraftfulla externa tjänster som Google Gemini och ElevenLabs. Dessa API:er fungerar som standardiserade "kontrakt" för hur olika program kan prata med varandra.
