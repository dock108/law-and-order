'use client';

import React from 'react';
import { useRouter } from 'next/navigation';

export default function AddClientButton() {
    const router = useRouter();

    const handleClick = () => {
        router.push('/new-client');
    };

    return (
        <button 
            type="button"
            onClick={handleClick}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out cursor-pointer shadow-md"
        >
            Add New Client
        </button>
    );
} 