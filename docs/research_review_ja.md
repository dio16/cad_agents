# research_review_ja.md

この文書は、原案 `docs/Origen/Design_document_for_a_machine_design_platform.md` の調査レビューを要約した索引です。

## 設計判断の要約

- 自然言語から直接 CAD コードを生成する構成は避ける。LLM は Requirement JSON / Specification JSON / Parametric DSL の構造化計画に限定する。
- CAD 実行と検証は OCCT / FreeCAD / Blender などの決定論的 worker に任せ、失敗や検証結果は機械可読な reason code で返す。
- 正本は Requirement JSON、Specification JSON、Parametric DSL、STEP AP242 / B-Rep、Validation Report に置く。メッシュやレンダリング出力は派生物として扱う。
- 商用API、オンプレLLM、hybrid ルートは data classification と human approval policy で切り替える。

## 参照すべき論点

- CAD agent 研究: パラメトリック操作列、拘束付きスケッチ、Validation feedback loop の有効性
- CAD kernel / worker: OCCT は STEP/XDE/Shape Healing、FreeCAD はヘッドレス Python worker、Blender はレンダリング・メッシュ後処理
- セキュリティ: prompt injection、schema escape、code escape、sensitive information disclosure、improper output handling
- 法規・運用: 個人情報、越境移転、著作権・契約、安全保障貿易管理、該非判定、export-controlled タグ

## 現在の検証状態

- Phase 1 contract/golden pipeline は `bash ./run_cad_agent.sh phase1-contract-test` と `phase1-golden-pipeline` で検証できる。
- Phase 2 Pilot は `bash ./run_cad_agent.sh phase2-pilot-run` で検証できる。
- Native FreeCAD/OCCT や Blender が未導入の環境では、現在のコードは deterministic surrogate adapter を記録して pass 扱いにする。
