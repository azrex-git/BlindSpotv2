"""Interactive human-in-the-loop authentication prompter for BlindSpot.

Enables the browser agent to pause upon encountering login walls, email/mobile fields,
passwords, or OTP verification codes, and prompt the user directly in Antigravity / Terminal
like asking for permissions.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import time
from typing import Any, Dict, Optional
import uuid

from rich.panel import Panel
from rich.prompt import Prompt

from blindspot.utils.console import console


class AuthPromptType:
    EMAIL_OR_PHONE = "email_or_phone"
    PASSWORD = "password"
    OTP = "otp"
    COUPON_CODE = "coupon_code"
    PINCODE = "pincode"
    CUSTOM = "custom"


def extract_input_field_label(el: Dict[str, Any]) -> str:
    """Extract a clean, human-readable label directly from an input element."""
    raw = (
        el.get("placeholder")
        or el.get("aria_label")
        or el.get("name")
        or el.get("text")
        or ""
    ).strip()

    if not raw:
        inp_type = (el.get("input_type") or el.get("element_type") or "text").lower()
        if inp_type in ("tel", "phone"):
            return "Phone or Mobile Number"
        if inp_type == "email":
            return "Email Address"
        if inp_type == "password":
            return "Password"
        return "Input Value"

    low = raw.lower()
    # Map common e-commerce inputs to clean readable names
    if any(k in low for k in ("email/mobile", "email or mobile", "mobile number", "phone number", "enter mobile", "enter phone")):
        return "Email or Mobile Number"
    if any(k in low for k in ("enter otp", "6-digit otp", "4-digit otp", "verification code", "one-time")):
        return "One-Time Password (OTP)"
    if any(k in low for k in ("coupon", "promo", "discount code")):
        return "Coupon Code"
    if any(k in low for k in ("pincode", "pin code", "postal code", "zip code")):
        return "Delivery Pincode"
    if "password" in low:
        return "Password"

    # Clean up prefixes like "Enter ", "Please enter "
    clean = re.sub(r"^(?:please\s+)?enter\s+(?:your\s+)?", "", raw, flags=re.IGNORECASE).strip()
    return clean.title() if clean else raw.title()


def detect_auth_input_type(element_desc: str, tag: str = "input", el_type: str = "text") -> Optional[str]:
    """Inspect element attributes to detect if an interactive input is requesting user information.

    Supports fully flexible variable names: Phone number, Email, OTP, Password, Coupon code, Pincode, etc.
    """
    tag_low = tag.lower()
    type_low = el_type.lower()
    is_input = tag_low in ("input", "textarea") or "input" in type_low
    if not is_input:
        return None

    low_desc = element_desc.lower()

    # Reject newsletter and search inputs, including common search names and
    # placeholders. A phone-like CSS class must never turn the search bar into
    # an authentication prompt.
    if any(k in low_desc for k in (
        "newsletter", "subscribe", "footer", "feedback", "search products",
        "search catalog", "search for products", "type=\"search\"", "name=\"q\"",
        "name='q'", "searchbox", "search input",
    )):
        return None

    # Priority 1: Email or Mobile login input detection (takes precedence over 'Request OTP' button text!)
    is_identity_type = type_low in ("email", "tel")
    has_identity_keyword = any(k in low_desc for k in (
        "email", "mobile number", "phone number", "username", "login id", "enter mobile",
        "enter email", "email/mobile", "enter your phone", "enter your mobile", "10-digit",
    ))
    has_otp_keyword = any(k in low_desc for k in (
        "enter otp", "6-digit otp", "4-digit otp", "verification code", "one-time password", "digit code", "passcode"
    ))
    if "verification code" in low_desc and "sent to mobile" in low_desc:
        return AuthPromptType.OTP
    if has_otp_keyword and not (is_identity_type or has_identity_keyword):
        return AuthPromptType.OTP

    if any(k in low_desc for k in ("pincode", "pin code", "postal code", "zip code", "delivery pin")):
        return None

    if is_identity_type or has_identity_keyword:
        return AuthPromptType.EMAIL_OR_PHONE

    # Priority 2: Genuine OTP input detection (must be the input itself asking for OTP, not a nearby button)
    has_otp_keyword = any(k in low_desc for k in (
        "enter otp", "6-digit otp", "4-digit otp", "verification code", "one-time password", "digit code"
    )) or (
        ("otp" in low_desc or "passcode" in low_desc) and not any(k in low_desc for k in ("request otp", "get otp", "send otp"))
    )
    if has_otp_keyword:
        return AuthPromptType.OTP

    # Priority 3: Password detection
    if type_low == "password" or any(k in low_desc for k in ("password", "passphrase", "login-password")):
        return AuthPromptType.PASSWORD

    # Priority 4: Coupon / Promo Code
    if any(k in low_desc for k in ("enter coupon", "apply promo", "promo code", "discount code", "voucher code")):
        return AuthPromptType.COUPON_CODE

    return None


def prompt_user_credential(
    prompt_type: str,
    message: Optional[str] = None,
    bridge_dir: Optional[Path] = None,
    page: Optional[Any] = None,
    field_label: Optional[str] = None,
) -> str:
    """Prompt the user for required credentials in Terminal with flexible variable naming and return input."""
    label_map = {
        AuthPromptType.EMAIL_OR_PHONE: "Email or Mobile Number",
        AuthPromptType.PASSWORD: "Password",
        AuthPromptType.OTP: "One-Time Password (OTP)",
        AuthPromptType.COUPON_CODE: "Coupon Code",
        AuthPromptType.PINCODE: "Delivery Pincode",
    }
    label = field_label or label_map.get(prompt_type, prompt_type.replace("_", " ").title())
    default_msg = f"The website requires your {label} to continue the user journey."
    user_prompt = message or default_msg

    # 1. Display prominent banner in live browser window if active
    if page:
        try:
            page.evaluate(
                """
                (label) => {
                    let banner = document.getElementById('__blindspot_auth_banner');
                    if (!banner) {
                        banner = document.createElement('div');
                        banner.id = '__blindspot_auth_banner';
                        banner.style.cssText = 'position:fixed;top:10px;left:50%;transform:translateX(-50%);background:#f59e0b;color:#1e293b;font-size:15px;font-weight:bold;padding:12px 28px;border-radius:8px;box-shadow:0 10px 25px rgba(0,0,0,0.5);z-index:99999999;font-family:system-ui,-apple-system,sans-serif;letter-spacing:0.3px;pointer-events:none;';
                        document.body.appendChild(banner);
                    }
                    banner.innerHTML = '📝 User Input Required — Please enter ' + label + ' in Terminal';
                }
                """,
                label,
            )
        except Exception:
            pass

    # 2. Check environment overrides (for automated CI testing)
    env_keys = {
        AuthPromptType.EMAIL_OR_PHONE: ["BLINDSPOT_AUTH_EMAIL", "BLINDSPOT_AUTH_PHONE"],
        AuthPromptType.PASSWORD: ["BLINDSPOT_AUTH_PASSWORD"],
        AuthPromptType.OTP: ["BLINDSPOT_AUTH_OTP"],
        AuthPromptType.COUPON_CODE: ["BLINDSPOT_COUPON_CODE"],
        AuthPromptType.PINCODE: ["BLINDSPOT_PINCODE"],
    }
    for env_k in env_keys.get(prompt_type, []):
        val = os.environ.get(env_k)
        if val:
            _clear_browser_banner(page)
            return val.strip()

    # 3. Write request to Antigravity bridge IPC directory if configured
    b_dir = bridge_dir or (Path.cwd() / ".blindspot" / "bridge")
    b_dir.mkdir(parents=True, exist_ok=True)
    req_id = f"auth_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"
    req_file = b_dir / "auth_request.json"
    resp_file = b_dir / "auth_response.json"

    req_payload = {
        "id": req_id,
        "type": "credential_request",
        "credential_type": prompt_type,
        "prompt": user_prompt,
        "label": label,
        "status": "pending",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        req_file.write_text(json.dumps(req_payload, indent=2), encoding="utf-8")
    except Exception:
        pass

    # 4. Display styled panel in Terminal console
    console.print()
    console.print(
        Panel(
            f"[bold yellow]📝 Input Required from User[/bold yellow]\n\n"
            f"[white]{user_prompt}[/white]\n\n"
            f"[dim]BlindSpot has paused the live browser session until you provide this input.[/dim]",
            title="[bold cyan]BlindSpot Human-in-the-Loop Input[/bold cyan]",
            border_style="yellow",
            padding=(1, 2),
        )
    )

    is_secret = (prompt_type == AuthPromptType.PASSWORD) or ("password" in label.lower())
    entered_value = ""

    # Check if a fresh response was already written via IPC bridge (within last 3 seconds)
    if resp_file.is_file():
        try:
            mtime = resp_file.stat().st_mtime
            if (time.time() - mtime) < 3.0:
                resp_data = json.loads(resp_file.read_text(encoding="utf-8"))
                if resp_data.get("value"):
                    entered_value = str(resp_data["value"]).strip()
            else:
                resp_file.unlink(missing_ok=True)
        except Exception:
            pass

    if not entered_value:
        try:
            entered_value = Prompt.ask(
                f"[bold cyan]?[/bold cyan] [bold white]Enter {label}[/bold white]",
                password=is_secret,
                default="",
            )
        except (KeyboardInterrupt, EOFError):
            entered_value = ""

    # Clean up bridge request files
    for f in (req_file, resp_file):
        try:
            if f.is_file():
                f.unlink()
        except Exception:
            pass

    _clear_browser_banner(page)
    return entered_value.strip()

    # Clean up bridge request files
    for f in (req_file, resp_file):
        try:
            if f.is_file():
                f.unlink()
        except Exception:
            pass

    _clear_browser_banner(page)
    return entered_value.strip()


def _clear_browser_banner(page: Optional[Any]) -> None:
    """Remove authentication banner from browser."""
    if page:
        try:
            page.evaluate(
                """
                () => {
                    const banner = document.getElementById('__blindspot_auth_banner');
                    if (banner) banner.remove();
                }
                """
            )
        except Exception:
            pass


__all__ = ["AuthPromptType", "detect_auth_input_type", "prompt_user_credential", "extract_input_field_label"]

