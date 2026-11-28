# 星海のランタンの贈り物箱に贈り物を足す（2026-11-28）。live.json の "gifts" に1件足すだけ。公開は git push（GitHub Pages）。
# アプリは起動のとき live.json を読むので、push してから数分〜1時間ほどで届く（1時間ごとに別の URL で読む）。
#
# 例（個別。お問い合わせの ID を書く。live.json には ID そのものではなく縮めた値が入る）:
#   python tools/add_gift.py --to 9XCY-XEZB --title "お詫び" --msg "ご不便をおかけしました。" --crystals 300 --until 2026-12-31
# 例（全員）:
#   python tools/add_gift.py --to all --title "メンテナンスのお詫び" --msg "..." --crystals 500 --fuel 100 --from 2026-12-01 --until 2026-12-14
#
# 送れる物: --crystals（星晶石・無償） --fuel（燃料。999 まで） --credits（資金） --materials（素材） --medals（星灯祭の灯火）
# 同じ人が同じ ID の贈り物を2回受け取ることはない（ID は自動で G-日付-番号）。期限を過ぎた贈り物は箱に出なくなる。
import argparse, datetime, hashlib, io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIVE = os.path.join(HERE, "..", "live.json")


def inbox_key(customer_id):
    # アプリの GameRules.InboxKey と同じ（SHA-256 の先頭16文字）
    s = "lantern-gift:" + customer_id.strip().upper()
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", required=True, help="お問い合わせの ID（例 9XCY-XEZB）か all")
    ap.add_argument("--title", required=True)
    ap.add_argument("--msg", default="")
    ap.add_argument("--title-en", default="")
    ap.add_argument("--msg-en", default="")
    ap.add_argument("--crystals", type=int, default=0)
    ap.add_argument("--fuel", type=int, default=0)
    ap.add_argument("--credits", type=int, default=0)
    ap.add_argument("--materials", type=int, default=0)
    ap.add_argument("--medals", type=int, default=0, help="星灯祭の灯火")
    ap.add_argument("--from", dest="frm", default="", help="yyyy-MM-dd（省くと今日から）")
    ap.add_argument("--until", default="", help="yyyy-MM-dd（受け取りの期限。省くと30日後）")
    ap.add_argument("--id", default="")
    a = ap.parse_args()
    if a.crystals + a.fuel + a.credits + a.materials + a.medals <= 0:
        sys.exit("送る物がありません（--crystals などを1つ以上）")
    today = datetime.date.today()
    frm = a.frm or today.isoformat()
    until = a.until or (today + datetime.timedelta(days=30)).isoformat()
    for d in (frm, until):
        datetime.date.fromisoformat(d)
    with io.open(LIVE, encoding="utf-8") as f:
        live = json.load(f)
    gifts = live.setdefault("gifts", [])
    gid = a.id
    if not gid:
        base = "G-" + today.strftime("%Y%m%d") + "-"
        n = 1
        while any(g.get("id") == base + "%02d" % n for g in gifts):
            n += 1
        gid = base + "%02d" % n
    if any(g.get("id") == gid for g in gifts):
        sys.exit("同じ ID の贈り物がもうあります: " + gid)
    to = "all" if a.to.strip().lower() == "all" else inbox_key(a.to)
    g = {"id": gid, "to": to, "from": frm, "until": until, "title": a.title, "msg": a.msg}
    if a.title_en: g["titleEn"] = a.title_en
    if a.msg_en: g["msgEn"] = a.msg_en
    for k in ("crystals", "fuel", "credits", "materials", "medals"):
        v = getattr(a, k)
        if v > 0: g[k] = v
    gifts.append(g)
    # 期限が切れて30日たった物は片付ける（受け取りの記録はアプリのセーブにあるので消しても2回は受け取れない）
    cut = (today - datetime.timedelta(days=30)).isoformat()
    live["gifts"] = [x for x in gifts if x.get("until", "9999") >= cut]
    with io.open(LIVE, "w", encoding="utf-8", newline="\n") as f:
        json.dump(live, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("足しました:", gid, "宛先", "全員" if to == "all" else a.to.strip().upper() + " (" + to + ")", until + " まで")


if __name__ == "__main__":
    main()
