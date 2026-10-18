// Secure token storage for the mobile client.
// Uses expo-secure-store when available (native) to avoid exposing JWTs in
// plaintext AsyncStorage.

import * as SecureStore from 'expo-secure-store';

const ACCESS_KEY = 'tc_access';
const REFRESH_KEY = 'tc_refresh';

export async function saveAuth(access: string, refresh: string) {
  await SecureStore.setItemAsync(ACCESS_KEY, access);
  await SecureStore.setItemAsync(REFRESH_KEY, refresh);
}

export async function loadAuth(): Promise<{ access: string | null; refresh: string | null }> {
  const access = await SecureStore.getItemAsync(ACCESS_KEY);
  const refresh = await SecureStore.getItemAsync(REFRESH_KEY);
  return { access, refresh };
}

export async function clearAuth() {
  await SecureStore.deleteItemAsync(ACCESS_KEY);
  await SecureStore.deleteItemAsync(REFRESH_KEY);
}