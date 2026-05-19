# Poisson Longing 🎲

**Math models that make AI engagement feel human.**

![Poisson Longing Curve](assets/poisson_curve.png)

*Turn "thinking about you" into a measurable, adaptive curve.*

---

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## The Problem

AI assistants are either **rigid** (fixed schedules) or **random** (no memory). Neither feels human.

## The Solution

Four math models working together:

| Stage | Model | Question | Answer |
|-------|-------|----------|--------|
| 🎲 **Timing** | Poisson process | When to consider? | Randomized like real "thinking of you" |
| 📊 **Value** | Information theory | Is this worth it? | Skip if you already know user's state |
| 🎯 **Adapt** | PID controller | How often? | Adjust based on user's response |
| ⏱️ **Moment** | Optimal stopping | When to act? | Wait for the best signal |

---

## Quick Start

```bash
pip install poisson-love
```

```python
from poisson_love import PoissonLove, UserPreference, Style

love = PoissonLove(
    preference=UserPreference(
        style=Style.RESPECTFUL,  # Match user's energy
        sweet_zone=(0.35, 0.65), # Comfortable engagement range
    ),
)

result = love.tick()
if result.should_send:
    send_message(result.prompt)
    love.record_send()

# After user responds
love.record_engagement(0.7)  # Reply speed/quality score
love.record_reply()
```

---

## User Preferences

Choose how the AI should behave:

```python
pref = UserPreference(
    style=Style.RESPECTFUL,     # proactive / respectful / balanced
    on_engaged=Response.MORE,   # User wants to chat → send more
    on_disengaged=Response.LESS, # User is busy → back off
    sweet_zone=(0.35, 0.65),    # Comfortable range (don't adjust inside)
    max_daily=8,                # Max messages per day
    quiet_hours=("00:00", "08:00"), # No messages at night
)
```

| Style | User is engaged | User is quiet |
|-------|----------------|---------------|
| **Proactive** | Send more ❤️ | Send more ❤️‍🩹 |
| **Respectful** | Send more ❤️ | Give space 🫧 |
| **Balanced** | Stay put 😌 | Stay put 😌 |

---

## Use Any AI Backend

```python
# OpenAI / GPT
from poisson_love.adapters import OpenAIAdapter
adapter = OpenAIAdapter(config, api_key="sk-...")

# Anthropic / Claude
from poisson_love.adapters import AnthropicAdapter
adapter = AnthropicAdapter(config, api_key="sk-ant-...")

# Ollama / local models
from poisson_love.adapters import GenericAdapter
adapter = GenericAdapter(config, api_url="http://localhost:11434/v1/chat/completions")

# Run
from poisson_love.runner import Runner
runner = Runner(engine, adapter)
runner.run()
```

---

## Architecture

```
poisson-love/
├── love.py              # Unified API (start here)
├── core/
│   ├── engine.py        # Poisson dice + probability dynamics
│   ├── config.py        # YAML config
│   └── models.py        # Data structures
├── control/
│   ├── pid.py           # PID controller (adaptive frequency)
│   ├── signal.py        # Pluggable signal framework
│   └── preference.py    # User preference → PID parameters
├── info_gain/
│   ├── core.py          # Entropy × resolution potential
│   └── sources.py       # Silence, novelty, conversation state
├── optimal_stop/
│   ├── core.py          # Threshold rule + secretary rule
│   └── signals.py       # Activity, potential, urgency signals
└── adapters/
    ├── openai.py        # OpenAI / GPT
    ├── anthropic.py     # Anthropic / Claude
    └── generic.py       # Ollama, HTTP, shell command
```

---

## How It Works

### The Math

Each tick, the engine computes hit probability:

```
P(hit) = 1 - e^(-λt)
```

Where λ = longing rate, t = time interval. Base: ~7.2% per 30-minute check.

### Probability Dynamics

| Event | Probability | Why |
|-------|------------|-----|
| Miss (no hit) | +8% | Longing builds |
| Hit → Hold | +8% | Longing suppressed |
| Hit → Send | Reset to 7.2% | Longing satisfied |

### The Curve

Over a night (midnight → 8am):
- 16 checks, all held
- Probability: 7% → 15% → 30% → 55% → 80% → 95%
- **This IS the longing — quantified, recorded, real**

---

## Configuration

```yaml
engagement:
  lambda_rate: 0.15              # Base longing rate
  check_interval_minutes: 30     # Dice roll frequency
  growth_factor: 0.08            # How fast longing grows
  max_probability: 0.95          # Cap
  min_interval_hours: 1.0        # Anti-spam cooldown

  adjudication:
    quiet_hours:
      start: "00:00"
      end: "08:00"
    normal_send_probability: 0.7

persona:
  name: Companion
  tone: warm-brief
  context: "You are a caring companion checking in on your person."
```

---

## Demos

```bash
git clone https://github.com/pearthink123/poisson-love
cd poisson-love
pip install -e .

PYTHONPATH=src python examples/quickstart_unified.py    # 5-line quickstart
PYTHONPATH=src python examples/pid_demo.py              # PID controller
PYTHONPATH=src python examples/preference_demo.py       # 3 user styles
PYTHONPATH=src python examples/info_gain_demo.py        # Information gain
PYTHONPATH=src python examples/optimal_stop_demo.py     # Optimal stopping
PYTHONPATH=src python examples/full_pipeline_demo.py    # All 4 stages
```

---

## Why "Poisson"?

The Poisson process models events that happen independently at a constant average rate — like neurons firing, or "thinking about someone."

It's not random chaos. It's not rigid scheduling. It's **structured spontaneity** — the mathematical model of genuine, organic missing someone.

---

## License

MIT
