# 变体字数据构建工具 / Variant Character Data Build Tools

This directory contains **one-time data build scripts** that produce the
runtime artifact `backend/app/services/variant_data/variant_groups_unified.py`
and the runtime CNS JSON files.

These tools are **not needed at runtime** — the platform ships with the
already-built artifact. They are provided here for **reproducibility** and
for users who want to update the variant character database from upstream
sources.

## 数据来源 / Data sources

- **CNS 11643** 全字库 — https://github.com/m80126colin/cns11643 (Public Domain)
- **CBETA 外字** — https://github.com/cbeta-org/cbeta_gaiji (Open License)
- **MOE 异体字** — Taiwan MOE / kcwu/moedict-variants (CC BY-SA)
- **OpenCC** — STCharacters / TSCharacters / HK / JP / TW Variants (Apache 2.0)
- **CHISE IDS** — https://www.chise.org/ (GPL)
- **Unihan** — Unicode Consortium (Unicode License)

## 使用 / Usage

```bash
# from repo root
cd scripts/dev/variant_data_build
python build_unified_dict.py
# output → variant_groups_unified.py (move to backend/app/services/variant_data/)

cd cns11643
python build_cns_data.py
# output → cns_unicode.json, char_attrs.json
# (move to backend/app/services/variant_data/cns11643/)
```

## 韩文藏经 PDF 处理 / Korean Tripitaka PDF processing

`process_korean_pdf.sh` and `korean_tripitaka/` were used to extract variant
character entries from a Korean Tripitaka dictionary PDF. The PDF itself is
not redistributed here (it's published material with copyright); the script
is preserved as a reproducibility reference.
