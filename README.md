# FutureFund

FutureFund is an AI-powered financial decision simulator.

## AI Configuration
The backend supports multiple AI providers for its natural language parsing and decision generation workflows.

### Setting the AI Provider
In the backend's `.env` file (`backend/backend/.env`), set the `AI_PROVIDER` variable to one of the following: `gemini`, `ollama`, or `groq`.

### Groq Integration
To use Groq as the AI provider:
1. Ensure the `groq` Python package is installed (`pip install groq`).
2. Set the following environment variables in `.env`:
   ```
   AI_PROVIDER=groq
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_MODEL=openai/gpt-oss-20b  # Or your desired model, e.g. llama-3.1-8b-instant
   ```
3. The system will now route "parse decision" and "second opinion" workflows to Groq automatically.