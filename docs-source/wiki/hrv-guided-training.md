---
title: "HRV-Guided Training"
summary: "[Auto-summary] HRV-Guided Training là training load management system sử dụng **Heart Rate Variability (HRV)** đo buổi sáng như objective indicator của CNS recovery state — thay vì dùng schedule cố định không điều chỉnh theo trạng thái thực tế của player."
source_vi: "wiki\hrv-guided-training.md"
translated: "2026-06-20"
translation_mode: "pass"
---


# HRV-Guided Training

HRV-Guided Training là training load management system sử dụng **Heart Rate Variability (HRV)** đo buổi sáng như objective indicator của CNS recovery state — thay vì dùng schedule cố định không điều chỉnh theo trạng thái thực tế của player.

> "Implement HRV monitoring every morning — a five-minute measurement before rising that provides the most reliable objective indicator of CNS recovery state available without a laboratory. **Let the number guide training intensity that day, not the programme schedule.**"

---

## HRV Là Gì

### Heart Rate Variability — Định Nghĩa
HRV đo **sự biến thiên trong khoảng thời gian giữa các nhịp tim**. Tim không đập đều — khoảng cách giữa hai nhịp liên tiếp dao động. HRV đo sự dao động này.

| HRV cao | HRV thấp |
|---|---|
| Autonomic nervous system trong trạng thái balanced và ready | Sympathetic dominance — stress, fatigue, under-recovery |
| CNS recovered và available for full training | CNS depleted — training will degrade, not build |
| Good heart-brain communication | Disrupted heart-brain communication |

### Tại Sao HRV Là CNS Indicator
CNS recovery state không có visible signal (không có soreness, không có swelling). HRV là **proxy indicator** vì:
- Autonomic nervous system (ANS) directly regulates both HRV và CNS function.
- ANS state reflective of overall neural recovery.
- Low HRV → ANS in sympathetic dominant state → CNS not recovered → performance will be throttled by [Central Governor Model](central-governor-model.md).

---

## Morning Measurement Protocol

### Timing Is Critical
**Measure before rising — lying in bed, immediately after waking**:
- HRV is highly sensitive to position (lying vs. standing → different readings).
- Measurement before any physical activity → pure baseline reading.
- Any movement, stress, or food intake → confounds the reading.

**Duration**: 5 phút minimum recording with chest strap or validated finger sensor.

### Interpretation Framework

| HRV vs Personal Baseline | Training Decision |
|---|---|
| **≥ +10%** above baseline | Full training intensity — potential high-performance day |
| **Within normal range** (±5%) | Planned session proceeds normally |
| **5–10% below** baseline | Reduce intensity — micro-load only, no maximum efforts |
| **>10% below** baseline | **CNS-only day**: Movement, light technical work, no loading. Do not train through this. |

**Personal baseline is key**: Absolute HRV numbers vary hugely between individuals. A reading of 45ms may be excellent for one player and poor for another. Track rolling 7-day average as personal baseline reference.

---

## HRV Decision Tree In Practice

```
Morning HRV measurement
         ↓
Normal or above → Planned training proceeds
         ↓
5-10% below → Micro-load only version of session
         ↓
>10% below → CNS-only day
         ↓
Check: 2+ days consecutive low HRV?
         ↓
Yes → Full rest day + investigate cause (sleep, nutrition, travel, emotional stress)
```

---

## Stacking HRV With Subjective "Despite" Signals

HRV + subjective [CNS Fatigue Signs](../ky-thuat/cns-fatigue-signs.md) together create most complete picture:

| HRV | "Despite" signs | Assessment |
|---|---|---|
| Low | Present | Confirmed CNS Fatigue — rest |
| Normal | Present | Acute stressor — investigate |
| Low | Absent | Systemic fatigue building — monitor, reduce load |
| Normal | Absent | Train fully |

---

## Tournament-Week Application

In tournament week, HRV governs every training decision:
- Match day: No strength training regardless of HRV.
- Day before match: If HRV normal → micro-load activation. If HRV low → rest only.
- Between consecutive matches: If HRV low → only recovery work. If HRV normal → light activation.

This prevents the most common tournament-week error: maintaining normal training intensity because "I feel okay" — when HRV is already trending downward toward performance-limiting CNS Fatigue.

---

## Khái Niệm Liên Quan

- [Explosive Durability](../ky-thuat/explosive-durability.md)
- [CNS Fatigue Signs](../ky-thuat/cns-fatigue-signs.md)
- [Undulating Periodisation](undulating-periodisation.md)
- [Micro-Loading](../ky-thuat/micro-loading.md)
- [Central Governor Model](central-governor-model.md)
- [Coaching Conditioning](../ky-thuat/coaching-conditioning.md)
