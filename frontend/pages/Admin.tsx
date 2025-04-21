// Admin.tsx
import React, { useEffect, useState } from 'react';
import {data, useNavigate} from 'react-router-dom';
import api from "../src/api.ts";

const Admin = () => {
    const [userData, setUserData] = useState(null);
    const navigate = useNavigate();
    const handleLogout = async () => {
        try {
            await api.post('/api/logout/'); // Backendga logout haqida xabar beriladi
        } catch (error) {
            console.error('Logout xatolik:', error);
        } finally {
            localStorage.removeItem('access_token');
            navigate('/login'); // login sahifaga qaytarish
        }
    };
    const handleAnimeAdd = async () => {
        navigate('/anime-add')
    }
    useEffect(() => {
        const token = localStorage.getItem('access_token');

        if (!token) {
            // Agar token bo'lmasa, login sahifasiga qaytaramiz
            navigate('/login');
        } else {
            // Token bilan foydalanuvchi ma'lumotlarini olish
            // Bu yerda siz o'zingizning API-dan ma'lumotni olishni qo'shishingiz mumkin
            api.get('/api/get-admin-data')
                .then(res => {
                    setUserData(res.data);
                })
                .catch(err => console.error('Xatolik:', err));

        }
    }, [navigate]);

    return (
        <div>
            <h2>Admin Panel</h2>
            {userData ? (
                <div>
                    <h3>Salom, {userData.full_name}!</h3>
                    <h3>Muvaffaqiyatli ro'yhatdan o'tdingiz: {userData.telegram_id}</h3>
                    <button onClick={handleAnimeAdd}>Anime Add</button>
                    <button onClick={handleLogout}>Logout</button>
                </div>
            ) : (
                <p>Loading...</p>
            )}
        </div>
    );
};

export default Admin;
