"""Compact 240x135 collection view. Uses installed portraits, never mutates state."""
from PIL import Image, ImageDraw, ImageFont
from scripts.content_loader import definition_for


def render_collection(build_dir, session):
    frame = Image.new("RGB", (240, 135), (18, 24, 26))
    draw = ImageDraw.Draw(frame)
    font = ImageFont.load_default(size=11)
    small = ImageFont.load_default(size=9)
    collection = session.collection
    count = len(collection.slots) if collection is not None else 1
    draw.rectangle((0, 0, 239, 23), fill=(34, 59, 58))
    titles = {"enable": "COLECCION", "list": "COLECCION", "founder": "NUEVO HUEVO",
              "detail": "MASCOTA", "activate": "CAMBIAR MASCOTA", "pairs": "ELEGIR PADRES",
              "breed": "REPRODUCCION", "preferences": "PREFERENCIAS"}
    draw.text((8, 6), titles[session.page], font=font, fill=(255, 255, 255))
    draw.text((230, 6), "%d/4" % count, anchor="ra", font=font, fill=(249, 220, 100))
    if session.page == "preferences":
        pet = collection.pet_at(session.target)
        if pet._learning is not None:
            domains = ((0, "ENTRENO", ("ATAQUE", "DEFENSA", "VELOCIDAD", "VIDA", "MP", "MENTE")),
                       (1, "ARENA", ("GOLPE", "LLAMA", "GUARDIA", "RAFAGA", "INFERNO")),
                       (2, "VIAJE", ("PATIO", "JORNADA", "NOCHE")))
            for row, (domain, name, labels) in enumerate(domains):
                choice = pet.learning.choose(domain, 0, (1 << len(labels)) - 1, 0)
                observed = any(pet.learning.estimate(domain, 0, a)[1] for a in range(len(labels)))
                inherited = any(pet.learning.estimate(domain, 0, a).bias for a in range(len(labels)))
                preference = labels[choice] if observed or inherited else "SIN DATOS"
                if inherited and not observed:
                    preference += " (HEREDADA)"
                draw.text((10, 32 + row * 20), name + ": " + preference,
                          font=font, fill=(150, 225, 215))
        else:
            draw.text((10, 34), "SIN EXPERIENCIAS", font=font, fill=(150, 225, 215))
        draw.text((10, 99), "VOLVER", font=font, fill=(249, 220, 100))
    else:
        choices = session.choices()
        start = min(max(0, session.index - 1), max(0, len(choices) - 3))
        for row, index in enumerate(range(start, min(start + 3, len(choices)))):
            y = 28 + row * 27
            selected = session.index == index
            draw.rectangle((4, y, 235, y + 24), fill=(52, 68, 67) if selected else (18, 24, 26))
            if selected:
                draw.line((4, y, 4, y + 24), fill=(249, 220, 100), width=3)
            x = 12
            if session.page == "list" and index < count:
                role = collection.slots[index]["pet"]["species"]
                path = build_dir / definition_for(build_dir).stage(role)["portrait"].lstrip("/")
                with Image.open(path) as original:
                    icon = original.convert("RGBA")
                    if original.mode == "P":
                        icon.putalpha(original.point([0] + [255] * 255, mode="L"))
                    icon.thumbnail((22, 22), Image.Resampling.NEAREST)
                    frame.paste(icon, (10, y + 1), icon)
                x = 38
            draw.text((x, y + 6), choices[index], font=font, fill=(255, 255, 255))
    if session.message:
        draw.rectangle((0, 113, 239, 134), fill=(18, 24, 26))
        draw.text((8, 119), session.message, font=small, fill=(255, 186, 133))
    return frame
