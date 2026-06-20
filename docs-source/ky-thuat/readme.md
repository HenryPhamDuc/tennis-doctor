---
title: "🎾 TENNIS FUTURE LAB — VAULT 3.0"
summary: "[Auto-summary] Vault được tổ chức theo **5 phần** của Framework RPM:"
source_vi: "ky-thuat\readme.md"
translated: "2026-06-20"
translation_mode: "pass"
---



# 🎾 TENNIS FUTURE LAB — VAULT 3.0

## Framework RPM (Reactive Perception-Movement)

> *"Tĩnh lặng bên trong, chủ động bên ngoài"*

## 🌳 Cấu trúc Vault

Vault được tổ chức theo **5 phần** của Framework RPM:

| Phần    | Ký hiệu  | Nội dung                                           | Thư mục                |
| ------- | -------- | -------------------------------------------------- | ---------------------- |
| **I**   | NỀN TẢNG | Motor map, deliberate practice, RPM, Đan Điền      | `01_NenTang/`          |
| **II**  | **R**    | Ball tracking, split step, đọc đối thủ, perception | `02_Pha_R_Nhan_Thuc/`  |
| **III** | **P**    | GRF, kinetic chain, spiral, thả lỏng               | `03_Pha_P_Noi_Luc/`    |
| **IV**  | **M**    | 5R, footwork, stance, run-around, defensive        | `04_Pha_M_Bo_Phap/`    |
| **V**   | TÍCH HỢP | Winning patterns, cognitive load, tự huấn luyện    | `05_Tich_Hop_Thi_Dau/` |

## 🚀 Bắt đầu nhanh

1. **Mới bắt đầu?** → Đọc _C03_Framework_RPM_ trước
2. **Cần lộ trình?** → Xem [_Lo_Trinh_4_Thang](lo-trinh-4-thang.md)
3. **Tìm bài tập?** → Dùng tag `#loại/bai_tap` trong từng chương
4. **Theo dõi tiến bộ?** → Dùng __Template_Nhat_Ky_Tap_ mỗi ngày

## 📊 Tiến độ tổng thể

```dataview
TABLE 
  phần AS "Phần",
  trạng_thái AS "Trạng thái",
  ngày_hoàn_thành AS "Hoàn thành"
FROM #chương
SORT phần ASC, số_chương ASC
```
