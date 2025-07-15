# Reddit User Persona Generator

A powerful Python application that analyzes Reddit user profiles and generates detailed user personas using AI. This tool scrapes a user's posts and comments, then uses Mistral AI (via Ollama) to create comprehensive personality profiles with insights into demographics, interests, communication patterns, and behavioral traits.

## 🚀 Features

- **Comprehensive User Analysis**: Scrapes posts and comments from Reddit user profiles
- **AI-Powered Persona Generation**: Uses Mistral AI model for intelligent analysis
- **Detailed Persona Profiles**: Generates insights on demographics, interests, personality traits, and more
- **Citation System**: Links persona traits to specific Reddit posts for verification
- **Execution Logging**: Tracks all runs with detailed statistics and error handling
- **Organized Output**: Saves scraped data and personas in structured directories
- **Robust Error Handling**: Graceful handling of API limits and network issues

## 📋 Requirements

- Python 3.8+
- Reddit API credentials (Client ID and Secret)
- Ollama with Mistral model installed
- Internet connection

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/Reddit-user-persona-generator.git
cd Reddit-user-persona-generator
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install and Setup Ollama
1. Install Ollama from [https://ollama.ai](https://ollama.ai)
2. Pull the Mistral model:
```bash
ollama pull mistral
```
3. Verify installation:
```bash
ollama list
```

### 5. Get Reddit API Credentials
1. Go to [Reddit App Preferences](https://www.reddit.com/prefs/apps)
2. Click "Create App" or "Create Another App"
3. Fill in the form:
   - **Name**: Your app name
   - **App type**: Select "script"
   - **Description**: Optional
   - **About URL**: Optional
   - **Redirect URI**: `http://localhost:8080`
4. Note down your **Client ID** (under the app name) and **Client Secret**

## 🚀 Usage

### Basic Usage
```bash
python main.py
```

The application will prompt you for:
- Reddit user profile URL (e.g., `https://www.reddit.com/user/username`)
- Reddit Client ID
- Reddit Client Secret

### Example Session
```
🚀 Reddit User Persona Generator v2.0
==================================================

📋 Configuration
--------------------
Enter Reddit user profile URL: https://www.reddit.com/user/example_user

🔑 Reddit API Configuration:
Enter Reddit Client ID: your_client_id
Enter Reddit Client Secret: your_client_secret
```

## 📁 Project Structure

```
Reddit-user-persona-generator/
├── main.py                       # Main application
├── requirements.txt               # Python dependencies
├── README.md                     # This file
├── scraped_data/                 # Scraped Reddit data (JSON)
├── persona_output/               # Generated persona files (TXT)
└── logs/                        # Execution logs and app logs
    ├── execution_log.json       # Detailed execution history
    └── app.log                  # Application logs
```

## 📊 Output

### Scraped Data
- **Location**: `scraped_data/{username}_scraped_data.json`
- **Content**: Raw Reddit posts and comments with metadata

### Persona Report
- **Location**: `persona_output/{username}_persona.txt`
- **Content**: Comprehensive persona analysis including:
  - Demographic information
  - Interests and hobbies
  - Personality traits
  - Communication style
  - Goals and motivations
  - Pain points and challenges
  - Technical proficiency
  - Social behavior patterns
  - Content preferences
  - Activity patterns
  - Citations linking to source posts

### Example Persona Output
```
# USER PERSONA: Tech-Savvy Developer
Generated for: u/example_user
Generated on: 2024-01-15 14:30:22

## DEMOGRAPHIC INFORMATION
- **Age Range:** 25-35
- **Location:** San Francisco Bay Area
- **Occupation:** Software Developer

## INTERESTS & HOBBIES
- Machine Learning and AI
- Open Source Programming
- Gaming (RPGs and Strategy)
- Cryptocurrency and Blockchain

## PERSONALITY TRAITS
- Analytical and logical thinker
- Detail-oriented problem solver
- Collaborative team player
- Continuous learner
```

## 🔧 Configuration

### Constants (in `main.py`)
- `DEFAULT_POST_LIMIT`: Number of posts/comments to scrape (default: 100)
- `MISTRAL_MODEL`: AI model to use (default: "mistral")
- `DEFAULT_USER_AGENT`: Reddit API user agent string

### Directory Structure
- `SCRAPED_DATA_DIR`: Directory for scraped data files
- `PERSONA_OUTPUT_DIR`: Directory for persona output files
- `LOG_DIR`: Directory for log files

## 📈 Logging and Statistics

The application tracks:
- Total executions
- Success/failure rates
- Execution duration
- Number of posts/comments scraped
- Error messages and debugging info

View execution statistics in the console output or check `logs/execution_log.json` for detailed history.

## 🛡️ Privacy and Ethics

- **Data Usage**: This tool is for educational and research purposes
- **Respect Privacy**: Only analyze public Reddit profiles
- **Rate Limiting**: Built-in delays to respect Reddit's API limits
- **Data Storage**: All data is stored locally on your machine
- **No Data Sharing**: No data is sent to external services except for AI analysis

## 🔍 Troubleshooting

### Common Issues

**1. "Reddit API Error"**
- Verify your Client ID and Secret
- Check that your Reddit app is configured as a "script" type
- Ensure your Reddit account has API access

**2. "Ollama Connection Error"**
- Make sure Ollama is running: `ollama serve`
- Verify Mistral model is installed: `ollama list`
- Check if Ollama is accessible at default port

**3. "No Posts Found"**
- User profile might be private or deleted
- User might have very few posts
- Check if the username is correct

**4. "JSON Parse Error"**
- Mistral model might be returning malformed JSON
- Check Ollama logs for detailed error messages
- Try restarting Ollama service

### Debug Mode
For detailed debugging, check the log files:
```bash
# View application logs
tail -f logs/app.log

# View execution history
cat logs/execution_log.json
```

## 📝 Dependencies

Key dependencies include:
- `praw`: Reddit API wrapper
- `ollama`: AI model interface
- `beautifulsoup4`: HTML parsing
- `requests`: HTTP requests
- `dataclasses`: Data structure management

See `requirements.txt` for complete dependency list.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📜 License

This project is licensed under the MIT License. See the LICENSE file for details.

## ⚠️ Disclaimer

This tool is provided for educational and research purposes. Users are responsible for:
- Complying with Reddit's Terms of Service
- Respecting user privacy and data protection laws
- Using the tool ethically and responsibly
- Not using generated personas for harassment or malicious purposes

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the log files for detailed error messages
3. Ensure all dependencies are properly installed
4. Verify your Reddit API credentials are correct

For additional support, please create an issue in the repository with:
- Error messages from logs
- Steps to reproduce the issue
- Your environment details (OS, Python version, etc.)
 
