"use client";

import { useState } from "react";
import { createClientComponentClient } from "@supabase/auth-helpers-nextjs";

export default function Login() {
  const supabase = createClientComponentClient();
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");

  const handleLogin = async () => {
    const { error } = await supabase.auth.signInWithOtp({ email });
    if (error) setMessage(error.message);
    else setMessage("Check your email for login link");
  };

  return (
    <div className="p-6">
      <h1 className="text-xl font-bold mb-4">Login / Signup</h1>
      <input
        type="email"
        placeholder="your email"
        className="border p-2 mb-4 w-full"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <button
        className="bg-blue-600 text-white px-4 py-2 rounded"
        onClick={handleLogin}
      >
        Send Magic Link
      </button>
      {message && <p className="mt-4">{message}</p>}
    </div>
  );
}
