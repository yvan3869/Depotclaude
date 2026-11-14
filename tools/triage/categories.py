"""Categories de LoRA et familles de modeles : ce que le hub classe, ce que l'atelier autorise a chaque temps.

Une LoRA n'est proposee et acceptee dans une scene qu'a partir du temps de sa categorie. Une LoRA sans categorie
(inscrite a la main avant le hub) est traitee comme reservee : elle n'est admise qu'aux temps 3 et 4.
"""

# cle : (intitule, premier temps ou elle est admise, ce qu'elle apporte)
CATS = {
    "realisme": ("Réalisme", 1, "Rendu photo crédible : grain, optique, défauts d'une vraie photo."),
    "smartphone": ("Smartphone, photo amateur", 1, "Image prise au téléphone, cadrage et lumière ordinaires."),
    "peau": ("Peau et détails", 1, "Texture de peau, mains, yeux, cheveux."),
    "lumiere": ("Lumière", 1, "Éclairage : fenêtre, flash, soir, néon."),
    "pose": ("Pose et cadrage", 1, "Selfie, miroir, plongée, cadrages tous publics."),
    "mouvement": ("Bougé naturel", 1, "Vidéo : mouvement du corps, de la caméra tenue à la main, respiration."),
    "vitesse": ("Vitesse", 1, "Calcul en moins de pas, donc moins cher."),
    "tenue": ("Tenue, lingerie", 2, "Vêtements, lingerie, maillot."),
    "corps": ("Corps", 2, "Silhouette, formes, proportions."),
    "nu": ("Nu", 3, "Nudité sans acte."),
    "porno": ("Porno", 4, "Actes explicites."),
    "autre": ("Autre", 3, "Non classée : admise aux temps 3 et 4 tant qu'elle n'a pas de catégorie."),
}

# Familles de modeles de base du projet : une LoRA ne fonctionne qu'avec sa famille.
FAMILLES = {
    "zimage": {"label": "Z-Image Turbo", "usage": "images", "civitai": ["ZImageTurbo", "ZImageBase"],
               "hf": ["Tongyi-MAI/Z-Image-Turbo", "Tongyi-MAI/Z-Image"]},
    "wan22": {"label": "Wan 2.2 image vers vidéo", "usage": "clips", "civitai": ["Wan Video 2.2 I2V-A14B"],
              "hf": ["Wan-AI/Wan2.2-I2V-A14B"]},
}


def temps_min(cat):
    return CATS.get(cat or "autre", CATS["autre"])[1]


def reservee(cat):
    """Vrai si la LoRA releve du proprietaire seul (nu, porno, non classee) : une scene qui la porte n'est jamais
    envoyee au redacteur, au relecteur ni a l'analyste."""
    return temps_min(cat) >= 3
