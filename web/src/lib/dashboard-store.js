/**
 * dashboard-store.js
 * ──────────────────────────────────────────────────────────────
 * Dedicated module for persisting ALL dashboard data to Firebase
 * Firestore. This is the single source of truth for saving and
 * reading user assessment data.
 *
 * Collections used:
 *   • users/{uid}           — user profile (PII, separate)
 *   • assessments/{auto-id} — individual risk assessments
 *
 * IMPORTANT: If `isDummyConfig` is true (Firebase env vars missing),
 * all writes fall back to sessionStorage and a console warning is
 * emitted so you can immediately see why data isn't persisting.
 * ──────────────────────────────────────────────────────────────
 */

import {
  collection,
  addDoc,
  getDocs,
  deleteDoc,
  query,
  where,
  orderBy,
  doc,
  setDoc,
  getDoc,
  serverTimestamp,
} from "firebase/firestore";
import { db, isDummyConfig } from "./firebase";

// ── Logging Helper ────────────────────────────────────────────
function logDummyWarning(action) {
  console.warn(
    `[dashboard-store] ⚠️ isDummyConfig=true — "${action}" used sessionStorage fallback. ` +
    `Set NEXT_PUBLIC_FIREBASE_* env vars to persist data to Firestore.`
  );
}

// ── SESSION STORAGE FALLBACK (demo / missing config) ──────────
const DEMO_KEY = "risklens_demo_assessments";

function getDemoList() {
  try {
    return JSON.parse(sessionStorage.getItem(DEMO_KEY) || "[]");
  } catch {
    return [];
  }
}

function setDemoList(list) {
  try {
    sessionStorage.setItem(DEMO_KEY, JSON.stringify(list));
  } catch {
    // sessionStorage not available
  }
}

// ═══════════════════════════════════════════════════════════════
//  PUBLIC API
// ═══════════════════════════════════════════════════════════════

/**
 * Save a user profile to Firestore (or update lastLogin if exists).
 * Called automatically by `saveDashboardAssessment`.
 */
export async function saveUserProfile(userId, userData) {
  if (isDummyConfig) {
    logDummyWarning("saveUserProfile");
    return;
  }

  try {
    const userRef = doc(db, "users", userId);
    const existing = await getDoc(userRef);

    if (existing.exists()) {
      await setDoc(userRef, { lastLogin: serverTimestamp() }, { merge: true });
    } else {
      await setDoc(userRef, {
        name: userData.name || "",
        email: userData.email || "",
        phone: userData.phone || "",
        createdAt: serverTimestamp(),
        lastLogin: serverTimestamp(),
      });
    }
  } catch (error) {
    console.error("[dashboard-store] saveUserProfile failed:", error);
    throw error;
  }
}

/**
 * Save a complete assessment to Firestore AND update the user profile.
 * This is the main entry point — call this after ML prediction completes.
 *
 * @param {string} userId        Firebase Auth UID
 * @param {object} assessmentData  { riskScore, riskLevel, inputs, shapValues, topDrivers, protectiveFactors, clinicalAction }
 * @param {object} [userProfile]   { name, email, phone } — optional, saves/updates user doc
 * @returns {string} The new assessment document ID
 */
export async function saveDashboardAssessment(userId, assessmentData, userProfile = null) {
  // ── Demo / dummy fallback ──────────────────────────────────
  if (isDummyConfig) {
    logDummyWarning("saveDashboardAssessment");

    const list = getDemoList();
    const newId = "demo-" + Date.now();
    const item = {
      id: newId,
      userId,
      timestamp: new Date().toISOString(),
      riskScore: assessmentData.riskScore,
      riskLevel: assessmentData.riskLevel,
      inputs: assessmentData.inputs || {},
      shapValues: assessmentData.shapValues || {},
      topDrivers: assessmentData.topDrivers || [],
      protectiveFactors: assessmentData.protectiveFactors || [],
      clinicalAction: assessmentData.clinicalAction || "",
      downloaded: false,
    };
    list.push(item);
    setDemoList(list);
    return newId;
  }

  // ── Real Firestore save ────────────────────────────────────
  try {
    // 1. Save / update user profile
    if (userProfile) {
      await saveUserProfile(userId, userProfile);
    }

    // 2. Save the assessment document
    const assessmentRef = await addDoc(collection(db, "assessments"), {
      userId,
      timestamp: serverTimestamp(),
      riskScore: assessmentData.riskScore,
      riskLevel: assessmentData.riskLevel,
      inputs: assessmentData.inputs || {},
      shapValues: assessmentData.shapValues || {},
      topDrivers: assessmentData.topDrivers || [],
      protectiveFactors: assessmentData.protectiveFactors || [],
      clinicalAction: assessmentData.clinicalAction || "",
      downloaded: false,
    });

    console.log("[dashboard-store] ✅ Assessment saved:", assessmentRef.id);
    return assessmentRef.id;
  } catch (error) {
    console.error("[dashboard-store] saveDashboardAssessment failed:", error);
    throw error;
  }
}

/**
 * Retrieve all assessments for a user, sorted newest-first.
 */
export async function getDashboardHistory(userId) {
  if (isDummyConfig) {
    logDummyWarning("getDashboardHistory");
    const list = getDemoList();
    return list
      .filter((item) => item.userId === userId)
      .map((item) => ({ ...item, timestamp: new Date(item.timestamp) }))
      .sort((a, b) => b.timestamp - a.timestamp);
  }

  try {
    const q = query(
      collection(db, "assessments"),
      where("userId", "==", userId),
      orderBy("timestamp", "desc")
    );
    const snapshot = await getDocs(q);
    return snapshot.docs.map((d) => ({
      id: d.id,
      ...d.data(),
      timestamp: d.data().timestamp?.toDate?.() || new Date(),
    }));
  } catch (error) {
    console.error("[dashboard-store] getDashboardHistory failed:", error);
    throw error;
  }
}

/**
 * Retrieve a single assessment by its document ID.
 */
export async function getDashboardAssessment(assessmentId) {
  if (isDummyConfig) {
    logDummyWarning("getDashboardAssessment");
    const list = getDemoList();
    const found = list.find((item) => item.id === assessmentId);
    if (found) return { ...found, timestamp: new Date(found.timestamp) };
    return null;
  }

  try {
    const docRef = doc(db, "assessments", assessmentId);
    const docSnap = await getDoc(docRef);
    if (docSnap.exists()) {
      return { id: docSnap.id, ...docSnap.data() };
    }
    return null;
  } catch (error) {
    console.error("[dashboard-store] getDashboardAssessment failed:", error);
    throw error;
  }
}

/**
 * Delete an assessment by its document ID.
 */
export async function deleteDashboardAssessment(assessmentId) {
  if (isDummyConfig) {
    logDummyWarning("deleteDashboardAssessment");
    const list = getDemoList().filter((item) => item.id !== assessmentId);
    setDemoList(list);
    return;
  }

  try {
    await deleteDoc(doc(db, "assessments", assessmentId));
    console.log("[dashboard-store] 🗑️ Assessment deleted:", assessmentId);
  } catch (error) {
    console.error("[dashboard-store] deleteDashboardAssessment failed:", error);
    throw error;
  }
}

/**
 * Compute dashboard stats from the assessment list.
 * Call getDashboardHistory first, then pass the result here.
 */
export function getDashboardStats(assessments) {
  const count = assessments.length;
  const latestScore = count > 0 ? assessments[0].riskScore : null;

  let trend = null;
  if (count >= 2) {
    const latest = assessments[0].riskScore;
    const previous = assessments[1].riskScore;
    const diff = latest - previous;
    trend = {
      direction: diff > 0 ? "up" : diff < 0 ? "down" : "same",
      value: Math.abs(diff),
      bad: diff > 0,
    };
  }

  return { count, latestScore, trend };
}
