import inspect
import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from .analyser import Dreamanalyser, LLMDreamanalyser
from .database import DreamDatabase
from .models import DreamInput, DreamRecord, SymbolResponse
from .symbol_generator import AISymbolGenerator, SymbolGenerator

app = FastAPI(
    title="Dream Interpreter API",
    description="AI-powered dream interpretation with symbolic visualization",
    version="0.1.0",
)

# Both variants are kept ready at startup.
# AI instances are set to None when the required API key is absent.
_legacy_analyser = Dreamanalyser()
_llm_analyser = LLMDreamanalyser() if os.getenv("ANTHROPIC_API_KEY") else None
_legacy_symbols = SymbolGenerator()
_ai_symbols = AISymbolGenerator() if os.getenv("OPENAI_API_KEY") else None
database = DreamDatabase()


def _select_analyser(mode: str):
    """Return the appropriate analyser for the requested mode."""
    if mode == "legacy" or _llm_analyser is None:
        return _legacy_analyser
    return _llm_analyser


def _select_symbol_generator(mode: str):
    """Return the appropriate symbol generator for the requested mode."""
    if mode == "legacy" or _ai_symbols is None:
        return _legacy_symbols
    return _ai_symbols


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve a simple web interface."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dream Interpreter</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; margin-bottom: 30px; }
            textarea { width: 100%; height: 120px; margin: 10px 0; padding: 10px; border: 2px solid #ddd; border-radius: 5px; box-sizing: border-box; }
            button { background: #667eea; color: white; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; font-size: 16px; }
            button:hover { background: #5a67d8; }
            .result { margin-top: 20px; padding: 20px; background: #f8f9fa; border-radius: 5px; }
            .symbol img { max-width: 300px; border: 2px solid #ddd; border-radius: 10px; }
            .coordinates { font-family: monospace; background: #e2e8f0; padding: 10px; border-radius: 5px; }
            .controls { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-top: 10px; }
            .mode-toggle { display: flex; align-items: center; gap: 10px; padding: 10px 14px; background: #f0f4ff; border-radius: 8px; border: 1px solid #e0e7ff; }
            .switch { position: relative; display: inline-block; width: 52px; height: 26px; flex-shrink: 0; }
            .switch input { opacity: 0; width: 0; height: 0; }
            .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background: #cbd5e0; transition: .3s; border-radius: 26px; }
            .slider:before { position: absolute; content: ""; height: 20px; width: 20px; left: 3px; bottom: 3px; background: white; transition: .3s; border-radius: 50%; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }
            input:checked + .slider { background: #667eea; }
            input:checked + .slider:before { transform: translateX(26px); }
            .mode-label { font-weight: 600; font-size: 14px; color: #4a5568; transition: color .2s; }
            .mode-desc { color: #888; font-size: 12px; }
            .badge { font-size: 11px; padding: 2px 8px; border-radius: 10px; font-weight: 600; vertical-align: middle; margin-left: 4px; }
            .badge-ai { background: #667eea; color: white; }
            .badge-classic { background: #a0aec0; color: white; }
            .loading { color: #667eea; font-style: italic; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌙 Dream Interpreter</h1>
            <p>Describe your dream and discover its symbolic meaning. Your dreams will be analyzed on two dimensions:</p>
            <ul>
                <li><strong>Upper/Downer</strong>: Emotional valence of your dream</li>
                <li><strong>Static/Dynamic</strong>: Energy level and activity in your dream</li>
            </ul>

            <textarea id="dreamText" placeholder="Enter your dream here... (e.g., 'I was flying over a beautiful landscape, feeling free and joyful...')"></textarea>

            <div class="controls">
                <input type="text" id="userId" placeholder="Your name (optional)" style="width: 200px; padding: 10px; border: 2px solid #ddd; border-radius: 5px;">
                <div class="mode-toggle">
                    <span class="mode-label" id="classicLabel" style="color:#667eea;">Classic</span>
                    <label class="switch">
                        <input type="checkbox" id="aiMode" onchange="updateModeLabel()">
                        <span class="slider"></span>
                    </label>
                    <span class="mode-label" id="aiLabel">AI</span>
                    <span class="mode-desc" id="modeDesc">TextBlob + matplotlib</span>
                </div>
                <button onclick="analyzeDream()">Analyze Dream</button>
            </div>

            <div id="result" class="result" style="display:none;">
                <h3>Dream Analysis</h3>
                <div id="analysis"></div>
                <div id="symbolContainer" class="symbol"></div>
                <button onclick="getUserStats()" style="margin-top: 10px;">View My Dream Statistics</button>
            </div>

            <div id="stats" style="display:none; margin-top: 20px; padding: 20px; background: #e8f4fd; border-radius: 5px;">
                <h3>Your Dream Statistics</h3>
                <div id="statsContent"></div>
            </div>
        </div>

        <script>
        function updateModeLabel() {
            const ai = document.getElementById('aiMode').checked;
            document.getElementById('modeDesc').textContent = ai ? 'Claude + DALL\u00b7E 3' : 'TextBlob + matplotlib';
            document.getElementById('aiLabel').style.color    = ai ? '#667eea' : '#4a5568';
            document.getElementById('classicLabel').style.color = ai ? '#4a5568' : '#667eea';
        }

        async function analyzeDream() {
            const dreamText = document.getElementById('dreamText').value;
            const userId    = document.getElementById('userId').value || 'anonymous';
            const aiMode    = document.getElementById('aiMode').checked;
            const mode      = aiMode ? 'ai' : 'legacy';

            if (!dreamText.trim()) { alert('Please enter your dream first!'); return; }

            try {
                const response = await fetch('/analyze-dream', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({dream_text: dreamText, user_id: userId, mode: mode})
                });
                const data = await response.json();

                const analyserBadge = aiMode
                    ? '<span class="badge badge-ai">Claude</span>'
                    : '<span class="badge badge-classic">Classic</span>';

                document.getElementById('analysis').innerHTML = `
                    <div class="coordinates">
                        <strong>Coordinates:</strong> (${data.analysis.static_dynamic_score.toFixed(2)}, ${data.analysis.upper_downer_score.toFixed(2)})
                    </div>
                    <p><strong>Emotional Tone:</strong> ${data.analysis.upper_downer_score > 0 ? 'Upper' : 'Downer'} (${data.analysis.upper_downer_score.toFixed(2)})</p>
                    <p><strong>Energy Level:</strong> ${data.analysis.static_dynamic_score > 0 ? 'Dynamic' : 'Static'} (${data.analysis.static_dynamic_score.toFixed(2)})</p>
                    <p><strong>Confidence:</strong> ${(data.analysis.confidence * 100).toFixed(1)}%</p>
                    <p><strong>Keywords</strong> ${analyserBadge}: ${data.analysis.keywords.join(', ') || 'None identified'}</p>
                `;

                const symbolContainer = document.getElementById('symbolContainer');
                symbolContainer.innerHTML = aiMode
                    ? '<p class="loading">\u2728 Generating symbol with DALL\u00b7E\u00a03, this may take ~20 seconds\u2026</p>'
                    : '<p class="loading">Generating symbol\u2026</p>';
                document.getElementById('result').style.display = 'block';

                const symbolResponse = await fetch(`/generate-symbol/${userId}?mode=${mode}`);
                const symbolData = await symbolResponse.json();

                const symbolBadge = aiMode
                    ? '<span class="badge badge-ai">DALL\u00b7E\u00a03</span>'
                    : '<span class="badge badge-classic">Classic</span>';

                symbolContainer.innerHTML = `
                    <h4>Your Personal Dream Symbol ${symbolBadge}</h4>
                    <img src="data:image/png;base64,${symbolData.symbol_base64}" alt="Dream Symbol">
                    <p><em>This symbol evolves as you add more dreams (${symbolData.dream_count} dreams analyzed)</em></p>
                `;

            } catch (error) {
                alert('Error analyzing dream: ' + error.message);
            }
        }

        async function getUserStats() {
            const userId = document.getElementById('userId').value || 'anonymous';
            try {
                const response = await fetch(`/user-stats/${userId}`);
                const stats = await response.json();
                document.getElementById('statsContent').innerHTML = `
                    <p><strong>Total Dreams:</strong> ${stats.total_dreams}</p>
                    <p><strong>Average Emotional Score:</strong> ${stats.average_emotional_score}</p>
                    <p><strong>Average Dynamic Score:</strong> ${stats.average_dynamic_score}</p>
                    <p><strong>Average Confidence:</strong> ${(stats.average_confidence * 100).toFixed(1)}%</p>
                    <p><strong>Dominant Pattern:</strong> ${stats.dominant_quadrant}</p>
                `;
                document.getElementById('stats').style.display = 'block';
            } catch (error) {
                alert('Error fetching stats: ' + error.message);
            }
        }
        </script>
    </body>
    </html>
    """
    return html_content


@app.post("/analyze-dream")
async def analyze_dream(dream_input: DreamInput):
    """Analyze a dream and store the results."""
    try:
        selected = _select_analyser(dream_input.mode)
        if inspect.iscoroutinefunction(selected.analyze_dream):
            analysis = await selected.analyze_dream(dream_input.dream_text)
        else:
            analysis = selected.analyze_dream(dream_input.dream_text)

        dream_record = DreamRecord(
            id="",
            dream_text=dream_input.dream_text,
            user_id=dream_input.user_id,
            analysis=analysis,
            timestamp=datetime.now(),
        )

        dream_id = database.store_dream(dream_record)
        dream_record.id = dream_id

        return dream_record

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing dream: {str(e)}")


@app.get("/generate-symbol/{user_id}")
async def generate_symbol(user_id: str, mode: str = "auto") -> SymbolResponse:
    """Generate a symbol based on all user dreams."""
    try:
        user_dreams = database.get_user_dreams(user_id)
        selected = _select_symbol_generator(mode)
        if inspect.iscoroutinefunction(selected.generate_symbol):
            symbol_base64 = await selected.generate_symbol(user_dreams)
        else:
            symbol_base64 = selected.generate_symbol(user_dreams)

        if user_dreams:
            latest_dream = user_dreams[-1]
            coordinates = (
                latest_dream.analysis.static_dynamic_score,
                latest_dream.analysis.upper_downer_score,
            )
        else:
            coordinates = (0.0, 0.0)

        return SymbolResponse(
            symbol_base64=symbol_base64,
            dream_count=len(user_dreams),
            coordinates=coordinates,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating symbol: {str(e)}"
        )


@app.get("/user-stats/{user_id}")
async def get_user_stats(user_id: str):
    """Get statistics for a user's dreams."""
    try:
        stats = database.get_user_stats(user_id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching user stats: {str(e)}"
        )


@app.get("/dream/{dream_id}")
async def get_dream(dream_id: str):
    """Get a specific dream by ID."""
    dream = database.get_dream(dream_id)
    if not dream:
        raise HTTPException(status_code=404, detail="Dream not found")
    return dream


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
