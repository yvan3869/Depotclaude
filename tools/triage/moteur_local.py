"""Redacteur de secours de l'atelier : scenarios de teasers tires de structures toutes faites.

Sert quand le redacteur IA (server/writer) ne repond pas. Meme format de sortie que lui. Les
structures sont suggestives, jamais explicites : tout passe par le regard, le geste lent et la coupe.
Chaque texte existe en anglais et en francais (langue du personnage).
"""

# Chaque structure : titre, pitch, accroche (texte a l'ecran de la premiere seconde), scenes.
# Une scene : (titre, role, image, mouvement, image de fin ou "", texte a l'ecran, voix off).
# {lieu} et {tenue} sont remplaces par un lieu et une tenue du personnage (partie anglaise).
STRUCTURES = [
    {
        "titre": "La coupe au mauvais moment",
        "pitch": "Elle commence un geste lent, regarde l'objectif, et la vidéo coupe juste avant la suite.",
        "accroche": ("Don't blink.", "Ne cligne pas des yeux."),
        "scenes": [
            ("Regard", "accroche", "close-up portrait, {lieu}, {tenue}, looking straight at the camera with a knowing half-smile, soft natural light",
             "She holds the gaze of the camera, then slowly smiles and tilts her head.", "", ("Don't blink.", "Ne cligne pas des yeux."), ""),
            ("Le geste", "montee", "medium shot from the waist up, {lieu}, {tenue}, one hand on the strap at her shoulder, playful look at the camera, soft natural light",
             "She slowly slides the strap down off her shoulder with one finger, eyes on the camera.", "", ("You sure?", "Tu es sûr ?"), ""),
            ("La coupe", "chute", "medium close-up, {lieu}, {tenue}, leaning toward the camera, biting her lower lip, hand reaching toward the lens",
             "She leans toward the camera and reaches her hand to the lens as if to cover it.", "", ("The rest? Not here.", "La suite ? Pas ici."), ""),
        ],
    },
    {
        "titre": "POV : tu arrives trop tôt",
        "pitch": "Vue subjective : on entre, elle n'est pas prête, elle ne s'en excuse pas.",
        "accroche": ("POV: you're early.", "POV : tu arrives en avance."),
        "scenes": [
            ("Surprise", "accroche", "medium shot, {lieu}, {tenue}, turning her head toward the camera over her shoulder with a surprised amused look, soft natural light",
             "She notices the camera, raises her eyebrows, then smiles slowly.", "", ("POV: you're early.", "POV : tu arrives en avance."), ""),
            ("Elle s'approche", "montee", "medium shot, {lieu}, {tenue}, standing facing the camera, hands on her hips, teasing smile",
             "She walks slowly toward the camera, keeping eye contact.", "", ("I wasn't ready.", "Je n'étais pas prête."), ""),
            ("Tout près", "chute", "close-up, {lieu}, {tenue}, very close to the camera, looking up into the lens with a soft smile",
             "She leans in close to the camera and whispers something, then smiles.", "", ("Stay. I'll show you.", "Reste. Je te montre."), ""),
        ],
    },
    {
        "titre": "Trois secondes de trop",
        "pitch": "Elle soutient le regard trois secondes de trop, puis détourne les yeux : le sous-entendu fait tout.",
        "accroche": ("3 seconds. Hold my gaze.", "3 secondes. Soutiens mon regard."),
        "scenes": [
            ("Un", "accroche", "close-up portrait, {lieu}, {tenue}, chin resting on her hand, calm intense look into the camera, soft window light",
             "She looks into the camera without moving, breathing slowly.", "", ("3 seconds. Hold my gaze.", "3 secondes. Soutiens mon regard."), ""),
            ("Deux", "montee", "medium close-up, {lieu}, {tenue}, leaning slightly forward on her elbows, neckline visible, faint smile",
             "She leans slightly forward and bites her lower lip, eyes on the camera.", "", ("You looked down.", "Tu as baissé les yeux."), ""),
            ("Trois", "chute", "medium close-up, {lieu}, {tenue}, looking away with a wide amused smile, hand near her collarbone",
             "She looks away and smiles to herself, then glances back at the camera.", "", ("I saw that.", "J'ai vu."), ""),
        ],
    },
    {
        "titre": "Avant / après la séance",
        "pitch": "Même pièce, deux états : appliquée avant, relâchée après. La suite se passe hors champ.",
        "accroche": ("Before class vs after.", "Avant le cours / après."),
        "scenes": [
            ("Avant", "accroche", "medium shot, {lieu}, {tenue}, standing very straight, hands clasped, serious focused face, bright daylight",
             "She takes a slow deep breath and rolls her shoulders back, focused.", "", ("Before class.", "Avant le cours."), ""),
            ("Après", "montee", "medium shot, {lieu}, {tenue}, sitting on the floor leaning back on her hands, flushed cheeks, relaxed satisfied smile, warm light",
             "She stretches her neck slowly to one side and exhales, smiling at the camera.", "", ("After.", "Après."), ""),
            ("Et ensuite", "chute", "medium close-up, {lieu}, {tenue}, lying on her side propped on one elbow, looking at the camera with a mischievous smile, warm light",
             "She pats the floor next to her with one hand, inviting, eyes on the camera.", "", ("And after after?", "Et après après ?"), ""),
        ],
    },
    {
        "titre": "Le secret",
        "pitch": "Elle a quelque chose à dire, s'approche, et le dit ailleurs.",
        "accroche": ("Can you keep a secret?", "Tu sais garder un secret ?"),
        "scenes": [
            ("La question", "accroche", "medium close-up, {lieu}, {tenue}, finger on her lips in a hush gesture, playful eyes on the camera",
             "She keeps a finger on her lips and slowly smiles behind it.", "", ("Can you keep a secret?", "Tu sais garder un secret ?"), ""),
            ("Elle hésite", "montee", "medium shot, {lieu}, {tenue}, sitting cross-legged, looking down with a shy smile, one hand on her knee",
             "She looks down, laughs softly at herself, then looks back up at the camera.", "", ("Okay. Come closer.", "Bon. Approche."), ""),
            ("Presque", "chute", "close-up, {lieu}, {tenue}, leaning toward the camera, lips slightly parted, about to speak",
             "She leans toward the camera as if to whisper, then stops and smiles.", "", ("Not here. On my page.", "Pas ici. Sur ma page."), ""),
        ],
    },
    {
        "titre": "La tenue du soir",
        "pitch": "Elle demande un avis sur sa tenue. La deuxième option n'est visible qu'ailleurs.",
        "accroche": ("Help me choose.", "Aide-moi à choisir."),
        "scenes": [
            ("Option 1", "accroche", "full body shot, {lieu}, {tenue}, standing with one hand on her hip, questioning look at the camera, soft light",
             "She turns slightly from side to side to show the outfit, then looks at the camera.", "", ("Option 1.", "Option 1."), ""),
            ("Elle doute", "montee", "medium shot from the waist up, {lieu}, {tenue}, adjusting the neckline with both hands, looking down then up",
             "She adjusts her neckline slowly and raises her eyes to the camera with a smile.", "", ("Too much? Not enough?", "Trop ? Pas assez ?"), ""),
            ("Option 2", "chute", "medium close-up, {lieu}, {tenue}, holding the edge of the fabric at her shoulder, teasing look, about to change",
             "She starts to slide the fabric off her shoulder, then stops and winks at the camera.", "", ("Option 2 is on my page.", "L'option 2 est sur ma page."), ""),
        ],
    },
    {
        "titre": "Le réveil",
        "pitch": "Matin lent, draps, premier regard. Elle propose de rester.",
        "accroche": ("Good morning, you.", "Bonjour, toi."),
        "scenes": [
            ("Les yeux", "accroche", "close-up, lying in bed on white sheets, {tenue}, head on the pillow, sleepy eyes opening toward the camera, soft morning light",
             "She opens her eyes slowly, sees the camera and smiles sleepily.", "", ("Good morning, you.", "Bonjour, toi."), ""),
            ("Elle s'étire", "montee", "medium shot from above, lying in bed on white sheets, {tenue}, arms stretched above her head, soft morning light",
             "She stretches slowly in the sheets and arches her back slightly, eyes half closed.", "", ("Five more minutes.", "Encore cinq minutes."), ""),
            ("Reste", "chute", "medium close-up, sitting up in bed, {tenue}, sheet held against her chest, hair messy, inviting smile at the camera",
             "She lifts the edge of the sheet with one hand, inviting, and smiles.", "", ("Stay. I'm not getting up.", "Reste. Je ne me lève pas."), ""),
        ],
    },
    {
        "titre": "Ce que je ne poste pas",
        "pitch": "Elle montre ce qu'elle a le droit de publier, et dit clairement où se trouve le reste.",
        "accroche": ("What I can post here:", "Ce que je peux poster ici :"),
        "scenes": [
            ("Ici", "accroche", "medium shot, {lieu}, {tenue}, arms crossed, innocent smile at the camera, bright daylight",
             "She shrugs with an innocent smile and looks at the camera.", "", ("What I can post here:", "Ce que je peux poster ici :"), ""),
            ("Là-bas", "montee", "medium close-up, {lieu}, {tenue}, leaning against the wall, head tilted, looking at the camera through her lashes, warm low light",
             "She runs her fingers slowly along her collarbone, eyes on the camera.", "", ("What I post there:", "Ce que je poste là-bas :"), ""),
            ("Le doigt", "chute", "close-up, {lieu}, {tenue}, smiling, index finger pointing up toward the top of the frame",
             "She points upward with one finger and raises her eyebrows, smiling.", "", ("Link's up there.", "Le lien est là-haut."), ""),
        ],
    },
]


def _en(x):
    return str(x).split("|")[-1].strip()


def _txt(pair, fr):
    return pair[1] if fr else pair[0]


def scenario(perso, rng, structure=None, n=None):
    s = structure or rng.choice(STRUCTURES)
    fr = str(perso.get("langue", "en")).lower().startswith("fr")
    lieu = _en(rng.choice(perso.get("lieux") or ["in her bright apartment"]))
    tenue = _en(rng.choice(perso.get("tenues") or ["a low-cut tank top"]))
    scenes = []
    for titre, role, still, motion, end, texte, voix in s["scenes"][: n or 9]:
        scenes.append({"titre": titre, "role": role, "still": still.format(lieu=lieu, tenue=tenue), "motion": motion,
                       "end_edit": end, "texte": _txt(texte, fr), "voix": voix, "tattoos": True})
    ecr = perso.get("ecriture") or {}
    cta = ecr.get("cta") or ("The rest is on my page." if not fr else "La suite est sur ma page.")
    return {"titre": s["titre"], "pitch": s["pitch"], "accroche": _txt(s["accroche"], fr), "scenes": scenes,
            "legende": f"{_txt(s['accroche'], fr)} {cta}".strip(), "cta": cta, "hashtags": ecr.get("hashtags", "")}


def idees(perso, rng, n=8):
    pool = STRUCTURES[:]
    rng.shuffle(pool)
    fr = str(perso.get("langue", "en")).lower().startswith("fr")
    return [{"titre": s["titre"], "pitch": s["pitch"], "accroche": _txt(s["accroche"], fr)} for s in pool[:n]]


def par_titre(titre):
    return next((s for s in STRUCTURES if s["titre"] == titre), None)
