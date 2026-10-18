# Fill job.json for every "เลือกนักมักได้แร่" job: body, outfit (proven items only), hair (random, no repeats).
import json, os, shutil, subprocess, sys

P = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio")
JOBS = os.path.join(P, "snapgen_data", "cc5_jobs")
OUT = os.path.join(os.environ["USERPROFILE"], "Desktop", "เลือกนักมักได้แร่")
R = "G:\\คอมพิวเตอร์เครื่องอื่นๆ\\คอมพิวเตอร์ของฉัน\\โมชั่น\\Prop ของใช้ต่างๆ\\เสื้อผ้า-ทรงผม\\"
MO, RC = R + "!Converted STUFFS\\Male Outfits\\", R + "Reallusion Custom\\Cloth\\"
# outfits = [lower, upper, shoes]; all items already worn on a finished character
F = [[RC + "Others\\กางเกงขายาว.ccCloth", RC + "Shirts\\Shirts(1).ccCloth", MO + "Dash\\Shoes 01.ccShoes"],
     [RC + "Pants\\Pants(28).ccCloth", RC + "Shirts\\Professional Outfit\\Open collar short sleeves shirt\\Open_collar_short_sleeves_shirt_C.ccCloth", MO + "Oahu\\Flip Flops.ccShoes"],
     [RC + "Others\\กางเกงขายาว.ccCloth", RC + "Shirts\\Professional Outfit\\Close collar short sleeves shirt\\Close_collar_short_sleeves_shirt_A.ccCloth", MO + "Oahu\\Sandals 02.ccShoes"],
     [RC + "Pants\\Pants(28).ccCloth", RC + "Shirts\\Shirts(1).ccCloth", MO + "Oahu\\Flip Flops.ccShoes"]]
M = [[MO + "Blood Hunter\\Pants.ccCloth", MO + "Lift & Haul\\Shirt 03.ccCloth", MO + "Dash\\Shoes 01.ccShoes"],
     [MO + "Owen\\Pants.ccCloth", RC + "Shirts\\เสื้อชาย.ccCloth", MO + "Oahu\\Flip Flops.ccShoes"],
     [MO + "Billybob\\Pants.ccCloth", RC + "Shirts\\Shirts(22).ccCloth", MO + "Casual 01\\Shoes.ccShoes"],
     [MO + "Casual 04\\Pants.ccCloth", MO + "Detective\\Shirt.ccCloth", MO + "Casual 03\\Shoes.ccShoes"],
     [MO + "Old\\Pants.ccCloth", MO + "Streetstyle\\Shirt 01.ccCloth", MO + "Oahu\\Sandals 02.ccShoes"]]
KID = [[RC + "Pants\\Pants(4).ccCloth", R + "Reallusion Custom\\Cloth\\Others\\Others(8).ccCloth", MO + "Oahu\\Flip Flops.ccShoes"],
       [MO + "Leisure\\Shorts.ccCloth", R + "Reallusion Custom\\Cloth\\Others\\Others(8).ccCloth", MO + "Oahu\\Flip Flops.ccShoes"]]
# job: (sex, age_group, outfit list, index)
PLAN = {
 "wina_young": ("female", "adult", F, 0), "wina_58": ("female", "middle", F, 1),
 "lamduan": ("female", "adult", F, 1), "wandee": ("female", "adult", F, 2),
 "lamduan_old": ("female", "old", F, 3), "wandee_old": ("female", "old", F, 0),
 "son_child": ("male", "child", KID, 1), "son_adult": ("male", "adult", M, 0),
 "daughter_child": ("female", "child", KID, 0), "daughter_adult": ("female", "adult", F, 3),
 "father": ("male", "middle", M, 4), "mother": ("female", "middle", F, 2),
 "soldier": ("male", "adult", M, 1), "somchai": ("male", "adult", M, 3),
 "soldier_old": ("male", "old", M, 2), "somchai_old": ("male", "old", M, 0),
 "pranee": ("female", "adult", F, 0), "pranee_husband": ("male", "adult", M, 2),
 "pranee_58": ("female", "middle", F, 3), "rice_farmer": ("male", "adult", M, 4),
 "chicken_farmer": ("male", "adult", M, 1), "nai_chai": ("male", "adult", M, 3),
 "mill_daughter": ("female", "adult", F, 2), "somphop": ("male", "adult", M, 0),
 "ratree": ("female", "adult", F, 1), "airport_officer": ("male", "adult", M, 3),
}
NAMES = {"wina_young": "Wina"}
ready = []
for job, (sex, age, pool, i) in PLAN.items():
    d = os.path.join(JOBS, job)
    if not os.path.exists(os.path.join(d, "face.png")):
        print("no face yet:", job); continue
    meta = os.path.join(d, "meta.json")
    name = NAMES.get(job) or json.load(open(meta, encoding="utf-8"))["name"]
    items = []
    for src, n in zip(pool[i], ("pants", "shirt", "shoes")):
        dst = n + os.path.splitext(src)[1]
        if not os.path.exists(os.path.join(d, dst)):
            shutil.copy(src, os.path.join(d, dst))
        items.append(dst)
    jf = os.path.join(d, "job.json")
    old = json.load(open(jf, encoding="utf-8")) if os.path.exists(jf) else {}
    job_data = {"name": name, "face": "face.png", "body": "child" if age == "child" else "neutral",
                "skip_headshot": False, "items": items, "out_dir": OUT}
    if "hair.rlHair" in old.get("items", []):
        job_data["items"] = ["hair.rlHair"] + items; job_data["hair_rgb"] = old.get("hair_rgb", [18, 16, 15]); job_data["hair_source"] = old.get("hair_source", "")
    json.dump(job_data, open(jf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if "hair.rlHair" not in job_data["items"]:
        subprocess.run([sys.executable, os.path.join(P, "snapgen_modules", "cc5", "cc5_pick_hair.py"), d, sex, age], check=True)
    ready.append(d)
open(os.path.join(JOBS, "batch_luek.txt"), "w", encoding="utf-8").write("\n".join(ready))
print(len(ready), "jobs ready")
