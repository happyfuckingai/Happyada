# Guide: Installation och Konfiguration av Coqui TTS för ADA

Denna guide beskriver hur du installerar, konfigurerar och använder Coqui TTS (Text-to-Speech) som röstmotor för din ADA-assistent. Coqui TTS är ett kraftfullt alternativ för dig som vill köra röstsyntesen lokalt på din egen dator.

## 1. Introduktion till Coqui TTS

### Vad är Coqui TTS?

Coqui TTS är ett öppet källkods-ramverk för avancerad text-till-tal-syntes (TTS). Det är utvecklat för att generera högkvalitativa, naturligt klingande röster direkt på din egen maskin. Till skillnad från molnbaserade tjänster som ElevenLabs, körs Coqui TTS helt lokalt, vilket ger dig full kontroll över processen och dina data.

### Varför använda Coqui TTS?

*   **Integritet och Offline-användning:** Eftersom Coqui TTS körs lokalt, skickas ingen ljuddata till externa servrar. Detta är idealiskt för integritetsmedvetna användare eller för användning i miljöer utan internetanslutning.
*   **Inga API-nycklar:** Du behöver inga API-nycklar eller prenumerationer för att använda Coqui TTS, vilket kan vara kostnadseffektivt på lång sikt.
*   **Anpassningsbarhet:** Med Coqui TTS kan du experimentera med olika röstmodeller och till och med träna egna modeller (även om det senare är en avancerad uppgift).

### Jämförelse med ElevenLabs och System TTS

| Funktion/Aspekt | Coqui TTS (Lokal)                               | ElevenLabs (Molnbaserad)                               | System TTS (Lokal, OS-beroende)                     |
| :-------------- | :---------------------------------------------- | :----------------------------------------------------- | :-------------------------------------------------- |
| **Körplats**    | Din dator (lokalt)                              | Molnet (kräver internet)                               | Din dator (lokalt, inbyggt i OS)                    |
| **Kvalitet**    | Mycket hög, naturlig (beroende på modell)       | Extremt hög, mycket naturlig, expressiv                | Varierande, ofta robotliknande eller mindre naturlig |
| **Latens**      | Låg till medel (beroende på hårdvara/modell)    | Mycket låg (optimerad för realtid)                     | Medel till hög                                      |
| **Kostnad**     | Gratis (efter initial hårdvaruinvestering)     | Kostnad per användning (API-nyckel, prenumeration)     | Gratis                                              |
| **Integritet**  | Hög (data lämnar inte din dator)                | Medel (data skickas till molntjänst)                   | Hög (data lämnar inte din dator)                    |
| **Hårdvara**    | Kan vara resurskrävande (CPU/GPU, RAM)          | Ingen lokal hårdvara krävs för TTS-generering          | Låg resursanvändning                                |
| **Installation**| Mer komplex (Python, modeller, ev. CUDA)        | Enkel (bara API-nyckel)                                | Ingen (redan installerad)                           |

## 2. Förberedelser (Prerequisites)

Innan du installerar Coqui TTS, se till att du har följande:

*   **Python:** Python 3.8 eller nyare rekommenderas. Se till att du har `pip` (Pythons pakethanterare) installerat.
*   **Virtuell Miljö:** Det är starkt rekommenderat att du arbetar inom en Python virtuell miljö för att undvika konflikter med andra Python-projekt.
*   **CUDA (Valfritt, men starkt rekommenderat för GPU):** Om din dator har ett NVIDIA-grafikkort (GPU) med CUDA-stöd, kommer Coqui TTS att dra stor nytta av detta för betydligt snabbare röstgenerering. Se till att du har CUDA Toolkit och cuDNN installerat och konfigurerat korrekt för din PyTorch-installation. Utan GPU kommer Coqui TTS att köra på CPU, vilket kan vara långsamt för större modeller.
*   **FFmpeg:** Coqui TTS och dess underliggande bibliotek kan behöva FFmpeg för ljudbehandling. Om du stöter på fel relaterade till ljud, installera FFmpeg och se till att det finns i din dators PATH.

## 3. Installation av Coqui TTS

Följ dessa steg för att installera Coqui TTS i ditt ADA-projekt:

1.  **Navigera till projektets rotmapp:**
    ```bash
    cd /home/m/ada
    ```

2.  **Aktivera din Python virtuella miljö:**
    Om du inte redan har en, skapa en:
    ```bash
    python -m venv venv
    ```
    Aktivera den:
    ```bash
    source venv/bin/activate # På Linux/macOS
    # Eller på Windows:
    # venv\Scripts\activate
    ```
    Du bör se `(venv)` framför din kommandorad.

3.  **Installera Coqui TTS och RealtimeTTS:**
    `RealtimeTTS` är biblioteket som ADA använder för att hantera realtidsröstsyntes, och det har stöd för Coqui TTS som en "motor". Du kan installera `RealtimeTTS` med Coqui-beroendena direkt:
    ```bash
    pip install RealtimeTTS[coqui]
    ```
    **Viktigt om `torch`:** Installationen ovan kommer att försöka installera `torch` (PyTorch). Om du har en NVIDIA GPU och vill använda den, kan du behöva installera `torch` manuellt med rätt CUDA-version först, enligt instruktionerna på [PyTorch webbplats](https://pytorch.org/get-started/locally/). Om du inte har en GPU, eller om du stöter på problem, kan du behöva installera `torch-cpu` istället för den fullständiga `torch`-paketet.

    Om `pip install RealtimeTTS[coqui]` misslyckas, kan du prova att installera `TTS` (Coqui TTS-biblioteket) separat först, och sedan `RealtimeTTS`:
    ```bash
    pip install TTS
    pip install RealtimeTTS
    ```

## 4. Ladda ner Röstmodeller

Coqui TTS fungerar med specifika röstmodeller som du måste ladda ner. Dessa modeller är ofta stora (flera hundra MB till GB).

*   **Hitta modeller:** Coqui TTS har ett "modellbibliotek" (model zoo) med förtränade röster. Du kan hitta exempel och namn på modeller i Coqui TTS-dokumentationen eller i exempelkod. En vanlig modell är till exempel `tts_models/en/ljspeech/tacotron2-DDC`.
*   **Modellnedladdning:** När du initierar `CoquiEngine` i din kod för första gången, kommer den automatiskt att försöka ladda ner den specificerade modellen om den inte redan finns lokalt. Du behöver alltså inte ladda ner dem manuellt i förväg, men det kan ta tid vid första körningen.

## 5. Konfigurera ADA för att Använda Coqui TTS

Nu när Coqui TTS är installerat, måste du tala om för ADA att den ska använda Coqui TTS istället för ElevenLabs eller System TTS.

### För de fristående Python-skripten (`main_local.py`, `main_online.py`, `main_online_noelevenlabs.py`)

Dessa skript använder klasserna `ADA_Local.py` och `ADA_Online.py` som finns i mappen `ADA/`. Du behöver ändra i den relevanta `ADA_*.py`-filen.

**Exempel: Ändra `ADA/ADA_Online.py` för att använda Coqui TTS istället för ElevenLabs:**

1.  **Öppna filen:** `ADA/ADA_Online.py`
2.  **Ändra importen:** Byt ut `ElevenlabsEngine` mot `CoquiEngine`.
    ```python
    # Före:
    # from RealtimeTTS import ElevenlabsEngine
    # Efter:
    from RealtimeTTS import CoquiEngine
    ```
3.  **Ändra initieringen av TTS-motorn:** Leta upp raden där `self.tts_engine` initieras och ändra den till att använda `CoquiEngine`. Du måste också specificera vilken Coqui TTS-modell du vill använda.

    ```python
    # Före (om du använde ElevenLabs):
    # ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    # self.tts_engine = ElevenlabsEngine(api_key=ELEVENLABS_API_KEY)

    # Efter (för Coqui TTS):
    # Välj en modell. Exempel: "tts_models/en/ljspeech/tacotron2-DDC"
    # Du kan hitta fler modeller i Coqui TTS dokumentation.
    COQUI_MODEL_NAME = "tts_models/en/ljspeech/tacotron2-DDC"
    self.tts_engine = CoquiEngine(model_name=COQUI_MODEL_NAME)
    ```
    Om du vill använda en specifik röst från en modell som stöder flera röster, kan du behöva lägga till `speaker_name` eller liknande parametrar beroende på modellen. Se Coqui TTS dokumentation för detaljer om den valda modellen.

### För Webbapplikationens Backend (`ada_app/server/ADA_Online.py`)

Om du kör ADA via webbapplikationen (`ada_app`), behöver du göra samma typ av ändring i backend-filen som hanterar AI-logiken för servern.

1.  **Öppna filen:** `ada_app/server/ADA_Online.py`
2.  **Gör samma ändringar** som beskrivs ovan för `ADA/ADA_Online.py` (dvs. ändra import och initiering av `self.tts_engine` till `CoquiEngine` med önskad modell).

## 6. Användning och Prestanda

När du har konfigurerat ADA att använda Coqui TTS, kan du starta ADA som vanligt (t.ex. `python main_online.py` eller starta `ada_app` backend och frontend).

*   **Första körningen:** Vid första körningen med en ny Coqui TTS-modell kommer systemet att ladda ner modellen. Detta kan ta en stund beroende på din internetanslutning och modellens storlek.
*   **Prestanda:**
    *   **CPU:** Om du kör Coqui TTS enbart på din CPU, kan röstgenereringen vara märkbart långsammare än med ElevenLabs, särskilt för längre svar eller större modeller. Detta kan leda till en viss fördröjning innan ADA börjar tala.
    *   **GPU (rekommenderas):** Med en kompatibel NVIDIA GPU och korrekt CUDA-installation kommer Coqui TTS att vara betydligt snabbare och kan närma sig realtidsprestanda.
*   **Minnesanvändning:** Coqui TTS-modeller kan kräva en del RAM, särskilt större modeller. Se till att din dator har tillräckligt med minne.

## 7. Optimering för Ubuntu (utan GPU)

Att optimera Coqui TTS för en Ubuntu-miljö utan GPU handlar om att maximera CPU-prestanda och minimera andra flaskhalsar. Här är några tips:

*   **Välj Mindre Röstmodeller:** Detta är den enskilt viktigaste faktorn för CPU-prestanda. Större, mer komplexa modeller kräver betydligt mer beräkningskraft. Coqui TTS erbjuder ofta olika storlekar av samma röst (t.ex. mindre versioner för snabbare inferens). Experimentera med mindre modeller för att hitta en bra balans mellan kvalitet och hastighet.
*   **Säkerställ `torch-cpu` Installation:** Se till att du har installerat PyTorch:s CPU-version (`torch-cpu`) korrekt. Om du av misstag har en GPU-version installerad utan en GPU, kan det leda till onödiga fel och prestandaproblem när systemet försöker hitta en icke-existerande GPU.
    ```bash
    pip uninstall torch torchvision torchaudio # Avinstallera befintliga om osäkert
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    ```
*   **Maximera CPU-användning:**
    *   **Stäng andra program:** Minimera antalet bakgrundsprocesser och andra applikationer som använder CPU och RAM när du kör ADA.
    *   **CPU-frekvensskalning:** Se till att din CPU körs på sin maximala frekvens. På Ubuntu kan du ofta kontrollera detta med verktyg som `cpufrequtils` eller genom att titta i `/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor`. Se till att den är inställd på `performance` under användning.
        ```bash
        # Installera om det behövs
        sudo apt install cpufrequtils
        # Kontrollera nuvarande governor
        cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
        # Sätt till performance (kan behöva göras vid varje omstart eller konfigureras permanent)
        sudo cpufreq-set -g performance
        ```
*   **Minimera Swap-användning (Swappiness):** Om din dator börjar använda swap-utrymme (virtuellt minne på hårddisken) när RAM-minnet tar slut, kommer prestandan att sjunka drastiskt. Du kan justera `swappiness` för att få Linux att använda RAM längre innan det börjar swappa.
    *   Kontrollera nuvarande swappiness: `cat /proc/sys/vm/swappiness` (standard är ofta 60).
    *   För att minska swappiness (t.ex. till 10, vilket är mer aggressivt med RAM-användning):
        ```bash
        sudo sysctl vm.swappiness=10
        # För att göra det permanent, lägg till/ändra i /etc/sysctl.conf:
        # vm.swappiness=10
        ```
    *   Detta är en avvägning; om du får slut på RAM helt kan systemet bli instabilt.
*   **Kontrollera Python-trådar:** Vissa bibliotek (som PyTorch) kan ha miljövariabler som styr antalet CPU-trådar de använder. För PyTorch kan du experimentera med `OMP_NUM_THREADS` eller `MKL_NUM_THREADS`. Att sätta det till antalet fysiska kärnor kan ibland hjälpa, men för många trådar kan också leda till overhead.
    ```bash
    export OMP_NUM_THREADS=$(nproc) # Sätter till antalet tillgängliga processorer/kärnor
    python main_online.py # Kör ditt skript
    ```
    Detta bör sättas *innan* du startar Python-skriptet.
*   **Real-time Kernel (Avancerat):** För extremt låg latens i ljudapplikationer kan en realtids-kernel (t.ex. `linux-lowlatency`) vara ett alternativ. Detta är dock en avancerad konfiguration och kan påverka systemets stabilitet för allmän användning.
    ```bash
    sudo apt install linux-lowlatency
    ```
    Starta om och välj den nya kärnan vid uppstart.

Genom att tillämpa dessa optimeringar kan du förbättra prestandan för Coqui TTS avsevärt i en Ubuntu-miljö utan dedikerad GPU.

## 8. Felsökning (Coqui TTS)

*   **"Model not found" eller nedladdningsfel:**
    *   Kontrollera att modellnamnet du specificerat i `CoquiEngine` är korrekt stavat.
    *   Se till att din internetanslutning fungerar vid första nedladdningen.
    *   Kontrollera Coqui TTS dokumentation för att se om modellen har flyttats eller bytt namn.
*   **Långsam röstgenerering:**
    *   Detta är vanligt på CPU. Överväg att installera CUDA och använda en GPU om du har en.
    *   Prova en mindre Coqui TTS-modell.
    *   Se till att din Python-miljö är optimerad (t.ex. att `torch` använder GPU om det är tillgängligt).
*   **Ljudfel eller ingen röst:**
    *   Kontrollera att FFmpeg är installerat och i din PATH.
    *   Se till att dina ljudenheter (högtalare) fungerar korrekt.
    *   Kontrollera Pythons konsol för felmeddelanden från `RealtimeTTS` eller Coqui TTS.
*   **Installation av `torch` problem:**
    *   Detta är den vanligaste källan till problem. Följ PyTorch:s officiella installationsguide noggrant för din specifika hårdvara och operativsystem. Om du inte har en GPU, installera `torch-cpu`.

Genom att följa denna guide bör du kunna installera och konfigurera Coqui TTS som din lokala röstmotor för ADA.
