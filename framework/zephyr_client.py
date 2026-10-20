"""Minimal Zephyr Scale (Cloud v2) REST client."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import requests


def _split_path(path: str) -> List[str]:
    return [part.strip() for part in path.split("/") if part.strip()]


class ZephyrClient:
    def __init__(self, base_url: str, token: str, project_key: str) -> None:
        self._base = base_url.rstrip("/")
        self._token = token
        self._project = project_key
        # Folders this client created (name -> id): Zephyr may not list a new folder yet, so never look it up by name.
        self._created_folders: Dict[str, int] = {}

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

    def execution_steps(self, execution_key: str) -> List[Dict[str, Any]]:
        """The steps of an execution (each has an ``inline`` dict with description and expectedResult)."""
        return self._send("GET", f"/testexecutions/{execution_key}/teststeps").get("values", [])

    def set_step_results(self, execution_key: str, items: List[Dict[str, str]]) -> None:
        """Sets status and actual result of every step, in order: [{"statusName": ..., "actualResult": ...}]."""
        if items:
            self._send("PUT", f"/testexecutions/{execution_key}/teststeps", {"steps": items})

    def list_cases(self, folder_name: str) -> Optional[List[Tuple[str, str]]]:
        """(name, key) of every case directly in the folder, duplicates included; None if there is no such folder."""
        folder_id = self._folder_id(folder_name)
        if folder_id is None:
            return None
        return [(str(c["name"]), str(c["key"])) for c in self._cases_in_folder(folder_id)]

    def cases_in_folder(self, folder_name: str) -> Optional[Dict[str, str]]:
        """Case name -> key for the folder; None if there is no such folder, {} if it is empty."""
        listing = self.list_cases(folder_name)
        return None if listing is None else dict(listing)

    def case_keys_in_folder(self, folder_name: str) -> Optional[List[str]]:
        """Keys of the cases in the folder; None if there is no such folder, [] if it is empty."""
        folder_id = self._folder_id(folder_name)
        if folder_id is None:
            return None
        return [c["key"] for c in self._cases_in_folder(folder_id)]

    def create_case(self, name: str, folder_name: str, objective: str,
                    steps: Sequence[Tuple[str, str]]) -> Tuple[str, bool]:
        """Creates a test case with (description, expected result) steps; returns (key, created).

        A case with the same name already in the folder is reused (created=False), so reruns never duplicate.
        """
        folder_id = self._folder_id(folder_name)
        if folder_id is None:
            raise IOError(f"Zephyr test-case folder '{folder_name}' not found in project {self._project}")
        for case in self._cases_in_folder(folder_id):
            if case.get("name") == name:
                return str(case["key"]), False
        res = self._send("POST", "/testcases", {
            "projectKey": self._project, "name": name, "folderId": folder_id, "objective": objective})
        key = str(res["key"])
        items = [{"inline": {"description": description, "expectedResult": expected}}
                 for description, expected in steps]
        if items:
            self._send("POST", f"/testcases/{key}/teststeps", {"mode": "OVERWRITE", "items": items})
        return key, True

    def reusable_cases(self) -> Dict[str, List[str]]:
        """Case name -> keys of every existing case with that name, to be reused for a new folder.

        Cases in no folder come first, then cases sitting in a folder; each group lowest key first.
        """
        loose: Dict[str, List[str]] = {}
        filed: Dict[str, List[str]] = {}
        start = 0
        while True:
            res = self._send("GET", f"/testcases?projectKey={self._project}&maxResults=1000&startAt={start}")
            values = res.get("values", [])
            for case in values:
                target = filed if case.get("folder") else loose
                target.setdefault(str(case["name"]), []).append(str(case["key"]))
            if res.get("isLast", True) or not values:
                break
            start += len(values)

        def number(key: str) -> int:
            tail = key.rsplit("-T", 1)[-1]
            return int(tail) if tail.isdigit() else 0

        return {name: sorted(loose.get(name, []), key=number) + sorted(filed.get(name, []), key=number)
                for name in {**loose, **filed}}

    def move_case(self, case_key: str, folder_path: str) -> None:
        """Puts an existing case into the folder at ``folder_path`` (keeps its name, steps and other fields)."""
        folder_id = self._folder_id(folder_path)
        if folder_id is None:
            raise IOError(f"Zephyr test-case folder '{folder_path}' not found in project {self._project}")
        self._put_case_folder(case_key, folder_id)

    def unfile_case(self, case_key: str) -> None:
        """Takes an existing case out of its folder (it is not deleted; it then belongs to no folder)."""
        self._put_case_folder(case_key, None)

    def _put_case_folder(self, case_key: str, folder_id: Optional[int]) -> None:
        case = self._send("GET", f"/testcases/{case_key}")
        body: Dict[str, Any] = {
            "id": case["id"], "key": case["key"], "name": case["name"], "project": {"id": case["project"]["id"]},
            "priority": {"id": case["priority"]["id"]}, "status": {"id": case["status"]["id"]},
            "folder": {"id": folder_id} if folder_id is not None else None, "labels": case.get("labels") or [],
            "customFields": case.get("customFields") or {}}
        for field in ("objective", "precondition", "estimatedTime"):
            body[field] = case.get(field)
        if case.get("component"):
            body["component"] = {"id": case["component"]["id"]}
        if case.get("owner"):
            body["owner"] = {"accountId": case["owner"]["accountId"]}
        self._send("PUT", f"/testcases/{case_key}", body)

    def create_folder(self, path: str) -> int:
        """Creates the test-case folder at ``path`` ("name" or "parent/child/...") and any missing parents.

        Returns the id of the last folder. Every id it creates is remembered, because Zephyr may not list a new
        folder yet.
        """
        parts, parent, listing = _split_path(path), None, None
        if not parts:
            raise ValueError("a folder name is required")
        for i, part in enumerate(parts):
            prefix = "/".join(parts[:i + 1])
            if prefix in self._created_folders:
                parent = self._created_folders[prefix]
                continue
            if listing is None:
                listing = self._folders()
            found = next((f["id"] for f in listing if f.get("name") == part and f.get("parentId") == parent), None)
            if found is None:
                body: Dict[str, Any] = {"projectKey": self._project, "name": part, "folderType": "TEST_CASE"}
                if parent is not None:
                    body["parentId"] = parent
                found = int(self._send("POST", "/folders", body)["id"])
            self._created_folders[prefix] = int(found)
            parent = int(found)
        return int(parent)

    def _folders(self) -> List[Dict[str, Any]]:
        return self._send(
            "GET", f"/folders?projectKey={self._project}&folderType=TEST_CASE&maxResults=500").get("values", [])

    def _folder_id(self, path: str) -> Optional[int]:
        """Id of the folder at ``path`` ("name" or "parent/child/..."), matched by name under each parent."""
        parts, parent, listing = _split_path(path), None, None
        for i, part in enumerate(parts):
            prefix = "/".join(parts[:i + 1])
            if prefix in self._created_folders:
                parent = self._created_folders[prefix]
                continue
            if listing is None:
                listing = self._folders()
            parent = next((f["id"] for f in listing if f.get("name") == part and f.get("parentId") == parent), None)
            if parent is None:
                return None
        return parent

    def _cases_in_folder(self, folder_id: int) -> List[Dict[str, Any]]:
        return self._send(
            "GET", f"/testcases?projectKey={self._project}&folderId={folder_id}&maxResults=500").get("values", [])

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
