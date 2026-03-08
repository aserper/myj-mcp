from __future__ import annotations

from pydantic import BaseModel


class UserSession(BaseModel):
    user_login_key: str = ""
    email: str = ""
    barcode: str = ""
    is_paid: int = 0
    user_name: str = ""
    api_key: str = ""
    university_id: int = 61
    bearer_token: str = ""


class ClassItem(BaseModel):
    id: int = 0
    name: str = ""
    slot_id: int = 0
    start_time: str = ""
    end_time: str = ""
    display_date: str = ""
    instructor_first_name: str = ""
    instructor_last_name: str = ""
    gym_name: str = ""
    room_name: str = ""
    spots_available: int = 0
    virtual_spots_available: int = 0
    walkin_spots: int = 0
    has_reservation: bool = False
    allow_reservations: bool = True
    is_waiting_allowed: bool = False
    waitlist_id: str | int = ""
    wait_position: str | int = ""
    reservation_id: str | int = ""
    class_type: str = ""
    entity_type: str = ""
    is_user_favorite: bool = False
    is_cancelled: dict = {}
    description: str = ""
    price: float = 0.0

    @classmethod
    def from_api(cls, data: dict) -> ClassItem:
        return cls(
            id=data.get("id") or 0,
            name=data.get("name") or "",
            slot_id=data.get("slot_id") or 0,
            start_time=data.get("start_time") or "",
            end_time=data.get("end_time") or "",
            display_date=data.get("display_date") or "",
            instructor_first_name=data.get("instructor_first_name") or "",
            instructor_last_name=data.get("instructor_last_name") or "",
            gym_name=data.get("gym_name") or "",
            room_name=data.get("room_name") or "",
            spots_available=data.get("spots_available") or 0,
            virtual_spots_available=data.get("virtual_spots_available") or 0,
            walkin_spots=data.get("walkin_spots") or 0,
            has_reservation=bool(data.get("has_reservation")),
            allow_reservations=data.get("allow_reservations", True),
            is_waiting_allowed=bool(data.get("is_waiting_allowed")),
            waitlist_id=data.get("waitlist_id") or "",
            wait_position=data.get("wait_position") or "",
            reservation_id=data.get("reservation_id") or "",
            class_type=data.get("class_type") or "",
            entity_type=data.get("entity_type") or "",
            is_user_favorite=bool(data.get("is_user_favorite")),
            is_cancelled=data.get("is_cancelled") or {},
            description=data.get("description") or "",
            price=data.get("price") or 0.0,
        )


class Reservation(BaseModel):
    id: int = 0
    name: str = ""
    start_time: str = ""
    end_time: str = ""
    reservation_type: str = ""
    entity_type: str = ""
    display_date: str = ""
    gym_name: str = ""
    room_name: str = ""

    @classmethod
    def from_api(cls, data: dict) -> Reservation:
        return cls(
            id=data.get("id") or data.get("reservation_id") or 0,
            name=data.get("name") or "",
            start_time=data.get("start_time") or "",
            end_time=data.get("end_time") or "",
            reservation_type=data.get("reservation_type") or "",
            entity_type=data.get("entity_type") or "",
            display_date=data.get("display_date") or "",
            gym_name=data.get("gym_name") or "",
            room_name=data.get("room_name") or "",
        )


class EquipmentItem(BaseModel):
    id: int = 0
    name: str = ""
    gym_name: str = ""
    room_name: str = ""
    slot_id: str = ""
    start_time: str = ""
    end_time: str = ""
    has_reservation: bool = False
    total_slots: int = 0
    max_attending_persons: int = 1
    available_time_slots: list[dict] = []
    available_durations: list[dict] = []
    attending_persons: list[dict] = []
    show_terms: bool = False
    terms_body: str = ""
    notes: str = ""

    @classmethod
    def from_api(cls, data: dict) -> EquipmentItem:
        return cls(
            id=int(data.get("id") or 0),
            name=data.get("name") or "",
            gym_name=data.get("gym_name") or "",
            room_name=data.get("room_name") or "",
            slot_id=str(data.get("slot_id") or ""),
            start_time=data.get("start_time") or "",
            end_time=data.get("end_time") or "",
            has_reservation=bool(data.get("has_reservation")),
            total_slots=int(data.get("total_slots") or 0),
            max_attending_persons=int(data.get("max_attending_persons") or 1),
            available_time_slots=data.get("available_time_slots") or [],
            available_durations=data.get("available_durations") or [],
            attending_persons=data.get("attending_persons") or [],
            show_terms=data.get("show_terms") in (1, "1", True),
            terms_body=data.get("terms_body") or "",
            notes=data.get("notes") or "",
        )
