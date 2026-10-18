# New outfits + fabrics for the 17 main characters of "เลือกนักมักได้แร่" -> cc5_jobs\redress_luek.json
import json, os
from fabric_onto_garment import make
L = os.environ["LOCALAPPDATA"]
cat = json.load(open(os.path.join(L, "Tidmunz Studio", "cc5_catalog", "catalog.json"), encoding="utf-8"))["items"]
FAB = os.path.join(os.environ["USERPROFILE"], "Desktop", "ลายผ้า")
JOBS = os.path.join(L, "Tidmunz Studio", "snapgen_data", "cc5_jobs")
R = "G:\\คอมพิวเตอร์เครื่องอื่นๆ\\คอมพิวเตอร์ของฉัน\\โมชั่น\\Prop ของใช้ต่างๆ\\เสื้อผ้า-ทรงผม\\"
MO, RC = R + "!Converted STUFFS\\Male Outfits\\", R + "Reallusion Custom\\Cloth\\"
def c(i): return cat[i]["path"]
SH = {"flip": MO + "Oahu\\Flip Flops.ccShoes", "dash": MO + "Dash\\Shoes 01.ccShoes", "sand2": MO + "Oahu\\Sandals 02.ccShoes",
      "cas1": MO + "Casual 01\\Shoes.ccShoes", "cas3": MO + "Casual 03\\Shoes.ccShoes"}
PINK = RC + "Shirts\\Professional Outfit\\Open collar short sleeves shirt\\Open_collar_short_sleeves_shirt_C.ccCloth"
SKIRT = RC + "Pants\\Pants(28).ccCloth"
TROUSER_F = RC + "Others\\กางเกงขายาว.ccCloth"
# job: [(item path, fabric or None), ...]  lower first, then upper, then shoes
P = {
 "wina_young":    [(SKIRT, "pha_sin_stripe"), (c("3ccaca6ac31b9d88"), "floral_red"), (SH["dash"], None)],
 "wina_58":       [(c("55e2cddc2cdf20af"), "pha_thung_batik"), (c("fc523c7f4baedf38"), "floral_maroon"), (SH["flip"], None)],
 "lamduan":       [(c("185f00bd16da529d"), "plaid_brown"), (c("8ee781090883e14f"), "floral_brown"), (SH["flip"], None)],
 "lamduan_old":   [(c("e2f30a0dea8cb107"), None), (SH["sand2"], None)],
 "wandee":        [(SKIRT, "pha_thung_green"), (c("193290aa7962a103"), None), (SH["dash"], None)],
 "wandee_old":    [(c("55e2cddc2cdf20af"), "cotton_rust"), (PINK, "floral_blue_faded"), (SH["flip"], None)],
 "pranee":        [(TROUSER_F, "cotton_khaki"), (PINK, "floral_green"), (SH["flip"], None)],
 "pranee_58":     [(c("04f1fc91b6e72811"), None), (SH["sand2"], None)],
 "mill_daughter": [(SKIRT, "silk_mudmee"), (c("fc523c7f4baedf38"), "cotton_cream"), (SH["dash"], None)],
 "ratree":        [(c("185f00bd16da529d"), "floral_maroon"), (c("3ccaca6ac31b9d88"), "cotton_cream"), (SH["dash"], None)],
 "soldier":       [(MO + "Casual 04\\Pants.ccCloth", None), (c("b67f5d51ef1ed00d"), "cotton_olive"), (SH["cas3"], None)],
 "soldier_old":   [(MO + "Old\\Pants.ccCloth", None), (c("a5f7c27ce9faee09"), None), (SH["sand2"], None)],
 "somchai":       [(MO + "Blood Hunter\\Pants.ccCloth", None), (c("60ceb651cbae9f85"), "cotton_khaki"), (SH["cas1"], None)],
 "somchai_old":   [(c("1790c8ff5e53a95a"), None), (c("753ea7"[:6] and "753ea73da4c3ebe5"), "plaid_red"), (SH["flip"], None)],
 "pranee_husband":[(c("0ce08ad1088368ab"), None), (c("189a5b74d6cc78d4"), "mohom"), (SH["flip"], None)],
 "nai_chai":      [(MO + "Billybob\\Pants.ccCloth", None), (c("c0f6931369cdc69d"), "stripe_grey"), (SH["cas1"], None)],
 "somphop":       [(MO + "Owen\\Pants.ccCloth", None), (MO + "Detective\\Shirt.ccCloth", "cotton_cream"), (SH["cas3"], None)],
}
out = []
for job, items in P.items():
    d = os.path.join(JOBS, job)
    name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8"))["name"]
    out.append({"dir": d, "project": os.path.join(d, name + ".ccProject"), "render": os.path.join(d, name + "_v2.png"),
                "items": [{"path": p, "fabric": (make(p, os.path.join(FAB, f + ".png")) if f else None)} for p, f in items]})
json.dump(out, open(os.path.join(JOBS, "redress_luek.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
missing = [i["fabric"] for o in out for i in o["items"] if i["fabric"] and not os.path.exists(i["fabric"])]
print(len(out), "jobs; missing fabrics:", sorted(set(os.path.basename(m) for m in missing)))
