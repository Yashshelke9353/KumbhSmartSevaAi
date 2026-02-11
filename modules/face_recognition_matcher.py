import os
from pathlib import Path

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    cv2 = None
    np = None

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class FaceRecognitionMatcher:
    """
    Face recognition module to match lost persons with found persons
    Supports both OpenCV and PIL-based image comparison fallback
    """

    def __init__(self, upload_folder=None):

        # Detect project root automatically
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

        # Set upload folder
        if upload_folder:
            self.UPLOAD_FOLDER = upload_folder
        else:
            self.UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "static", "uploads")

        print("📁 Upload folder:", self.UPLOAD_FOLDER)

        self.use_opencv = False
        self.use_pil = PIL_AVAILABLE

        if OPENCV_AVAILABLE:
            try:
                self.face_cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades +
                    "haarcascade_frontalface_default.xml"
                )

                self.orb = cv2.ORB_create(nfeatures=1000)

                self.use_opencv = True
                print("✅ OpenCV initialized")

            except Exception as e:
                print("⚠️ OpenCV init failed:", e)
                self.use_opencv = False

        if not self.use_opencv and not self.use_pil:
            print("⚠️ No image backend available")


    # --------------------------------------------------
    # FACE DETECTION
    # --------------------------------------------------

    def detect_face(self, image_path):

        try:

            if not os.path.exists(image_path):
                print("❌ File not found:", image_path)
                return None, None


            if self.use_opencv:

                img = cv2.imread(image_path)

                if img is None:
                    return self._detect_face_pil(image_path)


                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                gray = cv2.equalizeHist(gray)


                faces = self.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(40, 40)
                )


                if len(faces) == 0:
                    print("⚠️ No face:", os.path.basename(image_path))
                    return gray, img


                faces = sorted(
                    faces,
                    key=lambda x: x[2] * x[3],
                    reverse=True
                )


                x, y, w, h = faces[0]

                pad = int(max(w, h) * 0.15)

                x = max(0, x - pad)
                y = max(0, y - pad)

                w = min(gray.shape[1] - x, w + pad * 2)
                h = min(gray.shape[0] - y, h + pad * 2)


                face = gray[y:y+h, x:x+w]

                print("✅ Face detected:", os.path.basename(image_path))

                return face, img


            return self._detect_face_pil(image_path)


        except Exception as e:
            print("❌ detect_face error:", e)
            return None, None


    def _detect_face_pil(self, image_path):

        try:

            if not self.use_pil:
                return None, None


            img = Image.open(image_path).convert("L")
            img = img.resize((300, 300))

            arr = np.array(img)

            print("✅ PIL loaded:", os.path.basename(image_path))

            return arr, arr


        except Exception as e:
            print("❌ PIL error:", e)
            return None, None


    # --------------------------------------------------
    # FEATURE EXTRACTION
    # --------------------------------------------------

    def extract_features(self, face):

        try:

            if face is None:
                return None, None


            if self.use_opencv and isinstance(face, np.ndarray):

                if len(face.shape) == 3:
                    face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)


                face = cv2.resize(face, (300, 300))


                clahe = cv2.createCLAHE(2.0, (8, 8))
                face = clahe.apply(face)


                kp, desc = self.orb.detectAndCompute(face, None)


                if desc is None:
                    return self._extract_hist(face)


                return kp, desc


            return self._extract_hist(face)


        except Exception as e:
            print("❌ extract_features error:", e)
            return None, None


    def _extract_hist(self, face):

        try:

            if not isinstance(face, np.ndarray):
                return None, None


            if len(face.shape) == 3:
                face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)


            face = cv2.resize(face, (300, 300))


            hist = cv2.calcHist([face], [0], None, [256], [0, 256])
            hist = cv2.normalize(hist, hist).flatten()


            return None, hist


        except Exception as e:
            print("❌ hist error:", e)
            return None, None


    # --------------------------------------------------
    # MATCHING
    # --------------------------------------------------

    def match_faces(self, d1, d2):

        if d1 is None or d2 is None:
            return 0


        if len(d1.shape) == 1:
            return self._match_hist(d1, d2)


        return self._match_orb(d1, d2)


    def _match_hist(self, h1, h2):

        try:

            score = cv2.compareHist(h1, h2, cv2.HISTCMP_CORREL)

            return max(0, min(100, score * 100))


        except:
            return 0


    def _match_orb(self, d1, d2):

        try:

            if len(d1) < 10 or len(d2) < 10:
                return 0


            bf = cv2.BFMatcher(cv2.NORM_HAMMING)


            matches = bf.knnMatch(d1, d2, k=2)


            good = []


            for m, n in matches:

                if m.distance < 0.8 * n.distance:
                    good.append(m)


            if not good:
                return 0


            avg = sum(m.distance for m in good) / len(good)

            sim = max(0, 100 - avg)


            return round(sim, 2)


        except:
            return 0


    # --------------------------------------------------
    # MAIN BATCH MATCHING
    # --------------------------------------------------

    def batch_match_all(self, lost_list, found_list, threshold=40):

        results = {}

        print("\n" + "=" * 60)
        print("🔗 BATCH MATCHING")
        print("=" * 60)


        for lost in lost_list:

            if not lost.get("photo_path"):
                continue


            lost_path = os.path.join(
                self.UPLOAD_FOLDER,
                lost["photo_path"]
            )


            print("🔍 Lost:", lost_path)


            if not os.path.exists(lost_path):
                print("⚠️ Missing:", lost_path)
                continue


            lost_face, _ = self.detect_face(lost_path)

            _, lost_desc = self.extract_features(lost_face)


            if lost_desc is None:
                continue


            matches = []


            for found in found_list:

                if not found.get("photo_path"):
                    continue


                found_path = os.path.join(
                    self.UPLOAD_FOLDER,
                    found["photo_path"]
                )


                if not os.path.exists(found_path):
                    continue


                print("   ↳ Found:", found_path)


                found_face, _ = self.detect_face(found_path)

                _, found_desc = self.extract_features(found_face)


                if found_desc is None:
                    continue


                score = self.match_faces(lost_desc, found_desc)


                print(
                    f"      → {found['id']} = {score}%"
                )


                if score >= threshold:
                    matches.append({
                        "found_id": found["id"],
                        "similarity": score
                    })


            if matches:
                results[lost["id"]] = sorted(
                    matches,
                    key=lambda x: x["similarity"],
                    reverse=True
                )


        print("\n📊 Total matches:",
              sum(len(v) for v in results.values()))

        return results

    def find_matches(self, lost_path, found_list, threshold=40):
        """
        Find matches for a single lost person against a list of found persons
        
        Args:
            lost_path: Path to the lost person's photo
            found_list: List of tuples [(found_id, found_path), ...]
            threshold: Similarity threshold (default 40%)
        
        Returns:
            List of matches with found_id and similarity score
        """
        try:
            print(f"\n🔍 Finding matches for: {lost_path}")
            
            # Detect and extract features from lost person's photo
            lost_face, _ = self.detect_face(lost_path)
            if lost_face is None:
                print("⚠️ No face detected in lost person's photo")
                return []
            
            _, lost_desc = self.extract_features(lost_face)
            if lost_desc is None:
                print("⚠️ Could not extract features from lost person")
                return []
            
            matches = []
            
            # Compare against each found person
            for found_id, found_path in found_list:
                try:
                    if not os.path.exists(found_path):
                        print(f"⚠️ Found person photo not found: {found_path}")
                        continue
                    
                    found_face, _ = self.detect_face(found_path)
                    if found_face is None:
                        print(f"⚠️ No face detected in found person #{found_id}")
                        continue
                    
                    _, found_desc = self.extract_features(found_face)
                    if found_desc is None:
                        print(f"⚠️ Could not extract features from found person #{found_id}")
                        continue
                    
                    score = self.match_faces(lost_desc, found_desc)
                    print(f"   → Found #{found_id}: {score}% similarity")
                    
                    if score >= threshold:
                        matches.append({
                            "found_id": found_id,
                            "similarity": score
                        })
                
                except Exception as e:
                    print(f"⚠️ Error processing found person #{found_id}: {str(e)}")
                    continue
            
            print(f"✓ Found {len(matches)} match(es) above {threshold}% threshold")
            return sorted(matches, key=lambda x: x['similarity'], reverse=True)
        
        except Exception as e:
            print(f"❌ Error in find_matches: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
