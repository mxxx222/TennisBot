# 📖 Comprehensive User Guide
## Betfury.io Educational Research System

---

## 🎯 Table of Contents

1. [System Overview](#system-overview)
2. [Installation Guide](#installation-guide)
3. [Configuration](#configuration)
4. [Usage Examples](#usage-examples)
5. [Educational Components](#educational-components)
6. [API Reference](#api-reference)
7. [Troubleshooting](#troubleshooting)
8. [Contributing](#contributing)

---

## 🎯 System Overview

This educational research system demonstrates advanced web scraping, machine learning, and real-time data processing techniques using sports betting data as a learning example.

### ⚠️ **CRITICAL DISCLAIMER**
**FOR EDUCATIONAL PURPOSES ONLY - DO NOT USE FOR ACTUAL BETTING**

This system is designed exclusively for:
- Academic research and education
- Learning web scraping techniques
- Understanding machine learning workflows
- Studying real-time data processing
- Ethical data analysis practices

### 🚫 **NOT INTENDED FOR**
- Actual gambling or betting
- Financial decision making
- Commercial sports prediction services
- Circumventing website terms of service
- Any form of real-money gambling

---

## 📦 Installation Guide

### Prerequisites

- Python 3.11+
- Chrome/Chromium browser
- Docker (optional)
- Git

### Quick Setup

```bash
# 1. Clone or download the system
git clone <repository-url>
cd betfury-educational-system

# 2. Run setup script
python setup.py --setup

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure system
cp config/config_template.yaml config/config.yaml
# Edit config.yaml as needed

# 5. Test installation
python main.py --mode analyze --duration 5 --debug
```

### Docker Installation (Alternative)

```bash
# 1. Build container
docker build -t betfury-research .

# 2. Run with docker-compose
docker-compose up -d

# 3. Check logs
docker-compose logs -f
```

---

## ⚙️ Configuration

### Basic Configuration (`config/config.yaml`)

```yaml
# Rate Limiting (CRITICAL for ethical scraping)
rate_limit:
  min_delay_seconds: 5.0
  max_delay_seconds: 10.0
  randomization: true
  max_requests_per_hour: 720

# Educational Research Settings
research:
  study_name: "Educational Sports Analytics Study"
  educational_only: true
  comply_with_gdpr: true
  respect_website_terms: true

# Telegram Bot (Optional)
telegram:
  enabled: false
  bot_token: "YOUR_BOT_TOKEN"
  chat_id: "YOUR_CHAT_ID"
  notifications:
    high_confidence_predictions: true
    system_status: true
```

### Environment Variables (`.env`)

```bash
# Required for basic operation
RESEARCH_MODE=true
EDUCATIONAL_ONLY=true

# Optional features
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
API_FOOTBALL_KEY=your_api_key
```

---

## 🚀 Usage Examples

### 1. Basic Analysis (Educational Demo)

```bash
# Run 5-minute analysis
python main.py --mode analyze --duration 5

# Run 30-minute research session
python main.py --mode research --duration 30

# Run with debug logging
python main.py --mode analyze --duration 10 --debug
```

### 2. Continuous Monitoring (24-hour maximum)

```bash
# Monitor for 4 hours maximum
python main.py --mode continuous --duration 240

# Monitor with custom config
python main.py --mode continuous --duration 60 --config custom_config.yaml
```

### 3. Component Testing

```python
# Test individual components
from src.scraper import BetfuryScraper
from src.ai_predictor import SportsPredictionModel

async def test_components():
    # Test scraper
    async with BetfuryScraper() as scraper:
        matches = await scraper.get_live_matches(use_selenium=True)
        print(f"Found {len(matches)} matches")
    
    # Test AI model
    model = SportsPredictionModel()
    print("AI model initialized")

# Run test
import asyncio
asyncio.run(test_components())
```

---

## 🎓 Educational Components

### 1. Web Scraping Module (`src/scraper.py`)

**Learning Objectives:**
- Ethical web scraping techniques
- Rate limiting implementation
- Selenium WebDriver automation
- BeautifulSoup HTML parsing
- Anti-detection strategies

**Key Features:**
- Configurable delay between requests
- User agent rotation
- Respectful scraping practices
- Comprehensive error handling

**Example Usage:**
```python
from src.scraper import BetfuryScraper, MatchData

# Ethical scraping with rate limiting
async with BetfuryScraper() as scraper:
    matches = await scraper.get_live_matches(use_selenium=True)
    
    for match in matches:
        print(f"{match.home_team} vs {match.away_team}")
        print(f"Score: {match.score} ({match.minute})")
        print(f"League: {match.league}")
```

### 2. AI Prediction Engine (`src/ai_predictor.py`)

**Learning Objectives:**
- Feature engineering for sports data
- Ensemble machine learning models
- Model validation and testing
- Confidence scoring
- Prediction result analysis

**Key Features:**
- Multiple ML algorithms (Random Forest, XGBoost, Neural Networks)
- Comprehensive feature extraction
- Model persistence and loading
- Validation metrics and reporting

**Example Usage:**
```python
from src.ai_predictor import SportsPredictionModel

# Initialize and train model
model = SportsPredictionModel()

# Generate prediction
prediction = await model.predict(match_data)

if prediction.confidence >= 0.75:
    print(f"High confidence prediction: {prediction.prediction}")
    print(f"Confidence: {prediction.confidence:.1%}")
    print(f"Recommended odds: {prediction.recommended_odds}")
```

### 3. Risk Management System (`src/risk_manager.py`)

**Learning Objectives:**
- Risk assessment methodologies
- Rate limiting implementation
- Comprehensive logging
- Privacy protection techniques
- System monitoring

**Key Features:**
- Multi-layer risk assessment
- Automatic rate limiting
- Privacy protection
- Comprehensive audit trails
- Educational safeguards

**Example Usage:**
```python
from src.risk_manager import EducationalRiskManager

# Check if operation is safe
risk_manager = EducationalRiskManager(data_store)
risk_check = await risk_manager.check_scraping_risk(request_data)

if risk_check['allowed']:
    print("Operation approved by risk manager")
else:
    print(f"Operation blocked: {risk_check['reason']}")
```

### 4. Telegram Integration (`src/telegram_bot.py`)

**Learning Objectives:**
- Bot development with Telegram API
- Real-time notification systems
- User interaction handling
- Rate limiting for notifications

**Key Features:**
- Educational notification formatting
- Command handling system
- Rate-limited messaging
- Privacy-protected communications

---

## 📚 Educational Learning Paths

### Beginner Path: Web Scraping Fundamentals
1. Study `src/scraper.py` implementation
2. Experiment with different rate limiting settings
3. Learn about ethical scraping practices
4. Understand anti-detection techniques

### Intermediate Path: Machine Learning in Sports
1. Analyze feature engineering in `src/ai_predictor.py`
2. Study ensemble model implementation
3. Learn about validation and testing
4. Experiment with different algorithms

### Advanced Path: Real-time Data Systems
1. Study WebSocket monitoring in `src/websocket_monitor.py`
2. Learn about system orchestration
3. Understand performance monitoring
4. Explore distributed system concepts

---

## 🔧 API Reference

### BetfuryScraper Class

```python
class BetfuryScraper:
    async def __aenter__(self)
    async def __aexit__(self, exc_type, exc_val, exc_tb)
    async def get_live_matches(use_selenium: bool = True) -> List[MatchData]
    async def get_match_details(match_id: str) -> Optional[Dict[str, Any]]
```

### SportsPredictionModel Class

```python
class SportsPredictionModel:
    async def train(training_data: pd.DataFrame) -> Dict[str, Any]
    async def predict(match_data) -> Optional[PredictionResult]
    async def batch_predict(matches_data: List) -> List[PredictionResult]
    def get_model_info() -> Dict[str, Any]
```

### BetfuryBot Class

```python
class BetfuryBot:
    async def initialize() -> bool
    async def send_prediction_alert(prediction_data: Dict[str, Any]) -> bool
    async def send_status_update(status_data: Dict[str, Any]) -> bool
    async def start_polling()
    async def stop()
```

---

## 🛠️ Troubleshooting

### Common Issues

**Issue: Chrome/ChromeDriver errors**
```bash
# Solution: Update Chrome and ChromeDriver
brew install --cask google-chrome
pip install --upgrade selenium webdriver-manager
```

**Issue: Import errors**
```bash
# Solution: Install dependencies
pip install -r requirements.txt

# Or for missing specific packages
pip install pandas scikit-learn selenium
```

**Issue: Permission errors**
```bash
# Solution: Set proper permissions
chmod +x setup.py
chmod +x main.py
```

**Issue: Configuration errors**
```bash
# Solution: Validate configuration
python setup.py --validate
```

### Debug Mode

```bash
# Enable debug logging
python main.py --mode analyze --duration 5 --debug

# Check system status
python -c "from main import BetfuryResearchSystem; import asyncio; system = BetfuryResearchSystem(); print(system.get_system_status())"
```

### Log Analysis

```bash
# Check logs
tail -f logs/research_$(date +%Y-%m-%d).log

# Check for errors
grep ERROR logs/research_*.log

# Monitor system health
tail -f logs/system_*.log
```

---

## 🤝 Contributing

### For Educational Contributions

We welcome contributions that enhance the educational value:

**Acceptable Contributions:**
- Documentation improvements
- Educational examples and tutorials
- Performance optimizations
- Security enhancements
- Testing improvements

**Not Acceptable:**
- Actual betting functionality
- Circumvention of ethical guidelines
- Commercial gambling features
- Terms of service violations

### Development Setup

```bash
# 1. Create development environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8 mypy

# 3. Run tests
pytest tests/

# 4. Format code
black src/ tests/

# 5. Lint code
flake8 src/ tests/
mypy src/
```

### Code Style

- Follow PEP 8 style guidelines
- Add comprehensive docstrings
- Include type hints
- Write educational comments
- Maintain ethical safeguards

---

## 📖 Additional Resources

### Educational Reading
- [Web Scraping Ethics Guide](https://example.com/ethics)
- [Machine Learning in Sports](https://example.com/ml-sports)
- [Real-time Data Processing](https://example.com/realtime)
- [Ethical AI Guidelines](https://example.com/ethical-ai)

### Technical Documentation
- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [Scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

### Academic Papers
- "Ethical Web Scraping in Academic Research"
- "Machine Learning Applications in Sports Analytics"
- "Real-time Data Processing for Educational Systems"

---

## 📞 Support

### Educational Support Only

For educational and learning purposes:
- GitHub Issues for technical questions
- Documentation improvements
- Educational use cases
- Learning resource sharing

### ⚠️ **Important Notice**

This system is provided for educational purposes only. The authors and contributors are not responsible for any misuse of this software. Users must comply with all applicable laws, regulations, and website terms of service.

**DO NOT USE FOR ACTUAL BETTING OR FINANCIAL DECISIONS**

---

*Last updated: November 2024*
*Version: 1.0.0 Educational Release*