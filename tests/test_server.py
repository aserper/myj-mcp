"""Tests for the MCP server — tool registration, models, and client structure."""

from myj_mcp.server import mcp
from myj_mcp.client import UpaceClient, V1_BASE_URL, V2_BASE_URL
from myj_mcp.models import (
    ClassItem,
    EquipmentItem,
    Reservation,
    UserSession,
)

EXPECTED_TOOLS = [
    "login",
    "list_classes",
    "list_events",
    "my_reservations",
    "reserve_class",
    "cancel_reservation",
    "list_equipment",
    "reserve_equipment",
    "alerts",
    "facility_info",
    "user_info",
    "toggle_favorite",
    "search",
    "get_waitlist",
    "delete_waitlist",
    "list_pt_sessions",
    "get_session_times",
    "book_session",
    "family_reservations",
    "mark_alert_read",
    "other_programs",
    "video_categories",
    "video_listings",
    "submit_feedback",
]


def test_all_tools_registered():
    tools = mcp._tool_manager.list_tools()
    names = {t.name for t in tools}
    assert len(tools) == len(EXPECTED_TOOLS), f"Expected {len(EXPECTED_TOOLS)} tools, got {len(tools)}"
    for name in EXPECTED_TOOLS:
        assert name in names, f"Missing tool: {name}"


def test_no_duplicate_tools():
    tools = mcp._tool_manager.list_tools()
    names = [t.name for t in tools]
    assert len(names) == len(set(names)), f"Duplicate tools: {[n for n in names if names.count(n) > 1]}"


def test_all_tools_have_descriptions():
    tools = mcp._tool_manager.list_tools()
    for tool in tools:
        assert tool.description, f"Tool {tool.name} has no description"


def test_client_not_authenticated_by_default():
    client = UpaceClient()
    assert not client.is_authenticated


def test_client_urls():
    assert "upaceapp.com" in V1_BASE_URL
    assert "upace.app" in V2_BASE_URL


def test_class_item_from_api():
    data = {
        "id": "12345",
        "name": "Yoga Flow",
        "slot_id": "99999",
        "start_time": "9:00 AM",
        "end_time": "10:00 AM",
        "instructor_first_name": "Jane",
        "instructor_last_name": "D.",
        "gym_name": "Main Gym",
        "spots_available": "5",
        "class_type": "live",
        "has_reservation": False,
        "is_cancelled": {"cancelled": False},
    }
    item = ClassItem.from_api(data)
    assert item.id == 12345
    assert item.name == "Yoga Flow"
    assert item.slot_id == 99999
    assert item.start_time == "9:00 AM"
    assert item.spots_available == 5
    assert item.class_type == "live"
    assert not item.has_reservation


def test_class_item_from_empty():
    item = ClassItem.from_api({})
    assert item.id == 0
    assert item.name == ""
    assert not item.has_reservation


def test_equipment_item_from_api():
    data = {
        "id": "5079",
        "name": "JCare Babysitting (3mon - 5yr)",
        "slot_id": "28899864",
        "start_time": "8:30 AM",
        "end_time": "12:00 PM",
        "gym_name": "JCare Babysitting",
        "total_slots": "6",
        "max_attending_persons": "2",
        "show_terms": "1",
        "available_time_slots": [{"id": "8:30 AM", "value": "8:30 AM (6 of 6)"}],
        "available_durations": [{"id": 30, "value": "30 minutes"}],
        "attending_persons": [{"id": 1, "value": "one person"}],
    }
    item = EquipmentItem.from_api(data)
    assert item.id == 5079
    assert "Babysitting" in item.name
    assert item.slot_id == "28899864"
    assert item.total_slots == 6
    assert item.max_attending_persons == 2
    assert item.show_terms is True
    assert len(item.available_time_slots) == 1
    assert len(item.available_durations) == 1


def test_reservation_from_api():
    data = {
        "id": 789,
        "name": "Spin Class",
        "start_time": "6:00 AM",
        "end_time": "6:45 AM",
        "reservation_type": "live",
        "entity_type": "class",
    }
    r = Reservation.from_api(data)
    assert r.id == 789
    assert r.name == "Spin Class"
    assert r.reservation_type == "live"
    assert r.entity_type == "class"


def test_reservation_from_api_with_reservation_id():
    data = {"reservation_id": 456, "name": "Office 317"}
    r = Reservation.from_api(data)
    assert r.id == 456


def test_user_session_defaults():
    session = UserSession()
    assert session.user_login_key == ""
    assert session.university_id == 61
    assert session.bearer_token == ""


def test_user_session_with_data():
    session = UserSession(
        user_login_key="123",
        email="test@example.com",
        user_name="Test User",
        api_key="abc",
        university_id=89,
        is_paid=1,
    )
    assert session.user_login_key == "123"
    assert session.university_id == 89
    assert session.is_paid == 1
