"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function Home() {
  const router = useRouter();
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Implement check for logged-in user using Supabase client
    // For demo, redirect to /login or /dashboard
    router.push("/login");
  }, []);

  return <div>Loading...</div>;
}
