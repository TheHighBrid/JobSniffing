import json
from pathlib import Path

from app.adapters.submit.base import AdapterInput
from app.adapters.submit.taleo_playwright import (
    CONFIG,
    _run_on_page,
    is_taleo_page,
    is_taleo_url,
)


LABEL_SELECTORS = {"label", "legend", "[role='group'] [aria-label]", "[data-testid*='question']"}


class FakeLocator:
    def __init__(self, scope, selector, *, values=None):
        self.scope = scope
        self.page = scope.page
        self.selector = selector
        self.values = list(values or [])

    @property
    def first(self):
        return self

    def count(self):
        if self.values:
            return len(self.values)
        return 1 if self.scope.has(self.selector) else 0

    def is_visible(self):
        return self.count() > 0

    def is_enabled(self):
        return self.count() > 0

    def fill(self, value):
        if self.count() <= 0:
            raise RuntimeError("missing field")
        self.page.filled[self.selector] = value

    def set_input_files(self, path):
        if self.count() <= 0:
            raise RuntimeError("missing file field")
        self.page.files[self.selector] = path

    def click(self):
        if self.count() <= 0:
            raise RuntimeError("missing control")
        label = self.scope.label(self.selector)
        self.page.clicks.append(label or self.selector)
        self.page.advance(self.selector, label)

    def inner_text(self):
        return self.scope.label(self.selector)

    def all_inner_texts(self):
        return self.values

    def get_attribute(self, name):
        label = self.scope.label(self.selector)
        lowered = self.selector.casefold()
        if name in {"value", "aria-label", "title"}:
            return label or None
        if name == "type":
            if "password" in lowered:
                return "password"
            if "type='email'" in lowered or 'type="email"' in lowered:
                return "email"
            if "type='file'" in lowered:
                return "file"
            if "type='submit'" in lowered:
                return "submit"
            if "type='button'" in lowered:
                return "button"
            return "text"
        if name == "required":
            return "required" if self.selector in self.scope.required else None
        return None

    def evaluate(self, script):
        selector = self.selector.casefold()
        if selector.startswith("button"):
            return "button"
        if selector.startswith("textarea"):
            return "textarea"
        if selector.startswith("select"):
            return "select"
        return "input"

    def locator(self, selector):
        return FakeLocator(self.scope, f"{self.selector} {selector}")


class FakeScope:
    def __init__(self, page, location):
        self.page = page
        self.location = location
        self.required = set()

    @property
    def url(self):
        return self.page.state.get(f"{self.location}_url", self.page.url)

    @property
    def present(self):
        return set(self.page.state.get(f"{self.location}_present", set()))

    @property
    def labels(self):
        return dict(self.page.state.get(f"{self.location}_labels", {}))

    def has(self, selector):
        if selector in self.present:
            return True
        if selector == "input":
            return any(item.startswith("input") for item in self.present)
        if selector == "textarea":
            return any(item.startswith("textarea") for item in self.present)
        if selector == "select":
            return any(item.startswith("select") for item in self.present)
        if selector == "button":
            return any(item.startswith("button") for item in self.present)
        return False

    def label(self, selector):
        return self.labels.get(selector, "")

    def locator(self, selector):
        if selector in LABEL_SELECTORS:
            return FakeLocator(self, selector, values=[])
        if "error" in selector.casefold() or "invalid" in selector.casefold() or "alert" in selector.casefold():
            return FakeLocator(self, selector, values=self.page.state.get("errors", []))
        return FakeLocator(self, selector)

    def get_by_label(self, label, exact=False):
        return FakeLocator(self, f"label:{label}")

    def get_by_role(self, role, name=None, exact=False):
        return FakeLocator(self, f"role:{role}:{name}")

    def evaluate(self, script):
        self.page.redaction_events += 1


class FakeTaleoPage(FakeScope):
    def __init__(self, states, *, initial_url=None, with_frame=False):
        self.states = states
        self.index = 0
        self.clicks = []
        self.filled = {}
        self.files = {}
        self.redaction_events = 0
        self.initial_url = initial_url or states[0].get("url", "https://acme.taleo.net/careersection/2/jobdetail.ftl")
        self.with_frame = with_frame
        super().__init__(self, "main")
        self.main_frame = self
        self.frame = FakeScope(self, "frame")
        self.frames = [self, self.frame] if with_frame else [self]

    @property
    def state(self):
        return self.states[self.index]

    @property
    def url(self):
        return self.state.get("url", self.initial_url)

    def content(self):
        return self.state.get("content", "Taleo application")

    def wait_for_timeout(self, milliseconds):
        pass

    def screenshot(self, path, full_page=True):
        Path(path).write_bytes(b"PNG")

    def advance(self, selector, label):
        normalized = (label or selector).casefold()
        if "sign in" in normalized or "log in" in normalized or "login" in normalized:
            self.index = min(self.index + 1, len(self.states) - 1)
            return
        if "apply online" in normalized or "apply for this job" in normalized:
            self.index = min(self.index + 1, len(self.states) - 1)
            return
        if "submit" in normalized and "review" not in normalized:
            self.state["content"] = "Thank you for applying. Your application has been submitted."
            self.state["main_present"] = set()
            self.state["frame_present"] = set()
            return
        self.index = min(self.index + 1, len(self.states) - 1)


def _state(*, content="Taleo application", main=(), frame=(), main_labels=None, frame_labels=None, url=None, frame_url=None):
    value = {
        "content": content,
        "main_present": set(main),
        "frame_present": set(frame),
        "main_labels": dict(main_labels or {}),
        "frame_labels": dict(frame_labels or {}),
    }
    if url:
        value["url"] = url
    if frame_url:
        value["frame_url"] = frame_url
    return value


def _ctx(tmp_path, *, live=False, profile=""):
    resume = tmp_path / "resume.pdf"
    resume.write_bytes(b"%PDF-1.4 Taleo fixture")
    job = {
        "id": 44,
        "company": "Acme Bank",
        "apply_url": "https://acme.taleo.net/careersection/2/jobdetail.ftl?job=44",
    }
    if profile:
        job["credential_profile"] = profile
    return AdapterInput(
        job=job,
        contact={"name": "Mohamed Alem", "email": "me@example.com", "phone": "613-555-0100"},
        resume_pdf=str(resume),
        cover_letter="Dear hiring team",
        live=live,
    )


def _classic_states():
    next_selector = "input[type='submit'][value*='Save and Continue' i]"
    review_selector = "input[type='submit'][value*='Review' i]"
    submit_selector = "input[type='submit'][value='Submit']"
    return [
        _state(
            frame={
                "input[id*='firstName' i]", "input[id*='lastName' i]",
                "input[id*='email' i]", "input[id*='phone' i]",
                "input[type='file'][id*='resume' i]", next_selector,
            },
            frame_labels={next_selector: "Save and Continue"},
            frame_url="https://acme.taleo.net/careersection/2/application.ftl",
        ),
        _state(
            frame={review_selector}, frame_labels={review_selector: "Review and Submit"},
            frame_url="https://acme.taleo.net/careersection/2/application.ftl",
        ),
        _state(
            frame={submit_selector}, frame_labels={submit_selector: "Submit"},
            frame_url="https://acme.taleo.net/careersection/2/application.ftl",
        ),
    ]


def test_taleo_url_detection_is_strict_about_hosts_and_paths():
    assert is_taleo_url("https://acme.taleo.net/careersection/2/jobdetail.ftl?job=44")
    assert is_taleo_url("https://chp.tbe.taleo.net/chp03/ats/careers/v2/viewRequisition?org=ACME")
    assert not is_taleo_url("https://jobs.oracle.com/en/sites/jobsearch/job/44")
    assert not is_taleo_url("https://acme.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/44")
    assert not is_taleo_url("https://example.com/careersection/2/jobdetail.ftl")


def test_custom_domain_requires_explicit_taleo_dom_marker():
    page = FakeTaleoPage([
        _state(main={"iframe[src*='.taleo.net' i]"}, url="https://careers.example.com/jobs/44")
    ], initial_url="https://careers.example.com/jobs/44")
    assert is_taleo_page(page)

    generic = FakeTaleoPage([_state(url="https://careers.oracle.com/jobs/44")], initial_url="https://careers.oracle.com/jobs/44")
    assert not is_taleo_page(generic)


def test_classic_nested_frame_traverses_to_submit_boundary_without_clicking(tmp_path):
    page = FakeTaleoPage(_classic_states(), with_frame=True)
    outcome = _run_on_page(page, _ctx(tmp_path, live=False), shots_dir=tmp_path / "shots")

    assert outcome.result == "manual_intervention"
    assert "dry-run preview completed through 3 wizard step" in outcome.message
    assert page.clicks == ["Save and Continue", "Review and Submit"]
    assert "Submit" not in page.clicks
    assert page.filled["input[id*='firstName' i]"] == "Mohamed"
    assert page.filled["input[id*='lastName' i]"] == "Alem"
    assert page.files["input[type='file'][id*='resume' i]"].endswith("resume.pdf")
    assert dict(outcome.evidence)["dry_run"] == "submit button intentionally not clicked"


def test_newer_taleo_layout_uses_shared_button_selectors(tmp_path):
    next_selector = "[data-testid*='next' i]"
    submit_selector = "[data-testid*='submit' i]"
    states = [
        _state(
            main={
                "input[name*='fullName' i]", "input[name='email']",
                "input[type='file'][name*='resume' i]", next_selector,
            },
            main_labels={next_selector: "Continue"},
        ),
        _state(main={submit_selector}, main_labels={submit_selector: "Submit Application"}),
    ]
    page = FakeTaleoPage(states)
    outcome = _run_on_page(page, _ctx(tmp_path, live=False))

    assert outcome.result == "manual_intervention"
    assert page.clicks == ["Continue"]
    assert page.filled["input[name*='fullName' i]"] == "Mohamed Alem"


def test_apply_online_then_external_credentials_login_then_wizard(tmp_path, monkeypatch):
    path = tmp_path / "credentials.json"
    path.write_text(json.dumps({
        "version": 1,
        "providers": {
            "taleo": {
                "acme": {"username": "candidate@example.com", "password": "very-secret-password"}
            }
        },
    }))
    path.chmod(0o600)
    monkeypatch.setenv("JOBSNIFFING_CREDENTIALS_FILE", str(path))

    apply_selector = "a:has-text('Apply Online')"
    sign_in_selector = "button:has-text('Sign In')"
    submit_selector = "input[type='submit'][value='Submit']"
    states = [
        _state(main={apply_selector}, main_labels={apply_selector: "Apply Online"}),
        _state(
            content="Sign in to continue your application",
            main={"input[name='username']", "input[type='password']", sign_in_selector},
            main_labels={sign_in_selector: "Sign In"},
            url="https://acme.taleo.net/careersection/2/login.jsf",
        ),
        _state(
            main={"input[name='email']", "input[type='file'][id*='resume' i]", submit_selector},
            main_labels={submit_selector: "Submit"},
            url="https://acme.taleo.net/careersection/2/application.ftl",
        ),
    ]
    page = FakeTaleoPage(states)
    outcome = _run_on_page(page, _ctx(tmp_path, live=False, profile="acme"))

    assert outcome.result == "manual_intervention"
    assert page.clicks == ["Apply Online", "Sign In"]
    assert page.filled["input[name='username']"] == "candidate@example.com"
    assert page.filled["input[type='password']"] == "very-secret-password"
    serialized = json.dumps(outcome.evidence)
    assert "very-secret-password" not in serialized
    assert "candidate@example.com" not in serialized
    assert dict(outcome.evidence)["credential_profile"] == "taleo/acme"


def test_login_wall_without_external_credentials_is_manual(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBSNIFFING_CREDENTIALS_FILE", str(tmp_path / "missing.json"))
    sign_in_selector = "button:has-text('Sign In')"
    page = FakeTaleoPage([
        _state(
            content="Sign in to continue your application",
            main={"input[name='username']", "input[type='password']", sign_in_selector},
            main_labels={sign_in_selector: "Sign In"},
            url="https://acme.taleo.net/careersection/2/login.jsf",
        )
    ])
    outcome = _run_on_page(page, _ctx(tmp_path))

    assert outcome.result == "manual_intervention"
    assert "credentials are not usable" in outcome.message
    assert page.filled == {}
    assert page.clicks == []


def test_account_creation_is_never_automated(tmp_path):
    page = FakeTaleoPage([
        _state(
            content="Create your candidate account to continue. New candidate registration.",
            url="https://acme.taleo.net/careersection/2/login.jsf",
        )
    ])
    outcome = _run_on_page(page, _ctx(tmp_path))

    assert outcome.result == "manual_intervention"
    assert "account creation is required" in outcome.message
    assert page.clicks == []


def test_mfa_after_existing_account_login_stays_human(tmp_path, monkeypatch):
    path = tmp_path / "credentials.json"
    path.write_text(json.dumps({
        "version": 1,
        "providers": {"taleo": {"default": {"email": "candidate@example.com", "password": "secret"}}},
    }))
    path.chmod(0o600)
    monkeypatch.setenv("JOBSNIFFING_CREDENTIALS_FILE", str(path))
    sign_in_selector = "button:has-text('Sign In')"
    page = FakeTaleoPage([
        _state(
            content="Sign in to continue your application",
            main={"input[type='email']", "input[type='password']", sign_in_selector},
            main_labels={sign_in_selector: "Sign In"},
            url="https://acme.taleo.net/careersection/2/login.jsf",
        ),
        _state(
            content="Check your email for a code. Enter the verification code.",
            url="https://acme.taleo.net/careersection/2/login.jsf",
        ),
    ])
    outcome = _run_on_page(page, _ctx(tmp_path))

    assert outcome.result == "manual_intervention"
    assert "two-factor" in outcome.message
    assert page.clicks == ["Sign In"]


def test_live_taleo_final_submit_requires_confirmation(tmp_path):
    submit_selector = "input[type='submit'][value='Submit']"
    page = FakeTaleoPage([
        _state(
            main={"input[name='email']", "input[type='file'][id*='resume' i]", submit_selector},
            main_labels={submit_selector: "Submit"},
            url="https://acme.taleo.net/careersection/2/application.ftl",
        )
    ])
    outcome = _run_on_page(page, _ctx(tmp_path, live=True))

    assert outcome.result == "submitted"
    assert page.clicks == ["Submit"]
    assert "confirmation_text" in dict(outcome.evidence)


def test_taleo_config_keeps_intermediate_submit_inputs_separate_from_final_submit():
    assert "input[type='submit'][value*='Save and Continue' i]" in CONFIG.next_selectors
    assert "input[type='submit'][value*='Review' i]" in CONFIG.review_selectors
    assert "input[type='submit'][value='Submit']" in CONFIG.submit_selectors
