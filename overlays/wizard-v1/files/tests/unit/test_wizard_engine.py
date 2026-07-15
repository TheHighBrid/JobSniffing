import json
from pathlib import Path

from app.adapters.submit.base import AdapterInput
from app.adapters.submit.browser_form import SinglePageFormConfig, find_form_scope
from app.adapters.submit.wizard import (
    StepFillResult,
    WizardConfig,
    WizardLimits,
    human_only_question,
    run_wizard,
)


class FakeLocator:
    def __init__(self, page, selector, *, label="", present=False, values=None):
        self.page = page
        self.selector = selector
        self.label = label
        self.present = present
        self.values = list(values or [])

    @property
    def first(self):
        return self

    def count(self):
        return 1 if self.present or self.values else 0

    def is_visible(self):
        return True

    def is_enabled(self):
        return True

    def inner_text(self):
        return self.label

    def get_attribute(self, name):
        return self.label if name in {"value", "aria-label", "title"} else None

    def all_inner_texts(self):
        return self.values

    def click(self):
        self.page.clicks.append(self.label or self.selector)
        self.page.advance(self.label)


class FakeWizardPage:
    frames = []
    main_frame = None

    def __init__(self, states):
        self.states = states
        self.index = 0
        self.clicks = []
        self.redaction_events = 0
        self.retry_can_advance = False

    @property
    def state(self):
        return self.states[self.index]

    @property
    def url(self):
        return self.state.get("url", "https://example.test/apply")

    def content(self):
        return self.state.get("content", "application form")

    def locator(self, selector):
        if selector in {"label", "legend", "[role='group'] [aria-label]", "[data-testid*='question']"}:
            return FakeLocator(self, selector, values=[])
        if selector in {"input", "textarea", "select", "button"}:
            return FakeLocator(self, selector, present=self.state.get(f"{selector}_count", 0) > 0)
        if "error" in selector or "invalid" in selector or "alert" in selector:
            return FakeLocator(self, selector, values=self.state.get("validation", []))
        for action in self.state.get("actions", []):
            if selector == action["selector"]:
                return FakeLocator(self, selector, label=action["label"], present=True)
        return FakeLocator(self, selector)

    def advance(self, label):
        normalized = label.casefold()
        if "submit" in normalized:
            self.state["content"] = "Thank you for applying. Your application has been submitted."
            self.state["actions"] = []
            return
        if self.state.get("loop"):
            return
        if self.state.get("validation_on_click"):
            self.state["validation"] = ["Please complete the required field"]
            if self.retry_can_advance:
                self.state["validation"] = []
                self.index = min(self.index + 1, len(self.states) - 1)
            return
        self.index = min(self.index + 1, len(self.states) - 1)

    def wait_for_timeout(self, ms):
        pass

    def screenshot(self, path, full_page=True):
        Path(path).write_bytes(b"PNG")

    def evaluate(self, script):
        self.redaction_events += 1


def action(label, selector=None):
    return {"label": label, "selector": selector or f"button:{label}"}


def ctx(*, live=False):
    return AdapterInput(
        job={"id": 1, "apply_url": "https://example.test/apply?candidate=secret"},
        contact={"name": "Private Candidate", "email": "private@example.com", "phone": "613-555-0123"},
        answers=[],
        resume_pdf="resume.pdf",
        live=live,
    )


def config(*, limits=None):
    return WizardConfig(
        adapter_name="Fixture ATS",
        next_selectors=("button:Next", "button:Continue", "button:Next 1", "button:Next 2", "button:Next 3", "button:Next 4"),
        review_selectors=("button:Review",),
        submit_selectors=("button:Submit",),
        limits=limits or WizardLimits(),
    )


def empty_fill(scope, step):
    return StepFillResult(
        fill_report=({"question": "Safe question", "field_type": "text", "success": True, "detail": "filled supersecret"},),
        filled_count=1,
    )


def evidence_map(outcome):
    return {kind: value for kind, value in outcome.evidence}


def test_dry_run_traverses_next_and_review_but_never_final_submit(tmp_path):
    page = FakeWizardPage([
        {"url": "https://example.test/apply?token=one", "actions": [action("Next")]},
        {"url": "https://example.test/apply/2?token=two", "actions": [action("Review")]},
        {"url": "https://example.test/apply/review?token=three", "actions": [action("Submit")]},
    ])
    outcome = run_wizard(
        page, ctx(live=False), config(), locate_scope=lambda: page,
        fill_step=empty_fill, screenshots_dir=tmp_path,
    )

    assert outcome.result == "manual_intervention"
    assert "dry-run preview completed through 3 wizard step" in outcome.message
    assert page.clicks == ["Next", "Review"]
    assert len(outcome.screenshots) == 5
    evidence = evidence_map(outcome)
    assert evidence["dry_run"] == "submit button intentionally not clicked"
    assert "supersecret" not in evidence["wizard_journal"]
    assert "supersecret" not in evidence["field_fill_report"]
    assert "private@example.com" not in json.dumps(evidence)
    assert "?token=" not in evidence["wizard_journal"]
    assert page.redaction_events >= len(outcome.screenshots) * 2


def test_live_run_submits_only_at_final_control_and_requires_confirmation():
    page = FakeWizardPage([
        {"url": "https://example.test/apply", "actions": [action("Continue")]},
        {"url": "https://example.test/apply/final", "actions": [action("Submit")]},
    ])
    outcome = run_wizard(
        page, ctx(live=True), config(), locate_scope=lambda: page, fill_step=empty_fill,
    )

    assert outcome.result == "submitted"
    assert page.clicks == ["Continue", "Submit"]
    assert "confirmation_text" in evidence_map(outcome)


def test_structure_loop_is_bounded_and_never_reaches_submit():
    page = FakeWizardPage([
        {"url": "https://example.test/apply", "actions": [action("Next")], "loop": True},
    ])
    outcome = run_wizard(
        page, ctx(), config(), locate_scope=lambda: page, fill_step=empty_fill,
    )
    assert outcome.result == "manual_intervention"
    assert "structure loop" in outcome.message
    assert page.clicks == ["Next", "Next"]


def test_url_loop_is_detected_even_when_structure_changes():
    page = FakeWizardPage([
        {"url": "https://example.test/apply", "actions": [action("Next 1")]},
        {"url": "https://example.test/apply", "actions": [action("Next 2")]},
        {"url": "https://example.test/apply", "actions": [action("Next 3")]},
        {"url": "https://example.test/apply", "actions": [action("Next 4")]},
    ])
    outcome = run_wizard(
        page, ctx(), config(), locate_scope=lambda: page, fill_step=empty_fill,
    )
    assert outcome.result == "manual_intervention"
    assert "URL loop" in outcome.message
    assert page.clicks == ["Next 1", "Next 2", "Next 3"]


def test_step_limit_is_a_manual_boundary():
    page = FakeWizardPage([
        {"url": "https://example.test/1", "actions": [action("Next")]},
        {"url": "https://example.test/2", "actions": [action("Next")]},
        {"url": "https://example.test/3", "actions": [action("Submit")]},
    ])
    outcome = run_wizard(
        page, ctx(), config(limits=WizardLimits(max_steps=2)),
        locate_scope=lambda: page, fill_step=empty_fill,
    )
    assert outcome.result == "manual_intervention"
    assert "step limit" in outcome.message
    assert page.clicks == ["Next", "Next"]


def test_recoverable_validation_gets_one_bounded_refill_attempt():
    page = FakeWizardPage([
        {"url": "https://example.test/1", "actions": [action("Next")], "validation_on_click": True},
        {"url": "https://example.test/2", "actions": [action("Submit")]},
    ])
    calls = {"count": 0}

    def recovery_fill(scope, step):
        calls["count"] += 1
        if calls["count"] == 2:
            page.retry_can_advance = True
        return empty_fill(scope, step)

    outcome = run_wizard(
        page, ctx(), config(), locate_scope=lambda: page, fill_step=recovery_fill,
    )
    assert outcome.result == "manual_intervention"
    assert "dry-run preview" in outcome.message
    assert calls["count"] >= 3
    assert page.clicks == ["Next", "Next"]


def test_persistent_validation_fails_closed_after_one_retry():
    page = FakeWizardPage([
        {"url": "https://example.test/1", "actions": [action("Next")], "validation_on_click": True},
    ])
    outcome = run_wizard(
        page, ctx(), config(), locate_scope=lambda: page, fill_step=empty_fill,
    )
    assert outcome.result == "manual_intervention"
    assert "validation remained" in outcome.message
    assert page.clicks == ["Next", "Next"]
    assert "validation_errors" in evidence_map(outcome)


def test_account_wall_hands_off_before_any_field_action():
    page = FakeWizardPage([
        {
            "url": "https://example.test/login",
            "content": "Sign in to continue your application",
            "actions": [action("Next")],
        }
    ])
    called = {"value": False}

    def fill(scope, step):
        called["value"] = True
        return empty_fill(scope, step)

    outcome = run_wizard(page, ctx(), config(), locate_scope=lambda: page, fill_step=fill)
    assert outcome.result == "manual_intervention"
    assert "authenticate manually" in outcome.message
    assert called["value"] is False
    assert page.clicks == []


def test_human_only_question_categories_are_explicit():
    assert human_only_question("What is your gender identity?") == "demographic_self_identification"
    assert human_only_question("I certify that this application is accurate") == "legal_declaration"
    assert human_only_question("Do you consent to a background check authorization?") == "legal_consent"
    assert human_only_question("Are you authorized to work in Canada?") is None


class CountLocator:
    def __init__(self, present):
        self.present = present

    @property
    def first(self):
        return self

    def count(self):
        return 1 if self.present else 0

    def all_inner_texts(self):
        return []


class Scope:
    def __init__(self, present):
        self.present = set(present)

    def locator(self, selector):
        return CountLocator(selector in self.present)


class FramedPage(Scope):
    def __init__(self, frame):
        super().__init__(set())
        self.main_frame = self
        self.frames = [self, frame]


def test_form_scope_finds_accessible_application_inside_iframe():
    config_value = SinglePageFormConfig(
        adapter_name="Iframe ATS",
        email_selectors=("#email",),
        resume_selectors=("#resume",),
        submit_selectors=("#submit",),
    )
    frame = Scope({"#email", "#resume", "#submit"})
    page = FramedPage(frame)
    assert find_form_scope(page, config_value) is frame
