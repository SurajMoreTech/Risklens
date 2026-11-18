import { initializeApp, getApps } from "firebase/app";
import { getAuth, setPersistence, browserLocalPersistence } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const isDummyConfig =
  !process.env.NEXT_PUBLIC_FIREBASE_API_KEY ||
  process.env.NEXT_PUBLIC_FIREBASE_API_KEY === "your_api_key_here";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || "dummy_key",
  // Must match the Firebase project's authDomain (e.g. risklens-eb4fo.firebaseapp.com).
  // Google OAuth redirects are registered against this domain in the Google Cloud Console.
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || "dummy.firebaseapp.com",
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "dummy-project",
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || "dummy.appspot.com",
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || "123456789",
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || "1:123456789:web:abcdef",
};

// Initialize Firebase only if real config is provided
let app = null;
let auth = null;
let db = null;

// A promise that resolves once Firebase persistence is configured.
// auth.js awaits this before calling onAuthStateChanged so the
// persistence layer is ready before we read cached auth state.
let authReady = Promise.resolve();

if (!isDummyConfig) {
  app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
  auth = getAuth(app);
  // setPersistence must resolve BEFORE onAuthStateChanged is attached;
  // otherwise IndexedDB may not be ready and the cached user is missed.
  authReady = setPersistence(auth, browserLocalPersistence).catch((err) => {
    console.warn("Firebase persistence setup warning:", err);
  });
  db = getFirestore(app);
}

export { app, auth, db, isDummyConfig, authReady };
