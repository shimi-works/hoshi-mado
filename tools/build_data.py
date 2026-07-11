# -*- coding: utf-8 -*-
"""HYG星表 + Stellarium modern星座線 から index.html 埋め込み用データを生成する。

入力(同ディレクトリに置く。無ければ自動ダウンロード):
  - hyg.csv          : HYG v4.1 (CC BY-SA 4.0, github.com/astronexus/HYG-Database)
  - modern_index.json: Stellarium modern skyculture (CC BY-SA 4.0, github.com/Stellarium/stellarium)

出力:
  - data_generated.js
  - index.html が存在すれば // ==DATA-START== / ==DATA-END== の間を差し替える
"""
import csv
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
HYG_URL = "https://raw.githubusercontent.com/astronexus/HYG-Database/main/hyg/CURRENT/hygdata_v41.csv"
SKY_URL = "https://raw.githubusercontent.com/Stellarium/stellarium/master/skycultures/modern/index.json"
MAG_LIMIT = 4.5

# 88星座の和名と一言解説（IAU略符 → [和名, 解説]）
JP_CONST = {
    "And": ["アンドロメダ座", "秋の星座。王女アンドロメダ。アンドロメダ銀河が有名。"],
    "Ant": ["ポンプ座", "南天の淡い星座。18世紀に作られた空気ポンプの星座。"],
    "Aps": ["ふうちょう座", "南天深くの小星座。極楽鳥（風鳥）を表す。"],
    "Aqr": ["みずがめ座", "黄道十二星座。水を注ぐ少年ガニメデの姿。"],
    "Aql": ["わし座", "夏の星座。α星アルタイルは七夕の彦星。"],
    "Ara": ["さいだん座", "さそり座の南にある祭壇。神々が誓いを立てた場所。"],
    "Ari": ["おひつじ座", "黄道十二星座。金色の毛皮を持つ空飛ぶ羊。"],
    "Aur": ["ぎょしゃ座", "冬の星座。五角形が目印。α星カペラは黄色く輝く。"],
    "Boo": ["うしかい座", "春の星座。オレンジ色のアルクトゥルスは春の大曲線の要。"],
    "Cae": ["ちょうこくぐ座", "南天の小さく淡い星座。彫刻に使うのみを表す。"],
    "Cam": ["きりん座", "北天の淡い星座。北極星の近くに広がるキリン。"],
    "Cnc": ["かに座", "黄道十二星座。中央のプレセペ星団が見どころ。"],
    "CVn": ["りょうけん座", "春の星座。うしかい座が連れる2匹の猟犬。"],
    "CMa": ["おおいぬ座", "冬の星座。全天一明るい恒星シリウスを持つ。"],
    "CMi": ["こいぬ座", "冬の星座。プロキオンは冬の大三角のひとつ。"],
    "Cap": ["やぎ座", "黄道十二星座。上半身が山羊、下半身が魚の姿。"],
    "Car": ["りゅうこつ座", "南天の星座。カノープスは全天2位の明るさ。見えると長寿の縁起物。"],
    "Cas": ["カシオペヤ座", "北天のW字。一年中北の空に見え、北極星探しの目印。"],
    "Cen": ["ケンタウルス座", "南天の星座。α星は太陽系に最も近い恒星系。"],
    "Cep": ["ケフェウス座", "北天の五角形。カシオペヤの夫、エチオピア王。"],
    "Cet": ["くじら座", "秋の星座。怪物クジラ。変光星ミラが有名。"],
    "Cha": ["カメレオン座", "天の南極近くの小さな星座。"],
    "Cir": ["コンパス座", "南天の小星座。製図用コンパスを表す。"],
    "Col": ["はと座", "冬の南天低くに見える。ノアの箱舟の鳩。"],
    "Com": ["かみのけ座", "春の星座。王妃ベレニケの髪。銀河が多い領域。"],
    "CrA": ["みなみのかんむり座", "いて座の南の小さな冠。"],
    "CrB": ["かんむり座", "春〜夏の星座。7つの星が描く美しい半円の冠。"],
    "Crv": ["からす座", "春の星座。4つの星の台形。アポロンの使いのカラス。"],
    "Crt": ["コップ座", "春の淡い星座。アポロンの聖杯。"],
    "Cru": ["みなみじゅうじ座", "全天最小の星座。南十字星。南天の方角の目印。"],
    "Cyg": ["はくちょう座", "夏の星座。北十字とも。デネブは夏の大三角のひとつ。"],
    "Del": ["いるか座", "夏の小星座。小さなひし形がイルカの体。"],
    "Dor": ["かじき座", "南天の星座。大マゼラン雲の大部分を含む。"],
    "Dra": ["りゅう座", "北天を長々と横たわる竜。かつての北極星トゥバンを持つ。"],
    "Equ": ["こうま座", "全天で2番目に小さい星座。子馬の頭。"],
    "Eri": ["エリダヌス座", "オリオンの足元から南へ流れる大河。河口にアケルナル。"],
    "For": ["ろ座", "南天の淡い星座。化学実験用の炉。"],
    "Gem": ["ふたご座", "黄道十二星座。カストルとポルックスの双子の兄弟。"],
    "Gru": ["つる座", "秋の南天に見える鶴。首をのばした姿。"],
    "Her": ["ヘルクレス座", "夏の星座。英雄ヘラクレス。球状星団M13が有名。"],
    "Hor": ["とけい座", "南天の淡い星座。振り子時計を表す。"],
    "Hya": ["うみへび座", "全天最大の星座。頭から尾まで100度以上に及ぶ。"],
    "Hyi": ["みずへび座", "天の南極近くの小星座。"],
    "Ind": ["インディアン座", "南天の星座。アメリカ先住民の姿。"],
    "Lac": ["とかげ座", "秋の淡い星座。カシオペヤとはくちょうの間。"],
    "Leo": ["しし座", "黄道十二星座。「?」を裏返した獅子の大鎌が目印。"],
    "LMi": ["こじし座", "しし座の頭上の小さな獅子。"],
    "Lep": ["うさぎ座", "オリオンの足元にうずくまる兎。"],
    "Lib": ["てんびん座", "黄道十二星座。正義の女神の天秤。"],
    "Lup": ["おおかみ座", "南天の星座。ケンタウルスに捕らえられた狼。"],
    "Lyn": ["やまねこ座", "北天の淡い星座。「山猫の目がないと見えない」が名の由来。"],
    "Lyr": ["こと座", "夏の星座。ベガは七夕の織姫星。オルフェウスの竪琴。"],
    "Men": ["テーブルさん座", "天の南極近く。南アフリカのテーブル山にちなむ。"],
    "Mic": ["けんびきょう座", "南天の淡い星座。顕微鏡を表す。"],
    "Mon": ["いっかくじゅう座", "冬の大三角の中に潜む一角獣。淡いが天の川が通る。"],
    "Mus": ["はえ座", "みなみじゅうじ座の南の小星座。ハエを表す。"],
    "Nor": ["じょうぎ座", "南天の小星座。製図用の定規。"],
    "Oct": ["はちぶんぎ座", "天の南極を含む星座。八分儀を表す。"],
    "Oph": ["へびつかい座", "夏の星座。大蛇を抱える医神アスクレピオス。"],
    "Ori": ["オリオン座", "冬の王者。三ツ星と大星雲。ベテルギウスとリゲルの対比が見事。"],
    "Pav": ["くじゃく座", "南天の星座。孔雀を表す。"],
    "Peg": ["ペガスス座", "秋の星座。胴体の「秋の四辺形」が秋の星座探しの起点。"],
    "Per": ["ペルセウス座", "秋〜冬の星座。メドゥーサ退治の英雄。変光星アルゴルを持つ。"],
    "Phe": ["ほうおう座", "秋の南天低くの星座。不死鳥フェニックス。"],
    "Pic": ["がか座", "南天の淡い星座。画家の画架を表す。"],
    "Psc": ["うお座", "黄道十二星座。リボンで結ばれた2匹の魚。"],
    "PsA": ["みなみのうお座", "秋の星座。フォーマルハウトは秋の空で唯一の1等星。"],
    "Pup": ["とも座", "南天の星座。アルゴ船の船尾。"],
    "Pyx": ["らしんばん座", "南天の小星座。アルゴ船の羅針盤。"],
    "Ret": ["レチクル座", "南天の小星座。望遠鏡の十字線（レチクル）。"],
    "Sge": ["や座", "夏の小星座。全天で3番目に小さい。愛の矢とも。"],
    "Sgr": ["いて座", "黄道十二星座。南斗六星を含む。天の川銀河の中心方向。"],
    "Sco": ["さそり座", "夏の星座。赤いアンタレスを心臓に持つ見事なS字。"],
    "Scl": ["ちょうこくしつ座", "秋の南天の淡い星座。彫刻家のアトリエ。"],
    "Sct": ["たて座", "夏の小星座。天の川の濃い部分（スクタム雲）がある。"],
    "Ser": ["へび座", "へびつかい座に持たれた蛇。頭と尾で二分される唯一の星座。"],
    "Sex": ["ろくぶんぎ座", "春の淡い星座。観測器具の六分儀。"],
    "Tau": ["おうし座", "黄道十二星座。アルデバランとプレアデス（すばる）を持つ。"],
    "Tel": ["ぼうえんきょう座", "南天の淡い星座。望遠鏡を表す。"],
    "Tri": ["さんかく座", "秋の小星座。細長い三角形。渦巻銀河M33が有名。"],
    "TrA": ["みなみのさんかく座", "南天の明るい三角形。"],
    "Tuc": ["きょしちょう座", "南天の星座。オオハシ（巨嘴鳥）。小マゼラン雲がある。"],
    "UMa": ["おおぐま座", "北斗七星を含む大熊。北の空の道しるべ。"],
    "UMi": ["こぐま座", "天の北極を含む小熊。尾の先が北極星ポラリス。"],
    "Vel": ["ほ座", "南天の星座。アルゴ船の帆。"],
    "Vir": ["おとめ座", "黄道十二星座。スピカは「真珠星」とも呼ばれる純白の1等星。"],
    "Vol": ["とびうお座", "南天の小星座。飛び魚を表す。"],
    "Vul": ["こぎつね座", "夏の淡い星座。はくちょう座の南の小狐。"],
}

# 主要恒星のカタカナ名（HYG proper名 → 表示名）
JP_STAR = {
    "Sirius": "シリウス", "Canopus": "カノープス", "Rigil Kentaurus": "リギル・ケンタウルス",
    "Arcturus": "アルクトゥルス", "Vega": "ベガ", "Capella": "カペラ", "Rigel": "リゲル",
    "Procyon": "プロキオン", "Achernar": "アケルナル", "Betelgeuse": "ベテルギウス",
    "Hadar": "ハダル", "Altair": "アルタイル", "Acrux": "アクルックス",
    "Aldebaran": "アルデバラン", "Antares": "アンタレス", "Spica": "スピカ",
    "Pollux": "ポルックス", "Fomalhaut": "フォーマルハウト", "Deneb": "デネブ",
    "Mimosa": "ミモザ", "Regulus": "レグルス", "Adhara": "アダーラ", "Castor": "カストル",
    "Shaula": "シャウラ", "Gacrux": "ガクルックス", "Bellatrix": "ベラトリックス",
    "Elnath": "エルナト", "Miaplacidus": "ミアプラキドゥス", "Alnilam": "アルニラム",
    "Alnair": "アルナイル", "Alnitak": "アルニタク", "Alioth": "アリオト",
    "Dubhe": "ドゥーベ", "Mirfak": "ミルファク", "Wezen": "ウェズン",
    "Kaus Australis": "カウス・アウストラリス", "Avior": "アヴィオール",
    "Alkaid": "アルカイド", "Sargas": "サルガス", "Menkalinan": "メンカリナン",
    "Atria": "アトリア", "Alhena": "アルヘナ", "Peacock": "ピーコック",
    "Alsephina": "アルセフィナ", "Mirzam": "ミルザム", "Alphard": "アルファルド",
    "Polaris": "ポラリス（北極星）", "Hamal": "ハマル", "Algieba": "アルギエバ",
    "Diphda": "ディフダ", "Mizar": "ミザール", "Nunki": "ヌンキ",
    "Menkent": "メンケント", "Mirach": "ミラク", "Alpheratz": "アルフェラッツ",
    "Rasalhague": "ラサルハゲ", "Kochab": "コカブ", "Saiph": "サイフ",
    "Denebola": "デネボラ", "Algol": "アルゴル", "Tiaki": "ティアキ",
    "Suhail": "スハイル", "Alphecca": "アルフェッカ", "Mintaka": "ミンタカ",
    "Sadr": "サドル", "Eltanin": "エルタニン", "Schedar": "シェダル",
    "Naos": "ナオス", "Almach": "アルマク", "Caph": "カフ", "Izar": "イザール",
    "Dschubba": "ジュバ", "Larawag": "ララワグ", "Merak": "メラク",
    "Ankaa": "アンカ", "Enif": "エニフ", "Scheat": "シェアト", "Sabik": "サビク",
    "Phecda": "フェクダ", "Aludra": "アルドラ", "Markab": "マルカブ",
    "Aljanah": "アルジャナー", "Acrab": "アクラブ", "Zubenelgenubi": "ズベン・エル・ゲヌビ",
    "Zubeneschamali": "ズベン・エス・カマリ", "Unukalhai": "ウヌカルハイ",
    "Sheratan": "シェラタン", "Kraz": "クラズ", "Ruchbah": "ルクバー",
    "Muphrid": "ムフリッド", "Arneb": "アルネブ", "Gienah": "ギェナー",
    "Zosma": "ゾスマ", "Cor Caroli": "コル・カロリ", "Vindemiatrix": "ヴィンデミアトリックス",
    "Megrez": "メグレズ", "Rasalgethi": "ラス・アルゲティ", "Kornephoros": "コルネフォロス",
    "Albireo": "アルビレオ", "Tarazed": "タラゼド", "Alderamin": "アルデラミン",
    "Menkar": "メンカル", "Mira": "ミラ", "Thuban": "トゥバン", "Sadalmelik": "サダルメリク",
    "Sadalsuud": "サダルスウド", "Skat": "スカット", "Meissa": "メイサ",
    "Propus": "プロプス", "Wasat": "ワサト", "Mebsuta": "メブスタ", "Alzirr": "アルジル",
    "Tejat": "テジャト", "Furud": "フルド", "Muscida": "ムスキダ", "Talitha": "タリタ",
    "Tania Australis": "タニア・アウストラリス", "Alula Borealis": "アルラ・ボレアリス",
    "Seginus": "セギヌス", "Nekkar": "ネッカル", "Yed Prior": "イェド・プリオル",
    "Cebalrai": "ケバルライ", "Vrischika": "ヴリシチカ", "Lesath": "レサト",
    "Kaus Media": "カウス・メディア", "Kaus Borealis": "カウス・ボレアリス",
    "Ascella": "アスケラ", "Albaldah": "アルバルダー", "Deneb Algedi": "デネブ・アルゲディ",
    "Dabih": "ダビー", "Algedi": "アルゲディ", "Homam": "ホマム", "Matar": "マタル",
    "Biham": "ビハム", "Algenib": "アルゲニブ", "Alrescha": "アルレシャ",
    "Torcular": "トルクラリス", "Botein": "ボテイン", "Zaurak": "ザウラク",
    "Cursa": "クルサ", "Acamar": "アカマル", "Angetenar": "アンゲテナル",
    "Alsafi": "アルサフィ", "Errai": "エライ", "Alfirk": "アルフィルク",
    "Segin": "セギン", "Achird": "アキルド", "Fulu": "フル", "Navi": "ナヴィ",
    "Miram": "ミラム", "Misam": "ミサム", "Atik": "アティク", "Menkib": "メンキブ",
    "Hassaleh": "ハッサレー", "Almaaz": "アルマーズ", "Haedus": "ハエドゥス",
    "Saclateni": "サクラテニ", "Mahasim": "マハシム", "Nihal": "ニハル",
    "Tabit": "タビト", "Hatysa": "ハティサ", "Muliphein": "ムリフェイン",
    "Azmidi": "アズミディ", "Tureis": "トゥレイス", "Aspidiske": "アスピディスケ",
    "Alsuhail": "アル・スハイル", "Markeb": "マルケブ", "Alsciaukat": "アルシャウカト",
    "Subra": "スブラ", "Rasalas": "ラサラス", "Adhafera": "アダフェラ",
    "Chertan": "チェルタン", "Alkes": "アルケス", "Alchiba": "アルキバ",
    "Minelauva": "ミネラウヴァ", "Heze": "ヘゼ", "Syrma": "シルマ", "Khambalia": "カンバリア",
    "Elgafar": "エルガファル", "Zaniah": "ザニア", "Porrima": "ポリマ", "Auva": "アウヴァ",
    "Brachium": "ブラキウム", "Fang": "ファン", "Iklil": "イクリル", "Jabbah": "ジャバー",
    "Alniyat": "アルニヤト", "Paikauhale": "パイカウハレ", "Xamidimura": "クサミディムラ",
    "Pipirima": "ピピリマ", "Fuyue": "フーユエ", "Yed Posterior": "イェド・ポステリオル",
    "Marsic": "マルシク", "Maasym": "マアシム", "Sarin": "サリン",
    "Athebyne": "アテビュネ", "Aldhibah": "アルディバー", "Grumium": "グルミウム",
    "Giausar": "ギアウサル", "Edasich": "エダシク", "Sham": "シャム",
    "Anser": "アンサー", "Rotanev": "ロタネブ", "Sualocin": "スアロキン",
    "Kitalpha": "キタルファ", "Sadachbia": "サダクビア", "Albali": "アルバリ",
    "Bunda": "ブンダ", "Fumalsamakah": "フム・アル・サマカー", "Revati": "レヴァティ",
    "Titawin": "ティタウィン", "Nembus": "ネンブス", "Mesarthim": "メサルティム",
    "Bharani": "バラニ", "Lilii Borea": "リリイ・ボレア", "Azha": "アザー",
    "Beid": "ベイド", "Keid": "ケイド", "Theemin": "テーミン", "Sceptrum": "スケプトルム",
    "Ain": "アイン", "Chamukuy": "チャムクイ", "Prima Hyadum": "プリマ・ヒアドゥム",
    "Secunda Hyadum": "セクンダ・ヒアドゥム", "Alcyone": "アルキオネ（すばる）",
    "Atlas": "アトラス", "Electra": "エレクトラ", "Maia": "マイア",
    "Merope": "メローペ", "Taygeta": "タイゲタ", "Pleione": "プレイオネ",
    "Celaeno": "ケラエノ", "Asterope": "アステロペ", "Tianguan": "ティアングァン",
    "Alhecka": "アルヘッカ", "Praecipua": "プラエキプア", "Alterf": "アルテルフ",
    "Tarf": "タルフ", "Asellus Borealis": "アセルス・ボレアリス",
    "Asellus Australis": "アセルス・アウストラリス", "Acubens": "アクベンス",
    "Piautos": "ピアウトス", "Copernicus": "コペルニクス", "Nahn": "ナーン",
    "Tegmine": "テグミネ", "Meleph": "メレフ", "Nusakan": "ヌサカン",
    "Alkalurops": "アルカルロプス", "Merga": "メルガ", "Xuange": "シュアンゲ",
    "Thiba": "ティバ", "Alrakis": "アルラキス", "Dziban": "ジバン",
    "Fafnir": "ファフニール", "Alruba": "アルルバ", "Taiyi": "タイイー",
    "Tianyi": "ティアンイー", "Pherkad": "フェルカド", "Yildun": "イルドゥン",
    "Anwar al Farkadain": "アンワル・アル・ファルカダイン",
    "Ahfa al Farkadain": "アフファ・アル・ファルカダイン",
}


def fetch(path, url):
    if not os.path.exists(path):
        print("downloading", url)
        urllib.request.urlretrieve(url, path)


def main():
    hyg_path = os.path.join(HERE, "hyg.csv")
    sky_path = os.path.join(HERE, "modern_index.json")
    fetch(hyg_path, HYG_URL)
    fetch(sky_path, SKY_URL)

    with open(sky_path, encoding="utf-8") as f:
        sky = json.load(f)

    # 星座線: {abbr: [polyline(HIPの列), ...]}
    con_lines = {}
    for c in sky["constellations"]:
        abbr = c["id"].split()[-1]
        con_lines[abbr] = c.get("lines", [])

    missing_jp = sorted(set(con_lines) - set(JP_CONST))
    if missing_jp:
        sys.exit(f"和名未定義の星座: {missing_jp}")

    needed_hips = {hip for lines in con_lines.values() for poly in lines for hip in poly}

    # HYG読み込み。RAは時→度に変換
    by_hip = {}
    stars = []  # [ra, dec, mag, name, con, hip]
    with open(hyg_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["id"] == "0":  # 太陽
                continue
            mag = float(row["mag"])
            hip = int(row["hip"]) if row["hip"] else None
            if mag > MAG_LIMIT and hip not in needed_hips:
                continue
            ra = round(float(row["ra"]) * 15.0, 4)
            dec = round(float(row["dec"]), 4)
            proper = row["proper"].strip()
            name = JP_STAR.get(proper, proper)
            entry = [ra, dec, round(mag, 2), name, row["con"], hip]
            if hip is not None and hip in by_hip:
                # 同一HIPの重複（多重星の成分）は明るい方を残す
                if mag < stars[by_hip[hip]][2]:
                    stars[by_hip[hip]] = entry
                continue
            if hip is not None:
                by_hip[hip] = len(stars)
            stars.append(entry)

    # 明るい順に並べ替え（描画・タップ判定で先頭優先にできる）
    order = sorted(range(len(stars)), key=lambda i: stars[i][2])
    stars = [stars[i] for i in order]
    hip_to_idx = {s[5]: i for i, s in enumerate(stars) if s[5] is not None}

    lost = needed_hips - set(hip_to_idx)
    if lost:
        print(f"警告: HYGに見つからないHIP {len(lost)}件をスキップ: {sorted(lost)[:10]}")

    # 線分を [i1,j1,i2,j2,...] のフラット配列へ
    lines_js = {}
    for abbr, polys in con_lines.items():
        flat = []
        for poly in polys:
            idxs = [hip_to_idx.get(h) for h in poly]
            for a, b in zip(idxs, idxs[1:]):
                if a is not None and b is not None:
                    flat += [a, b]
        lines_js[abbr] = flat

    named = sum(1 for s in stars if s[3])
    print(f"stars={len(stars)} (named={named}), constellations={len(lines_js)}, "
          f"segments={sum(len(v) for v in lines_js.values()) // 2}")

    def star_js(s):
        name = json.dumps(s[3], ensure_ascii=False) if s[3] else "0"
        return f"[{s[0]},{s[1]},{s[2]},{name},\"{s[4]}\"]"

    out = []
    out.append("// ==DATA-START==")
    out.append("// 出典: HYG v4.1 (CC BY-SA 4.0) / Stellarium modern skyculture (CC BY-SA 4.0)")
    out.append("// 生成: tools/build_data.py（手で編集しない）")
    out.append("const STARS=[" + ",".join(star_js(s) for s in stars) + "];")
    out.append("const LINES=" + json.dumps(lines_js, separators=(",", ":")) + ";")
    info = {k: {"jp": v[0], "desc": v[1]} for k, v in JP_CONST.items()}
    out.append("const CONST_INFO=" + json.dumps(info, ensure_ascii=False, separators=(",", ":")) + ";")
    out.append("// ==DATA-END==")
    blob = "\n".join(out)

    gen_path = os.path.join(HERE, "data_generated.js")
    with open(gen_path, "w", encoding="utf-8") as f:
        f.write(blob + "\n")
    print("wrote", gen_path, f"({len(blob) // 1024} KB)")

    html_path = os.path.join(HERE, "..", "index.html")
    if os.path.exists(html_path):
        with open(html_path, encoding="utf-8") as f:
            html = f.read()
        start = html.find("// ==DATA-START==")
        end = html.find("// ==DATA-END==")
        if start == -1 or end == -1:
            sys.exit("index.html にデータマーカーが見つからない")
        html = html[:start] + blob + html[end + len("// ==DATA-END=="):]
        with open(html_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)
        print("patched", os.path.abspath(html_path))


if __name__ == "__main__":
    main()
