// Firebase client was removed from the project.
// This file remains as a small placeholder to avoid import errors from
// older branches. Do not add Firebase logic here.

export const isMessagingAvailable = async () => false;
export const ensureMessagingInit = async () => null;
export const getNotificationPermission = () => 'unsupported';
export const enableNotificationsAndRegisterToken = async () => ({ granted: false });
export const hasFcmTokenCached = () => false;
export const useAuthEmulatorIfEnabled = () => false;
export const signOutWeb = async () => {};
