import { useState } from "react";

interface Props {
  onSearch: (q: string) => void;
  placeholder?: string;
}

export default function SearchBar({ onSearch, placeholder = "Search movies or ask for recommendations..." }: Props) {
  const [q, setQ] = useState("");
  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!q.trim()) return;
    onSearch(q.trim());
  };
  return (
    <form onSubmit={onSubmit} className="flex gap-2 items-center mb-6">
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder={placeholder}
        className="flex-1 input input-bordered"
      />
      <button className="btn btn-primary" type="submit">Search</button>
    </form>
  );
}
