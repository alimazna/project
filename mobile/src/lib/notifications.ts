// Push notification registration for the mobile client.
// Real Expo push delivery requires a development build and physical device;
// in Expo Go or web this degrades gracefully (explicit "skipped"/"failed").

import * as Notifications from 'expo-notifications';
import Constants from 'expo-constants';
import { Platform } from 'react-native';
import { api } from './api';

// AndroidImportance is re-exported by expo-notifications at runtime
// (enum value HIGH = 6, matching NotificationChannelManager.types).
const CHANNEL_IMPORTANCE_HIGH = 6;

let channelCreated = false;

export async function ensureNotificationPermission(): Promise<boolean> {
  if (Platform.OS === 'web') return false;
  const current = await Notifications.getPermissionsAsync();
  if (current.granted) return true;
  const req = await Notifications.requestPermissionsAsync();
  return req.granted;
}

export async function ensureAndroidChannel() {
  if (Platform.OS === 'android' && !channelCreated) {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'Default',
      importance: CHANNEL_IMPORTANCE_HIGH,
    });
    channelCreated = true;
  }
}

// Register this device with the backend. Never throws — the UI degrades
// gracefully with an explicit status instead of crashing.
export async function registerForPush(): Promise<{ status: string; token?: string; reason?: string }> {
  if (Platform.OS === 'web') {
    return { status: 'skipped', reason: 'web platform — no device push' };
  }
  try {
    const granted = await ensureNotificationPermission();
    if (!granted) {
      return { status: 'skipped', reason: 'permission denied' };
    }
    await ensureAndroidChannel();
    const projectId =
      Constants.expoConfig?.extra?.eas?.projectId ??
      Constants.easConfig?.projectId;
    const tokenData = await Notifications.getExpoPushTokenAsync(
      projectId ? { projectId } : undefined,
    );
    const token = tokenData.data;
    await api.registerDevice(Platform.OS, token, 'expo');
    return { status: 'registered', token };
  } catch (err) {
    return { status: 'failed', reason: err instanceof Error ? err.message : String(err) };
  }
}