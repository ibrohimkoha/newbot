from routers.database.models import Anime


async def response_for_anime(anime: Anime):
        name = f"🏷 𝗡𝗼𝗺𝗶:<b>{anime.title}</b>"
        genre = f"🎭 𝗝𝗮𝗻𝗿: <i>{anime.genre}</i>"
        episodes = f"🎞 𝗤𝗶𝘀𝗺: <code>{anime.count_episode}</code>"
        code = f"🆔 𝗞𝗼𝗱: <code>{anime.unique_id}</code>"
        status = f"📅 𝗛𝗼𝗹𝗮𝘁𝗶: <i>{anime.status}</i>"
        release_date = f"📅 𝗖𝗵𝗶𝗾𝗮𝗿𝗶𝗹𝗶𝘀𝗵𝗶: <i>{anime.release_date}</i>" if anime.release_date else ""
        end_date = f"📅 𝗧𝘂𝗴𝗮𝘀𝗵 𝘀𝗮𝗻𝗮𝘀𝗶: <i>{anime.end_date}</i>" if anime.end_date else ""
        studio = f"🏢 𝗦𝘁𝘂𝗱𝗶𝗼: <i>{anime.studio}</i>" if anime.studio else ""
        rating = f"⭐ 𝗥𝗲𝘆𝘁𝗶𝗻𝗴: <i>{anime.rating}</i>" if anime.rating else ""
        score = f"💯 𝗕𝗮𝗵𝗼: <i>{anime.score}</i>" if anime.score else ""

        return (
            "╭━━━⌈ 𝗔𝗡𝗜𝗠𝗘 𝗠𝗔’𝗟𝗨𝗠𝗢𝗧𝗜 ⌋━━━╮\n"
            f"┃ {name}\n"
            f"┃ {genre}\n"
            f"┃ {episodes}\n"
            f"┃ {code}\n"
            # f"┃ {status}\n"
            # f"┃ {release_date}\n"
            # f"┃ {end_date}\n"
            # f"┃ {studio}\n"
            # f"┃ {rating}\n"
            # f"┃ {score}\n"
            "╰━━━━━━━━━━━━━━━━━━━━━━━╯"
        )


async def response_for_anime_for_inline_mode(anime: Anime):
    name = f"🏷 𝗡𝗼𝗺𝗶: {anime.title}"
    genre = f"🎭 𝗝𝗮𝗻𝗿: {anime.genre}"
    episodes = f"🎞 𝗤𝗶𝘀𝗺: {anime.count_episode}"
    status = f"📅 𝗛𝗼𝗹𝗮𝘁𝗶: {anime.status}"
    release_date = f"📅 𝗖𝗵𝗶𝗾𝗮𝗿𝗶𝗹𝗶𝘀𝗵𝗶: {anime.release_date}" if anime.release_date else ""
    end_date = f"📅 𝗧𝘂𝗴𝗮𝘀𝗵 𝘀𝗮𝗻𝗮𝘀𝗶: {anime.end_date}" if anime.end_date else ""
    studio = f"🏢 𝗦𝘁𝘂𝗱𝗶𝗼: {anime.studio}" if anime.studio else ""
    rating = f"⭐ 𝗥𝗲𝘆𝘁𝗶𝗻𝗴: {anime.rating}" if anime.rating else ""
    score = f"💯 𝗕𝗮𝗵𝗼: {anime.score}" if anime.score else ""

    return (
        f"┃ {genre}\n"
        f"┃ {episodes}\n"
        # f"┃ {status}\n"
        # f"┃ {release_date}\n"
        # f"┃ {end_date}\n"
        # f"┃ {studio}\n"
        # f"┃ {rating}\n"
        # f"┃ {score}\n"
        "╰━━━━━━━━━━━━━━━━━━━━━━━╯"
    )

def generate_anime_list_text(animes, page, total_pages):
    lines = [f"📄 Sahifa {page}/{total_pages}\n"]
    for i, anime in enumerate(animes, start=1):
        lines.append(f"{i}. <b>{anime.title}</b> — <code>{anime.unique_id}</code>")
    return "\n".join(lines)
