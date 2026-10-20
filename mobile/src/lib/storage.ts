// Secure token storage for the mobile client.
// Uses expo-secure-store when available (native) to avoid exposing JWTs in
// plaintext AsyncStorage.

import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

const ACCESS_KEY = 'tc_access';
const REFRESH_KEY = 'tc_refresh';

const isWeb = Platform.OS === 'web';

// expo-secure-store has no web implementation (its web shim is empty), so on
// web we fall back to localStorage to keep the mobile web build working.
const webStore = {
  getItem(key: string): string | null {
    try {
      return globalThis.localStorage?.getItem(key) ?? null;
    } catch {
      return null;
    }
  },
  setItem(key: string, value: string) {
    try {
      globalThis.localStorage?.setItem(key, value);
    } catch {
      // ignore quota/private-mode errors
    }
  },
  removeItem(key: string) {
    try {
      globalThis.localStorage?.removeItem(key);
    } catch {
      // ignore
    }
  },
};

export async function saveAuth(access: string, refresh: string) {
  if (isWeb) {
    webStore.setItem(ACCESS_KEY, access);
    webStore.setItem(REFRESH_KEY, refresh);
    return;
  }
  await SecureStore.setItemAsync(ACCESS_KEY, access);
  await SecureStore.setItemAsync(REFRESH_KEY, refresh);
}

export async function loadAuth(): Promise<{ access: string | null; refresh: string | null }> {
  if (isWeb) {
    return { access: webStore.getItem(ACCESS_KEY), refresh: webStore.getItem(REFRESH_KEY) };
  }
  const access = await SecureStore.getItemAsync(ACCESS_KEY);
  const refresh = await SecureStore.getItemAsync(REFRESH_KEY);
  return { access, refresh };
}

export async function clearAuth() {
  if (isWeb) {
    webStore.removeItem(ACCESS_KEY);
    webStore.removeItem(REFRESH_KEY);
    return;
  }
  await SecureStore.deleteItemAsync(ACCESS_KEY);
  await SecureStore.deleteItemAsync(REFRESH_KEY);
}