import { createAction } from '@reduxjs/toolkit';
import type {
  BulkDownloadCompleteEvent,
  BulkDownloadFailedEvent,
  BulkDownloadStartedEvent,
  InvocationCompleteEvent,
  InvocationDenoiseProgressEvent,
  InvocationErrorEvent,
  InvocationStartedEvent,
  ModelInstallCompletedEvent,
  ModelInstallDownloadingEvent,
  ModelInstallErrorEvent,
  ModelLoadCompleteEvent,
  ModelLoadStartedEvent,
  QueueItemStatusChangedEvent,
  SessionCompleteEvent,
} from 'services/events/types';

// Create actions for each socket
// Middleware and redux can then respond to them as needed

export const socketConnected = createAction('socket/socketConnected');

export const socketDisconnected = createAction('socket/socketDisconnected');

export const socketSubscribedSession = createAction<{
  sessionId: string;
}>('socket/socketSubscribedSession');

export const socketUnsubscribedSession = createAction<{ sessionId: string }>('socket/socketUnsubscribedSession');

export const socketInvocationStarted = createAction<{
  data: InvocationStartedEvent;
}>('socket/socketInvocationStarted');

export const socketInvocationComplete = createAction<{
  data: InvocationCompleteEvent;
}>('socket/socketInvocationComplete');

export const socketInvocationError = createAction<{
  data: InvocationErrorEvent;
}>('socket/socketInvocationError');

export const socketGraphExecutionStateComplete = createAction<{
  data: SessionCompleteEvent;
}>('socket/socketGraphExecutionStateComplete');

export const socketGeneratorProgress = createAction<{
  data: InvocationDenoiseProgressEvent;
}>('socket/socketGeneratorProgress');

export const socketModelLoadStarted = createAction<{
  data: ModelLoadStartedEvent;
}>('socket/socketModelLoadStarted');

export const socketModelLoadComplete = createAction<{
  data: ModelLoadCompleteEvent;
}>('socket/socketModelLoadComplete');

export const socketModelInstallDownloading = createAction<{
  data: ModelInstallDownloadingEvent;
}>('socket/socketModelInstallDownloading');

export const socketModelInstallCompleted = createAction<{
  data: ModelInstallCompletedEvent;
}>('socket/socketModelInstallCompleted');

export const socketModelInstallError = createAction<{
  data: ModelInstallErrorEvent;
}>('socket/socketModelInstallError');

export const socketQueueItemStatusChanged = createAction<{
  data: QueueItemStatusChangedEvent;
}>('socket/socketQueueItemStatusChanged');

export const socketBulkDownloadStarted = createAction<{
  data: BulkDownloadStartedEvent;
}>('socket/socketBulkDownloadStarted');

export const socketBulkDownloadComplete = createAction<{
  data: BulkDownloadCompleteEvent;
}>('socket/socketBulkDownloadComplete');

export const socketBulkDownloadError = createAction<{
  data: BulkDownloadFailedEvent;
}>('socket/socketBulkDownloadError');
