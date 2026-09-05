from __future__ import annotations

import copy
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

try:
    from bson import ObjectId
    from pymongo import MongoClient
except ImportError:  # pragma: no cover - optional dependency in lightweight tests
    MongoClient = None
    ObjectId = None

from backend.config import get_settings

logger = logging.getLogger(__name__)
COLLECTIONS = ("meetings", "transcripts", "screen_text", "important_points", "reports")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MemoryCollection:
    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    def insert_one(self, document: dict[str, Any]) -> str:
        item = copy.deepcopy(document)
        item.setdefault("_id", str(uuid.uuid4()))
        self.documents.append(item)
        return str(item["_id"])

    def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        return copy.deepcopy(next((item for item in self.documents if _matches(item, query)), None))

    def find(self, query: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        query = query or {}
        return [copy.deepcopy(item) for item in self.documents if _matches(item, query)]

    def update_one(self, query: dict[str, Any], update: dict[str, Any]) -> bool:
        for item in self.documents:
            if _matches(item, query):
                item.update(copy.deepcopy(update.get("$set", update)))
                return True
        return False

    def delete_one(self, query: dict[str, Any]) -> bool:
        for index, item in enumerate(self.documents):
            if _matches(item, query):
                self.documents.pop(index)
                return True
        return False

    def delete_many(self, query: dict[str, Any]) -> int:
        before = len(self.documents)
        self.documents[:] = [item for item in self.documents if not _matches(item, query)]
        return before - len(self.documents)


def _matches(document: dict[str, Any], query: dict[str, Any]) -> bool:
    return all(document.get(key) == value for key, value in query.items())


class Database:
    """MongoDB adapter with an in-memory mode for development and tests."""

    def __init__(self) -> None:
        settings = get_settings()
        self.client = None
        self.db = None
        self.using_memory = True
        self.memory = {name: MemoryCollection() for name in COLLECTIONS}
        if MongoClient and settings.mongodb_uri:
            try:
                client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=800)
                client.admin.command("ping")
                self.client = client
                self.db = client[settings.database_name]
                self.using_memory = False
                self._ensure_indexes()
            except Exception as exc:  # MongoDB is optional for the college MVP demo.
                logger.warning("MongoDB unavailable; using in-memory storage: %s", exc)

    def _collection(self, name: str):
        return self.memory[name] if self.using_memory else self.db[name]

    def _ensure_indexes(self) -> None:
        if self.using_memory:
            return
        self.db.meetings.create_index("created_at")
        for name in ("transcripts", "screen_text", "important_points", "reports"):
            self.db[name].create_index("meeting_id")

    def status(self) -> dict[str, Any]:
        if self.using_memory:
            return {"connected": False, "mode": "memory", "message": "MongoDB unavailable; using temporary memory storage."}
        try:
            self.client.admin.command("ping")
            return {"connected": True, "mode": "mongodb", "message": "MongoDB is connected."}
        except Exception:
            return {"connected": False, "mode": "mongodb", "message": "MongoDB connection failed."}

    def insert(self, collection: str, document: dict[str, Any]) -> str:
        if self.using_memory:
            return self._collection(collection).insert_one(document)
        result = self._collection(collection).insert_one(document)
        return str(result.inserted_id)

    def get(self, collection: str, document_id: str) -> dict[str, Any] | None:
        return self._collection(collection).find_one({"_id": self._id(document_id)})

    def find(self, collection: str, query: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        items = self._collection(collection).find(query or {})
        return list(items) if self.using_memory else list(items)

    def update(self, collection: str, query: dict[str, Any], changes: dict[str, Any]) -> bool:
        query = self._convert_query(query)
        if self.using_memory:
            return self._collection(collection).update_one(query, {"$set": changes})
        return self._collection(collection).update_one(query, {"$set": changes}).matched_count > 0

    def delete_meeting(self, meeting_id: str) -> bool:
        result = self._collection("meetings").delete_one({"_id": self._id(meeting_id)})
        deleted = result if self.using_memory else result.deleted_count > 0
        for name in COLLECTIONS[1:]:
            self._collection(name).delete_many({"meeting_id": meeting_id})
        return bool(deleted)

    def _id(self, value: str) -> Any:
        if self.using_memory or not ObjectId:
            return value
        try:
            return ObjectId(value)
        except Exception:
            return value

    def _convert_query(self, query: dict[str, Any]) -> dict[str, Any]:
        return {key: self._id(value) if key == "_id" and isinstance(value, str) else value for key, value in query.items()}


db = Database()
