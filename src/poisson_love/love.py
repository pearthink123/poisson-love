"""
PoissonLove — unified API.

One class, four math models, one line to use.

Usage:
    from poisson_love import PoissonLove, UserPreference, Style

    love = PoissonLove(preference=UserPreference(style=Style.RESPECTFUL))
    result = love.tick()

    if result.should_send:
        send_message(result.prompt)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .core.engine import PoissonEngine
from .core.config import Config
from .core.models import Action, TickResult
from .control import PIDController, Signal, CombinedSignal, UserPreference, Style, Response
from .info_gain import InformationGain, SilenceDuration, ConversationFlow, MessageNovelty
from .optimal_stop import OptimalStop, ThresholdRule


@dataclass
class LoveResult:
    """Result of a PoissonLove tick."""

    should_send: bool           # Final decision
    stage: str                  # Which stage decided ("poisson", "infogain", "pid")
    poisson_hit: bool           # Did Poisson dice hit?
    infogain_passed: bool       # Did InfoGain approve?
    engagement: float           # User engagement score (0-1)
    lambda_rate: float          # Current lambda rate
    probability: float          # Current Poisson probability
    info_gain: float            # Information gain value
    prompt: str                 # Message to send
    reason: str                 # Human-readable explanation
    metadata: dict = field(default_factory=dict)


class PoissonLove:
    """
    Unified math-driven AI engagement engine.

    Combines four models:
    1. Poisson process — randomized timing
    2. Information gain — is this worth sending?
    3. PID controller — adaptive frequency
    4. Optimal stop — best moment to act

    Args:
        config: Engine configuration (or use defaults).
        preference: User interaction preference.
        infogain_threshold: Minimum info gain ratio to send.
        engagement_signals: Custom signal sources for PID.

    Example:
        >>> love = PoissonLove(
        ...     preference=UserPreference(style=Style.RESPECTFUL),
        ... )
        >>> for _ in range(100):
        ...     result = love.tick()
        ...     if result.should_send:
        ...         print(f"Send! Engagement={result.engagement:.2f}")
        ...     love.record_engagement(0.6)  # Simulate user response
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        preference: Optional[UserPreference] = None,
        infogain_threshold: float = 0.20,
        engagement_signals: Optional[list[tuple[Signal, float]]] = None,
        seed: Optional[int] = None,
    ):
        # Config
        self.config = config or Config.from_dict({
            "engagement": {
                "lambda_rate": 0.15,
                "check_interval_minutes": 30,
                "growth_factor": 0.08,
                "max_probability": 0.95,
                "min_interval_hours": 1.0,
                "adjudication": {
                    "quiet_hours": {"start": "00:00", "end": "08:00"},
                    "normal_send_probability": 0.7,
                },
            },
            "persona": {
                "name": "Companion",
                "tone": "warm-brief",
                "context": "You are a caring companion.",
            },
        })

        # User preference
        self.preference = preference or UserPreference(
            style=Style.RESPECTFUL,
            on_engaged=Response.MORE,
            on_disengaged=Response.LESS,
            sweet_zone=(0.35, 0.65),
        )

        # Modules
        self._engine = PoissonEngine(self.config, seed=seed)
        self._pid = PIDController.from_preference(self.preference)
        self._infogain = InformationGain(threshold=infogain_threshold)

        # Engagement signals
        self._signals = engagement_signals or self._default_signals()
        self._combined_signal = CombinedSignal(*self._signals)

        # State
        self._base_lambda = self.config.engagement.lambda_rate
        self._last_user_reply: Optional[datetime] = None
        self._my_unanswered: int = 0
        self._recent_messages: list[str] = []
        self._engagement_buffer: list[float] = []

    def tick(self, now: Optional[datetime] = None) -> LoveResult:
        """
        Run one tick of the full pipeline.

        Call this every check_interval_minutes.

        Returns:
            LoveResult with send decision and context.
        """
        if now is None:
            now = datetime.now()

        # ── Stage 1: Poisson Dice ──
        poisson_result = self._engine.tick(now)

        if poisson_result.action != Action.HIT_SEND:
            return LoveResult(
                should_send=False,
                stage="poisson",
                poisson_hit=False,
                infogain_passed=False,
                engagement=0,
                lambda_rate=self._base_lambda,
                probability=poisson_result.probability,
                info_gain=0,
                prompt="",
                reason=f"Poisson: {poisson_result.action.value}",
            )

        # ── Stage 2: Information Gain ──
        silence_src = SilenceDuration(
            last_reply_time=self._last_user_reply,
            now=now,
        )
        flow_src = ConversationFlow(
            my_unanswered_messages=self._my_unanswered,
            user_replied_in_last_hour=(
                self._last_user_reply is not None and
                (now - self._last_user_reply).total_seconds() < 3600
            ),
        )
        novelty_src = MessageNovelty(
            recent_messages=self._recent_messages[-5:],
            current_message="",
        )

        self._infogain.sources = [silence_src, flow_src, novelty_src]
        self._infogain._send_count = self._my_unanswered
        ig_result = self._infogain.evaluate()

        if not ig_result.worth_sending:
            return LoveResult(
                should_send=False,
                stage="infogain",
                poisson_hit=True,
                infogain_passed=False,
                engagement=0,
                lambda_rate=self._base_lambda,
                probability=poisson_result.probability,
                info_gain=ig_result.gain,
                prompt="",
                reason=f"InfoGain: {ig_result.reason}",
            )

        # ── Stage 3: Compute Engagement ──
        engagement = self._combined_signal.measure()

        # Transform based on preference
        low, high = self.preference.sweet_zone
        setpoint = (low + high) / 2
        if engagement < low:
            pid_input = setpoint - 0.2
        elif engagement > high:
            pid_input = setpoint + 0.2
        else:
            pid_input = setpoint

        # ── Stage 4: PID Update ──
        adj = self._pid.update(pid_input)
        self._base_lambda = max(0.05, min(0.4, self._base_lambda + adj))
        self.config.engagement.lambda_rate = self._base_lambda

        # Build prompt
        prompt = self._build_prompt(now, engagement, poisson_result.probability)

        return LoveResult(
            should_send=True,
            stage="full",
            poisson_hit=True,
            infogain_passed=True,
            engagement=engagement,
            lambda_rate=self._base_lambda,
            probability=poisson_result.probability,
            info_gain=ig_result.gain,
            prompt=prompt,
            reason=f"Send (engagement={engagement:.2f}, λ={self._base_lambda:.3f})",
        )

    def record_engagement(self, score: float) -> None:
        """
        Record user engagement after sending a message.

        Args:
            score: Engagement score (0-1). Use reply speed, quality, etc.
        """
        self._engagement_buffer.append(score)

        # Update signals
        if len(self._signals) >= 1:
            self._signals[0][0].value = score  # type: ignore

    def record_reply(self, message: str = "") -> None:
        """Record that the user replied."""
        self._last_user_reply = datetime.now()
        self._my_unanswered = 0
        self._infogain.on_receive()
        if message:
            self._recent_messages.append(message)

    def record_send(self, message: str = "") -> None:
        """Record that we sent a message."""
        self._my_unanswered += 1
        self._infogain.on_send()
        if message:
            self._recent_messages.append(message)

    def _build_prompt(self, now: datetime, engagement: float, probability: float) -> str:
        """Build the message prompt."""
        hour = now.hour
        if 6 <= hour < 10:
            time_ctx = "morning"
        elif 11 <= hour < 14:
            time_ctx = "midday"
        elif 14 <= hour < 18:
            time_ctx = "afternoon"
        elif 18 <= hour < 22:
            time_ctx = "evening"
        else:
            time_ctx = "late night"

        return (
            f"[Poisson Longing] "
            f"Time: {now.strftime('%H:%M')} ({time_ctx}), "
            f"Engagement: {engagement:.0%}, "
            f"Longing: {probability:.0%}"
        )

    def _default_signals(self) -> list[tuple[Signal, float]]:
        """Default engagement signal sources."""

        class DefaultSignal(Signal):
            def __init__(self):
                self.value = 0.5

            def measure(self) -> float:
                return self.value

        return [(DefaultSignal(), 1.0)]
