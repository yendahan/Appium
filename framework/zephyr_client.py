"""Minimal Zephyr Scale (Cloud v2) REST client."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests


class ZephyrClient:
    def __init__(self, base_url: str, token: str, project_key: str) -> None:
        self._base = base_url.rstrip("/")
        self._token = token
        self._project = project_key

    def create_cycle(self, name: str) -> str:
        res = self._send("POST", "/testcycles", {"projectKey": self._project, "name": name})
        return str(res.get("key", ""))

    def post_execution(self, cycle_key: str, case_key: str, status: str, comment: Optional[str]) -> str:
        body: Dict[str, Any] = {"projectKey": self._project, "testCaseKey": case_key,
                                "testCycleKey": cycle_key, "statusName": status}
        if comment is not None:
            body["comment"] = comment
        res = self._send("POST", "/testexecutions", body)
        return str(res["key"]) if res.get("key") else str(res.get("id", ""))

    def update_execution(self, execution_key: str, status: str, comment: Optional[str]) -> None:
        body: Dict[str, Any] = {"statusName": status}
        if comment is not None:
            body["comment"] = comment
        self._send("PUT", f"/testexecutions/{execution_key}", body)

    def update_step_results(self, execution_key: str, status: str, actual: str,
                            last_step_note: Optional[str]) -> None:
        """Marks every step; the note (e.g. screenshot link) is appended to the last step only."""
        steps = self._send("GET", f"/testexecutions/{execution_key}/teststeps").get("values", [])
        items: List[Dict[str, str]] = []
        for i, _ in enumerate(steps):
            last = i == len(steps) - 1
            items.append({"statusName": status,
                          "actualResult": f"{actual}<br>{last_step_note}" if last and last_step_note else actual})
        if items:
            self._send("PUT", f"/testexecutions/{execution_key}/teststeps", {"steps": items})

    def case_keys_in_folder(self, folder_name: str) -> List[str]:
        folders = self._send(
            "GET", f"/folders?projectKey={self._project}&folderType=TEST_CASE&maxResults=500").get("values", [])
        folder_id = next((f["id"] for f in folders if f.get("name") == folder_name), None)
        if folder_id is None:
            return []
        cases = self._send(
            "GET", f"/testcases?projectKey={self._project}&folderId={folder_id}&maxResults=500").get("values", [])
        return [c["key"] for c in cases]

    def latest_executions(self, cycle_key: str) -> Dict[str, str]:
        """Case key -> newest execution key in the cycle."""
        by_case: Dict[str, str] = {}
        ids: Dict[str, int] = {}
        res = self._send(
            "GET", f"/testexecutions?projectKey={self._project}&testCycle={cycle_key}&maxResults=500")
        for e in res.get("values", []):
            parts = str(e.get("testCase", {}).get("self", "")).split("/")
            case_key = parts[-3] if len(parts) >= 3 else ""
            exec_id = int(e.get("id", -1))
            if case_key and exec_id > ids.get(case_key, -1):
                ids[case_key] = exec_id
                by_case[case_key] = e.get("key", "")
        return by_case

    def _send(self, method: str, path: str, body: Optional[Any] = None) -> Dict[str, Any]:
        res = requests.request(method, self._base + path, json=body, timeout=20, headers={
            "Authorization": f"Bearer {self._token}", "Content-Type": "application/json"})
        if res.status_code // 100 != 2:
            raise IOError(f"Zephyr {path} returned {res.status_code}: {res.text}")
        return res.json() if res.text.strip() else {}
