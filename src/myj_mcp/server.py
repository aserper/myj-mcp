"""MCP server for uPace ERJCC (My J) — JCC class scheduling and facility management."""

from __future__ import annotations

import json
import os

from mcp.server.fastmcp import FastMCP

from .client import UpaceClient

mcp = FastMCP(
    "myj",
    instructions="JCC class scheduling, reservations, equipment booking, and facility management via uPace API",
)
_client = UpaceClient()


def _env_credentials() -> tuple[str, str] | None:
    email = os.environ.get("UPACE_EMAIL")
    password = os.environ.get("UPACE_PASSWORD", "")
    if email:
        return email, password
    return None


async def _ensure_auth() -> None:
    """Auto-login using env vars if not already authenticated."""
    if _client.is_authenticated:
        return
    creds = _env_credentials()
    if creds:
        await _client.login(*creds)


@mcp.tool()
async def login(email: str, password: str = "") -> str:
    """Authenticate with the uPace ERJCC (My J) API.

    Args:
        email: Account email address
        password: Account password (may not be required for some accounts)
    """
    result = await _client.login(email, password)
    return json.dumps(result, indent=2)


@mcp.tool()
async def list_classes(date: str = "", class_type: str = "class") -> str:
    """List available classes or events at the JCC.

    Args:
        date: Date in YYYY-MM-DD format. Empty for today.
        class_type: 'class' for regular classes, 'event' for events.
    """
    await _ensure_auth()
    classes = await _client.list_classes(date, class_type)
    return json.dumps([c.model_dump() for c in classes], indent=2)


@mcp.tool()
async def list_events(date: str = "") -> str:
    """List available events at the JCC.

    Args:
        date: Date in YYYY-MM-DD format. Empty for today.
    """
    await _ensure_auth()
    events = await _client.list_events(date)
    return json.dumps([e.model_dump() for e in events], indent=2)


@mcp.tool()
async def my_reservations() -> str:
    """List my current reservations (classes, events, equipment)."""
    await _ensure_auth()
    reservations = await _client.my_reservations()
    return json.dumps([r.model_dump() for r in reservations], indent=2)


@mcp.tool()
async def reserve_class(
    class_id: int, slot_id: int, date: str = "", class_type: str = "live"
) -> str:
    """Reserve/book a class or event.

    Args:
        class_id: The class ID from list_classes results.
        slot_id: The slot_id from list_classes results.
        date: Date in YYYY-MM-DD format. Empty for today.
        class_type: 'live' or 'virtual'.
    """
    await _ensure_auth()
    result = await _client.reserve_class(class_id, slot_id, date, class_type)
    return json.dumps(result, indent=2)


@mcp.tool()
async def cancel_reservation(reservation_id: int = 0, waitlist_id: int = 0) -> str:
    """Cancel a class/event reservation or leave a waitlist.

    Args:
        reservation_id: The reservation ID to cancel.
        waitlist_id: The waitlist ID to leave (if on waitlist).
    """
    await _ensure_auth()
    result = await _client.cancel_reservation(reservation_id, waitlist_id)
    return json.dumps(result, indent=2)


@mcp.tool()
async def list_equipment(date: str = "") -> str:
    """List available equipment for booking.

    Args:
        date: Date in YYYY-MM-DD format. Empty for today.
    """
    await _ensure_auth()
    equipment = await _client.list_equipment(date)
    return json.dumps([e.model_dump() for e in equipment], indent=2)


@mcp.tool()
async def reserve_equipment(
    equipment_id: int,
    slot_id: str,
    date: str,
    time: str,
    duration: int,
    attending_persons: int = 1,
) -> str:
    """Reserve equipment at the JCC (babysitting, offices, etc.).

    Use list_equipment first to get available time slots and durations.

    Args:
        equipment_id: The equipment ID from list_equipment results.
        slot_id: The slot_id from list_equipment results.
        date: Date in YYYY-MM-DD format.
        time: Start time from available_time_slots (e.g. '9:00 AM').
        duration: Duration in minutes from available_durations (e.g. 30, 45, 60, 75, 90).
        attending_persons: Number of children/people (default 1).
    """
    await _ensure_auth()
    result = await _client.reserve_equipment(
        equipment_id, slot_id, date, time, duration, attending_persons
    )
    return json.dumps(result, indent=2)


@mcp.tool()
async def alerts() -> str:
    """Get JCC alerts and notifications."""
    await _ensure_auth()
    result = await _client.get_alerts()
    return json.dumps(result, indent=2)


@mcp.tool()
async def facility_info() -> str:
    """Get JCC facility information (hours, location, etc.)."""
    await _ensure_auth()
    result = await _client.get_facility_info()
    return json.dumps(result, indent=2)


@mcp.tool()
async def user_info() -> str:
    """Get user profile information."""
    await _ensure_auth()
    result = await _client.get_user_info()
    return json.dumps(result, indent=2)


@mcp.tool()
async def toggle_favorite(class_id: int, is_favorite: bool) -> str:
    """Add or remove a class from favorites.

    Args:
        class_id: The class ID.
        is_favorite: True to add to favorites, False to remove.
    """
    await _ensure_auth()
    result = await _client.toggle_favorite(class_id, is_favorite)
    return json.dumps(result, indent=2)


@mcp.tool()
async def search(query: str) -> str:
    """Search for classes, equipment, and other offerings.

    Args:
        query: Search query string.
    """
    await _ensure_auth()
    result = await _client.search(query)
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_waitlist() -> str:
    """Get classes/events I'm on the waitlist for."""
    await _ensure_auth()
    result = await _client.get_waitlist()
    return json.dumps(result, indent=2)


@mcp.tool()
async def delete_waitlist(waitlist_id: int) -> str:
    """Remove myself from a waitlist.

    Args:
        waitlist_id: The waitlist entry ID.
    """
    await _ensure_auth()
    result = await _client.delete_waitlist(waitlist_id)
    return json.dumps(result, indent=2)


@mcp.tool()
async def list_pt_sessions() -> str:
    """List available personal training / appointment sessions (basketball, swimming, etc.)."""
    await _ensure_auth()
    result = await _client.list_pt_sessions()
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_session_times(session_id: int, date: str, trainer_id: str = "") -> str:
    """Get available time slots for a PT/appointment session.

    Args:
        session_id: Session ID from list_pt_sessions.
        date: Date in YYYY-MM-DD format.
        trainer_id: Optional trainer ID to filter by.
    """
    await _ensure_auth()
    result = await _client.get_session_times(session_id, date, trainer_id)
    return json.dumps(result, indent=2)


@mcp.tool()
async def book_session(
    session_id: int, date: str, time: str, trainer_id: str = ""
) -> str:
    """Book a personal training / appointment session.

    Args:
        session_id: Session ID from list_pt_sessions.
        date: Date in YYYY-MM-DD format.
        time: Time slot from get_session_times.
        trainer_id: Optional trainer ID.
    """
    await _ensure_auth()
    result = await _client.book_session(session_id, date, time, trainer_id)
    return json.dumps(result, indent=2)


@mcp.tool()
async def family_reservations() -> str:
    """Get reservations for family members."""
    await _ensure_auth()
    result = await _client.get_family_reservations()
    return json.dumps(result, indent=2)


@mcp.tool()
async def mark_alert_read(alert_id: int) -> str:
    """Mark an alert/notification as read.

    Args:
        alert_id: The alert ID.
    """
    await _ensure_auth()
    result = await _client.mark_alert_read(alert_id)
    return json.dumps(result, indent=2)


@mcp.tool()
async def other_programs() -> str:
    """Get other programs and custom links available at the JCC."""
    await _ensure_auth()
    result = await _client.get_custom_links()
    return json.dumps(result, indent=2)


@mcp.tool()
async def video_categories() -> str:
    """Get available video content categories."""
    await _ensure_auth()
    result = await _client.get_video_categories()
    return json.dumps(result, indent=2)


@mcp.tool()
async def video_listings(category_id: str = "") -> str:
    """Get video listings, optionally filtered by category.

    Args:
        category_id: Optional category ID to filter videos.
    """
    await _ensure_auth()
    result = await _client.get_video_listings(category_id)
    return json.dumps(result, indent=2)


@mcp.tool()
async def submit_feedback(
    entity_id: int, entity_type: str, rating: int, comment: str = ""
) -> str:
    """Submit feedback/rating for a class, equipment, or event.

    Args:
        entity_id: ID of the class/equipment/event.
        entity_type: 'class', 'equipment', or 'event'.
        rating: Rating score (1-5).
        comment: Optional comment text.
    """
    await _ensure_auth()
    result = await _client.submit_feedback(entity_id, entity_type, rating, comment)
    return json.dumps(result, indent=2)
