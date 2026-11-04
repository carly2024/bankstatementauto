---
name: ledger-diff-highlight
description: 総勘定元帳スプレッドシートの「作業先（最新）」と「元データ」を比べ、変更行は黄色、作業先のみの行は #99c1ff で列U〜AKをハイライトし、元データのみの行は新タブに貼る定型作業。「元データと比べてハイライト」「差分をハイライト」などの依頼で使う。
---

# 総勘定元帳の差分ハイライト

## 依頼の形
- １）作業先データ（最新）: 総勘定元帳スプレッドシート（ID `1rwNt4dlIXb8n95Yrji4yibCDn9fQdSs18kV_jlkmRec`、タブ「総勘定元帳」、sheetId 0）
- ２）元データ: 別の総勘定元帳スプレッドシート。毎回URLが渡されるので、その都度ID・gidを確認する。
- 処理:
  - ２）の情報が１）で変わっている → 1)の列U〜AKを**黄色**（red 1, green 1, blue 0）
  - ２）になく１）にだけある → １）の列U〜AKを **#99c1ff**（red 0.6, green 0.7569, blue 1）
  - ２）にあって１）にない → 新タブ「２）にあり１）にない行」を作り、列Aに**２）の行番号**、列B以降に２）の全37列を**値で**貼る

## 判定基準（ユーザー確認済み 2026-11-04）
- 行の突き合わせ: キー = 取引No(A) | 勘定科目(C) | 同キー内の出現順（COUNTIFの累積）。同じ取引No+勘定科目の行が多数あるため、出現順まで入れる。
- 「変更」の比較は**列A〜Tのみ**。ただし**列R（残高）は除く**（ユーザー指示。行の増減で後続の残高が全部ずれる）。
- 列U〜AKは比較に使わない。１）側にだけ N/A・チェックボックス・請求書リンクが入っていて、ほぼ全行が変更扱いになる。
- 数値は桁区切りカンマを除いて比べる（１）は「9,000」の文字列、２）は数値のことがある）。
- 実績（2026-11-04）: 変更122行、１）のみ2,702行、２）のみ58行、変更なし（残高のみ差を含む）14,119行。

## 手順
1. 両シートの `get_spreadsheet`（fields: sheets.properties, sheets.basicFilter）で行数・列数・フィルタを取得。**１）のフィルタ設定（range、filterSpecs、hiddenValues）を必ず控える**（後で復元する）。先頭数行を `get_values` で見て列構成を確認。列全体を `get_values` で読まない。
2. ２）のタブを `copy_sheet_to_another_spreadsheet` で１）に一時コピーし、タブ名を `tmp` に変更。`clearBasicFilter` し、`appendDimension` で列（約60＋）と行（１）の行数まで）を足す。
3. `tmp` に数式を作る（行2に書いて `copyPaste` PASTE_FORMULA で下に埋める。`update_formulas` で全行は書かない）。
   - ２）側（tmpの行番号＝２）の行番号）: キー、出現順、キー|出現順、比較用の文字列（`SUBSTITUTE(TEXTJOIN("¦",FALSE,A2:Q2,S2:T2),",","")`）。
   - １）側（`'総勘定元帳'!` を参照）: 同じ4つ、`MATCH` で２）の行を引く列、状態（NEW / SAME / CHANGED）。
   - ２）にだけある行: `COUNTIF`/`MATCH` で１）のキー列に無いものを MISSING とする。
   - **列ごとの差を `SUMPRODUCT`＋`VLOOKUP(配列)` で37列ぶん出す式は重くてタイムアウトする**（1回60秒超、サービス不可）。使わない。
4. 結果の行番号は、状態を 0/1/2 にした補助列から `ARRAYFORMULA(TEXTJOIN(",",TRUE,FILTER(行,開始条件)&"-"&FILTER(行,終了条件)))` で連続範囲にまとめて読む（`TEXTJOIN` の外側を `ARRAYFORMULA` で包まないと先頭1件しか返らない）。変更の行番号リストは `FILTER(ROW(..),状態="CHANGED")` の TEXTJOIN でよい。
5. １）の `clearBasicFilter` → `repeatCell`（範囲は列U〜AK = startColumnIndex 20, endColumnIndex 37、fields `userEnteredFormat.backgroundColor`）を連続行ごとに実行 → 控えた設定で `setBasicFilter` を復元。
   - **フィルタ中は `repeatCell` が非表示行に効かないので、必ずフィルタを一度解除する。**
   - `update_spreadsheet` の1回のペイロードは約10KB（requests 40件程度）ずつに分ける。最後のバッチに `setBasicFilter` を入れる。
6. 新タブ「２）にあり１）にない行」: `addSheet`、列Aに行番号（`update_values`）、B1 `=tmp!A1`、B2 `=INDEX(tmp!A$1:A$N,$A2)` を `copyPaste` で B〜AL に展開し、**PASTE_VALUES で値に変換**。日付が数値（シリアル）になるので、日付列（C）に `yyyy/m/d`、金額列（Q・R・S・V）に `#,##0` を設定。1行目を固定・太字。
7. 後片付け: `tmp` を `deleteSheet`。`get_spreadsheet` で１）の行数・列数が元と同じか、フィルタが控えと同じか、非表示行（`rowMetadata.hiddenByFilter` が true）にも色が付いているかを確認。

## 注意
- 貼り付け先の他の列、既存のフィルタ、書式は変えない。
- 一時タブの作業用セルは `tmp` にだけ置く。１）のヘッダー行の空きセルに数式を置かない。
- サービス不可（The service is currently unavailable）は一時的。時間を置いて再実行する。同じバッチを二重に適用しないよう、実行済みか確認してから再送する。
- 報告には、判定基準、各区分の行数、元に戻した内容（一時タブ削除、行数・列数、フィルタ復元）を書く。確認していないことは、確認していないと書く。
