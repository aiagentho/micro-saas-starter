"use client";

import { useState, useEffect } from "react";
import { createClientComponentClient } from "@supabase/auth-helpers-nextjs";

export default function Dashboard() {
  const supabase = createClientComponentClient();
  const [credits, setCredits] = useState(0);
  const [usage, setUsage] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      const user = supabase.auth.getUser();
      const token = (await supabase.auth.getSession()).data?.session?.access_token;

      // Fetch credits
      const resCredits = await fetch("http://localhost:8000/api/credits", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const creditsJson = await resCredits.json();
      setCredits(creditsJson.credits);

      // Fetch usage
      const resUsage = await fetch("http://localhost:8000/api/usage", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const usageJson = await resUsage.json();
      setUsage(usageJson.usage);
    };

    fetchData();
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <p className="mt-2">Your Credits: {credits}</p>
      <h2 className="mt-4 font-semibold">Usage History</h2>
      <ul>
        {usage.map((u, i) => (
          <li key={i}>
            [{new Date(u.timestamp).toLocaleString()}] {u.action} - {u.details}
          </li>
        ))}
      </ul>
      {/* TODO: Add Stripe checkout button here */}
    </div>
  );
}
