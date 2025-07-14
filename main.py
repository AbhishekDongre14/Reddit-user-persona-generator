import json
import os
import re
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import praw
from dataclasses import dataclass, asdict
import ollama

# Configuration Constants
DEFAULT_USER_AGENT = "RedditPersonaGenerator/2.0 (by /u/PersonaBot)"
DEFAULT_POST_LIMIT = 100
SCRAPED_DATA_DIR = "scraped_data"
PERSONA_OUTPUT_DIR = "persona_output"
LOG_DIR = "logs"
MISTRAL_MODEL = "mistral"

@dataclass
class RedditPost:
    """Data class for Reddit posts and comments"""
    title: str
    content: str
    subreddit: str
    score: int
    created_utc: float
    url: str
    post_type: str  # 'post' or 'comment'
    parent_context: Optional[str] = None

@dataclass
class UserPersona:
    """Data class for user persona"""
    name: str
    age_range: str
    location: str
    occupation: str
    interests: List[str]
    personality_traits: List[str]
    communication_style: str
    goals_motivations: List[str]
    pain_points: List[str]
    technical_proficiency: str
    social_behavior: str
    content_preferences: List[str]
    activity_patterns: str
    citations: Dict[str, List[str]]

@dataclass
class ExecutionLog:
    """Data class for execution logging"""
    username: str
    execution_time: str
    duration: float
    posts_scraped: int
    comments_scraped: int
    total_content: int
    persona_generated: bool
    error_message: Optional[str] = None
    model_used: str = MISTRAL_MODEL

class DirectoryManager:
    """Manages directory structure and file operations"""
    
    @staticmethod
    def setup_directories():
        """Create necessary directories if they don't exist"""
        directories = [SCRAPED_DATA_DIR, PERSONA_OUTPUT_DIR, LOG_DIR]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"✓ Directory ready: {directory}/")
    
    @staticmethod
    def get_scraped_data_path(username: str) -> str:
        """Get path for scraped data file"""
        return os.path.join(SCRAPED_DATA_DIR, f"{username}_scraped_data.json")
    
    @staticmethod
    def get_persona_output_path(username: str) -> str:
        """Get path for persona output file"""
        return os.path.join(PERSONA_OUTPUT_DIR, f"{username}_persona.txt")
    
    @staticmethod
    def get_log_path() -> str:
        """Get path for log file"""
        return os.path.join(LOG_DIR, "execution_log.json")

class Logger:
    """Handles logging functionality"""
    
    def __init__(self):
        self.log_file = DirectoryManager.get_log_path()
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(LOG_DIR, 'app.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log_execution(self, log_entry: ExecutionLog):
        """Log execution details"""
        # Load existing logs
        logs = self.load_logs()
        
        # Add new log entry
        logs.append(asdict(log_entry))
        
        # Save updated logs
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
        
        # Log to console
        if log_entry.error_message:
            self.logger.error(f"Execution failed for {log_entry.username}: {log_entry.error_message}")
        else:
            self.logger.info(f"Successfully processed {log_entry.username} in {log_entry.duration:.2f}s")
    
    def load_logs(self) -> List[Dict]:
        """Load existing execution logs"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
        return []
    
    def get_execution_stats(self) -> Dict:
        """Get execution statistics"""
        logs = self.load_logs()
        if not logs:
            return {
                "total_executions": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0.0,
                "last_execution": "Never"
            }
        
        successful = len([log for log in logs if log.get('persona_generated', False)])
        failed = len(logs) - successful
        
        return {
            "total_executions": len(logs),
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / len(logs)) * 100 if logs else 0.0,
            "last_execution": logs[-1]['execution_time'] if logs else "Never"
        }

class RedditScraper:
    """Handles Reddit data scraping using PRAW"""
    
    def __init__(self, client_id: str, client_secret: str, user_agent: str = DEFAULT_USER_AGENT):
        """Initialize Reddit scraper"""
        self.logger = logging.getLogger(__name__)
        try:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            self.logger.info("Reddit API connection established")
        except Exception as e:
            self.logger.error(f"Failed to initialize Reddit API: {e}")
            raise
    
    def extract_username_from_url(self, url: str) -> str:
        """Extract username from Reddit profile URL"""
        patterns = [
            r'reddit\.com/user/([^/]+)',
            r'reddit\.com/u/([^/]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                username = match.group(1)
                self.logger.info(f"Extracted username: {username}")
                return username
        
        raise ValueError(f"Could not extract username from URL: {url}")
    
    def scrape_user_data(self, username: str, limit: int = DEFAULT_POST_LIMIT) -> Tuple[List[RedditPost], Dict]:
        """Scrape user's posts and comments"""
        posts = []
        stats = {"posts": 0, "comments": 0, "errors": 0}
        
        try:
            user = self.reddit.redditor(username)
            self.logger.info(f"Scraping data for user: {username}")
            
            # Scrape posts
            self.logger.info("Scraping user posts...")
            for submission in user.submissions.new(limit=limit):
                try:
                    post = RedditPost(
                        title=submission.title or "No title",
                        content=submission.selftext or "",
                        subreddit=str(submission.subreddit) if submission.subreddit else "Unknown",
                        score=submission.score or 0,
                        created_utc=submission.created_utc or 0,
                        url=f"https://reddit.com{submission.permalink}",
                        post_type="post"
                    )
                    posts.append(post)
                    stats["posts"] += 1
                except Exception as e:
                    stats["errors"] += 1
                    self.logger.warning(f"Error processing submission: {e}")
                    continue
            
            # Scrape comments
            self.logger.info("Scraping user comments...")
            for comment in user.comments.new(limit=limit):
                try:
                    parent_context = self._get_parent_context(comment)
                    
                    post = RedditPost(
                        title=f"Comment in r/{comment.subreddit}" if comment.subreddit else "Comment",
                        content=comment.body or "",
                        subreddit=str(comment.subreddit) if comment.subreddit else "Unknown",
                        score=comment.score or 0,
                        created_utc=comment.created_utc or 0,
                        url=f"https://reddit.com{comment.permalink}",
                        post_type="comment",
                        parent_context=parent_context
                    )
                    posts.append(post)
                    stats["comments"] += 1
                except Exception as e:
                    stats["errors"] += 1
                    self.logger.warning(f"Error processing comment: {e}")
                    continue
            
            self.logger.info(f"Scraped {stats['posts']} posts and {stats['comments']} comments")
            return posts, stats
            
        except Exception as e:
            self.logger.error(f"Error scraping user data: {e}")
            raise
    
    def _get_parent_context(self, comment) -> str:
        """Get parent context for a comment"""
        try:
            if hasattr(comment, 'parent') and comment.parent():
                parent = comment.parent()
                if hasattr(parent, 'body'):
                    context = parent.body[:200] + "..." if len(parent.body) > 200 else parent.body
                    return context
                elif hasattr(parent, 'title'):
                    return parent.title
        except:
            pass
        return ""

class PersonaGenerator:
    """Generates user personas using Mistral AI"""
    
    def __init__(self, model_name: str = MISTRAL_MODEL):
        """Initialize persona generator"""
        self.model_name = model_name
        self.logger = logging.getLogger(__name__)
        
        try:
            self.client = ollama.Client()
            self.logger.info(f"Ollama client initialized with model: {model_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Ollama client: {e}")
            raise
    
    def generate_persona(self, posts: List[RedditPost], username: str) -> UserPersona:
        """Generate user persona from scraped posts"""
        self.logger.info(f"Generating persona for {username} using {len(posts)} posts")
        
        # Prepare data for analysis
        posts_text = self._prepare_posts_for_analysis(posts)
        
        # Generate persona using Mistral
        persona_data = self._analyze_with_mistral(posts_text, username)
        
        # Extract citations
        citations = self._extract_citations(posts, persona_data)
        
        persona = UserPersona(
            name=persona_data.get("name", f"Reddit User: {username}"),
            age_range=persona_data.get("age_range", "Unknown"),
            location=persona_data.get("location", "Unknown"),
            occupation=persona_data.get("occupation", "Unknown"),
            interests=persona_data.get("interests", []),
            personality_traits=persona_data.get("personality_traits", []),
            communication_style=persona_data.get("communication_style", "Unknown"),
            goals_motivations=persona_data.get("goals_motivations", []),
            pain_points=persona_data.get("pain_points", []),
            technical_proficiency=persona_data.get("technical_proficiency", "Unknown"),
            social_behavior=persona_data.get("social_behavior", "Unknown"),
            content_preferences=persona_data.get("content_preferences", []),
            activity_patterns=persona_data.get("activity_patterns", "Unknown"),
            citations=citations
        )
        
        self.logger.info(f"Persona generated successfully for {username}")
        return persona
    
    def _prepare_posts_for_analysis(self, posts: List[RedditPost]) -> str:
        """Prepare posts data for AI analysis"""
        analysis_text = []
        
        for i, post in enumerate(posts[:50]):  # Limit to first 50 posts for analysis
            title = str(post.title) if post.title else "No title"
            content = str(post.content) if post.content else "No content"
            subreddit = str(post.subreddit) if post.subreddit else "Unknown"
            
            content_preview = content[:500] + "..." if len(content) > 500 else content
            
            post_info = f"""
Post {i+1}:
Type: {post.post_type}
Subreddit: r/{subreddit}
Title: {title}
Content: {content_preview}
Score: {post.score}
Date: {datetime.fromtimestamp(post.created_utc).strftime('%Y-%m-%d')}
URL: {post.url}
{"Parent Context: " + str(post.parent_context)[:200] + "..." if post.parent_context else ""}
---
"""
            analysis_text.append(post_info)
        
        return "\n".join(analysis_text)
    
    def _analyze_with_mistral(self, posts_text: str, username: str) -> Dict:
        """Analyze posts using Mistral AI"""
        
        prompt = f"""
Analyze the following Reddit user's posts and comments to create a detailed user persona. 
Username: {username}

Based on the content below, provide a JSON response with the following structure:
{{
    "name": "Persona name (e.g., 'Tech-Savvy Gamer' or 'Aspiring Developer')",
    "age_range": "Estimated age range (e.g., '25-35')",
    "location": "Estimated location/region if mentioned",
    "occupation": "Estimated profession/occupation",
    "interests": ["List of interests and hobbies"],
    "personality_traits": ["List of personality characteristics"],
    "communication_style": "Description of how they communicate",
    "goals_motivations": ["List of goals and motivations"],
    "pain_points": ["List of challenges and frustrations"],
    "technical_proficiency": "Level of technical skills",
    "social_behavior": "How they interact socially online",
    "content_preferences": ["Types of content they engage with"],
    "activity_patterns": "When and how often they post"
}}

Reddit Data:
{posts_text}

Please analyze the content carefully and provide insights based on:
1. Language patterns and vocabulary used
2. Topics and subreddits they engage with
3. Timing and frequency of posts
4. Interaction style with other users
5. Interests and expertise areas
6. Geographic or cultural references
7. Professional or academic mentions
8. Personal challenges or goals mentioned

IMPORTANT: Respond with ONLY valid JSON. No additional text, explanations, or markdown formatting.
"""
        
        try:
            self.logger.info("Sending data to Mistral for analysis...")
            response = self.client.chat(model=self.model_name, messages=[
                {"role": "user", "content": prompt}
            ])
            
            response_text = response['message']['content'].strip()
            self.logger.info(f"Raw Mistral response: {response_text[:200]}...")
            
            # Clean up response text
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            # Extract JSON from response using multiple methods
            json_str = None
            
            # Method 1: Try to find JSON block
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            
            # Method 2: If no match, assume entire response is JSON
            if not json_str:
                json_str = response_text
            
            # Method 3: Try to fix common JSON issues
            if json_str:
                # Fix common issues with quotes and escaping
                json_str = re.sub(r'(?<!\\)"(?=\s*[a-zA-Z_][a-zA-Z0-9_]*\s*:)', '"', json_str)
                json_str = re.sub(r'(?<=:)\s*"([^"]*)"(?=\s*[,}])', r'"\1"', json_str)
            
            if json_str:
                try:
                    result = json.loads(json_str)
                    self.logger.info("Successfully parsed Mistral response")
                    return result
                except json.JSONDecodeError as je:
                    self.logger.error(f"JSON decode error: {je}")
                    self.logger.error(f"Problematic JSON: {json_str[:500]}...")
                    return self._get_default_persona(username)
            else:
                self.logger.warning("Could not extract JSON from Mistral response")
                return self._get_default_persona(username)
                
        except Exception as e:
            self.logger.error(f"Error analyzing with Mistral: {e}")
            return self._get_default_persona(username)
    
    def _get_default_persona(self, username: str) -> Dict:
        """Return default persona structure if AI analysis fails"""
        return {
            "name": f"Reddit User: {username}",
            "age_range": "Unknown",
            "location": "Unknown",
            "occupation": "Unknown",
            "interests": [],
            "personality_traits": [],
            "communication_style": "Unknown",
            "goals_motivations": [],
            "pain_points": [],
            "technical_proficiency": "Unknown",
            "social_behavior": "Unknown",
            "content_preferences": [],
            "activity_patterns": "Unknown"
        }
    
    def _extract_citations(self, posts: List[RedditPost], persona_data: Dict) -> Dict[str, List[str]]:
        """Extract citations linking persona traits to specific posts"""
        citations = {}
        
        for field, value in persona_data.items():
            citations[field] = []
            
            if isinstance(value, list):
                for item in value:
                    if item:
                        relevant_posts = self._find_relevant_posts(posts, item)
                        citations[field].extend(relevant_posts[:2])
            elif value and str(value).strip() and str(value) != "Unknown":
                relevant_posts = self._find_relevant_posts(posts, value)
                citations[field] = relevant_posts[:3]
            
            # Remove duplicates while preserving order
            citations[field] = list(dict.fromkeys(citations[field]))
        
        return citations
    
    def _find_relevant_posts(self, posts: List[RedditPost], keyword) -> List[str]:
        """Find posts relevant to a specific keyword or trait"""
        relevant = []
        
        if not isinstance(keyword, str):
            keyword = str(keyword)
        
        keyword_lower = keyword.lower()
        
        for post in posts:
            title = str(post.title) if post.title else ""
            content = str(post.content) if post.content else ""
            
            content_to_search = f"{title} {content}".lower()
            if keyword_lower in content_to_search or any(word in content_to_search for word in keyword_lower.split()):
                relevant.append(post.url)
        
        return relevant

class PersonaFormatter:
    """Formats persona data for output"""
    
    @staticmethod
    def format_persona_to_text(persona: UserPersona, username: str, generation_time: str) -> str:
        """Format persona data to readable text"""
        
        text = f"""
# USER PERSONA: {persona.name}
Generated for: u/{username}
Generated on: {generation_time}

## DEMOGRAPHIC INFORMATION
- **Age Range:** {persona.age_range}
- **Location:** {persona.location}
- **Occupation:** {persona.occupation}

## INTERESTS & HOBBIES
{PersonaFormatter._format_list(persona.interests)}

## PERSONALITY TRAITS
{PersonaFormatter._format_list(persona.personality_traits)}

## COMMUNICATION STYLE
{persona.communication_style}

## GOALS & MOTIVATIONS
{PersonaFormatter._format_list(persona.goals_motivations)}

## PAIN POINTS & CHALLENGES
{PersonaFormatter._format_list(persona.pain_points)}

## TECHNICAL PROFICIENCY
{persona.technical_proficiency}

## SOCIAL BEHAVIOR
{persona.social_behavior}

## CONTENT PREFERENCES
{PersonaFormatter._format_list(persona.content_preferences)}

## ACTIVITY PATTERNS
{persona.activity_patterns}

## CITATIONS
{PersonaFormatter._format_citations(persona.citations)}

---
Generated by Reddit Persona Generator v2.0
"""
        return text
    
    @staticmethod
    def _format_list(items: List[str]) -> str:
        """Format list items with bullet points"""
        if not items:
            return "- Not specified"
        return "\n".join(f"- {item}" for item in items)
    
    @staticmethod
    def _format_citations(citations: Dict[str, List[str]]) -> str:
        """Format citations with links"""
        if not citations:
            return "No citations available"
        
        citation_text = []
        for field, urls in citations.items():
            if urls:
                citation_text.append(f"**{field.replace('_', ' ').title()}:**")
                for url in urls:
                    citation_text.append(f"  - {url}")
                citation_text.append("")
        
        return "\n".join(citation_text)

class PersonaGeneratorApp:
    """Main application class"""
    
    def __init__(self):
        """Initialize the application"""
        self.logger_manager = Logger()
        self.logger = logging.getLogger(__name__)
        
        # Setup directories
        DirectoryManager.setup_directories()
        
        print("🚀 Reddit User Persona Generator v2.0")
        print("=" * 50)
    
    def run(self):
        """Main application runner"""
        try:
            # Get user inputs
            config = self._get_user_configuration()
            
            # Initialize components
            scraper = RedditScraper(
                client_id=config['client_id'],
                client_secret=config['client_secret']
            )
            persona_generator = PersonaGenerator(config['model_name'])
            
            # Extract username
            username = scraper.extract_username_from_url(config['reddit_url'])
            
            # Start execution timing
            start_time = time.time()
            execution_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Create execution log entry
            log_entry = ExecutionLog(
                username=username,
                execution_time=execution_time,
                duration=0,
                posts_scraped=0,
                comments_scraped=0,
                total_content=0,
                persona_generated=False,
                model_used=config['model_name']
            )
            
            try:
                # Scrape user data
                posts, scraping_stats = scraper.scrape_user_data(username, config['post_limit'])
                
                if not posts:
                    raise ValueError("No posts found or error occurred during scraping")
                
                # Update log entry
                log_entry.posts_scraped = scraping_stats['posts']
                log_entry.comments_scraped = scraping_stats['comments']
                log_entry.total_content = len(posts)
                
                # Save scraped data
                self._save_scraped_data(posts, username)
                
                # Generate persona
                persona = persona_generator.generate_persona(posts, username)
                
                # Save persona
                self._save_persona(persona, username, execution_time)
                
                # Update log entry
                log_entry.persona_generated = True
                log_entry.duration = time.time() - start_time
                
                # Log successful execution
                self._log_successful_execution(log_entry, username)
                
            except Exception as e:
                # Log failed execution
                log_entry.duration = time.time() - start_time
                log_entry.error_message = str(e)
                self.logger_manager.log_execution(log_entry)
                raise
            
            # Log execution
            self.logger_manager.log_execution(log_entry)
            
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            print(f"\n❌ Error: {e}")
            print("\nPlease check:")
            print("1. Valid Reddit API credentials")
            print("2. Ollama running with Mistral model installed")
            print("3. Internet connection")
    
    def _get_user_configuration(self) -> Dict:
        """Get configuration from user input"""
        print("\n📋 Configuration")
        print("-" * 20)
        
        reddit_url = input("Enter Reddit user profile URL: ").strip()
        
        print("\n🔑 Reddit API Configuration:")
        client_id = input("Enter Reddit Client ID: ").strip()
        client_secret = input("Enter Reddit Client Secret: ").strip()
        
        return {
            'reddit_url': reddit_url,
            'client_id': client_id,
            'client_secret': client_secret,
            'model_name': MISTRAL_MODEL,
            'post_limit': DEFAULT_POST_LIMIT
        }
    
    def _save_scraped_data(self, posts: List[RedditPost], username: str):
        """Save scraped data to file"""
        file_path = DirectoryManager.get_scraped_data_path(username)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([asdict(post) for post in posts], f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Scraped data saved: {file_path}")
        print(f"📁 Scraped data saved: {file_path}")
    
    def _save_persona(self, persona: UserPersona, username: str, generation_time: str):
        """Save persona to file"""
        file_path = DirectoryManager.get_persona_output_path(username)
        
        formatter = PersonaFormatter()
        persona_text = formatter.format_persona_to_text(persona, username, generation_time)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(persona_text)
        
        self.logger.info(f"Persona saved: {file_path}")
        print(f"📄 Persona saved: {file_path}")
    
    def _log_successful_execution(self, log_entry: ExecutionLog, username: str):
        """Log successful execution details"""
    
        # Log the execution first so it's included in statistics
        self.logger_manager.log_execution(log_entry)
        
        print(f"\n✅ Persona generation completed successfully!")
        print(f"📊 Execution Summary:")
        print(f"   • Username: {username}")
        print(f"   • Duration: {log_entry.duration:.2f} seconds")
        print(f"   • Posts scraped: {log_entry.posts_scraped}")
        print(f"   • Comments scraped: {log_entry.comments_scraped}")
        print(f"   • Total content analyzed: {log_entry.total_content}")
        print(f"   • Model used: {log_entry.model_used}")
        
        # Show execution statistics (now includes current execution)
        try:
            stats = self.logger_manager.get_execution_stats()
            print(f"\n📈 Overall Statistics:")
            print(f"   • Total executions: {stats.get('total_executions', 0)}")
            print(f"   • Success rate: {stats.get('success_rate', 0.0):.1f}%")
        except Exception as e:
            self.logger.error(f"Error getting execution stats: {e}")
            print(f"\n📈 Overall Statistics: Unable to retrieve statistics")

def main():
    """Main entry point"""
    app = PersonaGeneratorApp()
    app.run()

if __name__ == "__main__":
    main()