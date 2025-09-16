# TennisBot 🎾

A simple and interactive tennis game simulator and score tracker built for VS Code.

## Features

- Interactive tennis match simulation
- Proper tennis scoring system (15, 30, 40, deuce, advantage)
- Real-time score tracking
- Support for best-of-3 sets matches
- VS Code integration with launch configurations
- Command-line interface with multiple modes

## Usage

### Interactive Mode
Run the bot in interactive mode to manually control the match:
```bash
python tennis_bot.py
```

This allows you to:
- Set custom player names
- Award points manually to either player
- Simulate random points
- View current score at any time

### Simulation Mode
Automatically simulate a complete match:
```bash
python tennis_bot.py --simulate
```

### VS Code Integration
Open this project in VS Code and use the pre-configured launch configurations:
- "Run Tennis Bot (Interactive)" - Starts interactive mode
- "Run Tennis Bot (Simulate Match)" - Runs a full simulation

## Commands (Interactive Mode)

- `p1` - Award point to Player 1
- `p2` - Award point to Player 2  
- `sim` - Simulate a random point
- `score` - Display current score
- `quit` - Exit the program

## Tennis Scoring Rules

The bot implements standard tennis scoring:
- Points: 0, 15, 30, 40
- Deuce: When both players reach 40
- Advantage: One point ahead after deuce
- Games: First to 6 games, must win by 2
- Sets: Best of 3 sets to win the match

## Development

This project is designed to work seamlessly with VS Code. The `.vscode` folder contains:
- Launch configurations for easy debugging
- Recommended settings for Python development

## Requirements

- Python 3.6 or higher
- No external dependencies required