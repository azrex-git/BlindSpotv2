"""Unit and integration tests for TaskTracker, step-gating, and human-in-the-loop auth prompting."""

from pathlib import Path
import tempfile
import pytest

from blindspot.execution.auth_prompter import (
    AuthPromptType,
    detect_auth_input_type,
    prompt_user_credential,
)
from blindspot.execution.tracker import (
    MilestoneStatus,
    MilestoneStep,
    TaskTracker,
)
from blindspot.personas.models import PersonaTask


def test_task_tracker_decomposition_ecommerce():
    """Verify e-commerce journey task decomposes into ordered step-gate milestones."""
    task = PersonaTask(
        id="task_ecommerce_1",
        objective="Search Apple iPhone 16 and add to cart",
        starting_conditions="Homepage loaded",
        success_criteria=["Item added to cart", "Cart page reached"],
        evidence_to_collect=["Cart total", "Product title"],
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tracker_path = Path(tmpdir) / "task_tracker.md"
        tracker = TaskTracker(
            target_url="https://www.example.com",
            objective=task.objective,
            tracker_path=tracker_path,
            unlimited=True,
        )

        milestones = tracker.decompose_task(task, "https://www.example.com")
        assert len(milestones) >= 3

        # Step 1 must be Discovery & Search
        assert milestones[0].step_num == 1
        assert "Search" in milestones[0].title or "Discovery" in milestones[0].title
        assert milestones[0].status == MilestoneStatus.IN_PROGRESS

        # Step 2 must be Selection
        assert milestones[1].step_num == 2
        assert milestones[1].status == MilestoneStatus.PENDING

        # Authentication barriers are handled dynamically, not inserted into every task.
        titles = [m.title for m in milestones]
        assert not any("Authentication" in t or "Barrier" in t for t in titles)
        assert any("Cart" in t or "Conversion" in t for t in titles)

        # File must be persisted to disk
        assert tracker_path.exists()
        content = tracker_path.read_text(encoding="utf-8")
        assert "Milestone Execution Matrix" in content
        assert "Strict Precondition Gate" in content
        assert "Unlimited (Autonomous completion loop)" in content


def test_task_tracker_step_gate_progression():
    """Verify strict sequential unlock: Step N+1 is locked until Step N is PASSED."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tracker_path = Path(tmpdir) / "task_tracker.md"
        tracker = TaskTracker(
            target_url="https://www.example.com",
            objective="Test step gate",
            tracker_path=tracker_path,
            unlimited=False,
        )

        # Manually create milestones
        tracker.milestones = [
            MilestoneStep(
                step_num=1,
                title="Search Query",
                objective="Submit search",
                preconditions="Landing page loaded",
                verification_gate="Search results visible",
                status=MilestoneStatus.IN_PROGRESS,
            ),
            MilestoneStep(
                step_num=2,
                title="Select Product",
                objective="Click first item",
                preconditions="Step 1 PASSED",
                verification_gate="PDP loaded",
                status=MilestoneStatus.PENDING,
            ),
            MilestoneStep(
                step_num=3,
                title="Add to Cart",
                objective="Click Add to Cart",
                preconditions="Step 2 PASSED",
                verification_gate="Cart drawer visible",
                status=MilestoneStatus.PENDING,
            ),
        ]

        # Active milestone must be Step 1
        active = tracker.get_active_milestone()
        assert active is not None
        assert active.step_num == 1
        assert not tracker.all_milestones_passed()

        # Mark Step 1 PASSED
        tracker.mark_milestone_passed(1, "Search results loaded for iPhone 16")
        assert tracker.milestones[0].status == MilestoneStatus.PASSED
        assert tracker.milestones[0].evidence == "Search results loaded for iPhone 16"

        # Now Step 2 must be active and IN_PROGRESS
        active2 = tracker.get_active_milestone()
        assert active2 is not None
        assert active2.step_num == 2
        assert active2.status == MilestoneStatus.IN_PROGRESS

        # Mark Step 2 as WAITING_USER (e.g. OTP prompt)
        tracker.mark_milestone_waiting_user(2, "Waiting for user OTP")
        assert tracker.milestones[1].status == MilestoneStatus.WAITING_USER
        assert "Waiting for user OTP" in tracker.milestones[1].evidence

        # Now mark Step 2 PASSED
        tracker.mark_milestone_passed(2, "User provided OTP, PDP opened")
        assert tracker.milestones[1].status == MilestoneStatus.PASSED

        # Step 3 is unlocked
        active3 = tracker.get_active_milestone()
        assert active3 is not None
        assert active3.step_num == 3

        # Mark Step 3 PASSED -> All milestones passed
        tracker.mark_milestone_passed(3, "Cart item added")
        assert tracker.all_milestones_passed()
        assert tracker.get_active_milestone() is None

        # Verify Markdown rendering
        md = tracker.render_markdown()
        assert "✅ PASSED" in md
        assert "Cart item added" in md


def test_detect_auth_input_type():
    """Verify input detection for OTP, password, and email/phone barriers."""
    # 1. OTP detection
    assert detect_auth_input_type("Enter 6-digit OTP", tag="input", el_type="text") == AuthPromptType.OTP
    assert detect_auth_input_type("One-Time Password", tag="input", el_type="text") == AuthPromptType.OTP
    assert detect_auth_input_type("Verification code sent to mobile", tag="input") == AuthPromptType.OTP
    assert detect_auth_input_type("passcode", tag="input") == AuthPromptType.OTP

    # 2. Password detection
    assert detect_auth_input_type("", tag="input", el_type="password") == AuthPromptType.PASSWORD
    assert detect_auth_input_type("Enter your password", tag="input", el_type="text") == AuthPromptType.PASSWORD

    # 3. Email / Phone detection
    assert detect_auth_input_type("Enter Email / Mobile number", tag="input") == AuthPromptType.EMAIL_OR_PHONE
    assert detect_auth_input_type("Phone Number", tag="input", el_type="tel") == AuthPromptType.EMAIL_OR_PHONE
    assert detect_auth_input_type("Login ID or Username", tag="input") == AuthPromptType.EMAIL_OR_PHONE

    # 4. Non-auth inputs must return None
    assert detect_auth_input_type("Search for products, brands and more", tag="input") is None
    assert detect_auth_input_type('name="q" placeholder="Search for Products, Brands and More" mobile-search', tag="input") is None
    assert detect_auth_input_type("mobile-search", tag="input") is None
    assert detect_auth_input_type("Subscribe to newsletter", tag="input") is None
    assert detect_auth_input_type("Delivery Pincode", tag="input") is None


def test_prompt_user_credential_env_override(monkeypatch):
    """Verify prompt_user_credential safely resolves via environment variable override for automated runs."""
    monkeypatch.setenv("BLINDSPOT_AUTH_OTP", "987654")
    val = prompt_user_credential(AuthPromptType.OTP)
    assert val == "987654"

    monkeypatch.setenv("BLINDSPOT_AUTH_EMAIL", "shopper@example.com")
    val_email = prompt_user_credential(AuthPromptType.EMAIL_OR_PHONE)
    assert val_email == "shopper@example.com"


def test_agent_detect_active_auth_barrier():
    """Verify PersonaTaskAgent._detect_active_auth_barrier flags login walls and OTP inputs."""
    from unittest.mock import MagicMock
    from blindspot.ai.providers.antigravity import AntigravityProvider
    from blindspot.execution.agent import PersonaTaskAgent

    agent = PersonaTaskAgent(provider=AntigravityProvider(), headless=True)
    page_mock = MagicMock()
    page_mock.url = "https://www.flipkart.com/account/login?ret=/"
    page_mock.title.return_value = "Login to Flipkart"

    elements = [
        {"ref": "@e1", "tag": "input", "element_type": "text", "placeholder": "Enter Email/Mobile number", "bounding_box": {"y": 250}},
        {"ref": "@e2", "tag": "button", "element_type": "button", "text": "Request OTP"},
    ]

    barrier = agent._detect_active_auth_barrier(page_mock, elements)
    assert barrier is not None
    el, auth_type, field_label = barrier
    assert el["ref"] == "@e1"
    assert auth_type == AuthPromptType.EMAIL_OR_PHONE
    assert field_label == "Email or Mobile Number"

    # A phone-like search control on the storefront is not a login barrier.
    page_mock.url = "https://www.flipkart.com/search?q=iphone"
    page_mock.title.return_value = "Flipkart Search"
    page_mock.evaluate.return_value = "Search products Sign in"
    search_barrier = agent._detect_active_auth_barrier(page_mock, [
        {"ref": "@e1", "tag": "input", "element_type": "text", "name": "q", "placeholder": "Search for Products", "class": "mobile-search", "bounding_box": {"y": 100}},
    ])
    assert search_barrier is None

    # Now test OTP field detection
    page_mock.url = "https://www.flipkart.com/checkout/init"
    page_mock.title.return_value = "Verification"
    page_mock.evaluate.return_value = "Enter one-time verification code"
    elements_otp = [
        {"ref": "@e5", "tag": "input", "element_type": "text", "placeholder": "Enter 6-digit OTP", "bounding_box": {"y": 300}},
    ]
    barrier_otp = agent._detect_active_auth_barrier(page_mock, elements_otp)
    assert barrier_otp is not None
    el_otp, auth_type_otp, field_label_otp = barrier_otp
    assert auth_type_otp == AuthPromptType.OTP
    assert field_label_otp == "One-Time Password (OTP)"


def test_agent_evaluate_milestone_progression():
    """Verify milestone evaluation transitions milestones based on observed page states."""
    from unittest.mock import MagicMock
    from blindspot.ai.providers.antigravity import AntigravityProvider
    from blindspot.execution.agent import PersonaTaskAgent
    from blindspot.execution.models import ActionType, AgentAction

    agent = PersonaTaskAgent(provider=AntigravityProvider(), headless=True)
    task = PersonaTask(
        id="task_e2e",
        objective="Search Apple iPhone 16 and add to cart",
        starting_conditions="Homepage",
        success_criteria=["Item added to cart"],
        evidence_to_collect=["Cart status"],
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tracker = TaskTracker(
            target_url="https://www.flipkart.com",
            objective=task.objective,
            tracker_path=Path(tmpdir) / "task_tracker.md",
            unlimited=True,
        )
        tracker.decompose_task(task, "https://www.flipkart.com")

        # Active is Step 1 (Discovery & Search)
        assert tracker.get_active_milestone().step_num == 1

        # Simulate search results page loaded
        page_mock = MagicMock()
        page_mock.url = "https://www.flipkart.com/search?q=Apple+iPhone+16"
        page_mock.title.return_value = "Apple iPhone 16 - Buy Online"

        search_action = AgentAction(
            action=ActionType.CLICK,
            target="@e2",
            reasoning="Click search button",
        )
        agent._evaluate_milestone_progression(
            tracker=tracker,
            page=page_mock,
            page_text="Showing 1 - 24 of 1,200 results for Apple iPhone 16 Filters Sort By",
            task=task,
            action=search_action,
            exec_ok=True,
        )

        # Step 1 should now be PASSED
        assert tracker.milestones[0].status == MilestoneStatus.PASSED
        assert tracker.milestones[2].status == MilestoneStatus.PENDING

        # Step 2 (Selection) is now active
        active2 = tracker.get_active_milestone()
        assert active2.step_num == 2

        # Simulate PDP loaded
        page_mock.url = "https://www.flipkart.com/apple-iphone-16-128-gb/p/itm12345"
        page_mock.title.return_value = "Apple iPhone 16 (128 GB) Details"
        pdp_action = AgentAction(
            action=ActionType.CLICK,
            target="@e5",
            reasoning="Select first search listing",
        )
        agent._evaluate_milestone_progression(
            tracker=tracker,
            page=page_mock,
            page_text="Apple iPhone 16 (128 GB) ₹69,990 Add to Cart Buy Now Specifications Ratings & Reviews",
            task=task,
            action=pdp_action,
            exec_ok=True,
        )

        # Step 2 should now be PASSED
        assert tracker.milestones[1].status == MilestoneStatus.PASSED

