import threading
from typing import Dict, Optional
from app.models import MemberProfile, StateThread

class LocalMockDB:
    def __init__(self):
        self._lock = threading.Lock()
        
        # Prepopulate database with two target testing profiles
        self.profiles: Dict[str, MemberProfile] = {
            "member_busia_shea": MemberProfile(
                member_id="member_busia_shea",
                name="Auma Nakami",
                sub_county="Busia Central",
                crop_type="shea_butter",
                estimated_child_ages=[3, 4, 8, 12],  # 2 children under 5
                current_token_balance=150.0,
                gender="female",
                tribe="Luhya",
                is_salaried=False,
                average_harvest_income=45000.0,
                last_harvest_month=9  # September
            ),
            "member_nairobi_clerk": MemberProfile(
                member_id="member_nairobi_clerk",
                name="John Kamau",
                sub_county="Westlands",
                crop_type=None,
                estimated_child_ages=[10],  # No children under 5
                current_token_balance=5000.0,
                gender="male",
                tribe="Kikuyu",
                is_salaried=True,
                monthly_salary=35000.0,
                average_harvest_income=0.0
            )
        }
        
        # Track running state threads
        self.states: Dict[str, StateThread] = {}

    def get_profile(self, member_id: str) -> Optional[MemberProfile]:
        with self._lock:
            return self.profiles.get(member_id)

    def get_state(self, member_id: str) -> StateThread:
        with self._lock:
            if member_id not in self.states:
                self.states[member_id] = StateThread(member_id=member_id)
            return self.states[member_id]

    def save_state(self, state: StateThread):
        with self._lock:
            self.states[state.member_id] = state

    def clear(self):
        with self._lock:
            self.states.clear()

db = LocalMockDB()
