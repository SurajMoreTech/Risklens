import {
  collection,
  addDoc,
  getDocs,
  query,
  where,
  orderBy,
  doc,
  setDoc,
  getDoc,
  serverTimestamp,
} from "firebase/firestore";
import { db, isDummyConfig } from "./firebase";

// ── Users Collection (PII) ────────────────────────────────────
export async function saveUserProfile(userId, userData) {
  if (isDummyConfig) return;
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
}

// ── Assessments Collection (Health Data — Separate from PII) ──
export async function saveAssessment(userId, assessmentData) {
  if (isDummyConfig) {
    const list = JSON.parse(sessionStorage.getItem("risklens_demo_assessments") || "[]");
    const newId = "demo-" + Date.now();
    const item = {
      id: newId,
      userId,
      timestamp: new Date().toISOString(),
      ...assessmentData,
      downloaded: false,
    };
    list.push(item);
    sessionStorage.setItem("risklens_demo_assessments", JSON.stringify(list));
    return newId;
  }
  const assessmentRef = await addDoc(collection(db, "assessments"), {
    userId: userId,
    timestamp: serverTimestamp(),
    riskScore: assessmentData.riskScore,
    riskLevel: assessmentData.riskLevel,
    inputs: assessmentData.inputs,
    shapValues: assessmentData.shapValues || {},
    topDrivers: assessmentData.topDrivers || [],
    protectiveFactors: assessmentData.protectiveFactors || [],
    clinicalAction: assessmentData.clinicalAction || "",
    downloaded: false,
  });
  return assessmentRef.id;
}

// ── Get User's Assessment History ─────────────────────────────
export async function getUserAssessments(userId) {
  if (isDummyConfig) {
    const list = JSON.parse(sessionStorage.getItem("risklens_demo_assessments") || "[]");
    return list
      .filter((item) => item.userId === userId)
      .map((item) => ({ ...item, timestamp: new Date(item.timestamp) }))
      .sort((a, b) => b.timestamp - a.timestamp);
  }
  const q = query(
    collection(db, "assessments"),
    where("userId", "==", userId),
    orderBy("timestamp", "desc")
  );
  const snapshot = await getDocs(q);
  return snapshot.docs.map((doc) => ({
    id: doc.id,
    ...doc.data(),
    timestamp: doc.data().timestamp?.toDate?.() || new Date(),
  }));
}

// ── Get Single Assessment ─────────────────────────────────────
export async function getAssessment(assessmentId) {
  if (isDummyConfig) {
    const list = JSON.parse(sessionStorage.getItem("risklens_demo_assessments") || "[]");
    const found = list.find((item) => item.id === assessmentId);
    if (found) return { ...found, timestamp: new Date(found.timestamp) };
    return null;
  }
  const docRef = doc(db, "assessments", assessmentId);
  const docSnap = await getDoc(docRef);
  if (docSnap.exists()) {
    return { id: docSnap.id, ...docSnap.data() };
  }
  return null;
}

