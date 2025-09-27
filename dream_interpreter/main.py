from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from datetime import datetime
from .models import DreamInput, DreamRecord, SymbolResponse
from .analyser import Dreamanalyser
from .symbol_generator import SymbolGenerator
from .database import DreamDatabase

app = FastAPI(
    title="Dream Interpreter API",
    description="AI-powered dream interpretation with symbolic visualization",
    version="0.1.0"
)

# Initialize components
analyser = Dreamanalyser()
symbol_generator = SymbolGenerator()
database = DreamDatabase()


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve a simple web interface."""
    html_content = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dream Interpreter</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; margin-bottom: 30px; }
            textarea { width: 100%; height: 120px; margin: 10px 0; padding: 10px; border: 2px solid #ddd; border-radius: 5px; }
            button { background: #667eea; color: white; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; font-size: 16px; }
            button:hover { background: #5a67d8; }
            .result { margin-top: 20px; padding: 20px; background: #f8f9fa; border-radius: 5px; }
            .symbol img { max-width: 300px; border: 2px solid #ddd; border-radius: 10px; }
            .coordinates { font-family: monospace; background: #e2e8f0; padding: 10px; border-radius: 5px; }
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
            <br>
            <input type="text" id="userId" placeholder="Your name (optional)" style="width: 200px; padding: 10px; margin-right: 10px; border: 2px solid #ddd; border-radius: 5px;">
            <button onclick="analyzeDream()">Analyze Dream</button>
            
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
        async function analyzeDream() {
            const dreamText = document.getElementById('dreamText').value;
            const userId = document.getElementById('userId').value || 'anonymous';
            
            if (!dreamText.trim()) {
                alert('Please enter your dream first!');
                return;
            }

            try {
                const response = await fetch('/analyze-dream', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({dream_text: dreamText, user_id: userId})
                });
                
                const data = await response.json();
                
                document.getElementById('analysis').innerHTML = `
                    <div class="coordinates">
                        <strong>Coordinates:</strong> (${data.analysis.static_dynamic_score.toFixed(2)}, ${data.analysis.upper_downer_score.toFixed(2)})
                    </div>
                    <p><strong>Emotional Tone:</strong> ${data.analysis.upper_downer_score > 0 ? 'Upper' : 'Downer'} (${data.analysis.upper_downer_score.toFixed(2)})</p>
                    <p><strong>Energy Level:</strong> ${data.analysis.static_dynamic_score > 0 ? 'Dynamic' : 'Static'} (${data.analysis.static_dynamic_score.toFixed(2)})</p>
                    <p><strong>Confidence:</strong> ${(data.analysis.confidence * 100).toFixed(1)}%</p>
                    <p><strong>Keywords:</strong> ${data.analysis.keywords.join(', ') || 'None identified'}</p>
                `;
                
                const symbolResponse = await fetch(`/generate-symbol/${userId}`);
                const symbolData = await symbolResponse.json();
                
                document.getElementById('symbolContainer').innerHTML = `
                    <h4>Your Personal Dream Symbol</h4>
                    <img src="data:image/png;base64,${symbolData.symbol_base64}" alt="Dream Symbol">
                    <p><em>This symbol evolves as you add more dreams (${symbolData.dream_count} dreams analyzed)</em></p>
                `;
                
                document.getElementById('result').style.display = 'block';
                
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
    '''
    return html_content


@app.post("/analyze-dream")
async def analyze_dream(dream_input: DreamInput):
    """Analyze a dream and store the results."""
    try:
        # Analyze the dream
        analysis = analyser.analyze_dream(dream_input.dream_text)
        
        # Create and store dream record
        dream_record = DreamRecord(
            id="",  # Will be set by database
            dream_text=dream_input.dream_text,
            user_id=dream_input.user_id,
            analysis=analysis,
            timestamp=datetime.now()
        )
        
        dream_id = database.store_dream(dream_record)
        dream_record.id = dream_id
        
        return dream_record
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing dream: {str(e)}")


@app.get("/generate-symbol/{user_id}")
async def generate_symbol(user_id: str) -> SymbolResponse:
    """Generate a symbol based on all user dreams."""
    try:
        user_dreams = database.get_user_dreams(user_id)
        symbol_base64 = symbol_generator.generate_symbol(user_dreams)
        
        # Get average coordinates for the latest position
        if user_dreams:
            latest_dream = user_dreams[-1]
            coordinates = (
                latest_dream.analysis.static_dynamic_score,
                latest_dream.analysis.upper_downer_score
            )
        else:
            coordinates = (0.0, 0.0)
        
        return SymbolResponse(
            symbol_base64=symbol_base64,
            dream_count=len(user_dreams),
            coordinates=coordinates
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating symbol: {str(e)}")


@app.get("/user-stats/{user_id}")
async def get_user_stats(user_id: str):
    """Get statistics for a user's dreams."""
    try:
        stats = database.get_user_stats(user_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user stats: {str(e)}")


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