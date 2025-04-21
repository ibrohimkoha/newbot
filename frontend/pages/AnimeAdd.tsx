import api from "../src/api";
import {useState, useEffect} from "react";

const AnimeAdd = () => {
    const [title, setTitle] = useState('');
    const [original_title, setOriginal_title]= useState('');
    const [description, setDescription] = useState('');
    const [genre, setGenre] = useState('');
    const [type, setType] = useState<string | null>(null); // Default qiymat null
    const [status, setStatus] = useState<string | null>(null);
    const [release_date, setReleaseDate] = useState("");
    const [end_date, setEndDate] = useState("");
    const [studio, setStudio] = useState("");
    const [rating, setRating] = useState("");
    const [score, setScore] = useState(0);
    const [count_episode, setCountEpisode] = useState(0);
    const [unique_id, setUniqueId] = useState("");
    const [image, setImage] = useState<File | null>(null);
    const [uploadedUrl, setUploadedUrl] = useState<string>("");
    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setImage(e.target.files[0]);
        }
    };

    const uploadToImgBB = async () => {
        if (!image) return;

        const formData = new FormData();
        formData.append("image", image);

        const API_KEY = "53f03bd01bc945cd2ca1998aaceeae4d";

        try {
            const res = await fetch(`https://api.imgbb.com/1/upload?key=${API_KEY}`, {
                method: "POST",
                body: formData
            });

            const data = await res.json();
            setUploadedUrl(data.data.url);
        } catch (err) {
            console.error("Xatolik:", err);
        }
    };

    useEffect(() => {
        const fetchData = async () => {
            try {
                const typeRes = await api.get("api/get-anime-add-types/");
                setType(typeRes.data); // `type`ni saqlash
                const statusRes = await api.get("api/get-anime-status/");
                setStatus(statusRes.data); // `status`ni saqlash
            } catch (error) {
                console.error("Xatolik:", error);
            }
        };
        fetchData();
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        // Ma'lumotlarni yig'ish
        const animeData = {
            title,
            original_title,
            description,
            genre,
            type,
            status,
            release_date,
            end_date,
            studio,
            rating,
            score,
            count_episode,
            unique_id,
            image_url: uploadedUrl || "", // Agar rasm URL bo'lsa, uni qo'shamiz
        };
        console.log(animeData)
        // Ma'lumotlarni API'ga yuborish
        try {
            const response = await fetch("http://localhost:8000/api/create-anime", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(animeData),
            });

            const result = await response.json();
            console.log("Yuborish muvaffaqiyatli:", result);
        } catch (error) {
            console.error("Xatolik yuz berdi:", error);
        }
    };

    return (
        <div>
            <h1>Anime Qo'shish</h1>
            <form onSubmit={handleSubmit}>
                <div>
                    <label htmlFor="title">Anime nomi:</label>
                    <input
                        type="text"
                        id="title"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                    />
                </div>
                <div>
                    <label htmlFor="original_title">Original nomi:</label>
                    <input
                        type="text"
                        id="original_title"
                        value={original_title}
                        onChange={(e) => setOriginal_title(e.target.value)}
                    />
                </div>
                <div>
                    <label htmlFor="description">Tavsifi:</label>
                    <textarea
                        id="description"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                    />
                </div>
                <div>
                    <label htmlFor="genre">Janri:</label>
                    <input
                        type="text"
                        id="genre"
                        value={genre}
                        onChange={(e) => setGenre(e.target.value)}
                    />
                </div>
                <div>
                    <label htmlFor="type">Turi:</label>
                    <select
                        id="type"
                        value={type}
                        onChange={(e) => setType(e.target.value)}
                    >
                        <option value="TV">TV</option>
                        <option value="Movie">Movie</option>
                        <option value="OVA">OVA</option>
                        <option value="ONA">ONA</option>
                        <option value="Special">Special</option>
                    </select>
                </div>
                <div>
                    <label htmlFor="status">Status:</label>
                    <select
                        id="status"
                        value={status}
                        onChange={(e) => setStatus(e.target.value)}
                    >
                        <option value="Upcoming">Upcoming</option>
                        <option value="Ongoing">Ongoing</option>
                        <option value="Completed">Completed</option>
                    </select>
                </div>
                <div>
                    <label htmlFor="release_date">Chiqarilgan sana:</label>
                    <input
                        type="date"
                        id="release_date"
                        value={release_date}
                        onChange={(e) => setReleaseDate(e.target.value)}
                    />
                </div>
                <div>
                    <label htmlFor="end_date">Yakunlanish sanasi:</label>
                    <input
                        type="date"
                        id="end_date"
                        value={end_date}
                        onChange={(e) => setEndDate(e.target.value)}
                    />
                </div>
                <div>
                    <label htmlFor="studio">Studiya:</label>
                    <input
                        type="text"
                        id="studio"
                        value={studio}
                        onChange={(e) => setStudio(e.target.value)}
                    />
                </div>
                <div>
                    <label htmlFor="rating">Reytingi:</label>
                    <input
                        type="text"
                        id="rating"
                        value={rating}
                        onChange={(e) => setRating(e.target.value)}
                    />
                </div>
                <div>
                    <label htmlFor="score">Ball:</label>
                    <input
                        type="number"
                        id="score"
                        value={score}
                        onChange={(e) => setScore(Number(e.target.value))}
                    />
                </div>
                <div>
                    <label htmlFor="count_episode">Epizodlar soni:</label>
                    <input
                        type="number"
                        id="count_episode"
                        value={count_episode}
                        onChange={(e) => setCountEpisode(Number(e.target.value))}
                    />
                </div>
                <div>
                    <label htmlFor="unique_id">Unique ID:</label>
                    <input
                        type="text"
                        id="unique_id"
                        value={unique_id}
                        onChange={(e) => setUniqueId(Number(e.target.value))}
                    />
                </div>
                <div>
                    <label htmlFor="image">Rasm tanlash:</label>
                    <input
                        type="file"
                        id="image"
                        accept="image/*"
                        onChange={handleFileChange}
                    />
                    <button type="button" onClick={uploadToImgBB}>
                        Rasmni yuklash
                    </button>
                    {uploadedUrl && (
                        <div>
                            <h3>Yuklangan rasm:</h3>
                            <img src={uploadedUrl} alt="Uploaded" />
                        </div>
                    )}
                </div>
                <div>
                    <button type="submit">Qo'shish</button>
                </div>
            </form>
        </div>
    );
};

export default AnimeAdd;