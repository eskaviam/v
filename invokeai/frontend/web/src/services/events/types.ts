import type { Graph, GraphExecutionState, S } from 'services/api/types';

export type AnyInvocation = NonNullable<NonNullable<Graph['nodes']>[string]>;

export type AnyResult = NonNullable<GraphExecutionState['results'][string]>;

type BaseNode = {
  id: string;
  type: string;
  [key: string]: AnyInvocation[keyof AnyInvocation];
};

export type ModelLoadStartedEvent = S['ModelLoadStartedEvent'];
export type ModelLoadCompleteEvent = S['ModelLoadCompleteEvent'];

export type InvocationStartedEvent = S['InvocationStartedEvent'];
export type InvocationDenoiseProgressEvent = S['InvocationDenoiseProgressEvent'];
export type InvocationCompleteEvent = Omit<S['InvocationCompleteEvent'], 'result'> & { result: AnyResult };
export type InvocationErrorEvent = S['InvocationErrorEvent'];
export type ProgressImage = InvocationDenoiseProgressEvent['progress_image'];

export type ModelInstallDownloadingEvent = {
  bytes: number;
  local_path: string;
  source: string;
  timestamp: number;
  total_bytes: number;
  id: number;
};

export type ModelInstallCompletedEvent = {
  key: number;
  source: string;
  timestamp: number;
  id: number;
};

export type ModelInstallErrorEvent = {
  error: string;
  error_type: string;
  source: string;
  timestamp: number;
  id: number;
};

/**
 * A `generator_progress` socket.io event.
 *
 * @example socket.on('generator_progress', (data: GeneratorProgressEvent) => { ... }
 */
export type GeneratorProgressEvent = {
  queue_id: string;
  queue_item_id: number;
  queue_batch_id: string;
  graph_execution_state_id: string;
  node_id: string;
  source_node_id: string;
  progress_image?: ProgressImage;
  step: number;
  order: number;
  total_steps: number;
};
export type SessionCompleteEvent = S['SessionCompleteEvent'];
export type SessionCanceledEvent = S['SessionCanceledEvent'];

export type QueueItemStatusChangedEvent = S['QueueItemStatusChangedEvent'];

type ClientEmitSubscribeQueue = {
  queue_id: string;
};

export type ClientEmitUnsubscribeQueue = ClientEmitSubscribeQueue;

export type BulkDownloadStartedEvent = S['BulkDownloadStartedEvent'];
export type BulkDownloadCompleteEvent = S['BulkDownloadCompleteEvent'];
export type BulkDownloadFailedEvent = S['BulkDownloadErrorEvent'];

type ClientEmitSubscribeBulkDownload = {
  bulk_download_id: string;
};

type ClientEmitUnsubscribeBulkDownload = {
  bulk_download_id: string;
};

export type ServerToClientEvents = {
  invocation_denoise_progress: (payload: InvocationDenoiseProgressEvent) => void;
  invocation_complete: (payload: InvocationCompleteEvent) => void;
  invocation_error: (payload: InvocationErrorEvent) => void;
  invocation_started: (payload: InvocationStartedEvent) => void;
  session_complete: (payload: SessionCompleteEvent) => void;
  model_load_started: (payload: ModelLoadStartedEvent) => void;
  model_load_completed: (payload: ModelLoadCompleteEvent) => void;
  model_install_downloading: (payload: ModelInstallDownloadingEvent) => void;
  model_install_completed: (payload: ModelInstallCompletedEvent) => void;
  model_install_error: (payload: ModelInstallErrorEvent) => void;
  model_load_complete: (payload: ModelLoadCompleteEvent) => void;
  queue_item_status_changed: (payload: QueueItemStatusChangedEvent) => void;
  bulk_download_started: (payload: BulkDownloadStartedEvent) => void;
  bulk_download_complete: (payload: BulkDownloadCompleteEvent) => void;
  bulk_download_error: (payload: BulkDownloadFailedEvent) => void;
};

export type ClientToServerEvents = {
  connect: () => void;
  disconnect: () => void;
  subscribe_queue: (payload: ClientEmitSubscribeQueue) => void;
  unsubscribe_queue: (payload: ClientEmitUnsubscribeQueue) => void;
  subscribe_bulk_download: (payload: ClientEmitSubscribeBulkDownload) => void;
  unsubscribe_bulk_download: (payload: ClientEmitUnsubscribeBulkDownload) => void;
};
