# DNA_Mass_Pulse.py

from PIL import Image as PILImage
import numpy as np
import cv2
import random
from typing import List, Tuple, Optional, Literal
from PIL import Image as PILImage, ImageDraw, ImageFilter


class DNAColorEngine:
    """محرك ألوان DNA بسيط للتجربة"""
    def __init__(self):
        self.elements = ["Adenine", "Thymine", "Guanine", "Cytosine"]

    def generate_dnd_seed_color(self, elem: str, variation: float = 0.15, brightness_boost: float = 0.20):
        # ألوان أساسية حسب العنصر
        base = {
            "Adenine": (80, 220, 60),
            "Thymine": (220, 60, 180),
            "Guanine": (60, 180, 220),
            "Cytosine": (200, 140, 40)
        }.get(elem, (120, 200, 100))

        # إضافة تنويع عشوائي
        color = tuple(int(c * (1 + random.uniform(-variation, variation)) * (1 + brightness_boost)) for c in base)
        return tuple(max(0, min(255, c)) for c in color)

# ========================================
#     كلاس : DNA Mass Pulse
# ========================================
class DNA_Mass_Pulse:
    def __init__(self, random_seed: Optional[int] = None):
        """
        تهيئة نظام DNA Mass Pulse

        Parameters:
            random_seed: seed للـ random (اختياري) - لتكرار النتائج
        """
        # تهيئة محرك الألوان
        try:
            self.color_engine = DNAColorEngine()
            if hasattr(self, 'debug_mode') and self.debug_mode:
                print("✅ تم تهيئة DNAColorEngine بنجاح")
        except Exception as e:
            print(f"⚠️ خطأ في تهيئة Color Engine: {e}")
            self.color_engine = None

        # ضبط Random Seed
        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)
            print(f"🔄 تم ضبط Random Seed = {random_seed}")

        self.debug_mode = False

    def create_face_mask_mediapipe(self, image: PILImage.Image, blur_radius: int = 15) -> PILImage.Image:
        """
        إنشاء ماسك دقيق للوجه باستخدام MediaPipe Face Mesh مع refine_landmarks
        """
        try:
            import mediapipe as mp
            import cv2
            from PIL import ImageFilter

            mp_face_mesh = mp.solutions.face_mesh
            mp_drawing = mp.solutions.drawing_utils

            # تحويل PIL إلى OpenCV
            img_cv = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
            h, w = img_cv.shape[:2]

            # إنشاء ماسك أسود
            mask = np.zeros((h, w), dtype=np.uint8)

            with mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,          # ← التحسين المهم: دقة أعلى حول العيون والشفاه
                min_detection_confidence=0.5
            ) as face_mesh:

                results = face_mesh.process(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))

                if results.multi_face_landmarks:
                    for face_landmarks in results.multi_face_landmarks:
                        # طريقة 1: استخدام Face Oval (أفضل للوجه ككل)
                        oval_points = []
                        for idx in mp_face_mesh.FACEMESH_FACE_OVAL:
                            pt1 = face_landmarks.landmark[idx[0]]
                            oval_points.append([int(pt1.x * w), int(pt1.y * h)])

                        points = np.array(oval_points, dtype=np.int32)
                        cv2.fillPoly(mask, [points], 255)

                        # طريقة 2: تكميل بـ Tessellation لتغطية أفضل (اختياري)
                        # mp_drawing.draw_landmarks(
                        #     image=mask,
                        #     landmark_list=face_landmarks,
                        #     connections=mp_face_mesh.FACEMESH_TESSELATION,
                        #     landmark_drawing_spec=None,
                        #     connection_drawing_spec=mp_drawing.DrawingSpec(color=(255,255,255), thickness=2)
                        # )

                    print("✅ تم كشف الوجه بدقة عالية باستخدام MediaPipe (refine_landmarks=True)")
                else:
                    print("⚠️ لم يتم كشف وجه واضح → استخدام ماسك بيضاوي احتياطي")
                    # Fallback: بيضاوي مركزي
                    fallback = PILImage.new("L", (w, h), color=0)
                    draw = ImageDraw.Draw(fallback)
                    draw.ellipse([w*0.20, h*0.15, w*0.80, h*0.85], fill=255)
                    return fallback.filter(ImageFilter.GaussianBlur(radius=blur_radius))

            # تحويل إلى PIL + نعومة الحواف
            mask_pil = PILImage.fromarray(mask).convert("L")
            mask_pil = mask_pil.filter(ImageFilter.GaussianBlur(radius=blur_radius))

            return mask_pil

        except ImportError:
            print("⚠️ MediaPipe غير مثبت → استخدام ماسك بيضاوي بسيط")
            w, h = image.size
            mask = PILImage.new("L", (w, h), color=0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse([w*0.22, h*0.18, w*0.78, h*0.82], fill=255)
            return mask.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        except Exception as e:
            print(f"⚠️ خطأ في MediaPipe: {e} → استخدام ماسك بسيط")
            w, h = image.size
            mask = PILImage.new("L", (w, h), color=255)
            return mask

    def create_dna_pulse_animation(self,
                                  base_img: PILImage.Image,
                                  mask: PILImage.Image,
                                  output_folder: str,
                                  timestamp: str,
                                  frames: int = 45,
                                  pulse_steps_per_frame: int = 1,
                                  save_video: bool = True) -> None:
        """
        إنشاء أنيميشن لنبض DNA (30-60 إطار)
        - يحفظ كل إطار كصورة منفصلة
        - يمكن تحويله إلى فيديو MP4
        """
        print(f"\n🎞️ بدء إنشاء أنيميشن DNA Pulse ({frames} إطار)...")

        os.makedirs(output_folder, exist_ok=True)
        frame_folder = os.path.join(output_folder, f"DNA_Animation_{timestamp}")
        os.makedirs(frame_folder, exist_ok=True)

        frames_list = []

        for i in range(frames):
            progress = i / (frames - 1) if frames > 1 else 0

            # تعديل قوة النبض حسب الإطار (يبدأ قوي ثم يهدأ)
            current_pulse_steps = max(3, int(8 * (1 - progress * 0.6)))
            current_hue_std = 7.0 + (4.0 * (1 - progress))
            current_sat = 0.25 + (0.20 * (1 - progress))
            current_val = 0.15 + (0.12 * (1 - progress))

            # تطبيق النبض على الإطار الحالي
            frame = self.dna_full_pulse(
                base_img,
                mask,
                pulse_steps=current_pulse_steps,
                hue_std_base=current_hue_std,
                sat_boost=current_sat,
                val_boost=current_val,
                debug=False
            )

            # حفظ الإطار
            frame_path = os.path.join(frame_folder, f"frame_{i:04d}.png")
            frame.save(frame_path)
            frames_list.append(frame_path)

            if i % 10 == 0 or i == frames-1:
                print(f"   → تم حفظ الإطار {i+1}/{frames}")

        print(f"✅ تم حفظ {frames} إطار في المجلد:\n   {frame_folder}")

        # ====================== تحويل إلى فيديو ======================
        if save_video:
            try:
                video_path = os.path.join(output_folder, f"DNA_Pulse_Animation_{timestamp}.mp4")
                self._frames_to_video(frames_list, video_path, fps=15)
                print(f"🎥 تم إنشاء الفيديو بنجاح:")
                print(f"   {video_path}")
            except Exception as e:
                print(f"⚠️ فشل في إنشاء الفيديو: {e}")
                print("   يمكنك تحويل الصور يدويًا باستخدام FFmpeg أو أي برنامج")

    def _frames_to_video(self, frame_paths: list, output_video_path: str, fps: int = 15):
        """تحويل قائمة الصور إلى فيديو MP4 باستخدام OpenCV"""
        import cv2

        if not frame_paths:
            return

        first_frame = cv2.imread(frame_paths[0])
        height, width, _ = first_frame.shape

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

        for frame_path in frame_paths:
            img = cv2.imread(frame_path)
            video.write(img)

        video.release()

    def run_dna_examples(self,
                        base_img: PILImage.Image,
                        output_folder: str,
                        timestamp: str) -> None:
        """
        تشغيل 5 أمثلة مختلفة من تأثيرات DNA على وجه بشري (مع ماسك محسن)
        """
        print("\n🎯 بدء تنفيذ الـ 5 أمثلة على وجه بشري (MediaPipe Face Mesh محسن)...\n")

        # إنشاء الماسك الدقيق
        mask = self.create_face_mask_mediapipe(base_img, blur_radius=12)

        # الـ 5 أمثلة (مخصصة للوجوه)
        examples = [
            {"name": "01_DNA_Gradient_Face",      "blend_mode": "dna_gradient", "opacity": 0.45, "pulse_steps": 6,  "hue_std": 7.8,  "sat_boost": 0.30, "val_boost": 0.18, "desc": "تدرج DNA كلاسيكي"},
            {"name": "02_DNA_Strands_Face",       "blend_mode": "strand",       "opacity": 0.50, "pulse_steps": 7,  "hue_std": 8.5,  "sat_boost": 0.35, "val_boost": 0.15, "desc": "خيوط DNA بيولوجية"},
            {"name": "03_Neon_Edge_Glow_Face",    "blend_mode": "edge_glow",    "opacity": 0.58, "pulse_steps": 8,  "hue_std": 11.0, "sat_boost": 0.48, "val_boost": 0.28, "desc": "توهج نيوني قوي"},
            {"name": "04_Subtle_Balanced_Face",   "blend_mode": "balanced",     "opacity": 0.38, "pulse_steps": 5,  "hue_std": 5.5,  "sat_boost": 0.22, "val_boost": 0.12, "desc": "تأثير خفيف أنيق"},
            {"name": "05_Hybrid_DNA_Face",        "blend_mode": "edge_glow",    "opacity": 0.53, "pulse_steps": 9,  "hue_std": 10.2, "sat_boost": 0.42, "val_boost": 0.25, "desc": "هجين قوي"},
        ]

        for i, ex in enumerate(examples, 1):
            print(f"🔬 المثال {i}/5 : {ex['name']}")
            print(f"   → {ex['desc']}")

            dna_layer = self.add_dna_colored_layers(
                net_image=base_img,
                mask=mask,
                blend_mode=ex["blend_mode"],
                opacity=ex["opacity"],
                edge_boost=0.90,
                debug=False
            )

            result = self.dna_full_pulse(
                base_img,
                mask,
                pulse_steps=ex["pulse_steps"],
                hue_std_base=ex["hue_std"],
                sat_boost=ex["sat_boost"],
                val_boost=ex["val_boost"],
                debug=False
            )

            final = PILImage.alpha_composite(result.convert("RGBA"), dna_layer)

            filename = f"{ex['name']}_{timestamp}.png"
            save_path = os.path.join(output_folder, filename)
            final.save(save_path)

            print(f"   ✅ تم حفظ: {filename}\n")

        final.save(os.path.join(output_folder, "DNA_Pulse_Result_Latest.png"))
        print("📌 تم حفظ DNA_Pulse_Result_Latest.png بنجاح")

    # ==================== الدالة الأساسية (محسنة قليلاً) ====================
    def add_dna_colored_layers(
        self,
        net_image: PILImage.Image,
        mask: PILImage.Image,
        base_colors: Optional[List[Tuple[int, int, int]]] = None,
        blend_mode: Literal["dna_gradient", "strand", "balanced", "edge_glow"] = "dna_gradient",
        opacity: float = 0.45,
        edge_boost: float = 0.85,
        use_color_engine: bool = True,
        debug: bool = False,
    ) -> PILImage.Image:
        """
        إضافة طبقات لونية DNA-inspired (نسخة محسنة وآمنة 2026)
        """
        if debug:
            print("\n" + "="*75)
            print("بدء add_dna_colored_layers - النسخة الآمنة")
            print("="*75)

        # ====================== 1. التحضير ======================
        w, h = mask.size
        mask_arr = np.array(mask.convert("L"), dtype=np.float32) / 255.0
        mask_arr = np.expand_dims(mask_arr, axis=-1)

        # ====================== 2. توليد الألوان (مع حماية كاملة + توافق مع Pylance) ======================
        if base_colors is None:
            if (hasattr(self, 'color_engine') and
                self.color_engine is not None and
                use_color_engine):

                try:
                    elem = random.choice(self.color_engine.elements)
                    pos_raw = self.color_engine.generate_dnd_seed_color(
                        elem, variation=0.15, brightness_boost=0.20
                    )

                    # تحويل صريح إلى Tuple ثابت الحجم (3 عناصر) - هذا يحل المشكلة
                    pos: Tuple[int, int, int] = (int(pos_raw[0]), int(pos_raw[1]), int(pos_raw[2]))

                    neg_list = [max(0, int(c * 0.52 - 28)) for c in pos]
                    neg: Tuple[int, int, int] = (neg_list[0], neg_list[1], neg_list[2])

                    base_colors = [pos, neg]

                    if debug:
                        print(f"→ DNA Element: {elem} | Positive: {pos} | Negative: {neg}")

                except Exception as e:
                    if debug:
                        print(f"⚠️ خطأ في Color Engine: {e} → استخدام ألوان افتراضية")
                    base_colors = [(55, 195, 85), (175, 55, 125)]
            else:
                base_colors = [(55, 195, 85), (175, 55, 125)]

        # ====================== حماية نهائية ======================
        if base_colors is None or len(base_colors) == 0:
            base_colors = [(55, 195, 85), (175, 55, 125)]

        # ====================== تحويل إلى numpy (آمن تمامًا) ======================
        pos_color = np.array(base_colors[0], dtype=np.float32)
        neg_color = np.array(
            base_colors[1] if len(base_colors) > 1 else base_colors[0],
            dtype=np.float32
        )

        if debug:
            print(f"→ تم استخدام ألوان: Pos={base_colors[0]} | Neg={base_colors[1] if len(base_colors) > 1 else base_colors[0]}")

        # ====================== 3. استخراج الحواف ======================
        net_arr = np.array(net_image.convert("RGB"))
        gray = cv2.cvtColor(net_arr, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 40, 150).astype(np.float32) / 255.0

        # ====================== 4. إنشاء الطبقة اللونية ======================
        layer = np.zeros((h, w, 4), dtype=np.float32)

        if blend_mode == "dna_gradient":
            gradient = np.linspace(0.0, 1.0, w)
            gradient = np.tile(gradient, (h, 1))
            color_map = gradient[..., None] * pos_color + (1.0 - gradient[..., None]) * neg_color
            layer[..., :3] = color_map * mask_arr[..., 0, None]

        elif blend_mode == "strand":
            y = np.linspace(0, 1, h)[:, None]
            strand = np.sin(y * 12) * 0.5 + 0.5
            strand = np.tile(strand, (1, w))
            color_map = strand[..., None] * pos_color + (1.0 - strand[..., None]) * neg_color
            layer[..., :3] = color_map * mask_arr[..., 0, None]

        elif blend_mode == "balanced":
            ratio = 0.52
            color_map = ratio * pos_color + (1.0 - ratio) * neg_color
            layer[..., :3] = color_map * mask_arr[..., 0, None]

        elif blend_mode == "edge_glow":
            intensity = np.clip(mask_arr[..., 0] ** 1.35, 0.0, 1.0)
            color_map = 0.65 * pos_color + 0.35 * neg_color
            layer[..., :3] = color_map * intensity[..., None]
            # إضاءة الحواف داخل الماسك فقط
            layer[..., :3] += (edges[..., None] * edge_boost * 55) * mask_arr[..., 0, None]

        else:
            raise ValueError(f"blend_mode غير مدعوم: {blend_mode}")

        # ====================== 5. Alpha + تعزيز الحواف ======================
        alpha = mask_arr[..., 0] * 255 * opacity
        alpha = np.clip(alpha + (edges * 95 * mask_arr[..., 0]), 0, 255)

        layer[..., 3] = alpha
        layer[..., :3] = np.clip(layer[..., :3], 0, 255)

        # ====================== 6. التحويل النهائي ======================
        layer = np.round(layer).astype(np.uint8)
        dna_layer = PILImage.fromarray(layer, mode="RGBA")

        if debug:
            print(f"→ Blend Mode : {blend_mode}")
            print(f"→ Opacity    : {opacity:.2f} | Edge Boost : {edge_boost:.2f}")
            print("✅ تم إنشاء طبقة DNA Colored Layers بنجاح")
            print("="*75 + "\n")

        return dna_layer

    # ====================== 5. إسقاط نبضي DNA-inspired Coloring ======================

    def dna_color_pulse(
        self,
        img: PILImage.Image,
        mask: PILImage.Image,
        pulse_steps: int = 6,
        hue_std_base: float = 8.0,
        positive_sat_boost: float = 0.28,
        negative_sat_suppress: float = 0.22,
        factor_decay: float = 0.60,
        debug: bool = False,
    ) -> PILImage.Image:
        """
        نبض لوني DNA-inspired بسيط (Hue + Saturation فقط)
        بدون تغيير Value - مناسب لتأثيرات خفيفة وسريعة.
        """
        if debug:
            print("\n" + "="*70)
            print("🌊 بدء dna_color_pulse - النبض البسيط (Hue + Sat فقط)")
            print("="*70)

        # ====================== 1. التحضير ======================
        rgb = np.array(img.convert("RGB"), dtype=np.float32)
        mask_arr = np.expand_dims(
            np.array(mask.convert("L"), dtype=np.float32) / 255.0,
            axis=-1
        )

        if debug:
            print(f"  حجم الصورة: {rgb.shape} | خطوات: {pulse_steps} | decay: {factor_decay:.3f}")

        # ====================== 2. حلقة النبض ======================
        for step in range(pulse_steps):
            factor = max(0.0, 1.0 - (step / pulse_steps) * factor_decay)

            if debug:
                print(f"  → Step {step+1:2d}/{pulse_steps} | factor = {factor:.4f}")

            # طفرة Hue (DNA-like mutation)
            hue_shift = np.random.normal(0, hue_std_base * factor, size=rgb.shape[:2])
            hue_shift = hue_shift[..., None] * mask_arr   # جعلها (H, W, 1)

            # تعديل التشبع
            sat_boost = 1.0 + positive_sat_boost * factor * mask_arr
            sat_suppress = 1.0 - negative_sat_suppress * factor * mask_arr
            sat_mult = sat_boost * sat_suppress
            sat_mult = np.clip(sat_mult, 0.15, 2.8)

            # تحويل إلى HSV
            hsv = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)

            # تطبيق التغييرات
            hsv[..., 0] = (hsv[..., 0] + hue_shift[..., 0]) % 180
            hsv[..., 1] = np.clip(hsv[..., 1] * sat_mult, 0, 255)

            # العودة إلى RGB
            rgb = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32)

            if debug:
                print(f"    Hue shift mean: {hue_shift.mean():.3f} | "
                      f"Sat mult mean: {sat_mult.mean():.3f}")

        # ====================== 3. النتيجة النهائية ======================
        rgb_out = np.clip(rgb, 0, 255).astype(np.uint8)
        result = PILImage.fromarray(rgb_out)

        if debug:
            print("✅ انتهى dna_color_pulse بنجاح\n" + "="*70 + "\n")

        return result

    def dna_full_pulse(
        self,
        img: PILImage.Image,
        mask: PILImage.Image,
        pulse_steps: int = 6,
        hue_std_base: float = 7.2,
        sat_boost: float = 0.27,
        sat_suppress: float = 0.19,
        val_boost: float = 0.15,
        factor_decay: float = 0.63,
        enable_hue: bool = True,
        enable_sat: bool = True,
        enable_val: bool = True,
        clip_hue: bool = True,
        debug: bool = True,
    ) -> PILImage.Image:
        """
        نبض لوني DNA-inspired كامل ومحسن (الإصدار 2.1)

        يقوم بتطبيق طفرة لونية بيولوجية (Hue) + تعديل التشبع والسطوع
        بشكل تدريجي مع تناقص التأثير عبر الخطوات.
        """
        if debug:
            print("\n" + "="*75)
            print("🚀 بدء dna_full_pulse v2.1 - النبض اللوني DNA")
            print("="*75)
            print(f"الإعدادات: steps={pulse_steps} | decay={factor_decay:.3f} | "
                    f"Hue={enable_hue} | Sat={enable_sat} | Val={enable_val}")

        # ====================== 1. التحضير ======================
        # تحويل الصورة والماسك إلى مصفوفات
        rgb = np.array(img.convert("RGB"), dtype=np.float32)
        mask_arr = np.expand_dims(
            np.array(mask.convert("L"), dtype=np.float32) / 255.0,
            axis=-1
        )

        # تحويل واحد فقط إلى HSV (أفضل للأداء)
        hsv = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)

        if debug:
            print(f"  حجم الصورة: {rgb.shape} | خطوات النبض: {pulse_steps}")

        # ====================== 2. حلقة النبض الرئيسية ======================
        for step in range(pulse_steps):
            factor = max(0.0, 1.0 - (step / pulse_steps) * factor_decay)

            if debug:
                print(f"\n  → Step {step+1:2d}/{pulse_steps} | factor = {factor:.4f}")

            # --- 2.1 طفرة Hue (الطفرة الجينية) ---
            if enable_hue:
                # توليد طفرة عشوائية معتمدة على factor
                hue_shift = np.random.normal(0, hue_std_base * factor, size=hsv.shape[:2])
                hsv[..., 0] += hue_shift * mask_arr[..., 0]

                if clip_hue:
                    hsv[..., 0] = np.mod(hsv[..., 0], 180.0)

                if debug:
                    print(f"    Hue  → min: {hsv[...,0].min():5.1f} | "
                            f"max: {hsv[...,0].max():5.1f} | "
                            f"mean: {hsv[...,0].mean():5.1f}")

            # --- 2.2 تعديل التشبع (Saturation) ---
            if enable_sat:
                # دمج الزيادة والكبت في معامل واحد
                sat_mult = 1.0 + (sat_boost - sat_suppress) * factor * mask_arr[..., 0]
                sat_mult = np.clip(sat_mult, 0.12, 2.9)   # منع القيم المتطرفة

                hsv[..., 1] *= sat_mult
                hsv[..., 1] = np.clip(hsv[..., 1], 0, 255)

                if debug:
                    print(f"    Sat  → mean: {hsv[...,1].mean():5.1f} | "
                        f"range: [{hsv[...,1].min():.1f}, {hsv[...,1].max():.1f}]")

            # --- 2.3 تعديل السطوع (Value) ---
            if enable_val:
                val_mult = 1.0 + val_boost * factor * mask_arr[..., 0]
                val_mult = np.clip(val_mult, 0.65, 1.50)

                hsv[..., 2] *= val_mult
                hsv[..., 2] = np.clip(hsv[..., 2], 0, 255)

                if debug:
                    print(f"    Val  → mean: {hsv[...,2].mean():5.1f} | "
                            f"range: [{hsv[...,2].min():.1f}, {hsv[...,2].max():.1f}]")

        # ====================== 3. التحويل النهائي ======================
        # العودة من HSV إلى RGB
        rgb_out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
        rgb_out = np.clip(rgb_out, 0, 255).astype(np.uint8)

        result = PILImage.fromarray(rgb_out)

        if debug:
            print("\n✅ انتهى dna_full_pulse بنجاح (v2.1)")
            print("="*75 + "\n")

        return result

# ====================== التنفيذ الرئيسي ======================
if __name__ == "__main__":
    dna = DNA_Mass_Pulse()

    print("🚀 بدء DNA Mass Pulse Demo - تأثيرات على الوجوه...\n")

    # ====================== إعداد المسار التلقائي ======================
    import os
    from datetime import datetime

    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_folder = os.path.join(current_dir, "DNA Mass Pulse - Out Puts")
    os.makedirs(output_folder, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ====================== تحميل الصورة أو إنشاء صورة تجريبية ======================
    try:
        # محاولة تحميل صورة وجه حقيقية
        base_img = PILImage.open("input.jpg").convert("RGB").resize((800, 800))
        print("✅ تم تحميل صورة input.jpg بنجاح")

    except FileNotFoundError:
        print("⚠️ ملف input.jpg غير موجود → إنشاء صورة تجريبية (وجه افتراضي)")

        # إنشاء صورة خلفية داكنة مناسبة للوجوه
        base_img = PILImage.new("RGB", (800, 800), color=(18, 22, 48))

        # إضافة تدرج خفيف لإعطاء عمق
        draw_bg = ImageDraw.Draw(base_img)
        for i in range(800):
            intensity = int(18 + (i / 800) * 40)
            draw_bg.line([(0, i), (800, i)], fill=(intensity, intensity//2 + 10, 55))

        print("   → تم إنشاء صورة تجريبية داكنة")

    # ====================== تشغيل الـ 5 أمثلة على الوجه ======================
    print("🧬 جاري إنشاء ماسك الوجه باستخدام MediaPipe...\n")

    dna.run_dna_examples(
        base_img=base_img,
        output_folder=output_folder,
        timestamp=timestamp
    )

    # ====================== الرسالة النهائية ======================
    print("\n" + "="*85)
    print("🎉 تم تنفيذ الـ 5 أمثلة بنجاح على الوجه!")
    print(f"📁 المجلد: {output_folder}")
    print("📄 تم حفظ 5 صور مختلفة + DNA_Pulse_Result_Latest.png")
    print("="*85)

    # فتح آخر صورة تلقائيًا
    try:
        latest_path = os.path.join(output_folder, "DNA_Pulse_Result_Latest.png")
        final = PILImage.open(latest_path)
        final.show()
        print(f"🖼️ تم فتح الصورة: DNA_Pulse_Result_Latest.png")
    except Exception as e:
        print(f"⚠️ تعذر فتح الصورة: {e}")
