from __future__ import annotations

import os
from datetime import datetime
from urllib.parse import urlencode

import httpx

from .models import ClassItem, EquipmentItem, Reservation, UserSession

V1_BASE_URL = "https://www.upaceapp.com/Api"
V2_BASE_URL = "https://upace.app/api"
UNIVERSITY_ID = 61
DEFAULT_API_KEY = "Qm1KWFlsNCtVVEJXUHdnMUJYUlNiRkpUQUZnRVRBVkxWRlJUUFFNbkNEOERJRlU1VTJNRk1GQXRBMkpYZGwxclVITmVJQXdaVnlaU2NBbGdBbVZVTmxSaEFpWUFjQWwxRHoxV1B3ZzJVaUFHYjFjQ1hscFJUbFpQQ0ZZRmFsSnlVakVBT2dRekJUWlVOVk14"


class UpaceClient:
    """HTTP client for the uPace ERJCC API."""

    def __init__(self) -> None:
        self._session: UserSession | None = None
        self._http = httpx.AsyncClient(
            timeout=30.0,
            headers={"Accept": "*/*"},
        )

    @property
    def is_authenticated(self) -> bool:
        return self._session is not None and self._session.user_login_key != ""

    def _v1_form(self, extra: dict | None = None) -> dict:
        """Build common V1 form params with auth."""
        params: dict = {
            "uid": str(self._session.university_id) if self._session else str(UNIVERSITY_ID),
            "api_key": self._session.api_key if self._session else DEFAULT_API_KEY,
        }
        if self._session and self._session.user_login_key:
            params["user_id"] = self._session.user_login_key
        if extra:
            params.update(extra)
        return params

    async def _v1_post(self, endpoint: str, extra: dict | None = None) -> dict | list:
        """POST to V1 API with form-encoded body."""
        form = self._v1_form(extra)
        resp = await self._http.post(
            f"{V1_BASE_URL}/{endpoint}",
            content=urlencode(form),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        return resp.json()

    async def _v2_headers(self) -> dict[str, str]:
        """Build V2 API headers with bearer token."""
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        if self._session and self._session.bearer_token:
            headers["Authorization"] = f"Bearer {self._session.bearer_token}"
            headers["X-Source"] = "MOBILE"
        return headers

    async def _v2_post(self, endpoint: str, params: dict | None = None) -> dict | list:
        """POST to V2 API with bearer token."""
        resp = await self._http.post(
            f"{V2_BASE_URL}/{endpoint}",
            content=urlencode(params) if params else "",
            headers=await self._v2_headers(),
        )
        resp.raise_for_status()
        return resp.json()

    async def _v2_get(self, endpoint: str, params: dict | None = None) -> dict | list:
        """GET from V2 API with bearer token."""
        resp = await self._http.get(
            f"{V2_BASE_URL}/{endpoint}",
            params=params,
            headers=await self._v2_headers(),
        )
        resp.raise_for_status()
        return resp.json()

    async def _get_bearer_token(self) -> str:
        """Get bearer token from V2 auth endpoint."""
        if not self._session:
            return ""
        params = {
            "api_key": self._session.api_key,
            "university_id": str(self._session.university_id),
        }
        if self._session.user_login_key:
            params["user_login_key"] = self._session.user_login_key
        try:
            data = await self._v2_post("auth/login/legacy", params)
            if isinstance(data, dict) and data.get("error") == 0:
                return data.get("token", "")
        except Exception:
            pass
        return ""

    async def login(self, email: str, password: str = "") -> dict:
        """Authenticate with the uPace API.

        Flow:
        1. POST CheckTheUser to validate email and get user_login_key
        2. POST LoginTheUser with email + password + user_login_key
        3. Get bearer token for V2 API
        """
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        # Step 1: CheckTheUser to get user_login_key and university_id
        check_params = {"email": email, "uid": str(UNIVERSITY_ID)}
        resp = await self._http.post(
            f"{V1_BASE_URL}/CheckTheUser",
            content=urlencode(check_params),
            headers=headers,
        )
        resp.raise_for_status()
        check_data = resp.json()

        if check_data.get("registered") != 1:
            return {
                "authenticated": False,
                "error": check_data.get("error", 1),
                "message": check_data.get("message", "Email not found"),
            }

        user_login_key = check_data.get("user_login_key", "")
        university_id = int(check_data.get("university_id", UNIVERSITY_ID))

        # Step 2: LoginTheUser with credentials
        login_params: dict = {
            "email": email,
            "user_login_key": user_login_key,
            "app": "true",
        }
        if password:
            login_params["password"] = password

        resp = await self._http.post(
            f"{V1_BASE_URL}/LoginTheUser",
            content=urlencode(login_params),
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("error") != 0:
            return {
                "authenticated": False,
                "error": data.get("error"),
                "message": data.get("message", "Login failed"),
            }

        self._session = UserSession(
            user_login_key=data.get("user_login_key", user_login_key),
            email=email,
            barcode=str(data.get("barcode", "")),
            is_paid=int(data.get("is_paid", 0)),
            user_name=data.get("user_name", ""),
            api_key=data.get("api_key", DEFAULT_API_KEY),
            university_id=int(data.get("university_id", university_id)),
        )

        # Step 3: Get bearer token for V2 API
        bearer = await self._get_bearer_token()
        self._session.bearer_token = bearer

        return {
            "authenticated": True,
            "user_name": self._session.user_name,
            "barcode": self._session.barcode,
            "is_paid": self._session.is_paid,
            "university_id": self._session.university_id,
        }

    async def list_classes(
        self, date: str = "", class_type: str = "class"
    ) -> list[ClassItem]:
        """Get available classes/events for a date.

        Args:
            date: Date in YYYY-MM-DD format. Empty for today.
            class_type: 'class' or 'event'
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        time_param = datetime.now().strftime("%H:%M:%S")

        extra: dict = {
            "class_type": class_type,
            "date": date,
            "time": time_param,
        }
        data = await self._v1_post("upaceClasses", extra)
        if isinstance(data, dict):
            items = data.get("class_index", [])
            return [ClassItem.from_api(item) for item in items]
        return []

    async def list_events(self, date: str = "") -> list[ClassItem]:
        """Get available events for a date."""
        return await self.list_classes(date=date, class_type="event")

    async def my_reservations(self) -> list[Reservation]:
        """Get user's current reservations."""
        data = await self._v1_post("upaceMyReservations")
        if isinstance(data, dict):
            items = data.get("all_reservations", [])
            return [Reservation.from_api(item) for item in items]
        return []

    async def reserve_class(
        self,
        class_id: int,
        slot_id: int,
        date: str = "",
        class_type: str = "live",
    ) -> dict:
        """Reserve a class or event.

        Args:
            class_id: The class/event ID from list_classes results.
            slot_id: The slot_id from list_classes results.
            date: Date in YYYY-MM-DD format. Empty for today.
            class_type: 'live' or 'virtual'
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        extra = {
            "class_id": str(class_id),
            "slot_id": str(slot_id),
            "date": date,
            "class_type": class_type,
        }
        data = await self._v1_post("ReserveClass", extra)
        return data if isinstance(data, dict) else {"result": data}

    async def cancel_reservation(
        self, reservation_id: int = 0, waitlist_id: int = 0
    ) -> dict:
        """Cancel a class/event reservation or leave a waitlist.

        Args:
            reservation_id: The reservation ID to cancel.
            waitlist_id: The waitlist ID to leave (if on waitlist instead).
        """
        extra: dict = {}
        if reservation_id:
            extra["id"] = str(reservation_id)
        if waitlist_id:
            extra["waitlist_id"] = str(waitlist_id)
        data = await self._v1_post("upaceCancelReservation", extra)
        return data if isinstance(data, dict) else {"result": data}

    async def list_equipment(self, date: str = "") -> list[EquipmentItem]:
        """Get available equipment for a date."""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        extra = {"date": date}
        data = await self._v1_post("upaceEquipment", extra)
        if isinstance(data, dict):
            items = data.get("equipment_index", [])
            return [EquipmentItem.from_api(item) for item in items]
        return []

    async def reserve_equipment(
        self,
        equipment_id: int,
        slot_id: str,
        date: str,
        time: str,
        duration: int,
        attending_persons: int = 1,
    ) -> dict:
        """Reserve equipment (including babysitting, offices, etc.).

        Args:
            equipment_id: Equipment ID from list_equipment.
            slot_id: Slot ID from list_equipment.
            date: Date in YYYY-MM-DD format.
            time: Start time (e.g. '9:00 AM') from available_time_slots.
            duration: Duration in minutes (e.g. 30, 45, 60) from available_durations.
            attending_persons: Number of children/people (default 1).
        """
        extra: dict = {
            "equipment_id": str(equipment_id),
            "slot_id": slot_id,
            "date": date,
            "time": time,
            "duration": str(duration),
            "attending_persons": str(attending_persons),
        }
        data = await self._v1_post("ReserveEquipment", extra)
        return data if isinstance(data, dict) else {"result": data}

    async def get_alerts(self) -> list:
        """Get user alerts/notifications."""
        data = await self._v1_post("upaceAlerts")
        return data if isinstance(data, list) else (data.get("alerts", []) if isinstance(data, dict) else [])

    async def get_facility_info(self) -> dict:
        """Get university/facility information."""
        data = await self._v1_post("UpaceUniversity")
        return data if isinstance(data, dict) else {}

    async def get_user_info(self) -> dict:
        """Get user profile information."""
        data = await self._v1_post("upaceUserInfo")
        return data if isinstance(data, dict) else {}

    async def toggle_favorite(self, class_id: int, is_favorite: bool) -> dict:
        """Toggle favorite status of a class."""
        extra = {
            "class_id": str(class_id),
            "user_favorite": "1" if is_favorite else "0",
        }
        data = await self._v1_post("Favorites", extra)
        return data if isinstance(data, dict) else {"result": data}

    async def search(self, query: str) -> dict:
        """Search for classes, equipment, etc."""
        extra = {"search": query}
        data = await self._v1_post("upaceSearch", extra)
        return data if isinstance(data, dict) else {"results": data}

    async def get_recommendations(self) -> list:
        """Get recommended classes."""
        data = await self._v1_post("upaceRecommendations")
        return data if isinstance(data, list) else []

    async def get_waitlist(self) -> list:
        """Get classes/events user is waitlisted for."""
        data = await self._v1_post("GetWaitlist")
        if isinstance(data, dict):
            return data.get("data", [])
        return data if isinstance(data, list) else []

    async def delete_waitlist(self, waitlist_id: int) -> dict:
        """Remove from a waitlist."""
        extra = {"waitlist_id": str(waitlist_id)}
        data = await self._v1_post("DeleteWaitlist", extra)
        return data if isinstance(data, dict) else {"result": data}

    async def list_pt_sessions(self) -> dict:
        """Get available personal training / appointment sessions."""
        data = await self._v1_post("upacePT")
        if isinstance(data, dict):
            return {
                "sessions": data.get("sessions", []),
                "gyms": data.get("gyms", []),
                "session_categories": data.get("session_categories", []),
            }
        return {"sessions": []}

    async def get_session_times(
        self, session_id: int, date: str, trainer_id: str = ""
    ) -> list:
        """Get available time slots for a PT/appointment session.

        Args:
            session_id: Session ID from list_pt_sessions.
            date: Date in YYYY-MM-DD format.
            trainer_id: Optional trainer ID.
        """
        extra: dict = {
            "session_id": str(session_id),
            "date": date,
        }
        if trainer_id:
            extra["trainer_id"] = trainer_id
        data = await self._v1_post("getAvailableSessionTimes", extra)
        if isinstance(data, dict):
            return data.get("available_times", [])
        return []

    async def book_session(
        self,
        session_id: int,
        date: str,
        time: str,
        trainer_id: str = "",
    ) -> dict:
        """Book a personal training / appointment session.

        Args:
            session_id: Session ID from list_pt_sessions.
            date: Date in YYYY-MM-DD format.
            time: Time slot from get_session_times.
            trainer_id: Optional trainer ID.
        """
        extra: dict = {
            "session_id": str(session_id),
            "date": date,
            "time": time,
        }
        if trainer_id:
            extra["trainer_id"] = trainer_id
        data = await self._v1_post("upaceBookSession", extra)
        return data if isinstance(data, dict) else {"result": data}

    async def get_family_reservations(self) -> list:
        """Get reservations for family members."""
        data = await self._v1_post("upaceFamilyMemberReservations")
        if isinstance(data, dict):
            return data.get("family_members_reservations", [])
        return []

    async def mark_alert_read(self, alert_id: int) -> dict:
        """Mark an alert as read."""
        extra = {"alert_id": str(alert_id)}
        data = await self._v1_post("AlertRead", extra)
        return data if isinstance(data, dict) else {"result": data}

    async def get_custom_links(self) -> list:
        """Get other programs / custom links."""
        data = await self._v1_post("upaceCustomLinks")
        if isinstance(data, dict):
            return data.get("custom_links", data.get("programs", []))
        return data if isinstance(data, list) else []

    async def get_video_categories(self) -> list:
        """Get video content categories."""
        data = await self._v1_post("upaceVideoCategories")
        if isinstance(data, dict):
            return data.get("categories", data.get("video_categories", []))
        return data if isinstance(data, list) else []

    async def get_video_listings(self, category_id: str = "") -> list:
        """Get video listings, optionally filtered by category."""
        extra: dict = {}
        if category_id:
            extra["category_id"] = category_id
        data = await self._v1_post("upaceVideoListings", extra)
        if isinstance(data, dict):
            return data.get("videos", data.get("video_listings", []))
        return data if isinstance(data, list) else []

    async def submit_feedback(
        self, entity_id: int, entity_type: str, rating: int, comment: str = ""
    ) -> dict:
        """Submit feedback/rating for a class, equipment, or event.

        Args:
            entity_id: ID of the class/equipment/event.
            entity_type: 'class', 'equipment', or 'event'.
            rating: Rating score (1-5).
            comment: Optional comment.
        """
        extra: dict = {
            "entity_id": str(entity_id),
            "entity_type": entity_type,
            "rating": str(rating),
        }
        if comment:
            extra["comment"] = comment
        data = await self._v1_post("upaceSetFeedback", extra)
        return data if isinstance(data, dict) else {"result": data}

    async def close(self) -> None:
        await self._http.aclose()
