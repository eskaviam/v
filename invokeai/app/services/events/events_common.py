from typing import TYPE_CHECKING, Any, Coroutine, Optional, Protocol, TypeAlias, TypeVar

from fastapi_events.handlers.local import local_handler
from fastapi_events.registry.payload_schema import registry as payload_schema
from pydantic import BaseModel, ConfigDict, Field, SerializeAsAny

from invokeai.app.invocations.baseinvocation import BaseInvocation, BaseInvocationOutput
from invokeai.app.services.session_processor.session_processor_common import ProgressImage
from invokeai.app.services.session_queue.session_queue_common import (
    QUEUE_ITEM_STATUS,
    BatchStatus,
    EnqueueBatchResult,
    SessionQueueItem,
    SessionQueueStatus,
)
from invokeai.app.util.misc import get_timestamp
from invokeai.backend.model_manager.config import AnyModelConfig, SubModelType

if TYPE_CHECKING:
    from invokeai.app.services.model_install.model_install_common import ModelInstallJob


class EventBase(BaseModel):
    """Base class for all events. All events must inherit from this class.

    Events must define a class attribute `__event_name__` to identify the event.

    All other attributes should be defined as normal for a pydantic model.

    A timestamp is automatically added to the event when it is created.
    """

    timestamp: int = Field(description="The timestamp of the event", default_factory=get_timestamp)

    model_config = ConfigDict(json_schema_serialization_defaults_required=True)


TEvent = TypeVar("TEvent", bound=EventBase)

FastAPIEvent: TypeAlias = tuple[str, TEvent]
"""
A tuple representing a `fastapi-events` event, with the event name and payload.
Provide a generic type to `TEvent` to specify the payload type.
"""


class FastAPIEventFunc(Protocol):
    def __call__(self, event: FastAPIEvent[Any]) -> Optional[Coroutine[Any, Any, None]]: ...


def register_events(events: set[type[TEvent]], func: FastAPIEventFunc) -> None:
    """Register a function to handle a list of events.

    :param events: A list of event classes to handle
    :param func: The function to handle the events
    """
    for event in events:
        local_handler.register(event_name=event.__event_name__, _func=func)


class QueueEventBase(EventBase):
    """Base class for queue events"""

    queue_id: str = Field(description="The ID of the queue")


class QueueItemEventBase(QueueEventBase):
    """Base class for queue item events"""

    item_id: int = Field(description="The ID of the queue item")
    batch_id: str = Field(description="The ID of the queue batch")


class SessionEventBase(QueueItemEventBase):
    """Base class for session (aka graph execution state) events"""

    session_id: str = Field(description="The ID of the session (aka graph execution state)")


class InvocationEventBase(SessionEventBase):
    """Base class for invocation events"""

    queue_id: str = Field(description="The ID of the queue")
    item_id: int = Field(description="The ID of the queue item")
    batch_id: str = Field(description="The ID of the queue batch")
    session_id: str = Field(description="The ID of the session (aka graph execution state)")
    invocation_id: str = Field(description="The ID of the invocation")
    invocation_source_id: str = Field(description="The ID of the prepared invocation's source node")
    invocation_type: str = Field(description="The type of invocation")


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class InvocationStartedEvent(InvocationEventBase):
    """Emitted when an invocation is started"""

    __event_name__ = "invocation_started"

    @classmethod
    def build(cls, queue_item: SessionQueueItem, invocation: BaseInvocation) -> "InvocationStartedEvent":
        return cls(
            queue_id=queue_item.queue_id,
            item_id=queue_item.item_id,
            batch_id=queue_item.batch_id,
            session_id=queue_item.session_id,
            invocation_id=invocation.id,
            invocation_source_id=queue_item.session.prepared_source_mapping[invocation.id],
            invocation_type=invocation.get_type(),
        )


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class InvocationDenoiseProgressEvent(InvocationEventBase):
    """Emitted at each step during denoising of an invocation."""

    __event_name__ = "invocation_denoise_progress"

    progress_image: ProgressImage = Field(description="The progress image sent at each step during processing")
    step: int = Field(description="The current step of the invocation")
    total_steps: int = Field(description="The total number of steps in the invocation")

    @classmethod
    def build(
        cls,
        queue_item: SessionQueueItem,
        invocation: BaseInvocation,
        step: int,
        total_steps: int,
        progress_image: ProgressImage,
    ) -> "InvocationDenoiseProgressEvent":
        return cls(
            queue_id=queue_item.queue_id,
            item_id=queue_item.item_id,
            batch_id=queue_item.batch_id,
            session_id=queue_item.session_id,
            invocation_id=invocation.id,
            invocation_source_id=queue_item.session.prepared_source_mapping[invocation.id],
            invocation_type=invocation.get_type(),
            progress_image=progress_image,
            step=step,
            total_steps=total_steps,
        )


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class InvocationCompleteEvent(InvocationEventBase):
    """Emitted when an invocation is complete"""

    __event_name__ = "invocation_complete"

    result: SerializeAsAny[BaseInvocationOutput] = Field(description="The result of the invocation")

    @classmethod
    def build(
        cls, queue_item: SessionQueueItem, invocation: BaseInvocation, result: BaseInvocationOutput
    ) -> "InvocationCompleteEvent":
        return cls(
            queue_id=queue_item.queue_id,
            item_id=queue_item.item_id,
            batch_id=queue_item.batch_id,
            session_id=queue_item.session_id,
            invocation_id=invocation.id,
            invocation_source_id=queue_item.session.prepared_source_mapping[invocation.id],
            invocation_type=invocation.get_type(),
            result=result,
        )


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class InvocationErrorEvent(InvocationEventBase):
    """Emitted when an invocation encounters an error"""

    __event_name__ = "invocation_error"

    error_type: str = Field(description="The type of error")
    error: str = Field(description="The error message")

    @classmethod
    def build(
        cls, queue_item: SessionQueueItem, invocation: BaseInvocation, error_type: str, error: str
    ) -> "InvocationErrorEvent":
        return cls(
            queue_id=queue_item.queue_id,
            item_id=queue_item.item_id,
            batch_id=queue_item.batch_id,
            session_id=queue_item.session_id,
            invocation_id=invocation.id,
            invocation_source_id=queue_item.session.prepared_source_mapping[invocation.id],
            invocation_type=invocation.get_type(),
            error_type=error_type,
            error=error,
        )


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class SessionStartedEvent(SessionEventBase):
    """Emitted when a session has started"""

    __event_name__ = "session_started"

    @classmethod
    def build(cls, queue_item: SessionQueueItem) -> "SessionStartedEvent":
        return cls(
            queue_id=queue_item.queue_id,
            item_id=queue_item.item_id,
            batch_id=queue_item.batch_id,
            session_id=queue_item.session_id,
        )


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class SessionCompleteEvent(SessionEventBase):
    """Emitted when a session has completed all invocations"""

    __event_name__ = "session_complete"

    @classmethod
    def build(cls, queue_item: SessionQueueItem) -> "SessionCompleteEvent":
        return cls(
            queue_id=queue_item.queue_id,
            item_id=queue_item.item_id,
            batch_id=queue_item.batch_id,
            session_id=queue_item.session_id,
        )


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class SessionCanceledEvent(SessionEventBase):
    """Emitted when a session is canceled"""

    __event_name__ = "session_canceled"

    @classmethod
    def build(cls, queue_item: SessionQueueItem) -> "SessionCanceledEvent":
        return cls(
            queue_id=queue_item.queue_id,
            item_id=queue_item.item_id,
            batch_id=queue_item.batch_id,
            session_id=queue_item.session_id,
        )


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class QueueItemStatusChangedEvent(QueueItemEventBase):
    """Emitted when a queue item's status changes"""

    __event_name__ = "queue_item_status_changed"

    status: QUEUE_ITEM_STATUS = Field(description="The new status of the queue item")
    error: Optional[str] = Field(default=None, description="The error message, if any")
    created_at: Optional[str] = Field(default=None, description="The timestamp when the queue item was created")
    updated_at: Optional[str] = Field(default=None, description="The timestamp when the queue item was last updated")
    started_at: Optional[str] = Field(default=None, description="The timestamp when the queue item was started")
    completed_at: Optional[str] = Field(default=None, description="The timestamp when the queue item was completed")
    batch_status: BatchStatus = Field(description="The status of the batch")
    queue_status: SessionQueueStatus = Field(description="The status of the queue")

    @classmethod
    def build(
        cls, queue_item: SessionQueueItem, batch_status: BatchStatus, queue_status: SessionQueueStatus
    ) -> "QueueItemStatusChangedEvent":
        return cls(
            queue_id=queue_item.queue_id,
            item_id=queue_item.item_id,
            batch_id=queue_item.batch_id,
            status=queue_item.status,
            error=queue_item.error,
            created_at=str(queue_item.created_at) if queue_item.created_at else None,
            updated_at=str(queue_item.updated_at) if queue_item.updated_at else None,
            started_at=str(queue_item.started_at) if queue_item.started_at else None,
            completed_at=str(queue_item.completed_at) if queue_item.completed_at else None,
            batch_status=batch_status,
            queue_status=queue_status,
        )


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class BatchEnqueuedEvent(QueueEventBase):
    """Emitted when a batch is enqueued"""

    __event_name__ = "batch_enqueued"

    batch_id: str = Field(description="The ID of the batch")
    enqueued: int = Field(description="The number of invocations enqueued")
    requested: int = Field(
        description="The number of invocations initially requested to be enqueued (may be less than enqueued if queue was full)"
    )
    priority: int = Field(description="The priority of the batch")

    @classmethod
    def build(cls, enqueue_result: EnqueueBatchResult) -> "BatchEnqueuedEvent":
        return cls(
            queue_id=enqueue_result.queue_id,
            batch_id=enqueue_result.batch.batch_id,
            enqueued=enqueue_result.enqueued,
            requested=enqueue_result.requested,
            priority=enqueue_result.priority,
        )


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class QueueClearedEvent(QueueEventBase):
    """Emitted when a queue is cleared"""

    __event_name__ = "queue_cleared"

    @classmethod
    def build(cls, queue_id: str) -> "QueueClearedEvent":
        return cls(queue_id=queue_id)


class DownloadEventBase(EventBase):
    """Base class for events associated with a download"""

    source: str = Field(description="The source of the download")


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class DownloadStartedEvent(DownloadEventBase):
    """Emitted when a download is started"""

    __event_name__ = "download_started"

    download_path: str = Field(description="The local path where the download is saved")

    @classmethod
    def build(cls, source: str, download_path: str) -> "DownloadStartedEvent":
        return cls(source=source, download_path=download_path)


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class DownloadProgressEvent(DownloadEventBase):
    """Emitted at intervals during a download"""

    __event_name__ = "download_progress"

    download_path: str = Field(description="The local path where the download is saved")
    current_bytes: int = Field(description="The number of bytes downloaded so far")
    total_bytes: int = Field(description="The total number of bytes to be downloaded")

    @classmethod
    def build(cls, source: str, download_path: str, current_bytes: int, total_bytes: int) -> "DownloadProgressEvent":
        return cls(source=source, download_path=download_path, current_bytes=current_bytes, total_bytes=total_bytes)


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class DownloadCompleteEvent(DownloadEventBase):
    """Emitted when a download is completed"""

    __event_name__ = "download_complete"

    download_path: str = Field(description="The local path where the download is saved")
    total_bytes: int = Field(description="The total number of bytes downloaded")

    @classmethod
    def build(cls, source: str, download_path: str, total_bytes: int) -> "DownloadCompleteEvent":
        return cls(source=source, download_path=download_path, total_bytes=total_bytes)


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class DownloadCancelledEvent(DownloadEventBase):
    """Emitted when a download is cancelled"""

    __event_name__ = "download_cancelled"

    @classmethod
    def build(cls, source: str) -> "DownloadCancelledEvent":
        return cls(source=source)


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class DownloadErrorEvent(DownloadEventBase):
    """Emitted when a download encounters an error"""

    __event_name__ = "download_error"

    error_type: str = Field(description="The type of error")
    error: str = Field(description="The error message")

    @classmethod
    def build(cls, source: str, error_type: str, error: str) -> "DownloadErrorEvent":
        return cls(source=source, error_type=error_type, error=error)


class ModelEventBase(EventBase):
    """Base class for events associated with a model"""


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class ModelLoadStartedEvent(ModelEventBase):
    """Emitted when a model is requested"""

    __event_name__ = "model_load_started"

    config: AnyModelConfig = Field(description="The model's config")
    submodel_type: Optional[SubModelType] = Field(default=None, description="The submodel type, if any")

    @classmethod
    def build(cls, config: AnyModelConfig, submodel_type: SubModelType) -> "ModelLoadStartedEvent":
        return cls(config=config, submodel_type=submodel_type)


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class ModelLoadCompleteEvent(ModelEventBase):
    """Emitted when a model is requested"""

    __event_name__ = "model_load_complete"

    config: AnyModelConfig = Field(description="The model's config")
    submodel_type: Optional[SubModelType] = Field(default=None, description="The submodel type, if any")

    @classmethod
    def build(cls, config: AnyModelConfig, submodel_type: SubModelType) -> "ModelLoadCompleteEvent":
        return cls(config=config, submodel_type=submodel_type)


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class ModelInstallDownloadProgressEvent(ModelEventBase):
    """Emitted at intervals while the install job is in progress (remote models only)."""

    __event_name__ = "model_install_download_progress"

    id: int = Field(description="The ID of the install job")
    source: str = Field(description="Source of the model; local path, repo_id or url")
    local_path: str = Field(description="Where model is downloading to")
    bytes: int = Field(description="Number of bytes downloaded so far")
    total_bytes: int = Field(description="Total size of download, including all files")
    parts: list[dict[str, int | str]] = Field(
        description="Progress of downloading URLs that comprise the model, if any"
    )

    @classmethod
    def build(cls, job: "ModelInstallJob") -> "ModelInstallDownloadProgressEvent":
        parts: list[dict[str, str | int]] = [
            {
                "url": str(x.source),
                "local_path": str(x.download_path),
                "bytes": x.bytes,
                "total_bytes": x.total_bytes,
            }
            for x in job.download_parts
        ]
        return cls(
            id=job.id,
            source=str(job.source),
            local_path=job.local_path.as_posix(),
            parts=parts,
            bytes=job.bytes,
            total_bytes=job.total_bytes,
        )


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class ModelInstallStartedEvent(ModelEventBase):
    """Emitted once when an install job becomes active."""

    __event_name__ = "model_install_started"

    id: int = Field(description="The ID of the install job")
    source: str = Field(description="Source of the model; local path, repo_id or url")

    @classmethod
    def build(cls, job: "ModelInstallJob") -> "ModelInstallStartedEvent":
        return cls(id=job.id, source=str(job.source))


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class ModelInstallCompleteEvent(ModelEventBase):
    """Emitted when an install job is completed successfully."""

    __event_name__ = "model_install_complete"

    id: int = Field(description="The ID of the install job")
    source: str = Field(description="Source of the model; local path, repo_id or url")
    key: str = Field(description="Model config record key")
    total_bytes: Optional[int] = Field(description="Size of the model (may be None for installation of a local path)")

    @classmethod
    def build(cls, job: "ModelInstallJob") -> "ModelInstallCompleteEvent":
        assert job.config_out is not None
        return cls(id=job.id, source=str(job.source), key=(job.config_out.key), total_bytes=job.total_bytes)


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class ModelInstallCancelledEvent(ModelEventBase):
    """Emitted when an install job is cancelled."""

    __event_name__ = "model_install_cancelled"

    id: int = Field(description="The ID of the install job")
    source: str = Field(description="Source of the model; local path, repo_id or url")

    @classmethod
    def build(cls, job: "ModelInstallJob") -> "ModelInstallCancelledEvent":
        return cls(id=job.id, source=str(job.source))


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class ModelInstallErrorEvent(ModelEventBase):
    """Emitted when an install job encounters an exception."""

    __event_name__ = "model_install_error"

    id: int = Field(description="The ID of the install job")
    source: str = Field(description="Source of the model; local path, repo_id or url")
    error_type: str = Field(description="The name of the exception")
    error: str = Field(description="A text description of the exception")

    @classmethod
    def build(cls, job: "ModelInstallJob") -> "ModelInstallErrorEvent":
        assert job.error_type is not None
        assert job.error is not None
        return cls(id=job.id, source=str(job.source), error_type=job.error_type, error=job.error)


class BulkDownloadEventBase(EventBase):
    """Base class for events associated with a bulk image download"""

    bulk_download_id: str = Field(description="The ID of the bulk image download")
    bulk_download_item_id: str = Field(description="The ID of the bulk image download item")
    bulk_download_item_name: str = Field(description="The name of the bulk image download item")


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class BulkDownloadStartedEvent(BulkDownloadEventBase):
    """Emitted when a bulk image download is started"""

    __event_name__ = "bulk_download_started"

    @classmethod
    def build(
        cls, bulk_download_id: str, bulk_download_item_id: str, bulk_download_item_name: str
    ) -> "BulkDownloadStartedEvent":
        return cls(
            bulk_download_id=bulk_download_id,
            bulk_download_item_id=bulk_download_item_id,
            bulk_download_item_name=bulk_download_item_name,
        )


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class BulkDownloadCompleteEvent(BulkDownloadEventBase):
    """Emitted when a bulk image download is started"""

    __event_name__ = "bulk_download_complete"

    @classmethod
    def build(
        cls, bulk_download_id: str, bulk_download_item_id: str, bulk_download_item_name: str
    ) -> "BulkDownloadCompleteEvent":
        return cls(
            bulk_download_id=bulk_download_id,
            bulk_download_item_id=bulk_download_item_id,
            bulk_download_item_name=bulk_download_item_name,
        )


@payload_schema.register  # pyright: ignore [reportUnknownMemberType]
class BulkDownloadErrorEvent(BulkDownloadEventBase):
    """Emitted when a bulk image download is started"""

    __event_name__ = "bulk_download_error"

    error: str = Field(description="The error message")

    @classmethod
    def build(
        cls, bulk_download_id: str, bulk_download_item_id: str, bulk_download_item_name: str, error: str
    ) -> "BulkDownloadErrorEvent":
        return cls(
            bulk_download_id=bulk_download_id,
            bulk_download_item_id=bulk_download_item_id,
            bulk_download_item_name=bulk_download_item_name,
            error=error,
        )
