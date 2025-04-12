


async def response_for_anime(name, genre, count_episodes, unique_id):
    name = f"🎬 Anime nomi: <b>{name}</b>"
    genre = f"📝 Janri: <i>{genre}</i>"
    episodes = f"📺 Qismlar soni: <code>{count_episodes}</code>"
    code = f"🆔 Anime kodi: <code>{unique_id}</code>"

    return (
        "╭━━━•❁🔹❁•━━━╮\n"
        f"{name}\n"
        f"{genre}\n"
        f"{episodes}\n"
        f"{code}\n"
        "╰━━━•❁⛩❁•━━━╯"
    )

def generate_anime_list_text(animes, page, total_pages):
    lines = [f"📄 Sahifa {page}/{total_pages}\n"]
    for i, anime in enumerate(animes, start=1):
        lines.append(f"{i}. <b>{anime.name}</b> — <code>{anime.unique_id}</code>")
    return "\n".join(lines)
