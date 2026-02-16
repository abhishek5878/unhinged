import pytest

from apriori.models.shadow_vector import AttachmentStyle, ShadowVector


@pytest.fixture
def sample_shadow_a() -> ShadowVector:
    return ShadowVector(
        agent_id="agent_a",
        values={
            "autonomy": 0.8,
            "security": 0.3,
            "achievement": 0.7,
            "intimacy": 0.5,
            "novelty": 0.6,
            "stability": 0.2,
            "power": 0.4,
            "belonging": 0.5,
        },
        attachment_style=AttachmentStyle.SECURE,
        fear_architecture=["failure", "irrelevance"],
        linguistic_signature=["basically", "you know what I mean"],
        entropy_tolerance=0.7,
        communication_style="direct",
    )


@pytest.fixture
def sample_shadow_b() -> ShadowVector:
    return ShadowVector(
        agent_id="agent_b",
        values={
            "autonomy": 0.3,
            "security": 0.8,
            "achievement": 0.4,
            "intimacy": 0.7,
            "novelty": 0.2,
            "stability": 0.9,
            "power": 0.3,
            "belonging": 0.6,
        },
        attachment_style=AttachmentStyle.ANXIOUS,
        fear_architecture=["abandonment", "engulfment"],
        linguistic_signature=["na", "sun"],
        entropy_tolerance=0.3,
        communication_style="indirect",
    )
