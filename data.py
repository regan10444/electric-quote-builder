"""
data.py — persistence layer for Electric Quote Builder
"""

import json
import os


MATERIALS_DEFAULT = [
    {"id": 1001, "name": "14/2 Romex",                   "price": 60.00,  "category": "Cable"},
    {"id": 1002, "name": "12/2 Romex",                   "price": 80.00,  "category": "Cable"},
    {"id": 1003, "name": "12/3 Romex",                   "price": 110.00, "category": "Cable"},
    {"id": 1004, "name": "10/2 Romex",                   "price": 125.00, "category": "Cable"},
    {"id": 1005, "name": "10/3 Romex",                   "price": 150.00, "category": "Cable"},
    {"id": 1006, "name": "THHN 12 AWG",                  "price": 15.00,  "category": "Cable"},
    {"id": 1007, "name": "Low voltage/thermostat wire",  "price": 50.00,  "category": "Cable"},
    {"id": 1008, "name": "New work single gang",         "price": 0.70,   "category": "Boxes"},
    {"id": 1009, "name": "New work double gang",         "price": 1.20,   "category": "Boxes"},
    {"id": 1010, "name": "Octagon box",                  "price": 1.40,   "category": "Boxes"},
    {"id": 1011, "name": "4\" square box",               "price": 1.90,   "category": "Boxes"},
    {"id": 1012, "name": "Pancake box",                  "price": 3.23,   "category": "Boxes"},
    {"id": 1013, "name": "Weatherproof box",             "price": 4.00,   "category": "Boxes"},
    {"id": 1014, "name": "200A main panel",              "price": 120.00, "category": "Panels"},
    {"id": 1015, "name": "100A subpanel",                "price": 75.00,  "category": "Panels"},
    {"id": 1016, "name": "15A single pole breaker",      "price": 7.00,   "category": "Panels"},
    {"id": 1017, "name": "20A single pole breaker",      "price": 7.00,   "category": "Panels"},
    {"id": 1018, "name": "20A double pole breaker",      "price": 14.00,  "category": "Panels"},
    {"id": 1019, "name": "AFCI breaker",                 "price": 35.00,  "category": "Panels"},
    {"id": 1020, "name": "GFCI breaker",                 "price": 40.00,  "category": "Panels"},
    {"id": 1021, "name": "Grounding rod",                "price": 12.00,  "category": "Panels"},
    {"id": 1022, "name": "Standard 15A outlet",         "price": 1.00,   "category": "Devices"},
    {"id": 1023, "name": "Standard 20A outlet",         "price": 1.75,   "category": "Devices"},
    {"id": 1024, "name": "GFCI outlet 15A",             "price": 12.00,  "category": "Devices"},
    {"id": 1025, "name": "GFCI outlet 20A",             "price": 14.00,  "category": "Devices"},
    {"id": 1026, "name": "USB outlet",                  "price": 18.00,  "category": "Devices"},
    {"id": 1027, "name": "Single pole switch",          "price": 1.50,   "category": "Devices"},
    {"id": 1028, "name": "3-way switch",                "price": 3.65,   "category": "Devices"},
    {"id": 1029, "name": "Dimmer switch",               "price": 18.00,  "category": "Devices"},
    {"id": 1030, "name": "Single gang plate",           "price": 0.50,   "category": "Covers"},
    {"id": 1031, "name": "Double gang plate",           "price": 0.80,   "category": "Covers"},
    {"id": 1032, "name": "Weatherproof cover",          "price": 4.00,   "category": "Covers"},
    {"id": 1033, "name": "Blank plate",                 "price": 0.40,   "category": "Covers"},
]


class DataManager:
    def __init__(self, data_path: str):
        self.data_path   = data_path
        self._mat_file   = os.path.join(data_path, "materials.json")
        self._est_file   = os.path.join(data_path, "estimates.json")
        self._client_file= os.path.join(data_path, "clients.json")
        self._job_file   = os.path.join(data_path, "jobs.json")

        self.materials  = self._load_or_create(self._mat_file, MATERIALS_DEFAULT)
        self._estimates = self._load_or_create(self._est_file, [])
        self._clients   = self._load_or_create(self._client_file, [])
        self._jobs      = self._load_or_create(self._job_file, [])

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _load_or_create(self, path, default):
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        self._save_json(path, default)
        return list(default)

    def _save_json(self, path, data):
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    # ── Materials ─────────────────────────────────────────────────────────────
    def add_material(self, mat):
        self.materials.append(mat)
        self._save_json(self._mat_file, self.materials)

    def update_material_price(self, mat_id, price):
        for m in self.materials:
            if m["id"] == mat_id:
                m["price"] = price
        self._save_json(self._mat_file, self.materials)

    def delete_material(self, mat_id):
        self.materials = [m for m in self.materials if m["id"] != mat_id]
        self._save_json(self._mat_file, self.materials)

    # ── Estimates ─────────────────────────────────────────────────────────────
    def load_estimates(self):
        return self._estimates

    def save_estimate(self, data):
        for i, e in enumerate(self._estimates):
            if e["estimate_id"] == data["estimate_id"]:
                self._estimates[i] = data
                self._save_json(self._est_file, self._estimates)
                return
        self._estimates.append(data)
        self._save_json(self._est_file, self._estimates)

    def get_estimate(self, estimate_id):
        for e in self._estimates:
            if e["estimate_id"] == estimate_id:
                return e
        return None

    def delete_estimate(self, estimate_id):
        self._estimates = [e for e in self._estimates if e["estimate_id"] != estimate_id]
        self._save_json(self._est_file, self._estimates)

    # ── Clients ───────────────────────────────────────────────────────────────
    def load_clients(self):
        return self._clients

    def get_client_ids(self):
        return [c["id"] for c in self._clients]

    def get_client_names(self):
        return [f"{c['id']} — {c['name']}" for c in self._clients]

    def get_client(self, client_id):
        cid = client_id.split("—")[0].strip() if "—" in client_id else client_id
        for c in self._clients:
            if c["id"] == cid:
                return c
        return None

    def save_client(self, info):
        # Check if updating existing
        cid = info.get("id", "").strip()
        if cid:
            for i, c in enumerate(self._clients):
                if c["id"] == cid:
                    self._clients[i] = info
                    self._save_json(self._client_file, self._clients)
                    return cid
        # New client — auto-assign ID
        existing_ids = [int(c["id"]) for c in self._clients if str(c["id"]).isdigit()]
        new_id = str(max(existing_ids, default=10000) + 1)
        info["id"] = new_id
        self._clients.append(info)
        self._save_json(self._client_file, self._clients)
        return new_id

    def delete_client(self, client_id):
        self._clients = [c for c in self._clients if c["id"] != client_id]
        self._save_json(self._client_file, self._clients)

    # ── Jobs ──────────────────────────────────────────────────────────────────
    def load_jobs(self):
        return self._jobs

    def save_job(self, job):
        for i, j in enumerate(self._jobs):
            if j["job_id"] == job["job_id"]:
                self._jobs[i] = job
                self._save_json(self._job_file, self._jobs)
                return
        self._jobs.append(job)
        self._save_json(self._job_file, self._jobs)

    def get_job(self, job_id):
        for j in self._jobs:
            if j["job_id"] == job_id:
                return j
        return None

    def delete_job(self, job_id):
        self._jobs = [j for j in self._jobs if j["job_id"] != job_id]
        self._save_json(self._job_file, self._jobs)

    def next_job_id(self):
        if not self._jobs:
            return "JOB-1001"
        last = self._jobs[-1].get("job_id", "JOB-1000")
        try:
            num = int(last.split("-")[1]) + 1
        except Exception:
            num = 1001
        return f"JOB-{num}"
