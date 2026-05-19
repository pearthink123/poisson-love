"""
Quick Start — 5 lines to use PoissonLove.

Run: PYTHONPATH=src python examples/quickstart_unified.py
"""

from poisson_love import PoissonLove, UserPreference, Style

# Create engine with your preference
love = PoissonLove(
    preference=UserPreference(
        style=Style.RESPECTFUL,      # Match user's energy
        on_engaged="more",            # User wants to chat → send more
        on_disengaged="less",         # User is busy → back off
        sweet_zone=(0.35, 0.65),      # Comfortable engagement range
        max_daily=8,                  # Max 8 messages per day
    ),
)

# Simulate a day
from datetime import datetime, timedelta
import random

rng = random.Random(42)
now = datetime(2026, 5, 19, 8, 0)

print("PoissonLove — Quick Start")
print("=" * 50)

for i in range(48):  # 24 hours, 30-min ticks
    result = love.tick(now)

    if result.should_send:
        # Simulate user response
        engagement = rng.uniform(0.2, 0.9)
        love.record_engagement(engagement)
        love.record_send()

        if rng.random() < 0.6:  # 60% chance user replies
            love.record_reply()

        tag = "❤️" if engagement < 0.35 else ("🫧" if engagement > 0.65 else "😌")
        print(f"  {now.strftime('%m/%d %H:%M')} → SEND {tag} "
              f"engagement={engagement:.2f} λ={result.lambda_rate:.3f}")

    now += timedelta(minutes=30)
