# ADA (Advanced Design Assistant) - En Komplett Guide

Välkommen till ADA! Denna guide är skapad för att ge både programmerare och icke-programmerare en tydlig förståelse för vad ADA är, hur det fungerar, hur man installerar och använder det, samt hur man kan anpassa och ändra dess inställningar.

## 1. Introduktion

### Vad är ADA?

ADA, som står för "Advanced Design Assistant", är en smart AI-assistent som är specialiserad på ämnen inom STEM (vetenskap, teknik, ingenjörsvetenskap och matematik). Tänk på ADA som en digital medhjälpare som kan ge dig snabb och korrekt information, samt hjälpa till med olika uppgifter. Du kan prata med ADA eller skriva dina frågor, och ADA svarar antingen med röst eller text.

### Två Versioner: Lokal vs. Online

ADA finns i två huvudversioner, anpassade för olika behov:

*   **ADA Lokal (`ada_local`):** Denna version körs huvudsakligen direkt på din egen dator. Det innebär att den använder din dators processorkraft och minne för att fungera. Den är bra om du vill ha full kontroll över dina data och inte vill vara beroende av externa molntjänster. Prestandan kan dock variera beroende på hur kraftfull din dator är.
*   **ADA Online (`ada_online`):** Denna version använder sig av kraftfulla tjänster som körs i molnet (på internet), till exempel Google Gemini för AI-logiken och ElevenLabs för att generera röster. Detta gör att ADA Online oftast är snabbare, ger högre kvalitet på svaren och är mer pålitlig, eftersom den drar nytta av avancerad infrastruktur.

### Rekommendation

Vi **rekommenderar starkt att använda `ada_online`-versionen**. Anledningen är att den använder sig av avancerade molnbaserade AI-modeller (som Google Gemini) och rösttjänster (som ElevenLabs) som generellt ger snabbare, bättre och mer tillförlitliga svar. Dessa molntjänster har också utvecklats och förfinats under en längre tid.

## 2. Huvudfunktioner

ADA är utrustad med flera funktioner för att göra din interaktion smidig och effektiv:

*   **Två versioner:** Välj mellan att köra ADA lokalt på din dator eller använda de molnbaserade tjänsterna.
*   **Realtidsinteraktion:** Du kan kommunicera med ADA genom att prata (din röst omvandlas till text) och få svar som ADA läser upp för dig (text omvandlas till röst).
*   **Verktyg och funktioner (Widgets):** ADA kan utföra specifika uppgifter genom att använda inbyggda verktyg, som vi kallar "widgets" eller "funktioner". Den kan också använda externa verktyg som Google Sök för att hitta aktuell information. Exempel på vad ADA kan göra:
    *   Hämta systeminformation (t.ex. om din dator).
    *   Ställa in timers.
    *   Skapa projektmappar.
    *   Öppna kameran.
    *   Hantera en att-göra-lista (observera: denna funktion är inte fullt integrerad i de nuvarande huvudskripten).
    *   Hämta väderinformation.
    *   Beräkna restid.
*   **STEM-expertis:** ADA är särskilt utformad för att hjälpa till med frågor inom ingenjörsvetenskap, matematik och naturvetenskap.
*   **Konversationsförmåga:** Du kan prata med ADA på ett naturligt sätt, precis som med en människa.
*   **Multimodal Demo:** Det finns även ett separat skript (`multimodal_live_api.py`) som visar hur ADA kan interagera i realtid med både ljud och video (från din kamera eller skärm).

## 3. Hur Allt Hänger Ihop

För att förstå ADA är det bra att veta hur de olika delarna samarbetar.

### Övergripande Arkitektur

ADA-projektet består av flera delar som arbetar tillsammans:

*   **Kärnlogik (ADA):** Detta är hjärnan i ADA, där AI-modellerna och logiken för att förstå dina frågor och generera svar finns.
*   **Webbapplikation (`ada_app`):** Detta är den del som gör att du kan interagera med ADA via en webbläsare. Den består av två huvuddelar:
    *   **Backend (Server):** En Python-server som hanterar kommunikationen med AI-modellerna och de externa verktygen.
    *   **Frontend (Klient):** En webbsida (byggd med React) som du ser och interagerar med i din webbläsare.
*   **Kommunikation:** Frontend och Backend pratar med varandra i realtid med hjälp av något som kallas WebSockets (via SocketIO). Detta gör att meddelanden och röstdata kan skickas fram och tillbaka snabbt.

```mermaid
graph TD
    User[Användare] --> |Röst/Text| Frontend(Webbläsare - React App)
    Frontend --> |WebSockets (SocketIO)| Backend(Python Server - Flask)
    Backend --> |API Anrop| AI_Model(AI Modell - Google Gemini)
    Backend --> |API Anrop| External_Tools(Externa Verktyg - Google Sök, Väder, Kartor, ElevenLabs TTS)
    AI_Model --> |Svar/Verktygsanrop| Backend
    External_Tools --> |Resultat| Backend
    Backend --> |WebSockets (SocketIO)| Frontend
    Frontend --> |Ljud/Text| User
```

### `ADA` (Kärnlogik) vs. `ada_app` (Webbapplikation)

*   **`ADA` (mappen `ADA/`):** Denna mapp innehåller den grundläggande AI-logiken och de lokala verktygen (widgets) som ADA kan använda. Filerna här definierar hur ADA tänker och agerar.
    *   `ADA/ADA_Local.py`: Kärnlogiken för den lokala versionen.
    *   `ADA/ADA_Online.py`: Kärnlogiken för online-versionen (används av `main_online.py` och `ada_app/server/ADA_Online.py`).
    *   `ADA/WIDGETS/`: Mapp med Python-skript för lokala verktyg som kamera, timer, systeminfo, etc.
*   **`ada_app` (mappen `ada_app/`):** Detta är den kompletta webbapplikationen som låter dig använda ADA Online via en webbläsare.
    *   `ada_app/server/`: Innehåller Python-backend-servern (`app.py`) och en version av ADA:s online-logik (`ADA_Online.py`) som är anpassad för att fungera med webbservern.
    *   `ada_app/client/ada-online/`: Innehåller React-frontend-koden som bygger webbgränssnittet.

### Filöversikt - Vilken fil gör vad?

Här är en översikt över de viktigaste filerna och mapparna i projektet:

*   **Huvudskript (i rotmappen `/home/m/ada`):**
    *   `main_local.py`: Startar den lokala ADA-versionen. Använder Ollama för AI och lokala rösttjänster.
    *   `main_online.py`: Startar den online ADA-versionen med Google Gemini för AI och ElevenLabs för röst. Kräver API-nycklar.
    *   `main_online_noelevenlabs.py`: Startar online ADA-versionen med Google Gemini för AI, men använder din dators inbyggda rösttjänst istället för ElevenLabs. Kräver Google API-nyckel.
    *   `multimodal_live_api.py`: Ett separat skript som visar realtidsinteraktion med Gemini Live API, inklusive ljud och video.
    *   `README.md`: Denna fil du läser nu! (Den gamla filen beskrev projektet övergripande).
*   **`ADA/` (Kärnlogik och Lokala Verktyg):**
    *   `ADA/ADA_Local.py`: Innehåller klassen och logiken för den lokala ADA-assistenten.
    *   `ADA/ADA_Online.py`: Innehåller klassen och logiken för den online ADA-assistenten.
    *   `ADA/WIDGETS/`: Mapp som innehåller Python-skript för olika lokala verktyg (t.ex. `camera.py`, `project.py`, `system.py`, `timer.py`, `to_do_list.py`).
*   **`ada_app/` (Webbapplikationen):**
    *   `ada_app/server/`:
        *   `app.py`: Flask-servern som hanterar webbförfrågningar och SocketIO-kommunikation. Detta är hjärtat i backend.
        *   `ADA_Live_API.py`: (Kan vara en äldre/alternativ version av online-logiken, eller specifik för live-API:et).
        *   `ADA_Online.py`: (En kopia eller anpassad version av `ADA/ADA_Online.py` för servern).
    *   `ada_app/client/ada-online/`:
        *   `index.html`: Huvud-HTML-filen för webbapplikationen.
        *   `src/App.jsx`: Huvudkomponenten för React-applikationen, där mycket av gränssnittslogiken finns.
        *   `src/components/`: Mapp med individuella React-komponenter för chatt, inmatning, status, AI-visualisering, webbkamera, väder, kartor, sökresultat, etc. (t.ex. `ChatBox.jsx`, `InputArea.jsx`, `WebcamFeed.jsx`).
        *   `package.json`: Beskriver frontend-projektet och dess beroenden (vilka bibliotek React-appen behöver).
        *   `vite.config.js`: Konfigurationsfil för Vite, som är verktyget som bygger och kör React-applikationen.
        *   `README.md`: (Den gamla filen var en standard README för React/Vite-projekt).

## 4. Installation och Komma Igång

För att köra ADA behöver du installera några program och bibliotek. Dessa instruktioner förutsätter att du har Git, Python (version 3.7 eller nyare), pip (Pythons pakethanterare) och Node.js (med npm) installerat på din dator.

### Förberedelser (Prerequisites)

*   **Python:** Se till att du har Python installerat (helst version 3.11 eller nyare för full kompatibilitet).
*   **Ollama (för `ada_local`):** Om du vill köra den lokala versionen av ADA, måste du installera och köra Ollama. Ollama är ett program som låter dig köra stora AI-modeller direkt på din dator. Du behöver också ladda ner den specifika AI-modellen som används (t.ex. `gemma3:4b-it-q4_K_M`). Prestandan här beror mycket på din dators hårdvara.
*   **CUDA (Valfritt, för `ada_local` och lokala röstmodeller):** Om din dator har ett NVIDIA-grafikkort (GPU) med CUDA-stöd, rekommenderas detta starkt för bättre prestanda med lokala AI- och röstmodeller. ADA försöker automatiskt använda GPU:n om den finns.
*   **Mikrofon och Högtalare:** Krävs för röstinteraktion. **Hörlurar rekommenderas starkt** för att undvika eko och avbrott.
*   **API-nycklar (för `ada_online` och `multimodal_live_api.py`):** För online-versionerna behöver du speciella "nycklar" för att kunna använda molntjänsterna. Se avsnittet "API-nycklar" nedan.
*   **FFmpeg (Valfritt, Rekommenderas):** Vissa ljudbehandlingsbibliotek kan behöva FFmpeg. Om du får ljudfel, kan det hjälpa att installera FFmpeg och se till att det finns i din dators "PATH" (en lista över platser där program kan hittas).
*   **Systemberoenden (t.ex. `portaudio`):** Vissa Python-bibliotek för ljud (som `PyAudio`) kan kräva att du installerar ytterligare program på ditt operativsystem.

### Steg-för-steg Installation

1.  **Klona Projektet (Ladda ner koden):**
    Öppna din terminal eller kommandotolk och skriv:
    ```bash
    git clone https://github.com/Nlouis38/ada.git
    cd ada # Gå in i den nedladdade mappen
    ```

2.  **Installera Python-beroenden (för Backend):**
    Det är bäst att skapa en "virtuell miljö" för Python. Detta håller projektets bibliotek åtskilda från andra Python-projekt på din dator.
    ```bash
    python -m venv venv
    source venv/bin/activate # På Linux/macOS. På Windows: `venv\Scripts\activate`
    ```
    Du bör nu se `(venv)` framför din kommandorad, vilket indikerar att den virtuella miljön är aktiv.

    Installera sedan de nödvändiga Python-biblioteken. Se till att du är i rotmappen (`/home/m/ada`) eller i `ada_app/server/` beroende på vilken del du vill köra. För `ada_app/server/` finns en `requirements.txt` som du kan använda. För de fristående `main_*.py` skripten i rotmappen, behöver du installera alla listade bibliotek manuellt eller skapa en `requirements.txt` i rotmappen.

    **För `ada_app/server/`:**
    ```bash
    cd ada_app/server
    pip install -r requirements.txt
    cd ../.. # Gå tillbaka till rotmappen
    ```
    **För de fristående skripten i rotmappen (om du inte använder `ada_app`):**
    ```bash
    pip install ollama websockets pyaudio RealtimeSTT RealtimeTTS torch google-generativeai opencv-python pillow mss psutil GPUtil elevenlabs python-dotenv python-weather googlemaps googlesearch-python aiohttp beautifulsoup4 lxml requests eventlet
    ```
    *(Notera: `torch` kan vara krångligt att installera. Om du inte har ett NVIDIA GPU, överväg att installera `torch-cpu` istället. Besök [PyTorch webbplats](https://pytorch.org/) för specifika instruktioner.)*

3.  **Installera Frontend-beroenden (för Webbapplikationen):**
    Navigera till frontend-mappen och installera dess beroenden:
    ```bash
    cd ada_app/client/ada-online
    npm install
    cd ../../.. # Gå tillbaka till rotmappen
    ```
    Detta installerar React, Socket.IO-klienten och andra nödvändiga moduler för webbgränssnittet.

### API-nycklar (Konfiguration)

Både `ada_online` och `multimodal_live_api.py` samt `ada_app` kräver API-nycklar för att kunna kommunicera med molntjänsterna. **Det är mycket viktigt att du inte lägger in dessa nycklar direkt i koden!** Använd istället en `.env`-fil för säkerhet.

1.  **Skapa en `.env`-fil:**
    *   **För de fristående skripten (`main_online.py`, `multimodal_live_api.py`):** Skapa en fil som heter `.env` i **rotmappen** (`/home/m/ada`).
    *   **För webbapplikationens backend (`ada_app/server/`):** Skapa en fil som heter `.env` i mappen `ada_app/server/`.

2.  **Lägg till nycklar i `.env`-filen:** Öppna `.env`-filen och lägg till dina nycklar i följande format (ersätt platshållarna med dina riktiga nycklar):

    ```dotenv
    # .env-fil (exempel för rotmappen eller ada_app/server/)
    GOOGLE_API_KEY="DIN_GOOGLE_AI_STUDIO_NYCKEL_HÄR"
    ELEVENLABS_API_KEY="DIN_ELEVENLABS_NYCKEL_HÄR"
    MAPS_API_KEY="DIN_GOOGLE_MAPS_API_NYCKEL_HÄR"

    # Endast för ada_app/server/ .env-filen:
    FLASK_SECRET_KEY="en_mycket_stark_och_slumpmässig_hemlig_nyckel_vänligen_ändra_mig"
    REACT_APP_PORT="5173" # Standard för Vite. Använd 3000 för Create React App, eller din anpassade port.
    ```

3.  **Var får jag tag på nycklarna?**
    *   **Google Generative AI (Gemini API):**
        *   **Syfte:** Används för ADA:s AI-logik i online-versionerna.
        *   **Hämta:** Besök [Google AI Studio](https://aistudio.google.com/), logga in och skapa en API-nyckel.
    *   **ElevenLabs:**
        *   **Syfte:** Ger högkvalitativ röstsyntes (Text-till-Tal) för `ada_online`.
        *   **Hämta:** Gå till [ElevenLabs](https://elevenlabs.io/), logga in och hitta din API-nyckel i din profil/inställningar.
    *   **Google Maps:**
        *   **Syfte:** Används av funktionen för att beräkna restid i `ada_online`.
        *   **Hämta:** Gå till [Google Cloud Console](https://console.cloud.google.com/), skapa ett projekt (eller använd ett befintligt), aktivera "Directions API" och skapa en API-nyckel under "Credentials".

    **Viktigt:** Lägg till `.env` i din `.gitignore`-fil i både rotmappen och `ada_app/server/` för att förhindra att dina nycklar laddas upp till Git.

## 5. Köra ADA

Du kan köra ADA på flera sätt, beroende på vilken version du vill använda.

### Köra `ada_local` (Lokal version)

Denna version använder Ollama för AI och lokala rösttjänster. Prestandan beror mycket på din dators CPU/GPU och RAM.

*   **AI-modell (LLM):** Körs lokalt via Ollama (t.ex. `gemma3:4b-it-q4_K_M`).
*   **Röst-till-Text (STT):** Använder `RealtimeSTT`.
*   **Text-till-Röst (TTS):** Använder `RealtimeTTS` med din dators inbyggda röst (SystemEngine) eller CoquiEngine (kräver extra installation).
*   **Så här kör du:**
    ```bash
    # Se till att Ollama körs och att den nödvändiga modellen är nedladdad
    python main_local.py
    ```

### Köra `ada_online` (Online version med ElevenLabs)

Denna version använder Google Gemini (molnet) för AI och ElevenLabs (molnet) för röst. Kräver API-nycklar och internetanslutning. Generellt snabbare och högre kvalitet.

*   **AI-modell (LLM):** Google Gemini (t.ex. `gemini-2.0-flash-live-001`).
*   **Röst-till-Text (STT):** Använder `RealtimeSTT`.
*   **Text-till-Röst (TTS):** Använder `RealtimeTTS` med `ElevenlabsEngine` via WebSockets.
*   **Så här kör du:**
    ```bash
    # Se till att .env-filen i rotmappen är korrekt inställd med API-nycklar
    python main_online.py
    ```

### Köra `ada_online_noelevenlabs` (Online version utan ElevenLabs)

Denna version använder Google Gemini (molnet) för AI men din dators inbyggda rösttjänst för Text-till-Röst. Ett mellanting om du vill ha den bättre online-AI:n men inte har/vill ha en ElevenLabs-nyckel.

*   **AI-modell (LLM):** Google Gemini.
*   **Röst-till-Text (STT):** Använder `RealtimeSTT`.
*   **Text-till-Röst (TTS):** Använder `RealtimeTTS` med din dators inbyggda röst (SystemEngine).
*   **Så här kör du:**
    ```bash
    # Se till att .env-filen i rotmappen är korrekt inställd med GOOGLE_API_KEY och MAPS_API_KEY
    python main_online_noelevenlabs.py
    ```

### Köra Multimodal Live API Demo (`multimodal_live_api.py`)

Detta skript visar realtidsinteraktion med Gemini Live API, där både ljud från din mikrofon och videobilder (från kamera eller skärm) strömmas till Gemini-modellen, och ljudsvaret spelas upp.

*   **Förberedelser:** Se till att alla beroenden är installerade och att din `GOOGLE_API_KEY` är inställd i `.env`-filen i rotmappen. **Använd hörlurar!**
*   **Så här kör du:**
    *   **Med Kamera:**
        ```bash
        python multimodal_live_api.py --mode camera # eller bara python multimodal_live_api.py
        ```
    *   **Med Skärmdelning:**
        ```bash
        python multimodal_live_api.py --mode screen
        ```
    *   **Endast Ljud:**
        ```bash
        python multimodal_live_api.py --mode none
        ```
    Du kan också skriva textmeddelanden i konsolen medan ljud/video strömmas. Skriv 'q' och tryck Enter för att avsluta.

### Köra Webbapplikationen (`ada_app`)

För att köra webbapplikationen behöver du två separata terminalfönster: ett för backend (servern) och ett för frontend (webbgränssnittet).

1.  **Starta Backend-servern:**
    *   Öppna Terminal 1.
    *   Navigera till `ada_app/server`-mappen: `cd ada_app/server`
    *   Aktivera din Python virtuella miljö: `source venv/bin/activate` (eller `venv\Scripts\activate` på Windows).
    *   Kör Flask-applikationen:
        ```bash
        python app.py
        ```
    *   Vänta tills du ser meddelanden som indikerar att servern körs (t.ex. `* Running on http://0.0.0.0:5000`). Låt detta terminalfönster vara öppet.

2.  **Starta Frontend-utvecklingsservern:**
    *   Öppna Terminal 2.
    *   Navigera till `ada_app/client/ada-online`-mappen: `cd ada_app/client/ada-online`
    *   Starta utvecklingsservern:
        ```bash
        npm run dev
        ```
    *   Detta bör automatiskt öppna applikationen i din webbläsare, vanligtvis på `http://localhost:5173`.

3.  **Använd Applikationen:**
    *   Interagera med gränssnittet i din webbläsare. Godkänn behörigheter för mikrofon och webbkamera om du vill använda dessa funktioner.

### Stoppa Applikationen

1.  **Stoppa Frontend-servern:** Gå till Terminal 2 och tryck `Ctrl + C`.
2.  **Stoppa Backend-servern:** Gå till Terminal 1 och tryck `Ctrl + C`.
3.  **Avaktivera Virtuell Miljö (Valfritt):** I Terminal 1 kan du skriva `deactivate`.

## 6. Anpassa och Ändra Inställningar

Här beskrivs hur du kan ändra viktiga inställningar i ADA.

### Byta TTS-leverantör (Text-till-Röst)

Om du använder `ada_online` men vill byta från ElevenLabs till en annan rösttjänst, till exempel din dators inbyggda röst eller en lokal Gemini-modell (som inte har en egen TTS-tjänst, men kan använda lokala TTS-motorer via `RealtimeTTS`), kan du göra så här:

*   **Använda din dators inbyggda röst (System TTS) med online AI:**
    *   Om du vill använda Google Gemini för AI men din dators inbyggda röst för TTS, kör skriptet `main_online_noelevenlabs.py` istället för `main_online.py`. Detta skript är redan konfigurerat för att använda `SystemEngine` från `RealtimeTTS`.
    *   För webbapplikationen (`ada_app`): Du behöver ändra i `ada_app/server/ADA_Online.py`. Leta efter raden som initierar `ElevenlabsEngine` och byt ut den mot `SystemEngine` eller en annan lokal motor som `CoquiEngine` (om du har den installerad och konfigurerad).

    **Exempel på ändring i `ada_app/server/ADA_Online.py` (för programmerare):**

    Hitta något liknande:
    ```python
    # In ADA_Online.py (serverns version)
    from RealtimeTTS import ElevenlabsEngine
    # ...
    self.tts_engine = ElevenlabsEngine(api_key=ELEVENLABS_API_KEY)
    ```
    Ändra till (för System TTS):
    ```python
    # In ADA_Online.py (serverns version)
    from RealtimeTTS import SystemEngine
    # ...
    self.tts_engine = SystemEngine() # Ingen API-nyckel behövs
    ```
    Eller (för CoquiEngine, om installerad):
    ```python
    # In ADA_Online.py (serverns version)
    from RealtimeTTS import CoquiEngine
    # ...
    self.tts_engine = CoquiEngine() # Kan kräva modellnedladdning och konfiguration
    ```

*   **Använda en lokal TTS-motor med Gemini AI (om du inte vill använda ElevenLabs):**
    *   Som nämnts ovan, Gemini själv tillhandahåller inte en lokal TTS-motor. Däremot kan du använda Gemini som din AI-modell och sedan koppla den till en lokal TTS-motor via `RealtimeTTS`.
    *   Detta görs genom att ändra vilken `RealtimeTTS`-motor som används i `main_online.py` eller `ada_app/server/ADA_Online.py`. Följ exemplen ovan för att byta till `SystemEngine` eller `CoquiEngine`.

### Byta LLM-modell (AI-modell)

Du kan ändra vilken specifik AI-modell ADA använder:

*   **För `ada_local` (Ollama):**
    *   Öppna `ADA/ADA_Local.py`.
    *   Leta efter raden där Ollama-modellen specificeras, t.ex.:
        ```python
        self.ollama_model = "gemma3:4b-it-q4_K_M"
        ```
    *   Ändra `gemma3:4b-it-q4_K_M` till namnet på den Ollama-modell du vill använda (se till att du har laddat ner den med `ollama pull <modellnamn>`).
*   **För `ada_online` och `ada_app` (Google Gemini):**
    *   Öppna `ADA/ADA_Online.py` (för de fristående skripten) eller `ada_app/server/ADA_Online.py` (för webbapplikationen).
    *   Leta efter raden där Gemini-modellen specificeras, t.ex.:
        ```python
        self.model = genai.GenerativeModel("gemini-2.0-flash-live-001", ...)
        ```
    *   Ändra `"gemini-2.0-flash-live-001"` till namnet på den Gemini-modell du vill använda (t.ex. `"gemini-1.5-flash"`, `"gemini-1.5-pro"`).

### Byta ut Backend (för webbapplikationen `ada_app`)

Om du är en avancerad programmerare och vill byta ut hela backend-servern (t.ex. till ett annat språk eller ramverk), är det fullt möjligt, men kräver att du förstår hur frontend och backend kommunicerar.

*   **Kommunikationsprotokoll:** Frontend (React-appen) kommunicerar med backend via SocketIO. Detta innebär att den skickar och tar emot meddelanden via specifika "händelsenamn" (event names).
*   **Viktiga händelsenamn som frontend förväntar sig:**
    *   `receive_text_chunk`: För att ta emot textbitar som ska visas i chatten.
    *   `receive_audio_chunk`: För att ta emot ljudbitar som ska spelas upp.
    *   `weather_update`, `map_update`, `search_results_update`, `executable_code_received`: För att uppdatera de olika widgetarna med data.
    *   `status_update`: För att uppdatera statusmeddelanden (t.ex. "lyssnar", "tänker").
*   **Vad du behöver göra:**
    *   Du måste implementera en ny backend-server (i vilket språk/ramverk du vill) som kan hantera SocketIO-anslutningar.
    *   Din nya backend måste skicka data till frontend med exakt samma händelsenamn och dataformat som den nuvarande Python-backend gör.
    *   Du måste också se till att din nya backend kan ta emot de händelser som frontend skickar (t.ex. `send_text_message`, `send_transcribed_text`, `send_video_frame`).
    *   Studera `ada_app/server/app.py` och `ada_app/server/ADA_Online.py` noggrant för att förstå hur den nuvarande backend hanterar dessa meddelanden och integrerar med AI-modellen och verktygen.

## 7. Felsökning

Här är några vanliga problem och hur du kan lösa dem:

*   **Ljudproblem (ingen in- eller utdata):**
    *   Kontrollera att mikrofon och högtalare är korrekt anslutna och inte är avstängda eller mutade i ditt operativsystem.
    *   Se till att ADA har behörighet att använda din mikrofon (operativsystemets inställningar).
    *   Om du får felmeddelanden som nämner `PyAudio` eller `portaudio`, kan du behöva installera `portaudio` på ditt system.
    *   Om felmeddelanden nämner ljudkodning/avkodning, kontrollera att FFmpeg är installerat.
*   **API-nyckelfel (`ada_online`, `multimodal_live_api.py`, `ada_app`):**
    *   Dubbelkolla att nycklarna i din `.env`-fil är exakt korrekta.
    *   Se till att de relevanta API:erna (Gemini, Maps, ElevenLabs) är aktiverade i deras respektive molnkonsoler (Google Cloud Console, ElevenLabs webbplats).
    *   Kontrollera om du har överskridit några användningsgränser (kvoter) för API:erna eller om det finns problem med fakturering.
*   **Biblioteksfel:**
    *   Se till att alla bibliotek som listas i installationsavsnittet är korrekt installerade i din aktiva virtuella miljö.
    *   Vissa bibliotek (som `torch`) kan ha specifika krav på CPU/GPU-versioner.
*   **Ollama-problem (`ada_local`):**
    *   Kontrollera att Ollama-tjänsten körs i bakgrunden.
    *   Verifiera att den specifika AI-modellen du vill använda är nedladdad (`ollama pull <modellnamn>`).
    *   Titta i Ollamas loggar för att se om det finns några felmeddelanden där.
*   **TTS-problem (Text-till-Röst):**
    *   Om du använder ElevenLabs, kontrollera din API-nyckel och internetanslutning.
    *   Om du använder CoquiEngine, se till att den är korrekt installerad och att röstmodellerna är nedladdade.
    *   Om du använder din dators inbyggda röst (SystemEngine), se till att den fungerar korrekt i ditt operativsystem. Latensen kan vara högre med denna.
*   **STT-problem (Röst-till-Text):**
    *   Kontrollera mikrofonens volymnivåer.
    *   Se till att `RealtimeSTT`-modellen är lämplig för din hårdvara (större modeller kräver mer resurser).
    *   Bakgrundsljud kan störa. Använd hörlurar.
